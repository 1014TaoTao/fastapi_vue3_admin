from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import VersionModel
from .schema import VersionCreateSchema, VersionUpdateSchema


class VersionCRUD(CRUDBase[VersionModel, VersionCreateSchema, VersionUpdateSchema]):
    """版本数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=VersionModel, auth=auth, db=db)
