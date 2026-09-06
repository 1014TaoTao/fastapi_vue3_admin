import json
from datetime import datetime, timedelta
from typing import Any

from apscheduler.job import Job
from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from croniter import croniter
from sqlalchemy import false, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.setting import settings
from app.core.ap_scheduler import SchedulerUtil, scheduler
from app.core.base_schema import AuthSchema, PageResultSchema
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.core.validator import datetime_validator
from app.utils.common_util import search_to_dict

from .crud import NodeCRUD
from .model import NodeModel
from .schema import (
    NodeCreateSchema,
    NodeOutSchema,
    NodeQueryParam,
    NodeRunResultSchema,
    NodeUpdateSchema,
)

# APScheduler 正式任务 job id = 节点 id；手动执行用独立临时 id，避免覆盖正式计划
_MANUAL_JOB_PREFIX = ":manual:"


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
        if not obj:
            raise CustomException(msg="该节点不存在")
        out = NodeOutSchema.model_validate(obj)
        await self._enrich_runtime([out])
        return out

    async def get_list(
        self,
        search: NodeQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[NodeOutSchema]:
        obj_list = await NodeCRUD(self.auth, self.db).get_obj_list_crud(search=search_to_dict(search, {}), order_by=order_by)
        out_list = [NodeOutSchema.model_validate(obj) for obj in obj_list]
        await self._enrich_runtime(out_list)
        return out_list

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: NodeQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[NodeOutSchema]:
        offset = (page_no - 1) * page_size
        result = await NodeCRUD(self.auth, self.db).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search_to_dict(search, {}),
            out_schema=NodeOutSchema,
        )
        await self._enrich_runtime(list(result.items))
        return result

    async def create(self, data: NodeCreateSchema) -> NodeOutSchema:
        exist_obj = await NodeCRUD(self.auth, self.db).get(name=data.name)
        if exist_obj:
            raise CustomException(msg="创建失败，该节点已存在")

        _validate_node_plan(data.trigger, data.trigger_args)
        obj = await NodeCRUD(self.auth, self.db).create_obj_crud(data=data)
        if not obj:
            raise CustomException(msg="创建失败")
        # 保存即注册：配置了触发方式则注册/刷新 APScheduler 任务
        try:
            register_node_job(obj)
        except (ValueError, CustomException) as e:
            await NodeCRUD(self.auth, self.db).delete_obj_crud(ids=[obj.id])
            raise CustomException(msg=f"创建成功但任务注册失败: {e!s}") from e
        out = NodeOutSchema.model_validate(obj)
        await self._enrich_runtime([out])
        return out

    async def update(self, id: int, data: NodeUpdateSchema) -> NodeOutSchema:
        exist_obj = await NodeCRUD(self.auth, self.db).get_obj_by_id_crud(id=id)
        if not exist_obj:
            raise CustomException(msg="更新失败，该节点不存在")

        # 预先校验新计划参数，避免 DB 更新后注册失败造成定义与调度不一致
        if data.trigger is not None:
            _validate_node_plan(data.trigger, data.trigger_args)

        obj = await NodeCRUD(self.auth, self.db).update_obj_crud(id=id, data=data)
        if not obj:
            raise CustomException(msg="更新失败")
        # 编辑即生效：按最新定义重新注册（代码/参数/计划任一变化都会同步到调度器）
        try:
            register_node_job(obj)
        except (ValueError, CustomException) as e:
            raise CustomException(msg=f"更新成功但任务注册失败: {e!s}") from e
        out = NodeOutSchema.model_validate(obj)
        await self._enrich_runtime([out])
        return out

    async def delete(self, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        for mid in ids:
            exist_obj = await NodeCRUD(self.auth, self.db).get_obj_by_id_crud(id=mid)
            if not exist_obj:
                raise CustomException(msg="删除失败，该节点不存在")
            unregister_node_job(node_id=mid)
        await NodeCRUD(self.auth, self.db).delete_obj_crud(ids=ids)

    async def clear(self) -> None:
        NodeCRUD(self.auth, self.db)
        SchedulerUtil.clear_jobs()
        await NodeCRUD(self.auth, self.db).clear_obj_crud()

    async def execute(self, id: int) -> NodeRunResultSchema:
        """手动执行一次：基于节点当前定义创建临时 job，不占用/覆盖正式计划。"""
        obj = await NodeCRUD(self.auth, self.db).get_obj_by_id_crud(id=id)
        if not obj:
            raise CustomException(msg="执行失败，该节点不存在")
        try:
            temp_job_id = run_node_once(node=obj)
        except (ValueError, CustomException) as e:
            raise CustomException(msg=f"执行失败: {e!s}") from e
        return NodeRunResultSchema(job_id=temp_job_id, status="executed", trigger="manual")

    async def batch_set_status(self, ids: list[int], status: int) -> None:
        """批量启停：0=启用 1=停用。启停直接作用于调度器 job（DB 与运行态一致）。"""
        if not ids:
            raise CustomException(msg="请选择要操作的数据")
        for mid in ids:
            obj = await NodeCRUD(self.auth, self.db).get_obj_by_id_crud(id=mid)
            if not obj:
                continue
            if status == 1:
                unregister_node_job(node_id=mid)
            else:
                try:
                    register_node_job(obj)
                except (ValueError, CustomException) as e:
                    raise CustomException(msg=f"启用任务失败: {e!s}") from e
        await NodeCRUD(self.auth, self.db).set(ids=ids, status=status)

    # ── 运行时信息补充（下次运行/最近运行，来自调度器与执行日志）──────────
    async def _enrich_runtime(self, items: list[NodeOutSchema]) -> None:
        """补充 next_run_time / last_run_time / last_run_status。

        直接查当前请求 db 会话的执行日志表（job_id = 节点 id，含手动执行记录），
        不受 JobCRUD 数据权限模型影响。
        """
        if not items:
            return
        from ..job.model import JobModel  # 延迟导入：避免模块级相互依赖

        jobs = {job.id: job for job in SchedulerUtil.get_jobs()}
        for item in items:
            node_id = str(item.id) if item.id is not None else ""
            job = jobs.get(node_id)
            if job:
                item.next_run_time = str(job.next_run_time) if job.next_run_time else None
            stmt = (
                select(JobModel)
                .where(JobModel.job_id == node_id, JobModel.is_deleted == false())
                .order_by(JobModel.created_time.desc())
                .limit(1)
            )
            row = (await self.db.execute(stmt)).scalars().first()
            if row:
                item.last_run_time = row.created_time.isoformat() if row.created_time else None
                item.last_run_status = row.status


# ── NodeModel 封装的调度操作（模块级函数，供 service / 启动自愈复用）────


def _build_job_trigger(
    trigger: str | None,
    trigger_args: str | None,
    start_date: str | None,
    end_date: str | None,
) -> Any:
    """依据节点持久化计划构造 APScheduler Trigger，非法参数抛 ValueError。"""
    if trigger == "cron":
        cron_expr = (trigger_args or "").strip()
        fields = cron_expr.split()
        if len(fields) not in (6, 7):
            raise ValueError("无效的 Cron 表达式，格式: 秒 分 时 日 月 周 [年]")
        # Quartz 风格的 ? 仅表示"该位无具体值"，croniter 不支持，先统一规范化为 * 再校验
        parsed = [field if field != "?" else "*" for field in fields]
        try:
            croniter(" ".join(parsed))
        except (KeyError, ValueError):
            raise ValueError(f"Cron表达式不正确: {cron_expr}")
        if len(fields) == 6:
            parsed.append("*")
        second, minute, hour, day, month, day_of_week, year = parsed
        if second == "*" and minute == "*" and hour == "*" and day == "*" and month == "*" and day_of_week in ("*", "?"):
            raise ValueError("Cron表达式不允许每秒执行，请至少指定秒数（如：0 * * * * ? * 表示每分钟执行）")
        return CronTrigger(
            second=second,
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            year=year,
            start_date=start_date,
            end_date=end_date,
            timezone="Asia/Shanghai",
        )
    if trigger == "interval":
        interval_args = (trigger_args or "").strip()
        fields = interval_args.split()
        if len(fields) != 5:
            raise ValueError("无效的 interval 表达式，格式: 秒 分 时 天 周")
        second, minute, hour, day, week = tuple(int(field) if field != "*" else 0 for field in fields)
        return IntervalTrigger(
            weeks=week,
            days=day,
            hours=hour,
            minutes=minute,
            seconds=second,
            start_date=start_date,
            end_date=end_date,
            timezone="Asia/Shanghai",
        )
    if trigger == "date":
        date_str = (trigger_args or "").strip()
        if not date_str:
            raise ValueError("date触发器缺少执行时间参数")
        try:
            datetime_validator(date_str)
        except Exception:
            raise ValueError("date触发时间必须为 YYYY-MM-DD HH:MM:SS")
        return DateTrigger(run_date=date_str, timezone="Asia/Shanghai")
    raise ValueError(f"不支持的触发方式: {trigger}")


def _validate_node_plan(
    trigger: str | None,
    trigger_args: str | None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> None:
    """保存前预校验计划参数，避免 DB 落库后再注册失败。"""
    if not trigger:
        return
    _build_job_trigger(trigger, trigger_args, start_date, end_date)


def _add_job_with_trigger(
    job_info: NodeModel,
    trigger,
    *,
    job_id_override: str | None = None,
    name_suffix: str = "",
) -> Job:
    """将 NodeModel 封装的任务添加到 APScheduler 调度器。"""
    code_block = job_info.func
    if not code_block or not code_block.strip():
        raise ValueError("任务代码块不能为空")
    if not settings.SCHEDULER_ALLOW_CODE_EXEC:
        raise CustomException(msg="服务已禁用定时任务代码执行（SCHEDULER_ALLOW_CODE_EXEC=False），无法注册代码块任务")

    jobstore = job_info.jobstore or "default"
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

    job_id = job_id_override or str(job_info.id)

    try:
        job = scheduler.add_job(
            func=SchedulerUtil._task_wrapper,
            trigger=trigger,
            args=[str(job_info.id), code_block, *job_args],
            kwargs=job_kwargs,
            id=job_id,
            name=f"{job_info.name}{name_suffix}",
            coalesce=job_info.coalesce,
            max_instances=job_info.max_instances or 1,
            jobstore=jobstore,
            executor=executor,
        )
        logger.info(f"任务 {job_id} 添加到 {jobstore} 存储器成功")
        return job
    except ConflictingIdError:
        try:
            scheduler.remove_job(job_id=job_id, jobstore=jobstore)
        except JobLookupError:
            pass
        job = scheduler.add_job(
            func=SchedulerUtil._task_wrapper,
            trigger=trigger,
            args=[str(job_info.id), code_block, *job_args],
            kwargs=job_kwargs,
            id=job_id,
            name=f"{job_info.name}{name_suffix}",
            coalesce=job_info.coalesce,
            max_instances=job_info.max_instances or 1,
            jobstore=jobstore,
            executor=executor,
        )
        logger.info(f"任务 {job_id} 已存在，已移除旧任务并重新添加")
        return job


def register_node_job(node: NodeModel) -> Job | None:
    """按节点持久化计划注册/刷新正式任务（job id = 节点 id）。

    - 停用节点 / 未配置触发方式：从调度器移除（若有），返回 None；
    - 其余：按 trigger/trigger_args 注册，编辑时旧任务会自动被覆盖。
    """
    if not node or node.status == 1 or not node.trigger or not (node.func or "").strip():
        unregister_node_job(node_id=node.id)
        return None
    trigger = _build_job_trigger(node.trigger, node.trigger_args, node.start_date, node.end_date)
    return _add_job_with_trigger(node, trigger)


def unregister_node_job(node_id: int | str) -> None:
    """将节点从调度器移除（幂等）。"""
    try:
        SchedulerUtil.remove_job(job_id=str(node_id))
    except JobLookupError:
        pass


def run_node_once(node: NodeModel) -> str:
    """手动执行一次：创建带独立临时 job id 的一次性任务，不覆盖正式计划。

    执行成功/失败会像正式任务一样写入 task_job 执行日志（job_id 归一到节点 id）。
    """
    if not node.func or not node.func.strip():
        raise ValueError("任务代码块不能为空")
    if not settings.SCHEDULER_ALLOW_CODE_EXEC:
        raise CustomException(msg="服务已禁用定时任务代码执行（SCHEDULER_ALLOW_CODE_EXEC=False），无法执行代码块任务")
    temp_job_id = f"{node.id}{_MANUAL_JOB_PREFIX}{datetime.now():%Y%m%d%H%M%S}"
    trigger = DateTrigger(run_date=datetime.now() + timedelta(seconds=0.1), timezone="Asia/Shanghai")
    _add_job_with_trigger(node, trigger, job_id_override=temp_job_id, name_suffix=" - 手动执行")
    return temp_job_id
