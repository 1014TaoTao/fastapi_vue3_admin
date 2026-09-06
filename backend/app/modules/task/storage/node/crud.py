from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import StorageNodeModel
from .schema import StorageNodeCreateSchema, StorageNodeUpdateSchema


class StorageNodeCRUD(CRUDBase[StorageNodeModel, StorageNodeCreateSchema, StorageNodeUpdateSchema]):
    """存储源模块数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=StorageNodeModel, auth=auth, db=db)
