from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema
from app.core.exceptions import CustomException
from app.utils.common_util import search_to_dict
from app.utils.excel_util import ExcelUtil

from .crud import PositionCRUD
from .schema import (
    PositionCreateSchema,
    PositionOutSchema,
    PositionQueryParam,
    PositionUpdateSchema,
)


class PositionService:
    """岗位管理服务

    提供岗位 CRUD、批量启/禁用、Excel 导出等业务能力。
    """

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def detail(self, id: int) -> PositionOutSchema:
        obj = await PositionCRUD(self.auth, self.db).get_or_404(id=id)
        return PositionOutSchema.model_validate(obj)

    async def get_options(self) -> list[dict[str, Any]]:
        """获取岗位下拉选项，委托给 PositionCRUD"""
        return await PositionCRUD(self.auth, self.db).get_options()

    async def get_list(
        self,
        search: PositionQueryParam | None = None,
        order_by: list[dict] | None = None,
    ) -> list[PositionOutSchema]:
        position_list = await PositionCRUD(self.auth, self.db).get_list(search=search_to_dict(search), order_by=order_by)
        return [PositionOutSchema.model_validate(position) for position in position_list]

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: PositionQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[PositionOutSchema]:
        offset = (page_no - 1) * page_size
        return await PositionCRUD(self.auth, self.db).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search_to_dict(search),
            out_schema=PositionOutSchema,
        )

    async def create(self, data: PositionCreateSchema) -> PositionOutSchema:
        position = await PositionCRUD(self.auth, self.db).get(name=data.name)
        if position:
            raise CustomException(msg="创建失败，该数据已存在")
        new_position = await PositionCRUD(self.auth, self.db).create(data=data)
        return await self.detail(id=new_position.id)

    async def update(self, id: int, data: PositionUpdateSchema) -> PositionOutSchema:
        _ = await PositionCRUD(self.auth, self.db).get_or_404(id=id, msg="更新失败，该数据不存在")
        exist_position = await PositionCRUD(self.auth, self.db).get(name=data.name)
        if exist_position and exist_position.id != id:
            raise CustomException(msg="更新失败，名称已存在")
        await PositionCRUD(self.auth, self.db).update(id=id, data=data)
        return await self.detail(id=id)

    async def delete(self, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        positions = await PositionCRUD(self.auth, self.db).get_list(search={"id": ("in", ids)})
        position_map = {p.id: p for p in positions}
        for pid in ids:
            if pid not in position_map:
                raise CustomException(msg="删除失败，该数据不存在")
        await PositionCRUD(self.auth, self.db).delete(ids=ids)

    async def set_available(self, data: BatchSetAvailable) -> None:
        positions = await PositionCRUD(self.auth, self.db).get_list(search={"id": ("in", data.ids)})
        position_map = {p.id: p for p in positions}
        for pid in data.ids:
            if pid not in position_map:
                raise CustomException(msg="该数据不存在")
        await PositionCRUD(self.auth, self.db).set(ids=data.ids, status=data.status)

    @staticmethod
    async def export_list(position_list: list[dict]) -> bytes:
        mapping_dict = {
            "id": "编号",
            "name": "岗位名称",
            "order": "显示顺序",
            "status": "状态",
            "description": "备注",
            "created_time": "创建时间",
            "updated_time": "更新时间",
            "created_id": "创建者ID",
            "updated_id": "更新者ID",
        }
        data = position_list.copy()
        for item in data:
            item["status"] = "启用" if item.get("status") == 0 else "停用"
            item["creator"] = item.get("created_by", {}).get("name", "未知") if isinstance(item.get("created_by"), dict) else "未知"
        return await ExcelUtil.aexport_list2excel(list_data=data, mapping_dict=mapping_dict)
