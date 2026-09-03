from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_system.user.model import UserModel
from app.core.base_schema import AuthSchema, PageResultSchema
from app.core.exceptions import CustomException
from app.utils.common_util import search_to_dict
from app.utils.excel_util import ExcelUtil

from .crud import TicketCommentCRUD, TicketCRUD
from .schema import (
    TicketBatchSchema,
    TicketCommentCreateSchema,
    TicketCommentOutSchema,
    TicketCreateSchema,
    TicketOutSchema,
    TicketQueryParam,
    TicketUpdateSchema,
)

_TICKET_STATUS_TRANSITIONS = {
    0: {1, 3},
    1: {2, 3},
    2: {3},
    3: {0},
}

_TICKET_STATUS_LABELS = {
    0: "待处理",
    1: "处理中",
    2: "已完成",
    3: "已关闭",
}


_TICKET_PRELOAD = ["assigned_by"]


class TicketService:
    """工单管理服务"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    def _validate_status_transition(self, ticket, new_status: int) -> None:
        old_status = ticket.status if ticket.status is not None else 0
        old_label = _TICKET_STATUS_LABELS.get(old_status, str(old_status))
        new_label = _TICKET_STATUS_LABELS.get(new_status, str(new_status))

        if new_status not in _TICKET_STATUS_TRANSITIONS.get(old_status, set()):
            raise CustomException(msg=f"不允许从{old_label}转换为{new_label}")

        user = self.auth.user
        is_super = user.is_superuser if user else False
        is_creator = user and user.id and ticket.created_id == user.id
        is_assignee = user and user.id and ticket.assigned_id == user.id

        if new_status == 0:
            if not is_super:
                raise CustomException(msg="仅超管可以重新打开已关闭的工单")
        elif old_status == 0 and new_status == 1:
            if not (is_super or is_creator or is_assignee):
                raise CustomException(msg="仅创建人、处理人或超管可以受理工单")
        elif old_status == 0 and new_status == 3:
            if not (is_super or is_creator):
                raise CustomException(msg="仅创建人或超管可以取消工单")
        elif old_status == 1 and new_status == 2:
            if not (is_super or is_assignee):
                raise CustomException(msg="仅处理人或超管可以将工单标记为已完成")
        elif old_status == 1 and new_status == 3:
            if not (is_super or is_creator or is_assignee):
                raise CustomException(msg="仅创建人、处理人或超管可以关闭工单")
        elif old_status == 2 and new_status == 3:
            if not (is_super or is_creator):
                raise CustomException(msg="仅创建人或超管可以确认关闭工单")

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: TicketQueryParam | None = None,
        order_by: list | None = None,
    ) -> PageResultSchema[TicketOutSchema]:
        return await TicketCRUD(self.auth, self.db).page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"created_time": "desc"}],
            search=search_to_dict(search),
            out_schema=TicketOutSchema,
            preload=_TICKET_PRELOAD,
        )

    async def detail(self, id: int) -> TicketOutSchema:
        obj = await TicketCRUD(self.auth, self.db).get_or_404(id=id, preload=_TICKET_PRELOAD)
        return TicketOutSchema.model_validate(obj)

    async def create(self, data: TicketCreateSchema) -> TicketOutSchema:
        obj = await TicketCRUD(self.auth, self.db).create(data=data)
        if not obj:
            raise CustomException(msg="创建工单失败")
        return await self.detail(id=obj.id)

    async def update(self, id: int, data: TicketUpdateSchema) -> TicketOutSchema:
        obj = await TicketCRUD(self.auth, self.db).get_or_404(id=id, msg="工单不存在")

        if data.status is not None:
            self._validate_status_transition(obj, data.status)

        if data.assigned_id is not None:
            user_stmt = select(UserModel).where(
                UserModel.id == data.assigned_id,
                UserModel.is_deleted.is_(False),
            )
            user_result = await self.db.execute(user_stmt)
            assigned_user = user_result.scalar_one_or_none()
            if not assigned_user:
                raise CustomException(msg="指定的处理人不存在")

        updated = await TicketCRUD(self.auth, self.db).update(id=id, data=data)
        if not updated:
            raise CustomException(msg="工单不存在")

        return await self.detail(id=updated.id)

    async def delete(self, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除对象不能为空")
        await TicketCRUD(self.auth, self.db).delete(ids=ids)

    async def batch(self, data: TicketBatchSchema) -> None:
        if not data.ids:
            raise CustomException(msg="请选择要操作的工单")

        tickets = await TicketCRUD(self.auth, self.db).get_list(search={"id": ("in", data.ids)})
        ticket_map = {t.id: t for t in tickets}
        for tid in data.ids:
            obj = ticket_map.get(tid)
            if not obj:
                raise CustomException(msg=f"工单[{tid}]不存在")
            self._validate_status_transition(obj, data.status)
        await TicketCRUD(self.auth, self.db).set(ids=data.ids, status=data.status)

    async def get_list(
        self,
        search: TicketQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[TicketOutSchema]:
        obj_list = await TicketCRUD(self.auth, self.db).get_list(
            search=search_to_dict(search),
            order_by=order_by or [{"created_time": "desc"}],
            preload=_TICKET_PRELOAD,
        )
        return [TicketOutSchema.model_validate(obj) for obj in obj_list]

    @staticmethod
    async def export_list(ticket_list: list[dict[str, Any]]) -> bytes:
        """导出工单列表"""
        mapping_dict = {
            "id": "工单编号",
            "title": "工单标题",
            "ticket_type": "工单类型",
            "summary": "工单摘要",
            "status": "工单状态",
            "description": "备注",
            "created_time": "创建时间",
            "updated_time": "更新时间",
        }
        return await ExcelUtil.aexport_list2excel(list_data=ticket_list, mapping_dict=mapping_dict)


class TicketCommentService:
    """工单评论服务"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def page(self, ticket_id: int, page_no: int, page_size: int) -> PageResultSchema[TicketCommentOutSchema]:
        return await TicketCommentCRUD(self.auth, self.db).page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=[{"created_time": "desc"}],
            search={"ticket_id": ("eq", ticket_id)},
            out_schema=TicketCommentOutSchema,
        )

    async def create(self, ticket_id: int, data: TicketCommentCreateSchema) -> TicketCommentOutSchema:
        # 验证工单存在
        await TicketCRUD(self.auth, self.db).get_or_404(id=ticket_id, msg="工单不存在")
        create_data = data.model_dump() | {"ticket_id": ticket_id}
        obj = await TicketCommentCRUD(self.auth, self.db).create(data=create_data)  # type: ignore[arg-type]
        if not obj:
            raise CustomException(msg="评论失败")
        return TicketCommentOutSchema.model_validate(obj)

    async def delete(self, comment_id: int) -> None:
        await TicketCommentCRUD(self.auth, self.db).get_or_404(id=comment_id, msg="评论不存在")
        await TicketCommentCRUD(self.auth, self.db).delete(ids=[comment_id])
