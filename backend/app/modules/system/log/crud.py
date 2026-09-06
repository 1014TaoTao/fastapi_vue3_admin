from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import LoginLogModel, OperationLogModel
from .schema import LoginLogCreateSchema, OperationLogCreateSchema


class LoginLogCRUD(CRUDBase[LoginLogModel, LoginLogCreateSchema, None]):
    """登录日志数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=LoginLogModel, auth=auth, db=db)


class OperationLogCRUD(CRUDBase[OperationLogModel, OperationLogCreateSchema, None]):
    """操作日志 CRUD"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=OperationLogModel, auth=auth, db=db)
