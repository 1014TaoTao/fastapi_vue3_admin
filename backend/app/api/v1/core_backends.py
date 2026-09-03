"""api → core 能力登记（应用组合根唯一注入点）。

依赖方向约定：core 层保持纯基础层，不得反向 ``import app.api.*``；
本模块（api 层）由组合根 ``init_app.register_routers`` 调用 ``register_core_backends()``，
把 api 层的实现登记回 core 的注入点（操作日志落库、用户加载、数据权限、调度器）。
core 至多通过 set_* 持有回调，永不持有业务模型引用。
"""

from typing import Any

from app.core.logger import logger


async def _operation_log_writer(log_data: dict[str, Any]) -> None:
    """操作日志落库实现：仅持久化，异常由 core 调用方兜底记录。"""
    from app.api.v1.module_system.log.crud import OperationLogCRUD
    from app.api.v1.module_system.log.schema import OperationLogCreateSchema
    from app.core.base_schema import AuthSchema
    from app.core.database import async_db_session

    async with async_db_session() as session, session.begin():
        await OperationLogCRUD(AuthSchema(), session).create(data=OperationLogCreateSchema(**log_data))


async def _load_user_row(db: Any, user_id: int) -> Any | None:
    """按 ID 加载未删除用户行（HTTP / WebSocket 认证时校验用户仍存在）。"""
    from sqlalchemy import select

    from app.api.v1.module_system.user.model import UserModel

    result = await db.execute(select(UserModel).where(UserModel.id == user_id, UserModel.is_deleted == False))  # noqa: E712
    return result.scalars().first()


async def _load_user_role_scopes(db: Any, user_id: int) -> set[int]:
    """读取用户全部角色的数据权限范围集合（data_scope 值）。"""
    from sqlalchemy import select

    from app.api.v1.module_system.role.model import RoleModel
    from app.api.v1.module_system.user.model import UserModel

    stmt = select(RoleModel.data_scope).join(RoleModel.users).where(UserModel.id == user_id)
    rows = (await db.execute(stmt)).scalars().all()
    return {int(scope) for scope in rows}


async def _load_dept_children(db: Any, dept_id: int) -> set[int]:
    """按部门树计算某部门的子部门 ID 集合（含自身，语义与历史实现一致）。"""
    from sqlalchemy import select

    from app.api.v1.module_system.dept.model import DeptModel
    from app.utils.common_util import get_child_id_map, get_child_recursion

    dept_objs = (await db.execute(select(DeptModel))).scalars().all()
    return get_child_recursion(id=dept_id, id_map=get_child_id_map(dept_objs))


def _record_job_failure(record: dict[str, Any]) -> None:
    """任务执行失败落库（APScheduler 事件线程同步执行，仅持久化）。"""
    from sqlalchemy.orm import Session

    from app.api.v1.module_task.cronjob.job.model import JobModel
    from app.core.database import engine

    with Session(engine) as session:
        job_log = JobModel(**record)
        session.add(job_log)
        session.commit()
        logger.info(f"失败日志已记录: job_id={record['job_id']}, id={job_log.id}")


def _register_system_jobs() -> None:
    """登记系统级周期任务（调度器取得持有权后由 core 回调，幂等）。"""
    from apscheduler.triggers.cron import CronTrigger

    from app.api.v1.module_system.log.service import OperationLogService
    from app.core.ap_scheduler import SchedulerUtil

    SchedulerUtil.register_system_job(
        "system_cleanup_operation_log",
        OperationLogService.cleanup_operation_log,
        trigger=CronTrigger(day_of_week="sun", hour=3, minute=0),
        name="操作日志清理",
    )


def register_core_backends() -> None:
    """应用组合根调用：把 api 层能力登记进 core 注入点。"""
    from app.core.ap_scheduler import set_scheduler_backends
    from app.core.dependencies import set_user_loader
    from app.core.permission import set_data_scope_loaders
    from app.core.router_class import set_operation_log_writer

    set_operation_log_writer(_operation_log_writer)
    set_user_loader(_load_user_row)
    set_data_scope_loaders(_load_user_role_scopes, _load_dept_children)
    set_scheduler_backends(
        system_job_registrar=_register_system_jobs,
        job_failure_recorder=_record_job_failure,
    )
