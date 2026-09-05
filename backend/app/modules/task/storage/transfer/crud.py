from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import StorageTransferTaskModel


class StorageTransferTaskCRUD(CRUDBase[StorageTransferTaskModel, object, object]):
    """文件传输任务 CRUD"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(StorageTransferTaskModel, auth, db)
