from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Security, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute

from .schema import NodeCreateSchema, NodeOutSchema, NodeQueryParam, NodeRunResultSchema, NodeUpdateSchema
from .service import NodeService

CornJobNodeRouter = APIRouter(route_class=OperationLogRoute, prefix="/cronjob/node", tags=["定时任务节点管理"])


@CornJobNodeRouter.get("/options", summary="获取定时任务节点列表", response_model=ResponseSchema[list[NodeOutSchema]])
async def get_node_options_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:cronjob:node:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = NodeService(auth, db)
    result: list[NodeOutSchema] = await service.options()
    return SuccessResponse(data=result, msg="获取定时任务节点选项成功")


@CornJobNodeRouter.get("/detail/{id}", summary="获取节点详情", response_model=ResponseSchema[NodeOutSchema])
async def get_obj_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:cronjob:node:detail"]))],
    id: Annotated[int, Path(description="节点ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = NodeService(auth, db)
    result_dict: NodeOutSchema = await service.detail(id=id)
    return SuccessResponse(data=result_dict, msg="获取节点详情成功")


@CornJobNodeRouter.get("/list", summary="查询节点", response_model=ResponseSchema[PageResultSchema[NodeOutSchema]])
async def get_obj_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:cronjob:node:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[NodeQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = NodeService(auth, db)
    result_dict: PageResultSchema[NodeOutSchema] = await service.page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result_dict, msg="查询节点列表成功")


@CornJobNodeRouter.post("/create", status_code=status.HTTP_201_CREATED, summary="创建节点", response_model=ResponseSchema[NodeOutSchema])
async def create_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:cronjob:node:create"]))],
    data: Annotated[NodeCreateSchema, Body(description="创建节点参数")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = NodeService(auth, db)
    result_dict: NodeOutSchema = await service.create(data=data)
    return SuccessResponse(data=result_dict, msg="创建节点成功")


@CornJobNodeRouter.put("/update/{id}", summary="修改节点", response_model=ResponseSchema[NodeOutSchema])
async def update_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:cronjob:node:update"]))],
    id: Annotated[int, Path(description="节点ID")],
    data: Annotated[NodeUpdateSchema, Body(description="修改节点参数")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = NodeService(auth, db)
    result_dict: NodeOutSchema = await service.update(id=id, data=data)
    return SuccessResponse(data=result_dict, msg="修改节点成功")


@CornJobNodeRouter.delete("/delete", summary="删除节点", response_model=ResponseSchema[None])
async def delete_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:cronjob:node:delete"]))],
    ids: Annotated[list[int], Body(description="ID列表")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = NodeService(auth, db)
    await service.delete(ids=ids)
    return SuccessResponse(msg="删除节点成功")


@CornJobNodeRouter.delete("/clear", summary="清空节点", response_model=ResponseSchema[None])
async def clear_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:cronjob:node:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = NodeService(auth, db)
    await service.clear()
    return SuccessResponse(msg="清空节点成功")


@CornJobNodeRouter.post("/execute/{id}", summary="手动执行节点（立即执行一次）", response_model=ResponseSchema[NodeRunResultSchema])
async def execute_job_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:cronjob:node:execute"]))],
    id: Annotated[int, Path(description="节点ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = NodeService(auth, db)
    result: NodeRunResultSchema = await service.execute(id=id)
    return SuccessResponse(data=result, msg="节点已触发执行")


@CornJobNodeRouter.patch("/status/batch", summary="批量设置节点状态", response_model=ResponseSchema[None])
async def batch_set_status_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:cronjob:node:update"]))],
    data: Annotated[BatchSetAvailable, Body(description="状态设置")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = NodeService(auth, db)
    await service.batch_set_status(ids=data.ids, status=data.status)
    return SuccessResponse(msg="批量设置节点状态成功")
