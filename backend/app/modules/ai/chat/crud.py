import json
import threading
import time
import uuid
from typing import Any

from agno.db.base import SessionType
from agno.db.mysql import AsyncMySQLDb
from agno.db.postgres import AsyncPostgresDb
from agno.db.sqlite import AsyncSqliteDb
from agno.session.team import TeamSession

from app.config.setting import settings
from app.core.base_schema import AuthSchema
from app.core.exceptions import CustomException
from app.core.logger import logger

from .schema import ChatSessionCreateSchema, ChatSessionUpdateSchema

# Team 标识：agno 会话按 user_id + team_id 隔离
TEAM_ID = "default"

# agno 异步 DB 实例为进程级单例：内部维护异步引擎与连接池，避免每请求重建
_db_instance: Any | None = None
_db_lock = threading.Lock()


def _get_agno_db() -> Any:
    """获取 agno 异步数据库实例（进程级单例）"""
    global _db_instance
    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                db_type = settings.DATABASE_TYPE
                db_uri = settings.DB_URI
                if db_type == "mysql":
                    _db_instance = AsyncMySQLDb(db_url=db_uri, db_schema=settings.DATABASE_NAME, create_schema=False)
                elif db_type == "postgres":
                    _db_instance = AsyncPostgresDb(db_url=db_uri, db_schema="public", create_schema=False)
                elif db_type == "sqlite":
                    _db_instance = AsyncSqliteDb(db_file=db_uri.replace("sqlite:///", ""))
                else:
                    raise CustomException(msg=f"不支持的数据库类型: {db_type}")
    return _db_instance


def _row_session_name(row: dict[str, Any]) -> str:
    """从 deserialize=False 的原始会话行中提取会话标题（session_data 可能是 JSON 字符串或字典）"""
    session_data = row.get("session_data")
    if isinstance(session_data, str):
        try:
            session_data = json.loads(session_data)
        except (json.JSONDecodeError, TypeError):
            return ""
    if isinstance(session_data, dict):
        return str(session_data.get("session_name") or "")
    return ""


class ChatSessionCRUD:
    """聊天会话数据层 - 使用 agno 异步数据库存储"""

    SESSION_TYPE = SessionType.TEAM

    def __init__(self, auth: AuthSchema) -> None:
        """初始化CRUD数据层

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        self.auth = auth
        self.user_id = auth.user.username or "user"
        self.team_id = TEAM_ID
        self.db = _get_agno_db()

    async def get_by_id(self, session_id: str) -> TeamSession | None:
        """获取会话详情；不存在或失败时返回 None"""
        try:
            return await self.db.get_session(
                session_id=session_id,
                session_type=self.SESSION_TYPE,
                user_id=self.user_id,
            )
        except Exception as e:
            logger.error(f"获取会话详情失败: {e}")
            return None

    async def list_page(
        self,
        page_no: int,
        page_size: int,
        title: str | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """分页查询会话（分页/排序/计数均在 DB 层完成）。

        使用 deserialize=False 返回原始字典，避免全量反序列化 runs 消息；
        返回 (会话字典列表, 总数)。
        """
        # 前端排序字段（created_time/updated_time）映射为 agno 会话表列名
        sort_by, sort_order = "updated_at", "desc"
        if order_by:
            column, direction = next(iter(order_by[0]))
            sort_by = {
                "created_time": "created_at",
                "updated_time": "updated_at",
                "created_at": "created_at",
                "updated_at": "updated_at",
            }.get(column, "updated_at")
            sort_order = direction if direction in ("asc", "desc") else "desc"

        # 标题搜索为低频操作：agno 未实现该过滤，需全量拉取当前用户会话后内存过滤+分页
        fetch_page = page_no if not title else None
        fetch_limit = page_size if not title else None

        try:
            result = await self.db.get_sessions(
                session_type=self.SESSION_TYPE,
                user_id=self.user_id,
                limit=fetch_limit,
                page=fetch_page,
                sort_by=sort_by,
                sort_order=sort_order,
                deserialize=False,
            )
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            raise CustomException(msg="获取会话列表失败") from e

        rows: list[dict[str, Any]] = []
        total = 0
        if isinstance(result, tuple) and len(result) == 2:
            rows, total = list(result[0] or []), int(result[1] or 0)
        else:
            rows, total = list(result or []), len(result or [])

        if title:
            keyword = title.strip().lower()
            filtered = [r for r in rows if keyword in _row_session_name(r).lower()]
            start = (page_no - 1) * page_size
            return filtered[start : start + page_size], len(filtered)
        return rows, total

    async def create(self, data: ChatSessionCreateSchema) -> TeamSession:
        """创建会话（Team 在运行时自动创建并管理 session）"""
        now = int(time.time())
        session_data = {"session_name": data.title} if data.title else {}
        session = TeamSession(
            session_id=str(uuid.uuid4()),
            user_id=self.user_id,
            team_id=self.team_id,
            session_data=session_data,
            created_at=now,
            updated_at=now,
        )
        try:
            result = await self.db.upsert_session(session=session)
        except Exception as e:
            logger.exception(f"创建会话失败: {e}")
            raise CustomException(msg="创建会话失败") from e
        if result is None:
            raise CustomException(msg="创建会话失败")
        return result

    async def rename(self, session_id: str, data: ChatSessionUpdateSchema) -> None:
        """重命名会话"""
        try:
            result = await self.db.rename_session(
                session_id=session_id,
                session_type=self.SESSION_TYPE,
                session_name=data.title,
                user_id=self.user_id,
            )
        except Exception as e:
            logger.error(f"更新会话失败: {e}")
            raise CustomException(msg="更新会话失败") from e
        if result is None:
            raise CustomException(msg="会话不存在", code=10404, status_code=404)

    async def delete(self, session_ids: list[str]) -> None:
        """批量删除会话"""
        for session_id in session_ids:
            try:
                await self.db.delete_session(session_id=session_id, user_id=self.user_id)
            except Exception as e:
                logger.error(f"删除会话失败: {session_id} - {e}")
                raise CustomException(msg=f"删除会话失败: {session_id}") from e
