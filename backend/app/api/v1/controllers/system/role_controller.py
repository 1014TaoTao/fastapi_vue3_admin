# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse

from app.common.response import StreamResponse, SuccessResponse
from app.core.router_class import OperationLogRoute
from app.core.base_params import PaginationQueryParams
from app.api.v1.params.system.role_param import RoleQueryParams
from app.core.dependencies import AuthPermission
from app.api.v1.services.system.role_service import RoleService
from app.api.v1.schemas.system.auth_schema import AuthSchema
from app.api.v1.schemas.system.role_schema import (
    RoleCreateSchema,
    RoleUpdateSchema,
    RolePermissionSettingSchema
)
from app.core.base_schema import BatchSetAvailable
from app.core.logger import logger
from app.common.request import PaginationService
from app.utils.common_util import bytes2file_response


router = APIRouter(route_class=OperationLogRoute)


@router.get("/list", summary="查询角色", description="查询角色")
async def get_obj_list_controller(
    page: PaginationQueryParams = Depends(),
    search: RoleQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:role:query"])),
) -> JSONResponse:
    result_dict_list = await RoleService.get_role_list_service(search=search, auth=auth, order_by=page.order_by)
    result_dict = await PaginationService.get_page_obj(data_list= result_dict_list, page_no= page.page_no, page_size = page.page_size)
    logger.info("查询角色成功")
    return SuccessResponse(data=result_dict, msg="查询角色成功")


@router.get("/detail", summary="查询角色详情", description="查询角色详情")
async def get_obj_detail_controller(
    id: str = Query(..., description="角色ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:role:query"])),
) -> JSONResponse:
    result_dict = await RoleService.get_role_detail_service(id=id, auth=auth)
    logger.info(f"获取角色详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取角色详情成功")


@router.post("/create", summary="创建角色", description="创建角色")
async def create_obj_controller(
    data: RoleCreateSchema,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:role:create"])),
) -> JSONResponse:
    result_dict = await RoleService.create_role_service(data=data, auth=auth)
    logger.info(f"创建角色成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="创建角色成功")


@router.put("/update", summary="修改角色", description="修改角色")
async def update_obj_controller(
    data: RoleUpdateSchema,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:role:update"])),
) -> JSONResponse:
    result_dict = await RoleService.update_role_service(data=data, auth=auth)
    logger.info(f"修改角色成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="修改角色成功")


@router.delete("/delete", summary="删除角色", description="删除角色")
async def delete_obj_controller(
    id: str = Query(..., description="角色ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:role:delete"])),
) -> JSONResponse:
    await RoleService.delete_role_service(id=id, auth=auth)
    logger.info(f"删除角色成功: {id}")
    return SuccessResponse(msg="删除角色成功")


@router.patch("/available/setting", summary="批量修改角色状态", description="批量修改角色状态")
async def batch_set_available_obj_controller(
    data: BatchSetAvailable,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:role:patch"])),
) -> JSONResponse:
    await RoleService.set_role_available_service(data=data, auth=auth)
    logger.info(f"批量修改角色状态成功: {data.ids}")
    return SuccessResponse(msg="批量修改角色状态成功")


@router.patch("/permission/setting", summary="角色授权", description="角色授权")
async def set_role_permission_controller(
    data: RolePermissionSettingSchema,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:role:permission"])),
) -> JSONResponse:
    await RoleService.set_role_permission_service(data=data, auth=auth)
    logger.info(f"设置角色权限成功: {data}")
    return SuccessResponse(msg="授权角色成功")


@router.post('/export', summary="导出角色", description="导出角色")
async def export_obj_list_controller(
    search: RoleQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:role:export"])),
) -> StreamingResponse:
    # 获取全量数据
    role_query_result = await RoleService.get_role_list_service(search=search, auth=auth)
    role_export_result = await RoleService.export_role_list_service(role_list=role_query_result)
    logger.info('导出角色成功')

    return StreamResponse(
        data=bytes2file_response(role_export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers = {
            'Content-Disposition': 'attachment; filename=data.xlsx'
        }
    )
