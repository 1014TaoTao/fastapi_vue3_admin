from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Security, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, StreamResponse, SuccessResponse
from app.core.base_schema import AuthSchema, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute
from app.utils.common_util import bytes2file_response

from .schema import TicketBatchSchema, TicketCommentCreateSchema, TicketCommentOutSchema, TicketCreateSchema, TicketOutSchema, TicketQueryParam, TicketUpdateSchema
from .service import TicketCommentService, TicketService

TicketRouter = APIRouter(route_class=OperationLogRoute, prefix="/ticket", tags=["工单管理"])


@TicketRouter.get("/list", summary="工单列表", response_model=ResponseSchema[PageResultSchema[TicketOutSchema]])
async def ticket_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:ticket:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[TicketQueryParam, Query()],
) -> JSONResponse:
    result = await TicketService(auth, db).page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询成功")


@TicketRouter.get("/detail/{id}", summary="获取工单详情", response_model=ResponseSchema[TicketOutSchema])
async def ticket_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:ticket:detail"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="工单ID")],
) -> JSONResponse:
    result = await TicketService(auth, db).detail(id=id)
    return SuccessResponse(data=result, msg="查询成功")


@TicketRouter.post("/create", status_code=status.HTTP_201_CREATED, summary="创建工单", response_model=ResponseSchema[TicketOutSchema])
async def ticket_create_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:ticket:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[TicketCreateSchema, Body(description="工单创建参数")],
) -> JSONResponse:
    result = await TicketService(auth, db).create(data=data)
    return SuccessResponse(data=result, msg="创建成功")


@TicketRouter.put("/update/{id}", summary="更新工单", response_model=ResponseSchema[TicketOutSchema])
async def ticket_update_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:ticket:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="工单ID", ge=1)],
    data: Annotated[TicketUpdateSchema, Body(description="工单更新参数")],
) -> JSONResponse:
    result = await TicketService(auth, db).update(id=id, data=data)
    return SuccessResponse(data=result, msg="更新成功")


@TicketRouter.put("/batch", summary="批量更新工单", response_model=ResponseSchema)
async def ticket_batch_update_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:ticket:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[TicketBatchSchema, Body(description="工单批量更新参数")],
) -> JSONResponse:
    await TicketService(auth, db).batch(data=data)
    return SuccessResponse(msg="批量操作成功")


@TicketRouter.delete("/delete", summary="删除工单", response_model=ResponseSchema[None])
async def ticket_delete_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:ticket:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    ids: Annotated[list[int], Body(description="工单ID列表")],
) -> JSONResponse:
    await TicketService(auth, db).delete(ids=ids)
    return SuccessResponse(msg="删除成功")


@TicketRouter.post("/export", summary="导出工单")
async def ticket_export_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:ticket:export"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    search: Annotated[TicketQueryParam, Body()],
) -> StreamingResponse:
    ticket_list = await TicketService(auth, db).get_list(search=search)
    export_result = await TicketService.export_list(ticket_list=[item.model_dump() for item in ticket_list])

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=ticket.xlsx"},
    )


@TicketRouter.get("/{ticket_id}/comments", summary="工单评论列表", response_model=ResponseSchema[PageResultSchema[TicketCommentOutSchema]])
async def ticket_comment_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:ticket:detail"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    ticket_id: Annotated[int, Path(description="工单ID")],
    page: Annotated[PaginationQueryParam, Depends()],
) -> JSONResponse:
    result = await TicketCommentService(auth, db).page(ticket_id=ticket_id, page_no=page.page_no, page_size=page.page_size)
    return SuccessResponse(data=result, msg="查询成功")


@TicketRouter.post("/{ticket_id}/comments", status_code=status.HTTP_201_CREATED, summary="创建评论", response_model=ResponseSchema[TicketCommentOutSchema])
async def ticket_comment_create_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:ticket:detail"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    ticket_id: Annotated[int, Path(description="工单ID")],
    data: Annotated[TicketCommentCreateSchema, Body(description="评论内容")],
) -> JSONResponse:
    result = await TicketCommentService(auth, db).create(ticket_id=ticket_id, data=data)
    return SuccessResponse(data=result, msg="评论成功")
