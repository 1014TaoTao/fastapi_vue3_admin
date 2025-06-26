# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.common.response import SuccessResponse
from app.core.dependencies import AuthPermission
from app.api.v1.params.system.menu_param import MenuQueryParams
from app.core.router_class import OperationLogRoute
from app.api.v1.services.system.menu_service import MenuService
from app.api.v1.schemas.system.menu_schema import (
    MenuCreateSchema,
    MenuUpdateSchema
)
from app.api.v1.schemas.system.auth_schema import AuthSchema
from app.core.base_schema import BatchSetAvailable
from app.core.logger import logger
from app.common.request import PaginationService
from app.core.base_params import PaginationQueryParams

router = APIRouter(route_class=OperationLogRoute)


@router.get("/list", summary="查询菜单", description="查询菜单")
async def get_obj_list_controller(
        page: PaginationQueryParams = Depends(),
        search: MenuQueryParams = Depends(),
        auth: AuthSchema = Depends(AuthPermission(permissions=["system:menu:query"]))
) -> JSONResponse:
    result_dict_list = await MenuService.get_menu_list_service(search=search, auth=auth)
    menu_items = await MenuService.convert_to_menu(result_dict_list)
    result_dict = await PaginationService.get_page_obj(data_list=menu_items, page_no=page.page_no,
                                                       page_size=page.page_size)
    logger.info("查询菜单成功")
    return SuccessResponse(data=result_dict, msg="查询菜单成功")


@router.get("/detail", summary="查询菜单详情", description="查询菜单详情")
async def get_obj_detail_controller(
        id: str = Query(..., description="菜单ID"),
        auth: AuthSchema = Depends(AuthPermission(permissions=["system:menu:query"]))
) -> JSONResponse:
    result_dict = await MenuService.get_menu_detail_service(id=id, auth=auth)
    logger.info(f"查询菜单情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取菜单成功")


@router.post("/create", summary="创建菜单", description="创建菜单")
async def create_obj_controller(
    data: MenuCreateSchema,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:menu:create"]))
) -> JSONResponse:
    result_dict = await MenuService.create_menu_service(data=data, auth=auth)
    logger.info(f"创建菜单成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="创建菜单成功")


@router.put("/update", summary="修改菜单", description="修改菜单")
async def update_obj_controller(
    data: MenuUpdateSchema,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:menu:update"]))
) -> JSONResponse:
    result_dict = await MenuService.update_menu_service(data=data, auth=auth)
    logger.info(f"修改菜单成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="修改菜单成功")


@router.delete("/delete", summary="删除菜单", description="删除菜单")
async def delete_obj_controller(
    id: str = Query(..., description="菜单ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:menu:delete"]))
) -> JSONResponse:
    await MenuService.delete_menu_service(id=id, auth=auth)
    logger.info(f"删除菜单成功: {id}")
    return SuccessResponse(msg="删除菜单成功")


@router.patch("/available/setting", summary="批量修改菜单状态", description="批量修改菜单状态")
async def batch_set_available_obj_controller(
    data: BatchSetAvailable,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:menu:patch"]))
) -> JSONResponse:
    await MenuService.set_menu_available_service(data=data, auth=auth)
    logger.info(f"批量修改菜单状态成功: {data.ids}")
    return SuccessResponse(msg="批量修改菜单状态成功")
