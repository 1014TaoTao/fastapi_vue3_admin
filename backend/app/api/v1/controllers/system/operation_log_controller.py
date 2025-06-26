# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse

from app.common.request import PaginationService
from app.common.response import SuccessResponse, StreamResponse
from app.core.router_class import OperationLogRoute
from app.core.dependencies import AuthPermission
from app.core.base_params import PaginationQueryParams
from app.api.v1.params.system.operation_log_param import OperationLogQueryParams
from app.api.v1.schemas.system.auth_schema import AuthSchema
from app.api.v1.services.system.operation_log_service import OperationLogService
from app.core.logger import logger
from app.utils.common_util import bytes2file_response

router = APIRouter(route_class=OperationLogRoute)


@router.get("/list", summary="查询日志", description="查询日志")
async def get_obj_list_controller(
    page: PaginationQueryParams = Depends(),
    search: OperationLogQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:log:query"]))
) -> JSONResponse:
    """ 查询日志 """
    result_dict_list = await OperationLogService.get_log_list_service(search=search, auth=auth, order_by=page.order_by)
    result_dict = await PaginationService.get_page_obj(data_list= result_dict_list, page_no= page.page_no, page_size = page.page_size)
    logger.info("查询日志成功")
    return SuccessResponse(data=result_dict, msg="查询日志成功")


@router.get("/detail", summary="日志详情", description="日志详情")
async def get_obj_detail_controller(
    id: str = Query(..., description="操作日志ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:log:query"]))
) -> JSONResponse:
    """ 详情日志 """
    result_dict = await OperationLogService.get_log_detail_service(id=id, auth=auth)
    logger.info(f"查询日志成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取日志详情成功")


@router.delete("/delete", summary="删除日志", description="删除日志")
async def delete_obj_log_controller(
    id: str = Query(..., description="操作日志ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:log:delete"]))
) -> JSONResponse:
    """ 删除日志 """
    await OperationLogService.delete_log_service(id=id, auth=auth)
    logger.info(f"删除日志成功 {id}")
    return SuccessResponse(msg="删除日志成功")


@router.post("/export", summary="导出日志", description="导出日志")
async def export_obj_list_controller(
    search: OperationLogQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:log:export"]))
) -> StreamingResponse:
    """ 导出日志 """
    operation_log_list = await OperationLogService.get_log_list_service(search=search, auth=auth)
    operation_log_export_result = await OperationLogService.export_log_list_service(operation_log_list=operation_log_list)
    logger.info('导出日志成功')

    return StreamResponse(
        data=bytes2file_response(operation_log_export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers = {
            'Content-Disposition': 'attachment; filename=data.xlsx'
        }
    )
