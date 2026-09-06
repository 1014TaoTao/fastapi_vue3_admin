import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Annotated, cast

from fastapi import APIRouter, Body, Depends, File, Form, Path, Query, Request, Security, UploadFile
from fastapi.responses import JSONResponse
from fastapi.sse import EventSourceResponse, ServerSentEvent
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.core.router_class import OperationLogRoute
from app.core.sse_manager import SSE_QUEUE_MAX_SIZE
from app.modules.task.storage.transfer.schema import (
    TransferTaskCreateResultSchema,
    TransferTaskCreateSchema,
    TransferTaskOutSchema,
    TransferTaskQueryParam,
    TransferTaskType,
)
from app.modules.task.storage.transfer.service import StorageTransferService
from app.modules.task.storage.transfer.sse_manager import transfer_stream_manager

StorageTransferRouter = APIRouter(route_class=OperationLogRoute, prefix="/storage/transfer", tags=["文件传输"])


@StorageTransferRouter.post("/task", summary="创建传输任务(远端源)", response_model=ResponseSchema[TransferTaskCreateResultSchema])
async def create_transfer_task_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:transfer:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[TransferTaskCreateSchema, Body(description="任务参数(远端源)")],
) -> JSONResponse:
    task_id: int = await StorageTransferService(auth, db).create(data=data)
    return SuccessResponse(data=TransferTaskCreateResultSchema(id=task_id), msg="创建传输任务成功")


@StorageTransferRouter.post("/task/upload", summary="创建传输任务(本地上传源)", response_model=ResponseSchema[TransferTaskCreateResultSchema])
async def create_local_transfer_task_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:transfer:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    file: Annotated[UploadFile, File(description="本地源文件")],
    name: Annotated[str, Form(description="任务名称")],
    task_type: Annotated[str, Form(description="任务类型(parallel:多目标 chain:链式)")],
    targets: Annotated[str, Form(description="目标列表JSON，如 [{\"target_id\":1,\"target_path\":\"a.txt\"}]")],
) -> JSONResponse:
    try:
        targets_data = json.loads(targets)
    except (json.JSONDecodeError, TypeError) as e:
        raise CustomException(msg=f"targets 参数格式错误: {e!s}") from e
    data = TransferTaskCreateSchema(name=name, task_type=cast("TransferTaskType", task_type), source_type="local", targets=targets_data)
    task_id: int = await StorageTransferService(auth, db).create_local(data=data, file=file)
    return SuccessResponse(data=TransferTaskCreateResultSchema(id=task_id), msg="创建传输任务成功")


@StorageTransferRouter.get("/task/page", summary="分页查询传输任务", response_model=ResponseSchema[PageResultSchema[TransferTaskOutSchema]])
async def get_transfer_task_page_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:transfer:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[TransferTaskQueryParam, Query()],
) -> JSONResponse:
    result: PageResultSchema[TransferTaskOutSchema] = await StorageTransferService(auth, db).page(
        search=search,
        page_no=page.page_no,
        page_size=page.page_size,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询传输任务分页成功")


@StorageTransferRouter.get("/task/{id}", summary="查询传输任务详情", response_model=ResponseSchema[TransferTaskOutSchema])
async def get_transfer_task_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:transfer:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="任务ID", ge=1)],
) -> JSONResponse:
    result: TransferTaskOutSchema = await StorageTransferService(auth, db).detail(task_id=id)
    return SuccessResponse(data=result, msg="查询传输任务详情成功")


@StorageTransferRouter.post("/task/{id}/cancel", summary="取消传输任务", response_model=ResponseSchema[None])
async def cancel_transfer_task_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:transfer:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="任务ID", ge=1)],
) -> JSONResponse:
    await StorageTransferService(auth, db).cancel(task_id=id)
    return SuccessResponse(msg="已请求取消传输任务")


@StorageTransferRouter.delete("/task", summary="删除传输任务", response_model=ResponseSchema[None])
async def delete_transfer_task_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:transfer:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    ids: Annotated[list[int], Body(description="任务ID列表")],
) -> JSONResponse:
    await StorageTransferService(auth, db).delete(ids=ids)
    return SuccessResponse(msg="删除传输任务成功")


@StorageTransferRouter.get("/stream", summary="传输任务进度实时流(SSE)", response_class=EventSourceResponse)
async def transfer_stream_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission())],
    request: Request,
) -> AsyncGenerator[ServerSentEvent, None]:
    """传输任务实时进度通道（SSE）：任务进度按创建者推送，客户端断开自动重连。

    令牌经 Authorization 头携带（复用 HTTP 认证链，不进 URL）；事件名 task_update，
    载荷为任务完整状态（含步骤）。空闲保活由框架内置 ping（15s 注释行）处理。
    """
    queue: asyncio.Queue = asyncio.Queue(maxsize=SSE_QUEUE_MAX_SIZE)
    transfer_stream_manager.connect(auth.user.id, queue, redis=getattr(request.app.state, "redis", None))
    logger.info("传输进度 SSE 已连接: user={}", auth.user.id)
    try:
        while True:
            message = await queue.get()
            yield ServerSentEvent(event=str(message.get("type", "message")), data=message.get("data", message))
    finally:
        transfer_stream_manager.disconnect(auth.user.id, queue)
        logger.info("传输进度 SSE 已断开: user={}", auth.user.id)
