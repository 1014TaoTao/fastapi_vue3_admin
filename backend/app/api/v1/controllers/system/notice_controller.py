# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse

from app.common.response import StreamResponse, SuccessResponse
from app.core.base_params import PaginationQueryParams
from app.core.dependencies import AuthPermission, get_current_user
from app.core.router_class import OperationLogRoute
from app.core.base_schema import BatchSetAvailable
from app.core.logger import logger
from app.common.request import PaginationService
from app.utils.common_util import bytes2file_response
from app.api.v1.schemas.system.auth_schema import AuthSchema
from app.api.v1.params.system.notice_param import NoticeQueryParams
from app.api.v1.services.system.notice_service import NoticeService
from app.api.v1.schemas.system.notice_schema import (
    NoticeCreateSchema,
    NoticeUpdateSchema
)


router = APIRouter(route_class=OperationLogRoute)

@router.get("/detail", summary="获取公告详情", description="获取公告详情")
async def get_obj_detail_controller(
    id: str = Query(..., description="公告ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:notice:query"]))
) -> JSONResponse:
    result_dict = await NoticeService.get_notice_detail_service(id=id, auth=auth)
    logger.info(f"获取公告详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取公告详情成功")

@router.get("/list", summary="查询公告", description="查询公告")
async def get_obj_list_controller(
    page: PaginationQueryParams = Depends(),
    search: NoticeQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:notice:query"]))
) -> JSONResponse:
    result_dict_list = await NoticeService.get_notice_list_service(auth=auth, search=search, order_by=page.order_by)
    result_dict = await PaginationService.get_page_obj(data_list= result_dict_list, page_no= page.page_no, page_size = page.page_size)
    logger.info("查询公告列表成功")
    return SuccessResponse(data=result_dict, msg="查询公告列表成功")

@router.post("/create", summary="创建公告", description="创建公告")
async def create_obj_controller(
    data: NoticeCreateSchema,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:notice:create"]))
) -> JSONResponse:
    result_dict = await NoticeService.create_notice_service(auth=auth, data=data)
    logger.info(f"创建公告成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="创建公告成功")

@router.put("/update", summary="修改公告", description="修改公告")
async def update_obj_controller(
    data: NoticeUpdateSchema,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:notice:update"]))
) -> JSONResponse:
    result_dict = await NoticeService.update_notice_service(auth=auth, data=data)
    logger.info(f"修改公告成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="修改公告成功")

@router.delete("/delete", summary="删除公告", description="删除公告")
async def delete_obj_controller(
    id: str = Query(..., description="公告ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:notice:delete"]))
) -> JSONResponse:
    await NoticeService.delete_notice_service(auth=auth, id=id)
    logger.info(f"删除公告成功: {id}")
    return SuccessResponse(msg="删除公告成功")

@router.patch("/available/setting", summary="批量修改公告状态", description="批量修改公告状态")
async def batch_set_available_obj_controller(
    data: BatchSetAvailable,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:notice:patch"]))
) -> JSONResponse:
    await NoticeService.set_notice_available_service(auth=auth, data=data)
    logger.info(f"批量修改公告状态成功: {data.ids}")
    return SuccessResponse(msg="批量修改公告状态成功")

@router.post('/export', summary="导出公告", description="导出公告")
async def export_obj_list_controller(
    search: NoticeQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:notice:export"]))
) -> StreamingResponse:
    # 获取全量数据
    result_dict_list = await NoticeService.get_notice_list_service(search=search, auth=auth)
    export_result = await NoticeService.export_notice_service(notice_list=result_dict_list)
    logger.info('导出公告成功')

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers = {
            'Content-Disposition': 'attachment; filename=data.xlsx'
        }
    )


@router.get("/info", summary="获取全局启用公告", description="获取全局启用公告")
async def get_obj_list_available_controller(
    auth: AuthSchema = Depends(get_current_user)
) -> JSONResponse:
    result_dict_list = await NoticeService.get_notice_list_available_service(auth=auth)
    result_dict = await PaginationService.get_page_obj(data_list= result_dict_list)
    logger.info("查询已启用公告列表成功")
    return SuccessResponse(data=result_dict, msg="查询已启用公告列表成功")
