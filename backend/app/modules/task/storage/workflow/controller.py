from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Security, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute
from app.modules.task.storage.workflow.schema import WorkflowCreateSchema, WorkflowExecuteSchema, WorkflowOutSchema, WorkflowQueryParam, WorkflowUpdateSchema
from app.modules.task.storage.workflow.service import WorkflowService

StorageWorkflowRouter = APIRouter(route_class=OperationLogRoute, prefix="/storage/workflow", tags=["传输流程"])


@StorageWorkflowRouter.get("/page", summary="分页查询传输流程", response_model=ResponseSchema[PageResultSchema[WorkflowOutSchema]])
async def get_flow_page_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:flow:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[WorkflowQueryParam, Query()],
) -> JSONResponse:
    result: PageResultSchema[WorkflowOutSchema] = await WorkflowService(auth, db).page(
        search=search,
        page_no=page.page_no,
        page_size=page.page_size,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询传输流程分页成功")


@StorageWorkflowRouter.get("/list", summary="查询传输流程列表", response_model=ResponseSchema[list[WorkflowOutSchema]])
async def get_flow_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:flow:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    search: Annotated[WorkflowQueryParam, Query()],
) -> JSONResponse:
    result: list[WorkflowOutSchema] = await WorkflowService(auth, db).get_list(search=search)
    return SuccessResponse(data=result, msg="查询传输流程列表成功")


@StorageWorkflowRouter.get("/detail/{id}", summary="查询传输流程详情", response_model=ResponseSchema[WorkflowOutSchema])
async def get_flow_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:flow:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="流程ID", ge=1)],
) -> JSONResponse:
    result: WorkflowOutSchema = await WorkflowService(auth, db).detail(id=id)
    return SuccessResponse(data=result, msg="查询传输流程详情成功")


@StorageWorkflowRouter.post("/create", status_code=status.HTTP_201_CREATED, summary="创建传输流程", response_model=ResponseSchema[WorkflowOutSchema])
async def create_flow_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:flow:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[WorkflowCreateSchema, Body(description="流程创建参数")],
) -> JSONResponse:
    result: WorkflowOutSchema = await WorkflowService(auth, db).create(data=data)
    return SuccessResponse(data=result, msg="创建传输流程成功")


@StorageWorkflowRouter.put("/update/{id}", summary="修改传输流程", response_model=ResponseSchema[WorkflowOutSchema])
async def update_flow_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:flow:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="流程ID", ge=1)],
    data: Annotated[WorkflowUpdateSchema, Body(description="流程修改参数")],
) -> JSONResponse:
    result: WorkflowOutSchema = await WorkflowService(auth, db).update(id=id, data=data)
    return SuccessResponse(data=result, msg="修改传输流程成功")


@StorageWorkflowRouter.delete("/delete", summary="删除传输流程", response_model=ResponseSchema[None])
async def delete_flow_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:flow:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    ids: Annotated[list[int], Body(description="流程ID列表")],
) -> JSONResponse:
    await WorkflowService(auth, db).delete(ids=ids)
    return SuccessResponse(msg="删除传输流程成功")


@StorageWorkflowRouter.post("/execute/{id}", summary="执行传输流程", response_model=ResponseSchema[list[int]])
async def execute_flow_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:transfer:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="流程ID", ge=1)],
    data: Annotated[WorkflowExecuteSchema | None, Body(description="执行参数（源文件/目录路径映射，可选）")] = None,
) -> JSONResponse:
    task_ids: list[int] = await WorkflowService(auth, db).execute(
        id=id, source_paths=data.source_paths if data else None
    )
    return SuccessResponse(data=task_ids, msg=f"执行传输流程成功，已生成 {len(task_ids)} 个传输任务")
