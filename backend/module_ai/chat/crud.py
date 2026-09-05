from typing import Any

from agno.db.base import SessionType
from agno.db.mysql import MySQLDb
from agno.db.postgres import PostgresDb
from agno.db.sqlite import SqliteDb
from agno.session.team import TeamSession

from app.config.setting import settings
from app.core.base_schema import AuthSchema
from app.core.logger import logger

from .schema import ChatSessionCreateSchema, ChatSessionUpdateSchema


class ChatSessionCRUD:
    """聊天会话数据层 - 使用 agno 数据库存储"""

    # 会话类型配置 - 使用 TEAM 类型因为创建的是 Team
    SESSION_TYPE = SessionType.TEAM

    def __init__(self, auth: AuthSchema) -> None:
        """初始化CRUD数据层"""
        self.auth = auth
        self.user_id = auth.user.username or "user"
        self.team_id = "default"
        self.db = self._get_db()

    def _get_db(self) -> Any:
        """获取数据库连接"""
        db_type = settings.DATABASE_TYPE
        db_uri = settings.DB_URI

        db_mapping = {
            "mysql": lambda: MySQLDb(db_url=db_uri, db_schema=settings.DATABASE_NAME, create_schema=False),
            "postgres": lambda: PostgresDb(db_url=db_uri, db_schema="public", create_schema=False),
            "sqlite": lambda: SqliteDb(db_file=db_uri.replace("sqlite:///", "")),
        }

        if db_type not in db_mapping:
            raise ValueError(f"不支持的数据库类型: {db_type}")

        return db_mapping[db_type]()

    async def get_by_id_crud(self, session_id: str) -> TeamSession | None:
        """获取会话详情。

        参数:
        - session_id (str): 会话 ID。

        返回:
        - TeamSession | None: 会话对象；失败或不存在时为 None。
        """
        try:
            return self.db.get_session(session_id=session_id, session_type=self.SESSION_TYPE, user_id=self.user_id)
        except Exception as e:
            logger.error(f"获取会话详情失败: {e}")
            return None

    async def list_crud(
        self,
        search: dict[str, Any] | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[TeamSession]:
        """列表查询，获取当前用户的所有会话。

        参数:
        - search (dict[str, Any] | None): 预留查询条件（当前实现未使用）。
        - order_by (list[dict[str, str]] | None): 预留排序（当前实现未使用）。

        返回:
        - list[TeamSession]: 会话列表；失败时为空列表。
        """
        try:
            result = self.db.get_sessions(session_type=self.SESSION_TYPE, user_id=self.user_id)
            if isinstance(result, tuple) and len(result) == 2:
                return result[0]
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return []

    async def create_crud(self, data: ChatSessionCreateSchema) -> TeamSession | None:
        """创建会话（Team 在运行时自动创建并管理 session）。

        参数:
        - data (ChatSessionCreateSchema): 创建参数（如标题）。

        返回:
        - TeamSession | None: 新建会话；失败时为 None。
        """
        import time
        import uuid

        try:
            session_id = str(uuid.uuid4())
            now = int(time.time())

            # 创建 session_data，包含 session_name
            session_data = {}
            if data.title:
                session_data["session_name"] = data.title

            # 创建 TeamSession 对象
            session = TeamSession(
                session_id=session_id,
                user_id=self.user_id,
                team_id=self.team_id,
                session_data=session_data,
                created_at=now,
                updated_at=now,
            )

            # 保存会话
            result = self.db.upsert_session(session=session)
            return result
        except Exception as e:
            logger.exception(f"创建会话失败: {e}")
            return None

    async def update_crud(self, session_id: str, data: ChatSessionUpdateSchema) -> bool:
        """更新会话（如重命名）。

        参数:
        - session_id (str): 会话 ID。
        - data (ChatSessionUpdateSchema): 更新数据。

        返回:
        - bool: 是否成功。
        """
        try:
            self.db.rename_session(
                session_id=session_id,
                session_type=self.SESSION_TYPE,
                session_name=data.title,
                user_id=self.user_id,
            )
            return True
        except Exception as e:
            logger.error(f"更新会话失败: {e}")
            return False

    async def delete_crud(self, session_ids: list[str]) -> bool:
        """批量删除会话。

        参数:
        - session_ids (list[str]): 会话 ID 列表。

        返回:
        - bool: 是否全部处理成功（任一出错则记日志并返回 False）。
        """
        try:
            for session_id in session_ids:
                self.db.delete_session(session_id=session_id, user_id=self.user_id)
            return True
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False
