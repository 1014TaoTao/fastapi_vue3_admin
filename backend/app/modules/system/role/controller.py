from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Query, Security, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, StreamResponse, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute
from app.utils.common_util import bytes2file_response

from .schema import RoleCreateSchema, RoleOutSchema, RolePermissionSettingSchema, RoleQueryParam, RoleUpdateSchema
from .service import RoleService

RoleRouter = APIRouter(route_class=OperationLogRoute, prefix="/role", tags=["角色管理"])


@RoleRouter.get("/list", summary="查询角色", response_model=ResponseSchema[PageResultSchema[RoleOutSchema]])
async def get_role_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:role:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[RoleQueryParam, Query()],
) -> JSONResponse:
    result_dict: PageResultSchema[RoleOutSchema] = await RoleService(auth, db).page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result_dict, msg="查询角色成功")


@RoleRouter.get("/detail/{id}", summary="查询角色详情", response_model=ResponseSchema[RoleOutSchema])
async def get_role_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:role:detail"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="角色ID", ge=1)],
) -> JSONResponse:
    result_dict: RoleOutSchema = await RoleService(auth, db).detail(id=id)
    return SuccessResponse(data=result_dict, msg="获取角色详情成功")


@RoleRouter.post("/create", status_code=status.HTTP_201_CREATED, summary="创建角色", response_model=ResponseSchema[RoleOutSchema])
async def create_role_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:role:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[RoleCreateSchema, Body(description="角色创建参数")],
) -> JSONResponse:
    result_dict: RoleOutSchema = await RoleService(auth, db).create(data=data)
    return SuccessResponse(data=result_dict, msg="创建角色成功")


@RoleRouter.put("/update/{id}", summary="修改角色", response_model=ResponseSchema[RoleOutSchema])
async def update_role_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:role:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="角色ID", ge=1)],
    data: Annotated[RoleUpdateSchema, Body(description="角色修改参数")],
) -> JSONResponse:
    result_dict: RoleOutSchema = await RoleService(auth, db).update(id=id, data=data)
    return SuccessResponse(data=result_dict, msg="修改角色成功")


@RoleRouter.delete("/delete", summary="删除角色", response_model=ResponseSchema[None])
async def delete_role_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:role:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    ids: Annotated[list[int], Body(description="ID列表")],
) -> JSONResponse:
    await RoleService(auth, db).delete(ids=ids)
    return SuccessResponse(msg="删除角色成功")


@RoleRouter.patch("/status/batch", summary="批量修改角色状态", response_model=ResponseSchema[None])
async def batch_set_available_role_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:role:patch"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[BatchSetAvailable, Body(description="状态设置")],
) -> JSONResponse:
    await RoleService(auth, db).set_available(data=data)
    return SuccessResponse(msg="批量修改角色状态成功")


@RoleRouter.put("/permission", summary="角色授权", response_model=ResponseSchema[None])
async def set_role_permission_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:role:permission"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[RolePermissionSettingSchema, Body(description="角色授权参数")],
) -> JSONResponse:
    await RoleService(auth, db).set_permission(data=data)
    return SuccessResponse(msg="授权角色成功")


@RoleRouter.get("/options", summary="获取角色下拉选项", response_model=ResponseSchema[list[dict[str, int | str]]])
async def get_role_options_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:role:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    options: list[dict[str, Any]] = await RoleService(auth, db).get_options()
    return SuccessResponse(data=options, msg="获取角色选项成功")


@RoleRouter.post("/export", summary="导出角色")
async def export_role_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:role:export"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    search: Annotated[RoleQueryParam, Body()],
) -> StreamingResponse:
    role_query_result: list[RoleOutSchema] = await RoleService(auth, db).get_list(search=search)
    role_export_result: bytes = await RoleService.export_list(role_list=[item.model_dump() for item in role_query_result])

    return StreamResponse(
        data=bytes2file_response(role_export_result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=role.xlsx"},
    )
