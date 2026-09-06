from datetime import datetime, timedelta
from typing import Any, cast

from sqlalchemy import delete
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import AuthSchema, PageResultSchema
from app.core.database import async_db_session
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.utils.common_util import search_to_dict
from app.utils.excel_util import ExcelUtil

from .crud import LoginLogCRUD, OperationLogCRUD
from .model import LoginLogModel, OperationLogModel
from .schema import (
    LoginLogDetailOutSchema,
    LoginLogOutSchema,
    LoginLogQueryParam,
    OperationLogDetailOutSchema,
    OperationLogOutSchema,
    OperationLogQueryParam,
)


class LoginLogService:
    """登录日志管理服务"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def detail(self, id: int) -> LoginLogDetailOutSchema:
        obj = await LoginLogCRUD(self.auth, self.db).get_or_404(id=id)
        return LoginLogDetailOutSchema.model_validate(obj)

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: LoginLogQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[LoginLogOutSchema]:
        return await LoginLogCRUD(self.auth, self.db).page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"updated_time": "desc"}],
            search=search_to_dict(search),
            out_schema=LoginLogOutSchema,
        )

    async def delete(self, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")

        existing = await LoginLogCRUD(self.auth, self.db).get_list(search={"id": ("in", ids)})
        existing_map = {obj.id for obj in existing}
        for nid in ids:
            if nid not in existing_map:
                raise CustomException(msg=f"删除失败，ID为{nid}的数据不存在")

        await LoginLogCRUD(self.auth, self.db).delete(ids=ids)


class OperationLogService:
    """操作日志管理服务"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: OperationLogQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[OperationLogOutSchema]:
        crud = OperationLogCRUD(self.auth, self.db)
        return await crud.page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"id": "desc"}],
            search=search_to_dict(search),
            out_schema=OperationLogOutSchema,
        )

    async def detail(self, id: int) -> OperationLogDetailOutSchema:
        crud = OperationLogCRUD(self.auth, self.db)
        obj = await crud.get_or_404(id=id)
        return OperationLogDetailOutSchema.model_validate(obj)

    async def delete(self, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        existing = await OperationLogCRUD(self.auth, self.db).get_list(search={"id": ("in", ids)})
        existing_map = {obj.id for obj in existing}
        for nid in ids:
            if nid not in existing_map:
                raise CustomException(msg="删除失败，该数据不存在")
        crud = OperationLogCRUD(self.auth, self.db)
        await crud.delete(ids=ids)

    async def get_list(
        self,
        search: OperationLogQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[OperationLogOutSchema]:
        crud = OperationLogCRUD(self.auth, self.db)
        obj_list = await crud.get_list(
            search=search_to_dict(search),
            order_by=order_by or [{"id": "desc"}],
        )
        return [OperationLogOutSchema.model_validate(obj) for obj in obj_list]

    @staticmethod
    async def export_list(operation_log_list: list[dict[str, Any]]) -> bytes:
        """导出操作日志列表"""
        mapping_dict = {
            "id": "日志编号",
            "request_path": "请求路径",
            "request_method": "请求方法",
            "request_ip": "请求IP",
            "request_payload": "请求参数",
            "response_code": "响应状态码",
            "process_time": "耗时(ms)",
            "created_time": "操作时间",
            "created_id": "操作用户ID",
        }
        return await ExcelUtil.aexport_list2excel(list_data=operation_log_list, mapping_dict=mapping_dict)


async def cleanup_expired_logs(days: int = 90) -> dict:
    """按保留天数物理清理过期日志（供定时任务调用：无请求上下文，自建会话）。

    参数:
    - days (int): 日志保留天数，默认 90 天。

    返回:
    - dict: 各表清理条数统计。
    """
    if days <= 0:
        raise ValueError("日志保留天数必须大于 0")

    cutoff = datetime.now() - timedelta(days=days)
    async with async_db_session() as session:
        # DML 语句运行时返回 CursorResult（含 rowcount），静态类型是 Result，需 cast 收窄
        op_result = cast(CursorResult, await session.execute(delete(OperationLogModel).where(OperationLogModel.created_time < cutoff)))
        login_result = cast(CursorResult, await session.execute(delete(LoginLogModel).where(LoginLogModel.created_time < cutoff)))
        await session.commit()

    # rowcount 类型为 int | None，未命中行时驱动可能返回 None，兜底为 0
    stats = {
        "days": days,
        "operation_deleted": op_result.rowcount or 0,
        "login_deleted": login_result.rowcount or 0,
    }
    logger.info(
        f"日志保留清理完成（保留 {days} 天）: 操作日志 {stats['operation_deleted']} 条，登录日志 {stats['login_deleted']} 条"
    )
    return stats
