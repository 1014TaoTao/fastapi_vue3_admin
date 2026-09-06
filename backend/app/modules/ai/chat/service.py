import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from agno.run.team import TeamRunOutput
from agno.session.team import TeamSession
from redis.asyncio import Redis

from app.common.enums import RedisInitKeyConfig
from app.core.base_schema import AuthSchema, PageResultSchema
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.core.redis_crud import RedisCURD
from app.utils.ai_factory import AgnoFactory
from app.utils.crypto_util import CryptoUtil

from .crud import TEAM_ID, ChatSessionCRUD
from .schema import (
    AiModelConfigSchema,
    ChatQuerySchema,
    ChatSessionCreateSchema,
    ChatSessionOutSchema,
    ChatSessionQueryParam,
    ChatSessionUpdateSchema,
)

# 导航建议：页面关键词/匹配词 -> 路由
_NAVIGATION_ROUTES: list[tuple[tuple[str, ...], str, str]] = [
    (("用户管理", "用户"), "/system/user", "用户管理"),
    (("角色管理", "角色"), "/system/role", "角色管理"),
    (("菜单管理", "菜单"), "/system/menu", "菜单管理"),
    (("部门管理", "部门"), "/system/dept", "部门管理"),
    (("字典管理", "字典"), "/system/dict", "字典管理"),
    (("系统日志", "日志"), "/system/log", "系统日志"),
]
_NAVIGATION_KEYWORDS = ("跳转", "打开", "进入", "前往", "去", "浏览", "查看")


def _session_to_dict(session: TeamSession | dict[str, Any]) -> dict[str, Any]:
    """将 TeamSession 对象或原始字典统一为会话字典"""
    if isinstance(session, dict):
        return session
    if hasattr(session, "to_dict"):
        return session.to_dict()
    return {
        "session_id": getattr(session, "session_id", ""),
        "agent_id": getattr(session, "agent_id", None),
        "team_id": getattr(session, "team_id", None),
        "workflow_id": getattr(session, "workflow_id", None),
        "user_id": getattr(session, "user_id", None),
        "session_data": getattr(session, "session_data", None),
        "runs": getattr(session, "runs", []),
        "summary": getattr(session, "summary", None),
        "created_at": getattr(session, "created_at", None),
        "updated_at": getattr(session, "updated_at", None),
    }


def _normalize_runs(runs: Any) -> list[dict[str, Any]]:
    """deserialize=False 时 runs 可能是 JSON 字符串，统一为字典列表"""
    if isinstance(runs, str):
        try:
            runs = json.loads(runs)
        except (json.JSONDecodeError, TypeError):
            return []
    return runs if isinstance(runs, list) else []


def _extract_messages(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """从 runs 中提取用户与助手消息"""
    messages = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        run_messages = run.get("messages", [])
        if isinstance(run_messages, list):
            for msg in run_messages:
                if isinstance(msg, dict) and msg.get("role") in ("user", "assistant"):
                    messages.append(
                        {
                            "id": msg.get("id"),
                            "role": msg["role"],
                            "content": msg.get("content", ""),
                            "created_at": msg.get("created_at"),
                        },
                    )
    return messages


def _unix_to_datetime(timestamp: int | None) -> str | None:
    """将Unix时间戳转换为日期时间字符串"""
    if timestamp is None:
        return None
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, OSError):
        return None


def _format_session_data(session: TeamSession | dict[str, Any], with_messages: bool = True) -> dict[str, Any]:
    """格式化会话数据，补充前端需要的字段。

    列表场景 with_messages=False：不展开消息正文，仅返回消息条数；
    详情场景 with_messages=True：返回完整消息列表。
    """
    session_dict = _session_to_dict(session)
    runs = _normalize_runs(session_dict.get("runs"))
    messages = _extract_messages(runs) if with_messages else []

    session_data = session_dict.get("session_data")
    if isinstance(session_data, str):
        try:
            session_data = json.loads(session_data)
        except (json.JSONDecodeError, TypeError):
            session_data = {}
    session_name = session_data.get("session_name") if isinstance(session_data, dict) else None

    result = {
        **session_dict,
        "session_data": session_data,
        "id": session_dict.get("session_id"),
        "title": session_name or str(session_dict.get("session_id", ""))[:8] or "未命名会话",
        "created_time": _unix_to_datetime(session_dict.get("created_at")),
        "updated_time": _unix_to_datetime(session_dict.get("updated_at")),
        "message_count": len(messages) if with_messages else len(runs),
        "messages": messages,
    }

    # summary 可能是 SessionSummary 对象，提取其 summary 字段
    summary = session_dict.get("summary")
    if isinstance(summary, dict):
        result["summary"] = summary.get("summary")
    elif summary is not None and not isinstance(summary, str):
        result["summary"] = str(summary)

    return result


async def _ensure_session(crud: ChatSessionCRUD, session_id: str | None) -> str:
    """会话 ID 为空时创建新会话，返回可用的会话 ID"""
    if session_id:
        return session_id
    session = await crud.create(data=ChatSessionCreateSchema(title="新对话"))
    return session.session_id


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
        crud = ChatSessionCRUD(self.auth)
        # 会话创建失败属于业务异常，直接抛出由连接层处理
        session_id = await _ensure_session(crud, query.session_id)

        agno_factory = AgnoFactory()
        agent = agno_factory.create_agent(
            user_id=self.auth.user.username or "user",
            team_id=TEAM_ID,
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
            if hasattr(stream, "__aiter__"):
                async for chunk in stream:  # type: ignore[union-attr]
                    if stop_event is not None and stop_event.is_set():
                        logger.info("用户主动停止生成: session_id={}", session_id)
                        return
                    if chunk and getattr(chunk, "content", None):
                        chunk_count += 1
                        yield str(chunk.content)
            else:
                # 兼容非流式直接返回结果的场景
                result: Any = stream
                if result and getattr(result, "content", None):
                    yield str(result.content)
        except asyncio.CancelledError:
            logger.info("生成任务被取消: session_id={}", session_id)
            raise
        except Exception as e:
            logger.error(f"流式生成失败: {e}", exc_info=True)
            yield "抱歉，AI 服务暂时不可用，请稍后重试"
            return

        logger.info("流式生成结束: session_id={} chunk_count={}", session_id, chunk_count)

    async def chat_non_stream(
        self,
        message: str,
        session_id: str | None,
        model_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """非流式 AI 对话"""
        crud = ChatSessionCRUD(self.auth)
        sid = await _ensure_session(crud, session_id)

        agno_factory = AgnoFactory()
        agent = agno_factory.create_agent(
            user_id=self.auth.user.username or "user",
            team_id=TEAM_ID,
            session_id=sid,
            db=crud.db,
            model_config=model_config,
        )

        try:
            response: TeamRunOutput = await agent.arun(input=message)
        except Exception as e:
            logger.error(f"非流式对话失败: {e}", exc_info=True)
            return {
                "response": "抱歉，AI 服务暂时不可用，请稍后重试",
                "session_id": sid,
                "function_calls": None,
                "action": None,
            }

        response_text = response.content if response and response.content else ""
        action = self._extract_action(response_text) if response_text else None

        return {
            "response": response_text,
            "session_id": sid,
            "function_calls": None,
            "action": action,
        }

    @staticmethod
    def _extract_action(response_text: str) -> dict[str, Any] | None:
        """从响应文本中提取结构化动作：优先解析 JSON 指令，其次解析页面导航建议"""
        text = response_text.strip()
        try:
            if text.startswith("{") and text.endswith("}"):
                return json.loads(text)
            if "```json" in text:
                json_start = text.find("```json") + 7
                json_end = text.find("```", json_start)
                if json_end > json_start:
                    return json.loads(text[json_start:json_end].strip())
        except (json.JSONDecodeError, TypeError):
            pass
        return ChatService._parse_action_from_response(response_text)

    @staticmethod
    def _parse_action_from_response(response_text: str) -> dict[str, Any] | None:
        """从响应文本中解析页面导航建议"""
        if not any(keyword in response_text for keyword in _NAVIGATION_KEYWORDS):
            return None

        for words, path, name in _NAVIGATION_ROUTES:
            if any(word in response_text for word in words):
                return {"type": "navigate", "path": path, "name": name}
        return None

    async def get_session(self, session_id: str) -> ChatSessionOutSchema:
        crud = ChatSessionCRUD(self.auth)
        session = await crud.get_by_id(session_id=session_id)
        if not session:
            raise CustomException(msg="会话不存在", code=10404, status_code=404)
        return ChatSessionOutSchema.model_validate(_format_session_data(session))

    async def create(self, data: ChatSessionCreateSchema) -> ChatSessionOutSchema:
        crud = ChatSessionCRUD(self.auth)
        session = await crud.create(data=data)
        return ChatSessionOutSchema.model_validate(_format_session_data(session))

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: ChatSessionQueryParam,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[ChatSessionOutSchema]:
        crud = ChatSessionCRUD(self.auth)
        rows, total = await crud.list_page(
            page_no=page_no,
            page_size=page_size,
            title=search.title,
            order_by=order_by,
        )
        items = [ChatSessionOutSchema.model_validate(_format_session_data(row, with_messages=False)) for row in rows]
        return PageResultSchema[ChatSessionOutSchema](
            page_no=page_no,
            page_size=page_size,
            total=total,
            has_next=page_no * page_size < total,
            items=items,
        )

    async def update(self, session_id: str, data: ChatSessionUpdateSchema) -> None:
        crud = ChatSessionCRUD(self.auth)
        if not await crud.get_by_id(session_id=session_id):
            raise CustomException(msg="会话不存在", code=10404, status_code=404)
        await crud.rename(session_id=session_id, data=data)

    async def delete(self, session_ids: list[str]) -> None:
        if not session_ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        crud = ChatSessionCRUD(self.auth)
        for session_id in session_ids:
            if not await crud.get_by_id(session_id=session_id):
                raise CustomException(msg=f"会话不存在: {session_id}", code=10404, status_code=404)
        await crud.delete(session_ids=session_ids)


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

    async def update(self, config_id: str, config: AiModelConfigSchema) -> dict[str, Any]:
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
