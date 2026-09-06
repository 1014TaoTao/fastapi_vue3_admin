from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Security, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute

from .schema import (
    VersionCreateSchema,
    VersionOutSchema,
    VersionQueryParam,
    VersionStatusSchema,
    VersionUpdateSchema,
)
from .service import VersionService

VersionRouter = APIRouter(route_class=OperationLogRoute, prefix="/versions", tags=["版本管理"])


@VersionRouter.get("/list", summary="分页查询版本", response_model=ResponseSchema[PageResultSchema[VersionOutSchema]])
async def get_version_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:version:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[VersionQueryParam, Query()],
) -> JSONResponse:
    service = VersionService(auth, db)
    result: PageResultSchema[VersionOutSchema] = await service.page(page_no=page.page_no, page_size=page.page_size, search=search)
    return SuccessResponse(data=result, msg="查询版本列表成功")


@VersionRouter.get("/published", summary="已发布版本列表", response_model=ResponseSchema[list[VersionOutSchema]])
async def get_published_versions_controller(
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    auth = AuthSchema()
    service = VersionService(auth, db)
    result: list[VersionOutSchema] = await service.get_published()
    return SuccessResponse(data=result, msg="查询成功")


@VersionRouter.get("/detail/{id}", summary="获取版本详情", response_model=ResponseSchema[VersionOutSchema])
async def get_version_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:version:detail"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="版本ID", ge=1)],
) -> JSONResponse:
    service = VersionService(auth, db)
    result: VersionOutSchema = await service.detail(id=id)
    return SuccessResponse(data=result, msg="获取版本详情成功")


@VersionRouter.post("/create", status_code=status.HTTP_201_CREATED, summary="创建版本", response_model=ResponseSchema[VersionOutSchema])
async def create_version_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:version:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[VersionCreateSchema, Body(description="创建参数")],
) -> JSONResponse:
    service = VersionService(auth, db)
    result: VersionOutSchema = await service.create(data=data)
    return SuccessResponse(data=result, msg="创建版本成功")


@VersionRouter.put("/update/{id}", summary="修改版本", response_model=ResponseSchema[VersionOutSchema])
async def update_version_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:version:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="版本ID", ge=1)],
    data: Annotated[VersionUpdateSchema, Body(description="修改参数")],
) -> JSONResponse:
    service = VersionService(auth, db)
    result: VersionOutSchema = await service.update(id=id, data=data)
    return SuccessResponse(data=result, msg="修改版本成功")


@VersionRouter.delete("/delete", summary="删除版本", response_model=ResponseSchema[None])
async def delete_version_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:version:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    ids: Annotated[list[int], Body(description="ID列表")],
) -> JSONResponse:
    service = VersionService(auth, db)
    await service.delete(ids=ids)
    return SuccessResponse(msg="删除版本成功")


@VersionRouter.put("/{id}/status", summary="变更版本状态", response_model=ResponseSchema[VersionOutSchema])
async def set_version_status_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:version:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="版本ID", ge=1)],
    data: Annotated[VersionStatusSchema, Body(description="状态参数")],
) -> JSONResponse:
    service = VersionService(auth, db)
    result: VersionOutSchema = await service.set_status(id=id, data=data)
    return SuccessResponse(data=result, msg="状态变更成功")
