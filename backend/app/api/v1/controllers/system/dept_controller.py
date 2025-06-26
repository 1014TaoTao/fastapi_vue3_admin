# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.common.response import SuccessResponse
from app.core.router_class import OperationLogRoute
from app.api.v1.params.system.dept_param import DeptQueryParams
from app.core.dependencies import AuthPermission
from app.api.v1.services.system.dept_service import DeptService
from app.api.v1.schemas.system.dept_schema import (
    DeptCreateSchema,
    DeptUpdateSchema
)
from app.api.v1.schemas.system.auth_schema import AuthSchema
from app.core.base_schema import BatchSetAvailable
from app.core.logger import logger
from app.common.request import PaginationService
from app.core.base_params import PaginationQueryParams


router = APIRouter(route_class=OperationLogRoute)


@router.get("/list", summary="查询部门", description="查询部门")
async def get_obj_list_controller(
    page: PaginationQueryParams = Depends(),
    search: DeptQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dept:query"]))
) -> JSONResponse:
    result_dict_list = await DeptService.get_dept_list_service(search=search, auth=auth, order_by=page.order_by)
    result_dict = await PaginationService.get_page_obj(data_list=result_dict_list, page_no=page.page_no, page_size=page.page_size)
    logger.info("查询部门成功")
    return SuccessResponse(data=result_dict, msg="查询部门成功")


@router.get("/detail", summary="查询部门详情", description="查询部门详情")
async def get_obj_detail_controller(
    id: str = Query(..., description="部门ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dept:query"]))
) -> JSONResponse:
    result_dict = await DeptService.get_dept_detail_service(id=id, auth=auth)
    logger.info(f"查询部门详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="查询部门详情成功")


@router.post("/create", summary="创建部门", description="创建部门")
async def create_obj_controller(
    data: DeptCreateSchema,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dept:create"]))
) -> JSONResponse:
    result_dict = await DeptService.create_dept_service(data=data, auth=auth)
    logger.info(f"创建部门成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="创建部门成功")


@router.put("/update", summary="修改部门", description="修改部门")
async def update_obj_controller(
    data: DeptUpdateSchema,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dept:update"]))
) -> JSONResponse:
    result_dict = await DeptService.update_dept_service(data=data, auth=auth)
    logger.info(f"修改部门成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="修改部门成功")


@router.delete("/delete", summary="删除部门", description="删除部门")
async def delete_obj_controller(
    id: str = Query(..., description="部门ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dept:delete"]))
) -> JSONResponse:
    await DeptService.delete_dept_service(id=id, auth=auth)
    logger.info(f"删除部门成功: {id}")
    return SuccessResponse(msg="删除部门成功")


@router.patch("/available/setting", summary="批量修改部门状态", description="批量修改部门状态")
async def batch_set_available_obj_controller(
    data: BatchSetAvailable,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:dept:patch"]))
) -> JSONResponse:
    await DeptService.batch_set_available_service(data=data, auth=auth)
    logger.info(f"批量修改部门状态成功: {data.ids}")
    return SuccessResponse(msg="批量修改部门状态成功")
