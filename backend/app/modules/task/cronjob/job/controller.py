from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Security
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute

from .schema import (
    JobOutSchema,
    JobQueryParam,
    SchedulerJobModifySchema,
    SchedulerJobSchema,
    SchedulerStatusSchema,
)
from .service import JobService

CronJobRouter = APIRouter(route_class=OperationLogRoute, prefix="/cronjob/job", tags=["定时任务管理"])


@CronJobRouter.get("/scheduler/status", summary="获取调度器状态", response_model=ResponseSchema[SchedulerStatusSchema], dependencies=[Security(AuthPermission(["module_task:cronjob:job:query"]))])
async def get_scheduler_status_controller() -> JSONResponse:
    data: SchedulerStatusSchema = JobService.get_scheduler_status()
    return SuccessResponse(data=data, msg="获取调度器状态成功")


@CronJobRouter.get("/scheduler/jobs", summary="获取调度器任务列表", response_model=ResponseSchema[list[SchedulerJobSchema]], dependencies=[Security(AuthPermission(["module_task:cronjob:job:query"]))])
async def get_scheduler_jobs_controller() -> JSONResponse:
    data: list[SchedulerJobSchema] = JobService.get_scheduler_jobs()
    return SuccessResponse(data=data, msg="获取调度器任务列表成功")


@CronJobRouter.post("/scheduler/start", summary="启动调度器", response_model=ResponseSchema[None], dependencies=[Security(AuthPermission(["module_task:cronjob:job:scheduler"]))])
async def start_scheduler_controller() -> JSONResponse:
    await JobService.start_scheduler()
    return SuccessResponse(msg="调度器已启动")


@CronJobRouter.post("/scheduler/pause", summary="暂停调度器", response_model=ResponseSchema[None], dependencies=[Security(AuthPermission(["module_task:cronjob:job:scheduler"]))])
async def pause_scheduler_controller() -> JSONResponse:
    JobService.pause_scheduler()
    return SuccessResponse(msg="调度器已暂停")


@CronJobRouter.post("/scheduler/resume", summary="恢复调度器", response_model=ResponseSchema[None], dependencies=[Security(AuthPermission(["module_task:cronjob:job:scheduler"]))])
async def resume_scheduler_controller() -> JSONResponse:
    JobService.resume_scheduler()
    return SuccessResponse(msg="调度器已恢复")


@CronJobRouter.post("/scheduler/shutdown", summary="关闭调度器", response_model=ResponseSchema[None], dependencies=[Security(AuthPermission(["module_task:cronjob:job:scheduler"]))])
async def shutdown_scheduler_controller() -> JSONResponse:
    await JobService.shutdown_scheduler()
    return SuccessResponse(msg="调度器已关闭")


@CronJobRouter.delete("/scheduler/jobs/clear", summary="清空所有任务", response_model=ResponseSchema[None], dependencies=[Security(AuthPermission(["module_task:cronjob:job:task"]))])
async def clear_jobs_controller() -> JSONResponse:
    JobService.clear_scheduler_jobs()
    return SuccessResponse(msg="已清空所有任务")


@CronJobRouter.get("/scheduler/console", summary="获取调度器控制台信息", response_model=ResponseSchema[str], dependencies=[Security(AuthPermission(["module_task:cronjob:job:query"]))])
async def get_scheduler_console_controller() -> JSONResponse:
    console_output = JobService.get_scheduler_console()
    return SuccessResponse(data=console_output, msg="获取控制台信息成功")


@CronJobRouter.post("/task/pause/{job_id}", summary="暂停任务", response_model=ResponseSchema[None], dependencies=[Security(AuthPermission(["module_task:cronjob:job:task"]))])
async def pause_job_controller(
    job_id: Annotated[str, Path(description="调度器任务ID")],
) -> JSONResponse:
    JobService.pause_job(job_id=job_id)
    return SuccessResponse(msg="暂停任务成功")


@CronJobRouter.post("/task/resume/{job_id}", summary="恢复任务", response_model=ResponseSchema[None], dependencies=[Security(AuthPermission(["module_task:cronjob:job:task"]))])
async def resume_job_controller(
    job_id: Annotated[str, Path(description="调度器任务ID")],
) -> JSONResponse:
    JobService.resume_job(job_id=job_id)
    return SuccessResponse(msg="恢复任务成功")


@CronJobRouter.post("/task/run/{job_id}", summary="立即执行任务", response_model=ResponseSchema[None], dependencies=[Security(AuthPermission(["module_task:cronjob:job:task"]))])
async def run_job_controller(
    job_id: Annotated[str, Path(description="调度器任务ID")],
) -> JSONResponse:
    JobService.run_job_now(job_id=job_id)
    return SuccessResponse(msg="立即执行任务成功")


@CronJobRouter.put("/task/modify/{job_id}", summary="修改任务", response_model=ResponseSchema[None], dependencies=[Security(AuthPermission(["module_task:cronjob:job:task"]))])
async def modify_job_controller(
    job_id: Annotated[str, Path(description="调度器任务ID")],
    data: Annotated[SchedulerJobModifySchema, Body(description="要修改的任务属性，如 name、coalesce、max_instances 等")],
) -> JSONResponse:
    JobService.modify_job(job_id=job_id, data=data)
    return SuccessResponse(msg="修改任务成功")


@CronJobRouter.delete("/task/remove/{job_id}", summary="移除任务", response_model=ResponseSchema[None], dependencies=[Security(AuthPermission(["module_task:cronjob:job:delete"]))])
async def remove_job_controller(
    job_id: Annotated[str, Path(description="调度器任务ID")],
) -> JSONResponse:
    JobService.remove_job(job_id=job_id)
    return SuccessResponse(msg="移除任务成功")


@CronJobRouter.get("/log/list", summary="查询执行日志列表", response_model=ResponseSchema[PageResultSchema[JobOutSchema]])
async def get_job_log_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:cronjob:job:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[JobQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result_dict: PageResultSchema[JobOutSchema] = await JobService(auth, db).get_job_log_page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result_dict, msg="查询执行日志列表成功")


@CronJobRouter.get("/log/detail/{id}", summary="获取执行日志详情", response_model=ResponseSchema[JobOutSchema])
async def get_job_log_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:cronjob:job:detail"]))],
    id: Annotated[int, Path(description="日志ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result_dict: JobOutSchema = await JobService(auth, db).get_job_log_detail(id=id)
    return SuccessResponse(data=result_dict, msg="获取执行日志详情成功")


@CronJobRouter.delete("/log/delete", summary="删除执行日志", response_model=ResponseSchema[None])
async def delete_job_log_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_task:cronjob:job:delete"]))],
    ids: Annotated[list[int], Body(description="ID列表")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    await JobService(auth, db).delete_job_log(ids=ids)
    return SuccessResponse(msg="删除执行日志成功")
