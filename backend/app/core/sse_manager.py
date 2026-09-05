"""SSE 连接管理（进程内连接表 + Redis pub/sub 跨进程广播）。

每个 SSE 连接对应一个有界 asyncio.Queue：业务方推送即入队，端点生成器消费队列
写响应流。队列打满说明消费端已死或网络阻塞，立即剔除该连接，避免无界堆积。

单 worker 部署时所有连接都在同一进程；多 worker 部署时，推送消息必须先经 Redis
分发给各进程的订阅者，否则收件人连在其它 worker 上时消息会静默丢失。
"""

import asyncio
import json
import uuid
from typing import Any

from redis.asyncio import Redis

from app.core.logger import logger

# 单连接消息队列上限：打满即视为慢消费者，踢除连接（SSE 断开后由客户端自动重连）
SSE_QUEUE_MAX_SIZE = 64

# 本进程实例令牌：消息经 Redis 广播后会回到发送方进程，用它识别并跳过，避免重复投递
_PROCESS_TOKEN = uuid.uuid4().hex

# 全部 manager 注册表：应用关闭时统一停止订阅协程
_managers: list["SSEConnectionManager"] = []


def stop_sse_relays() -> None:
    """应用关闭时停止所有跨进程订阅协程（幂等）。"""
    for manager in _managers:
        manager.stop_listener()


class SSEConnectionManager:
    """维护 user_id -> 连接队列集合，支持同一用户多标签页；慢消费者立即剔除。

    推送策略 = 本进程直发 + Redis publish；订阅协程负责把其它 worker 广播来的消息
    投递给本进程命中目标（all / user_id 列表）的连接。Redis 不可用时自动退化为
    仅本进程直发（等价于单机行为）。
    """

    def __init__(self, channel: str) -> None:
        """
        参数:
        - channel (str): 通道名，同时用于日志区分与 Redis 频道名（transfer / notice 等）。
        """
        self._channel = channel
        self._connections: dict[int, set[asyncio.Queue]] = {}
        self._redis: Redis | None = None
        self._listener: asyncio.Task | None = None
        _managers.append(self)

    # ------------------------------------------------------------------ #
    # 连接生命周期
    # ------------------------------------------------------------------ #
    def connect(self, user_id: int, queue: asyncio.Queue, redis: Redis | None = None) -> None:
        """登记连接队列；传入 Redis 时注入并懒启动跨进程订阅（均幂等）。"""
        if redis is not None and self._redis is None:
            self._redis = redis
        self._connections.setdefault(user_id, set()).add(queue)
        if self._redis is not None:
            self._start_listener()

    def disconnect(self, user_id: int, queue: asyncio.Queue) -> None:
        """注销连接队列（幂等）"""
        conns = self._connections.get(user_id)
        if conns is None:
            return
        conns.discard(queue)
        if not conns:
            self._connections.pop(user_id, None)

    def all_connections(self) -> list[asyncio.Queue]:
        """全部连接队列快照"""
        return [q for queues in self._connections.values() for q in queues]

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
        return f"fastapiadmin:sse:{self._channel}"

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
            pairs = [(None, q) for q in self.all_connections()]
        else:
            pairs = [
                (uid, q)
                for uid in target.get("users", [])
                for q in list(self._connections.get(uid, ()))
            ]
        for user_id, q in pairs:
            await self._send(user_id, q, data)

    # ------------------------------------------------------------------ #
    # 跨进程订阅
    # ------------------------------------------------------------------ #
    def _start_listener(self) -> None:
        """启动跨进程订阅协程（幂等；异常退出后由下一次 connect 重启）。"""
        if self._redis is None:
            return
        if self._listener is not None and not self._listener.done():
            return
        self._listener = asyncio.create_task(self._listen(self._redis), name=f"sse-relay-{self._channel}")

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

    async def _send(self, user_id: int | None, queue: asyncio.Queue, data: dict[str, Any]) -> None:
        try:
            queue.put_nowait(data)
        except asyncio.QueueFull:
            logger.warning("{} 通道推送失败，连接队列已满，已剔除慢消费者: user={}", self._channel, user_id)
            if user_id is not None:
                self.disconnect(user_id, queue)
