# -*- coding: utf-8 -*-

from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.responses import JSONResponse, StreamingResponse

from app.common.response import StreamResponse, SuccessResponse
from app.common.request import PaginationService
from app.utils.common_util import bytes2file_response
from app.core.base_params import PaginationQueryParam
from app.core.dependencies import AuthPermission
from app.core.router_class import OperationLogRoute
from app.core.logger import logger
from app.api.v1.module_system.auth.schema import AuthSchema
from .param import JobQueryParam, JobLogQueryParam
from .service import JobService, JobLogService
from .schema import (
    JobCreateSchema,
    JobUpdateSchema
)
from app.core.ap_scheduler import SchedulerUtil


JobRouter = APIRouter(route_class=OperationLogRoute, prefix="/job", tags=["定时任务"])

@JobRouter.get("/detail/{id}", summary="获取定时任务详情", description="获取定时任务详情")
async def get_obj_detail_controller(
    id: int = Path(..., description="定时任务ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["monitor:job:query"]))
) -> JSONResponse:
    result_dict = await JobService.get_job_detail_service(id=id, auth=auth)
    logger.info(f"获取定时任务详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取定时任务详情成功")

@JobRouter.get("/list", summary="查询定时任务", description="查询定时任务")
async def get_obj_list_controller(
    page: PaginationQueryParam = Depends(),
    search: JobQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["monitor:job:query"]))
) -> JSONResponse:
    result_dict_list = await JobService.get_job_list_service(auth=auth, search=search, order_by=page.order_by)
    result_dict = await PaginationService.paginate(data_list= result_dict_list, page_no= page.page_no, page_size = page.page_size)
    logger.info(f"查询定时任务列表成功")
    return SuccessResponse(data=result_dict, msg="查询定时任务列表成功")

@JobRouter.post("/create", summary="创建定时任务", description="创建定时任务")
async def create_obj_controller(
    data: JobCreateSchema,
    auth: AuthSchema = Depends(AuthPermission(permissions=["monitor:job:create"]))
) -> JSONResponse:
    result_dict = await JobService.create_job_service(auth=auth, data=data)
    logger.info(f"创建定时任务成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="创建定时任务成功")

@JobRouter.put("/update/{id}", summary="修改定时任务", description="修改定时任务")
async def update_obj_controller(
    data: JobUpdateSchema,
    id: int = Path(..., description="定时任务ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["monitor:job:update"]))
) -> JSONResponse:
    result_dict = await JobService.update_job_service(auth=auth, id=id, data=data)
    logger.info(f"修改定时任务成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="修改定时任务成功")

@JobRouter.delete("/delete", summary="删除定时任务", description="删除定时任务")
async def delete_obj_controller(
    ids: list[int] = Body(..., description="ID列表"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["monitor:job:delete"]))
) -> JSONResponse:
    await JobService.delete_job_service(auth=auth, ids=ids)
    logger.info(f"删除定时任务成功: {ids}")
    return SuccessResponse(msg="删除定时任务成功")

@JobRouter.post('/export', summary="导出定时任务", description="导出定时任务")
async def export_obj_list_controller(
    search: JobQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["monitor:job:export"]))
) -> StreamingResponse:
    # 获取全量数据
    result_dict_list = await JobService.get_job_list_service(search=search, auth=auth)
    export_result = await JobService.export_job_service(data_list=result_dict_list)
    logger.info('导出定时任务成功')

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers = {
            'Content-Disposition': 'attachment; filename=job.xlsx'
        }
    )

@JobRouter.delete("/clear", summary="清空定时任务日志", description="清空定时任务日志")
async def clear_obj_log_controller(
    auth: AuthSchema = Depends(AuthPermission(permissions=["monitor:job:delete"]))
) -> JSONResponse:
    await JobService.clear_job_service(auth=auth)
    logger.info(f"清空定时任务成功")
    return SuccessResponse(msg="清空定时任务成功")

@JobRouter.put("/option", summary="暂停/恢复/重启定时任务", description="暂停/恢复/重启定时任务")
async def option_obj_controller(
    id: int = Body(..., description="定时任务ID"),
    option: int = Body(..., description="操作类型 1: 暂停 2: 恢复 3: 重启"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["monitor:job:update"]))
) -> JSONResponse:
    await JobService.option_job_service(auth=auth, id=id, option=option)
    logger.info(f"操作定时任务成功: {id}")
    return SuccessResponse(msg="操作定时任务成功")

@JobRouter.get("/log", summary="获取定时任务日志", description="获取定时任务日志", dependencies=[Depends(AuthPermission(permissions=["monitor:job:query"]))])
async def get_job_log_controller():
    data = [
        {
            "id": i.id,
            "name": i.name,
            "trigger": i.trigger.__class__.__name__,
            "executor": i.executor,
            "func": i.func,
            "func_ref": i.func_ref,
            "args": i.args,
            "kwargs": i.kwargs,
            "misfire_grace_time": i.misfire_grace_time,
            "coalesce": i.coalesce,
            "max_instances": i.max_instances,
            "next_run_time": i.next_run_time,
            "state": SchedulerUtil.get_job_status()
        }
        for i in SchedulerUtil.get_all_jobs()
    ]

    return SuccessResponse(msg="获取定时任务日志成功", data=data)


# 定时任务日志管理接口
@JobRouter.get("/log/detail/{id}", summary="获取定时任务日志详情", description="获取定时任务日志详情")
async def get_job_log_detail_controller(
    id: int = Path(..., description="定时任务日志ID"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["monitor:job:query"]))
) -> JSONResponse:
    result_dict = await JobLogService.get_job_log_detail_service(id=id, auth=auth)
    logger.info(f"获取定时任务日志详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取定时任务日志详情成功")


@JobRouter.get("/log/list", summary="查询定时任务日志", description="查询定时任务日志")
async def get_job_log_list_controller(
    page: PaginationQueryParam = Depends(),
    search: JobLogQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["monitor:job:query"]))
) -> JSONResponse:
    order_by = [{"create_time": "desc"}]
    result_dict_list = await JobLogService.get_job_log_list_service(auth=auth, search=search, order_by=order_by)
    result_dict = await PaginationService.paginate(data_list=result_dict_list, page_no=page.page_no, page_size=page.page_size)
    logger.info(f"查询定时任务日志列表成功")
    return SuccessResponse(data=result_dict, msg="查询定时任务日志列表成功")


@JobRouter.delete("/log/delete", summary="删除定时任务日志", description="删除定时任务日志")
async def delete_job_log_controller(
    ids: list[int] = Body(..., description="ID列表"),
    auth: AuthSchema = Depends(AuthPermission(permissions=["monitor:job:delete"]))
) -> JSONResponse:
    await JobLogService.delete_job_log_service(auth=auth, ids=ids)
    logger.info(f"删除定时任务日志成功: {ids}")
    return SuccessResponse(msg="删除定时任务日志成功")


@JobRouter.delete("/log/clear", summary="清空定时任务日志", description="清空定时任务日志")
async def clear_job_log_controller(
    auth: AuthSchema = Depends(AuthPermission(permissions=["monitor:job:delete"]))
) -> JSONResponse:
    await JobLogService.clear_job_log_service(auth=auth)
    logger.info(f"清空定时任务日志成功")
    return SuccessResponse(msg="清空定时任务日志成功")


@JobRouter.post('/log/export', summary="导出定时任务日志", description="导出定时任务日志")
async def export_job_log_list_controller(
    search: JobLogQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(permissions=["monitor:job:export"]))
) -> StreamingResponse:
    # 获取全量数据
    result_dict_list = await JobLogService.get_job_log_list_service(search=search, auth=auth)
    export_result = await JobLogService.export_job_log_service(data_list=result_dict_list)
    logger.info('导出定时任务日志成功')

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            'Content-Disposition': 'attachment; filename=job_log.xlsx'
        }
    )
