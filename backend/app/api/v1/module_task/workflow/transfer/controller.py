import json
from typing import Annotated, cast

from fastapi import APIRouter, Body, Depends, File, Form, Path, Query, Security, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_task.workflow.transfer.schema import (
    TransferTaskCreateResultSchema,
    TransferTaskCreateSchema,
    TransferTaskOutSchema,
    TransferTaskQueryParam,
    TransferTaskType,
)
from app.api.v1.module_task.workflow.transfer.service import StorageTransferService
from app.api.v1.module_task.workflow.transfer.ws_manager import transfer_ws_manager
from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter, websocket_authenticate
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.core.router_class import OperationLogRoute

StorageTransferRouter = APIRouter(route_class=OperationLogRoute, prefix="/transfer", tags=["文件传输"])


@StorageTransferRouter.post("/task", summary="创建传输任务(远端源)", response_model=ResponseSchema[TransferTaskCreateResultSchema])
async def create_transfer_task_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:workflow:transfer:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[TransferTaskCreateSchema, Body(description="任务参数(远端源)")],
) -> JSONResponse:
    task_id = await StorageTransferService(auth, db).create(data=data)
    return SuccessResponse(data=TransferTaskCreateResultSchema(id=task_id), msg="创建传输任务成功")


@StorageTransferRouter.post("/task/upload", summary="创建传输任务(本地上传源)", response_model=ResponseSchema[TransferTaskCreateResultSchema])
async def create_local_transfer_task_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:workflow:transfer:create"]))],
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
    task_id = await StorageTransferService(auth, db).create_local(data=data, file=file)
    return SuccessResponse(data=TransferTaskCreateResultSchema(id=task_id), msg="创建传输任务成功")


@StorageTransferRouter.get("/task/page", summary="分页查询传输任务", response_model=ResponseSchema[PageResultSchema[TransferTaskOutSchema]])
async def get_transfer_task_page_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:workflow:transfer:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[TransferTaskQueryParam, Query()],
) -> JSONResponse:
    result = await StorageTransferService(auth, db).page(
        search=search,
        page_no=page.page_no,
        page_size=page.page_size,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询传输任务分页成功")


@StorageTransferRouter.get("/task/{id}", summary="查询传输任务详情", response_model=ResponseSchema[TransferTaskOutSchema])
async def get_transfer_task_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:workflow:transfer:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="任务ID", ge=1)],
) -> JSONResponse:
    result = await StorageTransferService(auth, db).detail(task_id=id)
    return SuccessResponse(data=result, msg="查询传输任务详情成功")


@StorageTransferRouter.post("/task/{id}/cancel", summary="取消传输任务", response_model=ResponseSchema[None])
async def cancel_transfer_task_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:workflow:transfer:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="任务ID", ge=1)],
) -> JSONResponse:
    await StorageTransferService(auth, db).cancel(task_id=id)
    return SuccessResponse(msg="已请求取消传输任务")


@StorageTransferRouter.delete("/task", summary="删除传输任务", response_model=ResponseSchema[None])
async def delete_transfer_task_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:workflow:transfer:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    ids: Annotated[list[int], Body(description="任务ID列表")],
) -> JSONResponse:
    await StorageTransferService(auth, db).delete(ids=ids)
    return SuccessResponse(msg="删除传输任务成功")


@StorageTransferRouter.websocket("/ws")
async def transfer_ws_endpoint(ws: WebSocket) -> None:
    """传输任务实时进度通道：令牌通过 Sec-WebSocket-Protocol 携带（小程序可用 ?token=），任务进度按创建者推送。"""
    try:
        auth, subprotocol = await websocket_authenticate(ws)
    except Exception as e:
        logger.warning("传输 WebSocket 认证失败: {}", e)
        await ws.close(code=4001, reason="无效令牌")
        return
    user_id = auth.user.id

    await transfer_ws_manager.connect(user_id, ws, subprotocol=subprotocol)
    logger.info("传输 WebSocket 已连接: user={}", user_id)
    try:
        while True:
            text = await ws.receive_text()
            if text == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning("传输 WebSocket 异常断开: user={}, err={}", user_id, e)
    finally:
        transfer_ws_manager.disconnect(user_id, ws)
        logger.info("传输 WebSocket 已断开: user={}", user_id)
