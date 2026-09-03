from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import StorageSourceModel
from .schema import StorageSourceCreateSchema, StorageSourceUpdateSchema


class StorageSourceCRUD(CRUDBase[StorageSourceModel, StorageSourceCreateSchema, StorageSourceUpdateSchema]):
    """存储源模块数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=StorageSourceModel, auth=auth, db=db)
