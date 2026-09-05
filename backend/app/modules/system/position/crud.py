from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import PositionModel
from .schema import PositionCreateSchema, PositionUpdateSchema


class PositionCRUD(CRUDBase[PositionModel, PositionCreateSchema, PositionUpdateSchema]):
    """岗位模块数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=PositionModel, auth=auth, db=db)

    async def get_options(self) -> list[dict[str, Any]]:
        """获取岗位下拉选项，返回 [{value, label}]"""
        items = await self.get_list(search={"status": 0})
        return [{"value": item.id, "label": item.name} for item in items]
