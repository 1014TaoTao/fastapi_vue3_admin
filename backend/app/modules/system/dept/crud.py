from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import DeptModel
from .schema import DeptCreateSchema, DeptUpdateSchema


class DeptCRUD(CRUDBase[DeptModel, DeptCreateSchema, DeptUpdateSchema]):
    """部门模块数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=DeptModel, auth=auth, db=db)
