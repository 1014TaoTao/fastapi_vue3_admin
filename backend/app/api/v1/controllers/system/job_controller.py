# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse

from app.common.response import StreamResponse, SuccessResponse
from app.core.base_params import PaginationQueryParams
from app.core.dependencies import AuthPermission
from app.core.router_class import OperationLogRoute
from app.core.logger import logger
from app.common.request import PaginationService
from app.utils.common_util import bytes2file_response
from app.api.v1.schemas.system.auth_schema import AuthSchema
from app.api.v1.params.system.job_param import JobQueryParams
from app.api.v1.services.system.job_service import JobService
from app.api.v1.schemas.system.job_schema import (
    JobCreateSchema,
    JobUpdateSchema
)
from app.core.ap_scheduler import SchedulerUtil


router = APIRouter(route_class=OperationLogRoute)

@router.get("/detail", summary="获取定时任务详情", description="获取定时任务详情")
async def get_obj_detail_controller(
    id: str = Query(..., description="定时任务ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:job:query"]))
) -> JSONResponse:
    result_dict = await JobService.get_job_detail_service(id=id, auth=auth)
    logger.info(f"获取定时任务详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取定时任务详情成功")

@router.get("/list", summary="查询定时任务", description="查询定时任务")
async def get_obj_list_controller(
    page: PaginationQueryParams = Depends(),
    search: JobQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:job:query"]))
) -> JSONResponse:
    result_dict_list = await JobService.get_job_list_service(auth=auth, search=search, order_by=page.order_by)
    result_dict = await PaginationService.get_page_obj(data_list= result_dict_list, page_no= page.page_no, page_size = page.page_size)
    logger.info("查询定时任务列表成功")
    return SuccessResponse(data=result_dict, msg="查询定时任务列表成功")

@router.post("/create", summary="创建定时任务", description="创建定时任务")
async def create_obj_controller(
    data: JobCreateSchema,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:job:create"]))
) -> JSONResponse:
    result_dict = await JobService.create_job_service(auth=auth, data=data)
    logger.info(f"创建定时任务成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="创建定时任务成功")

@router.put("/update", summary="修改定时任务", description="修改定时任务")
async def update_obj_controller(
    data: JobUpdateSchema,
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:job:update"]))
) -> JSONResponse:
    result_dict = await JobService.update_job_service(auth=auth, data=data)
    logger.info(f"修改定时任务成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="修改定时任务成功")

@router.delete("/delete", summary="删除定时任务", description="删除定时任务")
async def delete_obj_controller(
    id: str = Query(..., description="定时任务ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:job:delete"]))
) -> JSONResponse:
    await JobService.delete_job_service(auth=auth, id=id)
    logger.info(f"删除定时任务成功: {id}")
    return SuccessResponse(msg="删除定时任务成功")

@router.post('/export', summary="导出定时任务", description="导出定时任务")
async def export_obj_list_controller(
    search: JobQueryParams = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:job:export"]))
) -> StreamingResponse:
    # 获取全量数据
    result_dict_list = await JobService.get_job_list_service(search=search, auth=auth)
    export_result = await JobService.export_job_service(data_list=result_dict_list)
    logger.info('导出定时任务成功')

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers = {
            'Content-Disposition': 'attachment; filename=data.xlsx'
        }
    )

@router.delete("/clear", summary="清空定时任务日志", description="清空定时任务日志")
async def clear_obj_log_controller(
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:job:delete"]))
) -> JSONResponse:
    await JobService.clear_job_service(auth=auth)
    logger.info("清空定时任务成功")
    return SuccessResponse(msg="清空定时任务成功")

@router.put("/option", summary="暂停/恢复/重启定时任务", description="暂停/恢复/重启定时任务")
async def option_obj_controller(
    id: str = Query(..., description="定时任务ID"),
    option: int = Query(..., description="操作类型 1: 暂停 2: 恢复 3: 重启"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["system:job:update"]))
) -> JSONResponse:
    await JobService.option_job_service(auth=auth, id=id, option=option)
    logger.info(f"操作定时任务成功: {id}")
    return SuccessResponse(msg="操作定时任务成功")

@router.get("/log", summary="获取定时任务日志", description="获取定时任务日志", dependencies=[Depends(AuthPermission(permissions=["system:job:query"]))])
async def get_job_log_controller():
    data = [
        {
            "id": i.id,
            "name": i.name,
            "trigger": i.trigger.__class__.__name__,
            "executor": i.executor,
            "func": getattr(i.func, "__name__", str(i.func)),
            "func_ref": getattr(i, "func_ref", None),
            "args": str(i.args),
            "kwargs": str(i.kwargs),
            "misfire_grace_time": i.misfire_grace_time,
            "coalesce": i.coalesce,
            "max_instances": i.max_instances,
            "next_run_time": str(i.next_run_time) if i.next_run_time else None,
            "state": SchedulerUtil.get_job_status()
        }
        for i in SchedulerUtil.get_all_jobs()
    ]

    return SuccessResponse(msg="获取定时任务日志成功", data=data)
