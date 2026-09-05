from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Security, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute
from app.modules.workflow.flow.schema import WorkflowFlowCreateSchema, WorkflowFlowExecuteSchema, WorkflowFlowOutSchema, WorkflowFlowQueryParam, WorkflowFlowUpdateSchema
from app.modules.workflow.flow.service import WorkflowFlowService

WorkflowFlowRouter = APIRouter(route_class=OperationLogRoute, prefix="/flow", tags=["传输流程"])


@WorkflowFlowRouter.get("/page", summary="分页查询传输流程", response_model=ResponseSchema[PageResultSchema[WorkflowFlowOutSchema]])
async def get_flow_page_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:workflow:flow:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[WorkflowFlowQueryParam, Query()],
) -> JSONResponse:
    result: PageResultSchema[WorkflowFlowOutSchema] = await WorkflowFlowService(auth, db).page(
        search=search,
        page_no=page.page_no,
        page_size=page.page_size,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询传输流程分页成功")


@WorkflowFlowRouter.get("/list", summary="查询传输流程列表", response_model=ResponseSchema[list[WorkflowFlowOutSchema]])
async def get_flow_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:workflow:flow:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    search: Annotated[WorkflowFlowQueryParam, Query()],
) -> JSONResponse:
    result: list[WorkflowFlowOutSchema] = await WorkflowFlowService(auth, db).get_list(search=search)
    return SuccessResponse(data=result, msg="查询传输流程列表成功")


@WorkflowFlowRouter.get("/detail/{id}", summary="查询传输流程详情", response_model=ResponseSchema[WorkflowFlowOutSchema])
async def get_flow_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:workflow:flow:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="流程ID", ge=1)],
) -> JSONResponse:
    result: WorkflowFlowOutSchema = await WorkflowFlowService(auth, db).detail(id=id)
    return SuccessResponse(data=result, msg="查询传输流程详情成功")


@WorkflowFlowRouter.post("/create", status_code=status.HTTP_201_CREATED, summary="创建传输流程", response_model=ResponseSchema[WorkflowFlowOutSchema])
async def create_flow_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:workflow:flow:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[WorkflowFlowCreateSchema, Body(description="流程创建参数")],
) -> JSONResponse:
    result: WorkflowFlowOutSchema = await WorkflowFlowService(auth, db).create(data=data)
    return SuccessResponse(data=result, msg="创建传输流程成功")


@WorkflowFlowRouter.put("/update/{id}", summary="修改传输流程", response_model=ResponseSchema[WorkflowFlowOutSchema])
async def update_flow_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:workflow:flow:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="流程ID", ge=1)],
    data: Annotated[WorkflowFlowUpdateSchema, Body(description="流程修改参数")],
) -> JSONResponse:
    result: WorkflowFlowOutSchema = await WorkflowFlowService(auth, db).update(id=id, data=data)
    return SuccessResponse(data=result, msg="修改传输流程成功")


@WorkflowFlowRouter.delete("/delete", summary="删除传输流程", response_model=ResponseSchema[None])
async def delete_flow_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:workflow:flow:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    ids: Annotated[list[int], Body(description="流程ID列表")],
) -> JSONResponse:
    await WorkflowFlowService(auth, db).delete(ids=ids)
    return SuccessResponse(msg="删除传输流程成功")


@WorkflowFlowRouter.post("/execute/{id}", summary="执行传输流程", response_model=ResponseSchema[list[int]])
async def execute_flow_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:workflow:transfer:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="流程ID", ge=1)],
    data: Annotated[WorkflowFlowExecuteSchema | None, Body(description="执行参数（源文件/目录路径映射，可选）")] = None,
) -> JSONResponse:
    task_ids: list[int] = await WorkflowFlowService(auth, db).execute(
        id=id, source_paths=data.source_paths if data else None
    )
    return SuccessResponse(data=task_ids, msg=f"执行传输流程成功，已生成 {len(task_ids)} 个传输任务")
