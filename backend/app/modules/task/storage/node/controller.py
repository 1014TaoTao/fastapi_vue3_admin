from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Security, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute
from app.modules.task.storage.core.base import (
    ADVANCED_FIELD_DEFS,
    DEFAULT_PORTS,
    AdvancedFieldDefSchema,
    StorageProtocol,
    StorageProtocolDefSchema,
)

from .schema import StorageNodeCreateSchema, StorageNodeOutSchema, StorageNodeQueryParam, StorageNodeTestSchema, StorageNodeUpdateSchema
from .service import StorageNodeService

StorageNodeRouter = APIRouter(route_class=OperationLogRoute, prefix="/storage/node", tags=["节点管理"])


@StorageNodeRouter.get("/protocols", summary="查询支持的存储协议", response_model=ResponseSchema[list[StorageProtocolDefSchema]])
async def get_storage_protocols_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:node:query"]))],
) -> JSONResponse:
    result: list[StorageProtocolDefSchema] = [
        StorageProtocolDefSchema(protocol=p.value, name=p.name, default_port=DEFAULT_PORTS[p])
        for p in StorageProtocol
    ]
    return SuccessResponse(data=result, msg="查询存储协议成功")


@StorageNodeRouter.get("/advanced-fields", summary="查询存储 SDK 高级配置字段定义", response_model=ResponseSchema[dict[str, list[AdvancedFieldDefSchema]]])
async def get_advanced_fields_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:node:query"]))],
) -> JSONResponse:
    """返回按协议分组的 SDK 高级配置字段元数据，供前端「高级设置」面板按协议动态渲染。"""
    return SuccessResponse(data=ADVANCED_FIELD_DEFS, msg="查询高级配置字段成功")


@StorageNodeRouter.get("/page", summary="分页查询存储源", response_model=ResponseSchema[PageResultSchema[StorageNodeOutSchema]])
async def get_storage_source_page_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:node:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[StorageNodeQueryParam, Query()],
) -> JSONResponse:
    result: PageResultSchema[StorageNodeOutSchema] = await StorageNodeService(auth, db).page(
        search=search,
        page_no=page.page_no,
        page_size=page.page_size,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询存储源分页成功")


@StorageNodeRouter.get("/list", summary="查询存储源列表", response_model=ResponseSchema[list[StorageNodeOutSchema]])
async def get_storage_source_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:node:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    search: Annotated[StorageNodeQueryParam, Query()],
) -> JSONResponse:
    result: list[StorageNodeOutSchema] = await StorageNodeService(auth, db).get_list(search=search)
    return SuccessResponse(data=result, msg="查询存储源列表成功")


@StorageNodeRouter.get("/detail/{id}", summary="查询存储源详情", response_model=ResponseSchema[StorageNodeOutSchema])
async def get_storage_source_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:node:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="存储源ID", ge=1)],
) -> JSONResponse:
    result: StorageNodeOutSchema = await StorageNodeService(auth, db).detail(id=id)
    return SuccessResponse(data=result, msg="查询存储源详情成功")


@StorageNodeRouter.post("/create", status_code=status.HTTP_201_CREATED, summary="创建存储源", response_model=ResponseSchema[StorageNodeOutSchema])
async def create_storage_source_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:node:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[StorageNodeCreateSchema, Body(description="存储源创建参数")],
) -> JSONResponse:
    result: StorageNodeOutSchema = await StorageNodeService(auth, db).create(data=data)
    return SuccessResponse(data=result, msg="创建存储源成功")


@StorageNodeRouter.put("/update/{id}", summary="修改存储源", response_model=ResponseSchema[StorageNodeOutSchema])
async def update_storage_source_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:node:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="存储源ID", ge=1)],
    data: Annotated[StorageNodeUpdateSchema, Body(description="存储源修改参数")],
) -> JSONResponse:
    result: StorageNodeOutSchema = await StorageNodeService(auth, db).update(id=id, data=data)
    return SuccessResponse(data=result, msg="修改存储源成功")


@StorageNodeRouter.delete("/delete", summary="删除存储源", response_model=ResponseSchema[None])
async def delete_storage_source_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:node:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    ids: Annotated[list[int], Body(description="存储源ID列表")],
) -> JSONResponse:
    await StorageNodeService(auth, db).delete(ids=ids)
    return SuccessResponse(msg="删除存储源成功")


@StorageNodeRouter.post("/test/{id}", summary="测试存储源连接", response_model=ResponseSchema[bool])
async def test_storage_source_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:node:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="存储源ID", ge=1)],
) -> JSONResponse:
    result: bool = await StorageNodeService(auth, db).test_connection(id=id)
    return SuccessResponse(data=result, msg="连接成功")


@StorageNodeRouter.post("/test", summary="测试存储源连接(配置)", response_model=ResponseSchema[bool])
async def test_storage_source_config_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:storage:node:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[StorageNodeTestSchema, Body(description="存储源连接配置")],
) -> JSONResponse:
    result: bool = await StorageNodeService(auth, db).test_config(data=data)
    return SuccessResponse(data=result, msg="连接成功")
