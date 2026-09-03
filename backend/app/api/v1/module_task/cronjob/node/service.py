import json
from datetime import datetime, timedelta

from apscheduler.job import Job
from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from croniter import croniter
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.setting import settings
from app.core.ap_scheduler import (
    SchedulerUtil,
    scheduler,
)
from app.core.base_schema import AuthSchema, PageResultSchema
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.utils.common_util import search_to_dict

from .crud import NodeCRUD
from .model import NodeModel
from .schema import (
    NodeCreateSchema,
    NodeExecuteResultSchema,
    NodeExecuteSchema,
    NodeOutSchema,
    NodeQueryParam,
    NodeUpdateSchema,
)


class NodeService:
    """节点管理模块服务层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def options(self) -> list[NodeOutSchema]:
        obj_list = await NodeCRUD(self.auth, self.db).get_obj_list_crud()
        return [NodeOutSchema.model_validate(obj) for obj in obj_list]

    async def detail(self, id: int) -> NodeOutSchema:
        obj = await NodeCRUD(self.auth, self.db).get_obj_by_id_crud(id=id)
        return NodeOutSchema.model_validate(obj)

    async def get_list(
        self,
        search: NodeQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[NodeOutSchema]:
        obj_list = await NodeCRUD(self.auth, self.db).get_obj_list_crud(search=search_to_dict(search, {}), order_by=order_by)
        return [NodeOutSchema.model_validate(obj) for obj in obj_list]

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: NodeQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[NodeOutSchema]:
        offset = (page_no - 1) * page_size
        return await NodeCRUD(self.auth, self.db).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search_to_dict(search, {}),
            out_schema=NodeOutSchema,
        )

    async def create(self, data: NodeCreateSchema) -> NodeOutSchema:
        exist_obj = await NodeCRUD(self.auth, self.db).get(name=data.name)
        if exist_obj:
            raise CustomException(msg="创建失败，该节点已存在")

        obj = await NodeCRUD(self.auth, self.db).create_obj_crud(data=data)
        if not obj:
            raise CustomException(msg="创建失败")
        return NodeOutSchema.model_validate(obj)

    async def update(self, id: int, data: NodeUpdateSchema) -> NodeOutSchema:
        exist_obj = await NodeCRUD(self.auth, self.db).get_obj_by_id_crud(id=id)
        if not exist_obj:
            raise CustomException(msg="更新失败，该节点不存在")

        obj = await NodeCRUD(self.auth, self.db).update_obj_crud(id=id, data=data)
        if not obj:
            raise CustomException(msg="更新失败")
        return NodeOutSchema.model_validate(obj)

    async def delete(self, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        for mid in ids:
            exist_obj = await NodeCRUD(self.auth, self.db).get_obj_by_id_crud(id=mid)
            if not exist_obj:
                raise CustomException(msg="删除失败，该节点不存在")
            try:
                SchedulerUtil.remove_job(job_id=mid)
            except JobLookupError:
                pass
        await NodeCRUD(self.auth, self.db).delete_obj_crud(ids=ids)

    async def clear(self) -> None:
        SchedulerUtil.clear_jobs()
        await NodeCRUD(self.auth, self.db).clear_obj_crud()

    async def execute(self, id: int, execute_data: NodeExecuteSchema) -> NodeExecuteResultSchema:
        obj = await NodeCRUD(self.auth, self.db).get_obj_by_id_crud(id=id)
        if not obj:
            raise CustomException(msg="调试失败，该节点不存在")

        trigger = execute_data.trigger
        trigger_args = execute_data.trigger_args
        start_date = execute_data.start_date
        end_date = execute_data.end_date

        if trigger == "now":
            add_and_run_job_now(job_info=obj)
        elif trigger == "cron":
            if not trigger_args:
                raise CustomException(msg="Cron执行需要提供Cron表达式")
            try:
                croniter(trigger_args)
            except (KeyError, ValueError):
                raise CustomException(msg=f"Cron表达式不正确: {trigger_args}")
            add_cron_job(
                job_info=obj,
                trigger_args=trigger_args,
                start_date=start_date,
                end_date=end_date,
            )
        elif trigger == "interval":
            if not trigger_args:
                raise CustomException(msg="间隔执行需要提供间隔参数")
            add_interval_job(
                job_info=obj,
                trigger_args=trigger_args,
                start_date=start_date,
                end_date=end_date,
            )
        elif trigger == "date":
            if not trigger_args:
                raise CustomException(msg="指定时间执行需要提供执行时间")
            add_date_job(job_info=obj, run_date=trigger_args)
        else:
            raise CustomException(msg=f"不支持的触发方式: {trigger}")

        return NodeExecuteResultSchema(job_id=id, status="executed", trigger=trigger)

    async def batch_set_status(self, ids: list[int], status: int) -> None:
        if not ids:
            raise CustomException(msg="请选择要操作的数据")

        await NodeCRUD(self.auth, self.db).set(
            ids=ids,
            status=status,
        )


# ── NodeModel 封装的任务添加方法 ────────────────────────────


def _add_job_with_trigger(job_info: NodeModel, trigger) -> Job:
    """将 NodeModel 封装的任务添加到 APScheduler 调度器。"""
    code_block = job_info.func
    if not code_block or not code_block.strip():
        raise ValueError("任务代码块不能为空")
    if not settings.SCHEDULER_ALLOW_CODE_EXEC:
        raise CustomException(msg="服务已禁用定时任务代码执行（SCHEDULER_ALLOW_CODE_EXEC=False），无法注册代码块任务")

    jobstore = job_info.jobstore or "sqlalchemy"
    executor = job_info.executor or "threadpool"

    job_args = []
    if job_info.args:
        args_str = str(job_info.args).strip()
        if args_str:
            job_args = [arg.strip() for arg in args_str.split(",") if arg.strip()]

    job_kwargs = {}
    if job_info.kwargs:
        kwargs_str = str(job_info.kwargs).strip()
        if kwargs_str:
            try:
                job_kwargs = json.loads(kwargs_str)
            except json.JSONDecodeError:
                raise ValueError(f"关键字参数JSON格式无效: {kwargs_str}")

    try:
        job = scheduler.add_job(
            func=SchedulerUtil._task_wrapper,
            trigger=trigger,
            args=[str(job_info.id), code_block, *job_args],
            kwargs=job_kwargs,
            id=str(job_info.id),
            name=job_info.name,
            coalesce=job_info.coalesce,
            max_instances=1,
            jobstore=jobstore,
            executor=executor,
        )
        logger.info(f"任务 {job_info.id} 添加到 {jobstore} 存储器成功")
        return job
    except ConflictingIdError:
        scheduler.remove_job(job_id=str(job_info.id), jobstore=jobstore)
        job = scheduler.add_job(
            func=SchedulerUtil._task_wrapper,
            trigger=trigger,
            args=[str(job_info.id), code_block, *job_args],
            kwargs=job_kwargs,
            id=str(job_info.id),
            name=job_info.name,
            coalesce=job_info.coalesce,
            max_instances=1,
            jobstore=jobstore,
            executor=executor,
        )
        logger.info(f"任务 {job_info.id} 已存在，已移除旧任务并重新添加")
        return job


def add_and_run_job_now(job_info: NodeModel) -> Job:
    """立即执行任务（加入调度器并尽快触发一次）。"""
    trigger = DateTrigger(run_date=datetime.now() + timedelta(seconds=0.1))
    return _add_job_with_trigger(job_info, trigger)


def add_cron_job(
    job_info: NodeModel,
    trigger_args: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> Job:
    """创建 Cron 定时任务。"""
    cron_expr = trigger_args or job_info.trigger_args
    if not cron_expr:
        raise ValueError("Cron触发器缺少参数")

    fields = cron_expr.strip().split()
    if len(fields) not in (6, 7):
        raise ValueError("无效的 Cron 表达式")
    try:
        croniter(cron_expr)
    except (KeyError, ValueError):
        raise ValueError(f"Cron表达式不正确: {cron_expr}")

    parsed_fields = [field if field != "?" else "*" for field in fields]
    if len(fields) == 6:
        parsed_fields.append("*")

    second, minute, hour, day, month, day_of_week, year = tuple(parsed_fields)

    if second == "*" and minute == "*" and hour == "*" and day == "*" and month == "*" and day_of_week in ("*", "?"):
        raise ValueError("Cron表达式不允许每秒执行，请至少指定秒数（如：0 * * * * ? * 表示每分钟执行）")

    trigger = CronTrigger(
        second=second,
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
        year=year,
        start_date=start_date or job_info.start_date,
        end_date=end_date or job_info.end_date,
        timezone="Asia/Shanghai",
    )
    return _add_job_with_trigger(job_info, trigger)


def add_interval_job(
    job_info: NodeModel,
    trigger_args: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> Job:
    """创建间隔执行任务。"""
    interval_args = trigger_args or job_info.trigger_args
    if not interval_args:
        raise ValueError("interval触发器缺少参数")

    fields = interval_args.strip().split()
    if len(fields) != 5:
        raise ValueError("无效的 interval 表达式，格式: 秒 分 时 天 周")

    second, minute, hour, day, week = tuple(int(field) if field != "*" else 0 for field in fields)
    trigger = IntervalTrigger(
        weeks=week,
        days=day,
        hours=hour,
        minutes=minute,
        seconds=second,
        start_date=start_date or job_info.start_date,
        end_date=end_date or job_info.end_date,
        timezone="Asia/Shanghai",
    )
    return _add_job_with_trigger(job_info, trigger)


def add_date_job(job_info: NodeModel, run_date: str | None = None) -> Job:
    """创建指定时刻执行一次的任务。"""
    date_str = run_date or job_info.trigger_args
    if not date_str:
        raise ValueError("date触发器缺少执行时间参数")

    trigger = DateTrigger(run_date=date_str, timezone="Asia/Shanghai")
    return _add_job_with_trigger(job_info, trigger)
