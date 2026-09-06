from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import MenuModel
from .schema import MenuCreateSchema, MenuUpdateSchema


class MenuCRUD(CRUDBase[MenuModel, MenuCreateSchema, MenuUpdateSchema]):
    """菜单模块数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=MenuModel, auth=auth, db=db)
