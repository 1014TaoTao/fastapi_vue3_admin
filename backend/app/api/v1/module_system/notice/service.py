from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema
from app.core.exceptions import CustomException
from app.utils.common_util import search_to_dict

from .crud import NoticeCRUD
from .schema import NoticeCreateSchema, NoticeOutSchema, NoticeQueryParam, NoticeUpdateSchema


class NoticeService:
    """公告管理服务

    提供公告 CRUD、状态切换、已启用公告分页查询、Excel 导出等业务能力。
    """

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def detail(self, id: int) -> NoticeOutSchema:
        """获取公告详情

        参数:
        - id (int): 公告 ID

        返回:
        - NoticeOutSchema: 公告响应模型
        """
        obj = await NoticeCRUD(self.auth, self.db).get_or_404(id=id)
        return NoticeOutSchema.model_validate(obj)

    async def get_list(
        self,
        search: NoticeQueryParam | None = None,
        order_by: list[dict] | None = None,
    ) -> list[NoticeOutSchema]:
        """获取公告列表

        参数:
        - search (NoticeQueryParam | None): 查询参数
        - order_by (list[dict] | None): 排序规则

        返回:
        - list[NoticeOutSchema]: 公告列表
        """
        notice_obj_list = await NoticeCRUD(self.auth, self.db).get_list(search=search_to_dict(search), order_by=order_by)
        return [NoticeOutSchema.model_validate(notice_obj) for notice_obj in notice_obj_list]

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: NoticeQueryParam | None = None,
        order_by: list[dict] | None = None,
    ) -> PageResultSchema[NoticeOutSchema]:
        """分页查询公告

        参数:
        - page_no (int): 当前页码
        - page_size (int): 每页条数
        - search (NoticeQueryParam | None): 查询参数
        - order_by (list[dict] | None): 排序规则

        返回:
        - PageResultSchema[NoticeOutSchema]: 分页结果
        """
        offset = (page_no - 1) * page_size
        return await NoticeCRUD(self.auth, self.db).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search_to_dict(search),
            out_schema=NoticeOutSchema,
        )

    async def available_page(self) -> PageResultSchema[NoticeOutSchema]:
        """获取已启用的公告（首页展示用，最多 10 条）"""
        return await NoticeCRUD(self.auth, self.db).page(
            offset=0,
            limit=10,
            order_by=[{"id": "asc"}],
            search={"status": ("eq", 0)},
            out_schema=NoticeOutSchema,
        )

    async def create(self, data: NoticeCreateSchema) -> NoticeOutSchema:
        """创建公告

        参数:
        - data (NoticeCreateSchema): 公告创建模型

        返回:
        - NoticeOutSchema: 公告响应模型
        """
        notice = await NoticeCRUD(self.auth, self.db).get(notice_title=data.notice_title)
        if notice:
            raise CustomException(msg="创建失败，该数据已存在")
        notice_obj = await NoticeCRUD(self.auth, self.db).create(data=data)
        return await self.detail(id=notice_obj.id)

    async def update(self, id: int, data: NoticeUpdateSchema) -> NoticeOutSchema:
        """更新公告

        参数:
        - id (int): 公告 ID
        - data (NoticeUpdateSchema): 公告更新模型

        返回:
        - NoticeOutSchema: 公告响应模型
        """
        _ = await NoticeCRUD(self.auth, self.db).get_or_404(id=id, msg="更新失败，该数据不存在")
        exist_notice = await NoticeCRUD(self.auth, self.db).get(notice_title=data.notice_title)
        if exist_notice and exist_notice.id != id:
            raise CustomException(msg="更新失败，标题已存在")
        await NoticeCRUD(self.auth, self.db).update(id=id, data=data)
        return await self.detail(id=id)

    async def delete(self, ids: list[int]) -> None:
        """删除公告

        参数:
        - ids (list[int]): 公告 ID 列表
        """
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        notices = await NoticeCRUD(self.auth, self.db).get_list(search={"id": ("in", ids)})
        notice_map = {n.id: n for n in notices}
        for nid in ids:
            if nid not in notice_map:
                raise CustomException(msg="删除失败，该数据不存在")
        await NoticeCRUD(self.auth, self.db).delete(ids=ids)

    async def set_available(self, data: BatchSetAvailable) -> None:
        """批量启用/禁用公告

        参数:
        - data (BatchSetAvailable): 批量设置状态模型
        """
        await NoticeCRUD(self.auth, self.db).set(ids=data.ids, status=data.status)
