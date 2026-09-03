import asyncio
import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from agno.run.team import TeamRunOutput
from agno.session.team import TeamSession
from agno.team.team import Team
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import RedisInitKeyConfig
from app.common.request import PaginationService
from app.core.base_schema import AuthSchema, PageResultSchema
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.core.redis_crud import RedisCURD
from app.utils.ai_factory import AgnoFactory
from app.utils.crypto_util import CryptoUtil

from .crud import ChatSessionCRUD
from .schema import (
    AiModelConfigSchema,
    ChatQuerySchema,
    ChatSessionCreateSchema,
    ChatSessionQueryParam,
    ChatSessionUpdateSchema,
)


async def _format_session_data(session: TeamSession, auth: AuthSchema | None = None, db: AsyncSession | None = None) -> dict[str, Any]:
    """格式化会话数据，添加前端需要的字段"""
    if hasattr(session, "to_dict"):
        session_dict = session.to_dict()
    else:
        session_dict = {
            "session_id": getattr(session, "session_id", ""),
            "agent_id": getattr(session, "agent_id", None),
            "team_id": getattr(session, "team_id", None),
            "workflow_id": getattr(session, "workflow_id", None),
            "user_id": getattr(session, "user_id", None),
            "session_data": getattr(session, "session_data", None),
            "agent_data": getattr(session, "agent_data", None),
            "team_data": getattr(session, "team_data", None),
            "workflow_data": getattr(session, "workflow_data", None),
            "metadata": getattr(session, "metadata", None),
            "runs": getattr(session, "runs", []),
            "summary": getattr(session, "summary", None),
            "created_at": getattr(session, "created_at", None),
            "updated_at": getattr(session, "updated_at", None),
        }

    session_data = session_dict.get("session_data") or {}
    runs = session_dict.get("runs") or []
    messages = _extract_messages(runs)

    # 从 session_data 中获取 session_name 作为标题
    session_name = session_data.get("session_name") if session_data else None

    result = {
        **session_dict,
        "id": session_dict.get("session_id"),
        "title": session_name or session_dict.get("session_id", "")[:8] or "未命名会话",
        "created_time": _unix_to_datetime(session_dict.get("created_at")),
        "updated_time": _unix_to_datetime(session_dict.get("updated_at")),
        "message_count": len(messages),
        "messages": messages,
    }

    # 如果有 auth 和 db，查询部门名称
    if auth and db and session_dict.get("team_id"):
        try:
            team_id_str = session_dict.get("team_id")
            if team_id_str:
                result["team_name"] = None
        except Exception:
            result["team_name"] = None
    else:
        result["team_name"] = None

    # 如果 summary 是 SessionSummary 对象，提取 summary 字段
    summary = session_dict.get("summary")
    if summary:
        if isinstance(summary, dict):
            result["summary"] = summary.get("summary")
        else:
            result["summary"] = str(summary)

    return result


def _unix_to_datetime(timestamp: int | None) -> str | None:
    """将Unix时间戳转换为日期时间字符串"""
    if timestamp is None:
        return None
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, OSError):
        return None


def _extract_messages(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """从 runs 中提取消息"""
    messages = []
    if not runs:
        return messages
    for run in runs:
        if not isinstance(run, dict):
            continue
        run_messages = run.get("messages", [])
        if run_messages and isinstance(run_messages, list):
            for msg in run_messages:
                if isinstance(msg, dict):
                    role = msg.get("role")
                    if role in ("user", "assistant"):
                        messages.append(
                            {
                                "id": msg.get("id"),
                                "role": role,
                                "content": msg.get("content", ""),
                                "created_at": msg.get("created_at"),
                            },
                        )
    return messages


class ChatService:
    """聊天会话管理模块服务层"""

    def __init__(self, auth: AuthSchema) -> None:
        self.auth = auth

    async def chat_query(
        self,
        query: ChatQuerySchema,
        stop_event: asyncio.Event | None = None,
        model_config: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str | None, Any]:
        """流式 AI 对话"""
        try:
            crud = ChatSessionCRUD(self.auth)

            session_id = query.session_id
            if not session_id:
                import uuid

                session_id = str(uuid.uuid4())
                session: TeamSession | None = await crud.create_crud(data=ChatSessionCreateSchema(title="新对话"))
                if not session:
                    raise CustomException(msg="创建会话失败")
                session_id = session.session_id

            agno_factory = AgnoFactory()
            team_id = "default"
            agent = agno_factory.create_agent(
                user_id=self.auth.user.username or "user",
                team_id=team_id,
                session_id=session_id,
                db=crud.db,
                model_config=model_config,
            )

            message = (query.message or "").strip()
            if not message:
                yield "请输入消息内容"
                return

            logger.info("开始流式生成: session_id={} message={!r}", session_id, message[:80])
            chunk_count = 0
            try:
                stream = agent.arun(input=message, stream=True)
                logger.info("agent.arun 返回对象类型: {}", type(stream).__name__)
                if hasattr(stream, "__aiter__"):
                    async for chunk in stream:  # type: ignore[union-attr]
                        if stop_event is not None and stop_event.is_set():
                            logger.info("用户主动停止生成: session_id={}", session_id)
                            return
                        if chunk and getattr(chunk, "content", None):
                            chunk_count += 1
                            yield str(chunk.content)
                        else:
                            logger.debug("空 chunk 跳过: {}", type(chunk).__name__ if chunk else None)
                else:
                    # 兼容非流式直接返回结果的场景
                    logger.warning("agent.arun 未返回异步迭代器，尝试按单次结果处理")
                    result: Any = stream
                    if result and getattr(result, "content", None):
                        chunk_count += 1
                        yield str(result.content)
            except asyncio.CancelledError:
                logger.info("生成任务被取消: session_id={}", session_id)
                return

            logger.info("流式生成结束: session_id={} chunk_count={}", session_id, chunk_count)

        except Exception as e:
            logger.error(f"聊天查询失败: {e}", exc_info=True)
            yield f"抱歉，处理您的请求时出现错误：{e!s}"

    async def chat_non_stream(self, message: str, session_id: str | None) -> dict[str, Any]:
        """非流式 AI 对话"""
        try:
            crud = ChatSessionCRUD(self.auth)

            if not session_id:
                import uuid

                session_id = str(uuid.uuid4())
                session: TeamSession | None = await crud.create_crud(data=ChatSessionCreateSchema(title="新对话"))
                if not session:
                    raise CustomException(msg="创建会话失败")
                session_id = session.session_id

            agno_factory = AgnoFactory()
            team_id = "default"
            agent: Team = agno_factory.create_agent(
                user_id=self.auth.user.username or "user",
                team_id=team_id,
                session_id=session_id,
                db=crud.db,
            )

            response: TeamRunOutput = await agent.arun(input=message)

            response_text = ""
            action = None

            if response and response.content:
                response_text = response.content
                try:
                    if response_text.strip().startswith("{") and response_text.strip().endswith("}"):
                        action = json.loads(response_text)
                    elif "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        if json_end > json_start:
                            json_str = response_text[json_start:json_end].strip()
                            action = json.loads(json_str)
                except Exception:
                    pass

                if not action:
                    action = self._parse_action_from_response(response_text)

            return {
                "response": response_text,
                "session_id": session_id,
                "function_calls": None,
                "action": action,
            }

        except Exception as e:
            logger.error(f"聊天查询失败: {e}")
            return {
                "response": f"抱歉，处理您的请求时出现错误：{e!s}",
                "session_id": session_id,
                "function_calls": None,
                "action": None,
            }

    @staticmethod
    def _parse_action_from_response(response_text: str) -> dict[str, Any] | None:
        """从响应文本中解析操作建议"""
        route_config = {
            "用户管理": {"path": "/system/user", "name": "用户管理"},
            "角色管理": {"path": "/system/role", "name": "角色管理"},
            "菜单管理": {"path": "/system/menu", "name": "菜单管理"},
            "部门管理": {"path": "/system/dept", "name": "部门管理"},
            "字典管理": {"path": "/system/dict", "name": "字典管理"},
            "系统日志": {"path": "/system/log", "name": "系统日志"},
        }

        navigation_keywords = ["跳转", "打开", "进入", "前往", "去", "浏览", "查看"]
        has_navigation = any(keyword in response_text for keyword in navigation_keywords)

        if not has_navigation:
            return None

        for page_name, route_info in route_config.items():
            if page_name in response_text:
                return {
                    "type": "navigate",
                    "path": route_info["path"],
                    "name": route_info["name"],
                }

        keyword_mapping = {
            "用户": {"path": "/system/user", "name": "用户管理"},
            "角色": {"path": "/system/role", "name": "角色管理"},
            "菜单": {"path": "/system/menu", "name": "菜单管理"},
            "部门": {"path": "/system/dept", "name": "部门管理"},
            "字典": {"path": "/system/dict", "name": "字典管理"},
            "日志": {"path": "/system/log", "name": "系统日志"},
        }

        for keyword, route_info in keyword_mapping.items():
            if keyword in response_text:
                return {
                    "type": "navigate",
                    "path": route_info["path"],
                    "name": route_info["name"],
                }

        return None

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        crud = ChatSessionCRUD(self.auth)
        session: TeamSession | None = await crud.get_by_id_crud(session_id=session_id)
        if session:
            return await _format_session_data(session, self.auth)
        return None

    async def create(self, data: ChatSessionCreateSchema) -> dict[str, Any] | None:
        crud = ChatSessionCRUD(self.auth)
        session = await crud.create_crud(data=data)
        if session:
            return await _format_session_data(session, self.auth)
        return None

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: ChatSessionQueryParam,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[Any]:
        crud = ChatSessionCRUD(self.auth)
        sessions = await crud.list_crud()
        items = [await _format_session_data(s, self.auth) for s in sessions]
        return await PaginationService.paginate(
            data_list=items,
            page_no=page_no,
            page_size=page_size,
        )

    async def update(self, session_id: str, data: ChatSessionUpdateSchema) -> bool:
        crud = ChatSessionCRUD(self.auth)
        return await crud.update_crud(session_id=session_id, data=data)

    async def delete(self, session_ids: list[str]) -> None:
        await ChatSessionCRUD(self.auth).delete_crud(session_ids=session_ids)


# ================================================= #
# ******************* AI 模型配置 ****************** #
# ================================================= #


_AI_MODEL_TTL = 604800  # AI 模型配置缓存 7 天，不活跃用户自动清理
_AI_MODEL_LOCK_TTL = 10  # 读改写锁最长持有时间(秒)


@asynccontextmanager
async def _model_config_lock(redis: Redis, user_id: int) -> AsyncGenerator[None, None]:
    """用户模型配置读改写的分布式锁：配置以 JSON list 整体存取，并发写会互相覆盖。"""
    crud = RedisCURD(redis)
    key = f"{RedisInitKeyConfig.AI_MODEL_CONFIG.key}:lock:{user_id}"
    acquired, token = await crud.lock(key=key, expire=_AI_MODEL_LOCK_TTL)
    if not acquired:
        raise CustomException(msg="模型配置正在被修改，请稍后重试")
    try:
        yield
    finally:
        await crud.unlock(key=key, value=token)


def _ai_model_items_key(user_id: int) -> str:
    return f"{RedisInitKeyConfig.AI_MODEL_CONFIG.key}:items:{user_id}"


def _ai_model_active_key(user_id: int) -> str:
    return f"{RedisInitKeyConfig.AI_MODEL_CONFIG.key}:active:{user_id}"


# 配置项中需要静态加密的敏感字段：Redis 中的 api_key 一律以密文存储
_SECRET_FIELD = "api_key"


def _seal_item(item: dict[str, Any]) -> dict[str, Any]:
    """落盘前加密 api_key，其余字段保持明文（用于展示与检索）。"""
    sealed = dict(item)
    if sealed.get(_SECRET_FIELD):
        sealed[_SECRET_FIELD] = CryptoUtil.encrypt(sealed[_SECRET_FIELD])
    return sealed


def _open_item(item: dict[str, Any]) -> dict[str, Any]:
    """读取后解密 api_key；加密能力上线前的历史明文原样返回。"""
    opened = dict(item)
    if opened.get(_SECRET_FIELD):
        opened[_SECRET_FIELD] = CryptoUtil.decrypt_or_keep(opened[_SECRET_FIELD])
    return opened


async def get_user_model_config(redis: Redis, user_id: int) -> dict[str, Any] | None:
    """读取当前激活的 AI 模型配置；不存在或未激活返回 None。"""
    active_id = await RedisCURD(redis).get(_ai_model_active_key(user_id))
    if not active_id:
        return None
    items = await list_user_model_configs(redis, user_id)
    for item in items:
        if item.get("id") == active_id:
            return item
    return None


async def _read_raw_items(redis: Redis, user_id: int) -> list[dict[str, Any]]:
    """读取存储层的原始配置项（api_key 为密文）。"""
    raw = await RedisCURD(redis).get(_ai_model_items_key(user_id))
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, TypeError):
        logger.warning("AI 模型配置列表 JSON 解析失败: user_id={}", user_id)
        return []


async def _write_raw_items(redis: Redis, user_id: int, items: list[dict[str, Any]]) -> None:
    """写入配置项：加密敏感字段后整体落盘（调用方需持有读改写锁）。"""
    await RedisCURD(redis).set(
        _ai_model_items_key(user_id),
        json.dumps([_seal_item(it) for it in items], ensure_ascii=False),
        expire=_AI_MODEL_TTL,
    )


async def list_user_model_configs(redis: Redis, user_id: int) -> list[dict[str, Any]]:
    """列出用户的所有模型配置项（api_key 已解密为明文）。"""
    return [_open_item(it) for it in await _read_raw_items(redis, user_id)]


async def get_active_model_id(redis: Redis, user_id: int) -> str | None:
    """读取当前激活的模型配置 ID；为空表示使用系统默认。"""
    return await RedisCURD(redis).get(_ai_model_active_key(user_id))


async def create_user_model_config(
    redis: Redis,
    user_id: int,
    config: AiModelConfigSchema,
) -> dict[str, Any]:
    """新增一个模型配置项。"""
    import uuid

    async with _model_config_lock(redis, user_id):
        items = await list_user_model_configs(redis, user_id)
        item = {
            **config.model_dump(),
            "id": uuid.uuid4().hex,
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        items.append(item)
        await _write_raw_items(redis, user_id, items)

        # 若用户尚未激活任何配置，自动激活新增的
        if not await get_active_model_id(redis, user_id):
            await RedisCURD(redis).set(_ai_model_active_key(user_id), item["id"], expire=_AI_MODEL_TTL)

    logger.info("已新增 AI 模型配置: user_id={} name={} id={}", user_id, config.name, item["id"])
    return item


async def update_user_model_config(
    redis: Redis,
    user_id: int,
    config_id: str,
    config: AiModelConfigSchema,
) -> dict[str, Any] | None:
    """更新指定 ID 的模型配置项；不存在返回 None。"""
    async with _model_config_lock(redis, user_id):
        items = await list_user_model_configs(redis, user_id)
        target = next((it for it in items if it.get("id") == config_id), None)
        if not target:
            return None
        target.update(config.model_dump())
        await _write_raw_items(redis, user_id, items)
    logger.info("已更新 AI 模型配置: user_id={} id={}", user_id, config_id)
    return target


async def delete_user_model_config(redis: Redis, user_id: int, config_id: str) -> bool:
    """删除指定 ID 的模型配置项；若该 ID 是当前激活则清空激活。"""
    async with _model_config_lock(redis, user_id):
        items = await list_user_model_configs(redis, user_id)
        new_items = [it for it in items if it.get("id") != config_id]
        if len(new_items) == len(items):
            return False
        await _write_raw_items(redis, user_id, new_items)
        active_id = await get_active_model_id(redis, user_id)
        if active_id == config_id:
            await RedisCURD(redis).delete(_ai_model_active_key(user_id))
    logger.info("已删除 AI 模型配置: user_id={} id={}", user_id, config_id)
    return True


async def set_active_model_config(redis: Redis, user_id: int, config_id: str) -> bool:
    """设置当前激活的模型配置项；id 为空字符串或 "__default__" 表示使用系统默认。"""
    if config_id in ("", "__default__"):
        await RedisCURD(redis).delete(_ai_model_active_key(user_id))
        logger.info("已切换到系统默认模型: user_id={}", user_id)
        return True
    items = await list_user_model_configs(redis, user_id)
    if not any(it.get("id") == config_id for it in items):
        return False
    await RedisCURD(redis).set(_ai_model_active_key(user_id), config_id, expire=_AI_MODEL_TTL)
    logger.info("已切换 AI 模型: user_id={} id={}", user_id, config_id)
    return True


class AiModelConfigService:
    """AI 模型配置业务服务（多配置 + 激活切换）"""

    def __init__(self, auth: AuthSchema, redis: Redis) -> None:
        self.auth = auth
        self.redis = redis

    @property
    def _user_id(self) -> int:
        return self.auth.user.id

    async def list_configs(self) -> dict[str, Any]:
        """获取配置列表 + 当前激活 ID。"""
        items = await list_user_model_configs(self.redis, self._user_id)
        active_id = await get_active_model_id(self.redis, self._user_id)
        return {"items": items, "active_id": active_id}

    async def get_active(self) -> dict[str, Any] | None:
        return await get_user_model_config(self.redis, self._user_id)

    async def create(self, config: AiModelConfigSchema) -> dict[str, Any]:
        return await create_user_model_config(self.redis, self._user_id, config)

    async def update(self, config_id: str, config: AiModelConfigSchema) -> dict[str, Any] | None:
        result = await update_user_model_config(self.redis, self._user_id, config_id, config)
        if result is None:
            raise CustomException(msg="模型配置不存在", code=10404, status_code=404)
        return result

    async def delete(self, config_id: str) -> None:
        ok = await delete_user_model_config(self.redis, self._user_id, config_id)
        if not ok:
            raise CustomException(msg="模型配置不存在", code=10404, status_code=404)

    async def set_active(self, config_id: str) -> None:
        ok = await set_active_model_config(self.redis, self._user_id, config_id)
        if not ok:
            raise CustomException(msg="模型配置不存在", code=10404, status_code=404)
