"""WebSocket 连接管理（进程内连接表 + Redis pub/sub 跨进程广播）。

单 worker 部署时所有连接都在同一进程；多 worker 部署时，推送消息必须先经 Redis
分发给各进程的订阅者，否则收件人连在其它 worker 上时消息会静默丢失。
"""

import asyncio
import json
import uuid
from typing import Any

from fastapi import WebSocket
from redis.asyncio import Redis

from app.core.logger import logger

# 本进程实例令牌：消息经 Redis 广播后会回到发送方进程，用它识别并跳过，避免重复投递
_PROCESS_TOKEN = uuid.uuid4().hex

# 全部 manager 注册表：应用关闭时统一停止订阅协程
_managers: list["WSConnectionManager"] = []


def stop_ws_relays() -> None:
    """应用关闭时停止所有跨进程订阅协程（幂等）。"""
    for manager in _managers:
        manager.stop_listener()


class WSConnectionManager:
    """维护 user_id -> 连接集合，支持同一用户多标签页；发送失败的连接立即剔除。

    推送策略 = 本进程直发 + Redis publish；订阅协程负责把其它 worker 广播来的消息
    投递给本进程命中目标（all / user_id 列表）的连接。Redis 不可用时自动退化为
    仅本进程直发（等价于旧的单机行为）。

    is_online / online_count 反映的是本进程连接——在线人数跨 worker 的全局统计
    不在本类职责内，由各业务方按需自行汇总。
    """

    def __init__(self, channel: str) -> None:
        """
        参数:
        - channel (str): 通道名，同时用于日志区分与 Redis 频道名（chat / transfer）。
        """
        self._channel = channel
        self._connections: dict[int, set[WebSocket]] = {}
        self._redis: Redis | None = None
        self._listener: asyncio.Task | None = None
        _managers.append(self)

    # ------------------------------------------------------------------ #
    # 连接生命周期
    # ------------------------------------------------------------------ #
    async def connect(self, user_id: int, ws: WebSocket, subprotocol: str | None = None) -> None:
        """接受握手并登记连接。

        客户端通过 Sec-WebSocket-Protocol 携带令牌时，必须回显其提供的子协议，否则浏览器会判定握手失败。
        首个连接到达时懒启动跨进程订阅（幂等），此后本进程才能收到其它 worker 的推送。
        """
        await ws.accept(subprotocol=subprotocol)
        self._connections.setdefault(user_id, set()).add(ws)
        redis = getattr(ws.app.state, "redis", None)
        if redis is not None:
            self._start_listener(redis)

    def disconnect(self, user_id: int, ws: WebSocket) -> None:
        """注销连接（幂等）"""
        conns = self._connections.get(user_id)
        if conns is None:
            return
        conns.discard(ws)
        if not conns:
            self._connections.pop(user_id, None)

    def is_online(self, user_id: int) -> bool:
        """用户是否在线（本进程视角）"""
        return bool(self._connections.get(user_id))

    def online_count(self) -> int:
        """在线用户数（本进程视角）"""
        return len(self._connections)

    def all_connections(self) -> list[WebSocket]:
        """全部连接快照"""
        return [ws for conns in self._connections.values() for ws in conns]

    # ------------------------------------------------------------------ #
    # 推送
    # ------------------------------------------------------------------ #
    async def send_to_user(self, user_id: int | None, data: dict[str, Any]) -> None:
        """向指定用户的所有连接推送；单个连接异常不影响其余连接。"""
        if user_id is None:
            return
        await self._relay({"users": [user_id]}, data)

    async def send_to_users(self, user_ids: list[int], data: dict[str, Any]) -> None:
        """向多个用户推送"""
        ids = sorted(set(user_ids))
        if not ids:
            return
        await self._relay({"users": ids}, data)

    async def broadcast(self, data: dict[str, Any]) -> None:
        """向全部连接广播"""
        await self._relay({"all": True}, data)

    @property
    def _channel_name(self) -> str:
        return f"fastapiadmin:ws:{self._channel}"

    async def _relay(self, target: dict[str, Any], data: dict[str, Any]) -> None:
        """推送一条消息：先投本进程命中连接，再发布到 Redis 供其它 worker 投递。

        回环到本进程的那份由订阅协程依据 _PROCESS_TOKEN 跳过，因此不会重复。
        """
        await self._dispatch_local(target, data)
        if self._redis is None:
            return
        try:
            message = json.dumps({"sender": _PROCESS_TOKEN, "target": target, "data": data}, ensure_ascii=False)
            await self._redis.publish(self._channel_name, message)
        except Exception as e:
            logger.warning("{} 通道跨进程广播失败（本进程已尽力投递）: {}", self._channel, e)

    async def _dispatch_local(self, target: dict[str, Any], data: Any) -> None:
        """把消息投给本进程命中 target（{"all": true} 或 {"users": [...]}）的连接。"""
        if target.get("all"):
            pairs = [(None, ws) for ws in self.all_connections()]
        else:
            pairs = [
                (uid, ws)
                for uid in target.get("users", [])
                for ws in list(self._connections.get(uid, ()))
            ]
        for user_id, ws in pairs:
            await self._send(user_id, ws, data)

    # ------------------------------------------------------------------ #
    # 跨进程订阅
    # ------------------------------------------------------------------ #
    def _start_listener(self, redis: Redis) -> None:
        """启动跨进程订阅协程（幂等；异常退出后由下一次 connect 重启）。"""
        if self._redis is None:
            self._redis = redis
        if self._listener is not None and not self._listener.done():
            return
        self._listener = asyncio.create_task(self._listen(redis), name=f"ws-relay-{self._channel}")

    def stop_listener(self) -> None:
        """停止本 manager 的跨进程订阅协程。"""
        if self._listener is not None and not self._listener.done():
            self._listener.cancel()
            self._listener = None

    async def _listen(self, redis: Redis) -> None:
        """订阅 Redis 频道：把其它 worker 广播的消息投递给本进程命中目标的连接。"""
        pubsub = redis.pubsub()
        channel = self._channel_name
        try:
            await pubsub.subscribe(channel)
            logger.info("{} 通道跨进程监听已启动: {}", self._channel, channel)
            async for raw in pubsub.listen():
                if raw.get("type") != "message":
                    continue
                try:
                    payload = json.loads(raw["data"])
                except (TypeError, ValueError):
                    logger.warning("{} 频道收到无法解析的消息，已跳过", channel)
                    continue
                if payload.get("sender") == _PROCESS_TOKEN:
                    continue
                await self._dispatch_local(payload.get("target") or {}, payload.get("data"))
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("{} 通道跨进程监听中断: {}", channel, e)
        finally:
            try:
                await pubsub.unsubscribe(channel)
            finally:
                await pubsub.close()

    async def _send(self, user_id: int | None, ws: WebSocket, data: dict[str, Any]) -> None:
        try:
            await ws.send_json(data)
        except Exception as e:
            logger.warning("{} 通道推送失败，已剔除连接: user={}, err={}", self._channel, user_id, e)
            if user_id is not None:
                self.disconnect(user_id, ws)
