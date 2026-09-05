from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import AuthSchema, PageResultSchema
from app.core.exceptions import CustomException
from app.utils.common_util import search_to_dict

from .crud import VersionCRUD
from .schema import (
    VersionCreateSchema,
    VersionOutSchema,
    VersionQueryParam,
    VersionStatusSchema,
    VersionUpdateSchema,
)


class VersionService:
    """版本管理模块服务层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def detail(self, id: int) -> VersionOutSchema:
        obj = await VersionCRUD(self.auth, self.db).get(id=id)
        if not obj:
            raise CustomException(msg="该数据不存在")
        return VersionOutSchema.model_validate(obj)

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: VersionQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[VersionOutSchema]:
        offset = (page_no - 1) * page_size
        return await VersionCRUD(self.auth, self.db).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"sort": "asc"}, {"id": "desc"}],
            search=search_to_dict(search, {}),
            out_schema=VersionOutSchema,
        )

    async def create(self, data: VersionCreateSchema) -> VersionOutSchema:
        obj = await VersionCRUD(self.auth, self.db).create(data=data)
        return VersionOutSchema.model_validate(obj)

    async def update(self, id: int, data: VersionUpdateSchema) -> VersionOutSchema:
        obj = await VersionCRUD(self.auth, self.db).get(id=id)
        if not obj:
            raise CustomException(msg="更新失败，该数据不存在")
        obj = await VersionCRUD(self.auth, self.db).update(id=id, data=data)
        return VersionOutSchema.model_validate(obj)

    async def delete(self, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        objs = await VersionCRUD(self.auth, self.db).get_list(search={"id": ("in", ids)})
        obj_map = {o.id: o for o in objs}
        for id_ in ids:
            if id_ not in obj_map:
                raise CustomException(msg="删除失败，该数据不存在")
        await VersionCRUD(self.auth, self.db).delete(ids=ids)

    async def set_status(self, id: int, data: VersionStatusSchema) -> VersionOutSchema:
        obj = await VersionCRUD(self.auth, self.db).update(id=id, data={"status": data.status})
        return VersionOutSchema.model_validate(obj)

    async def get_published(self) -> list[VersionOutSchema]:
        objs = await VersionCRUD(self.auth, self.db).get_list(
            search={"status": ("eq", 1)},
            order_by=[{"sort": "asc"}],
        )
        return [VersionOutSchema.model_validate(obj) for obj in objs]
