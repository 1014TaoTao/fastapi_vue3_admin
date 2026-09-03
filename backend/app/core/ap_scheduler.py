import asyncio
import json
from collections.abc import Callable
from datetime import datetime
from typing import Any

from apscheduler.events import (
    EVENT_ALL,
    EVENT_ALL_JOBS_REMOVED,
    EVENT_JOB_ADDED,
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_MISSED,
    EVENT_JOB_REMOVED,
    EVENT_JOB_SUBMITTED,
    JobEvent,
)
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.job import Job
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from redis.asyncio import Redis

from app.config.setting import settings
from app.core.database import engine
from app.core.logger import logger

# 任务状态常量
JOB_STATUS_FAILED = 3

# 多 worker 下单实例调度锁：所有进程共享同一个 RedisJobStore，若每个进程都自行
# start，同一任务会被重复调度执行。仅持有锁的进程运行调度器并周期续期，其余进程
# 周期争抢——持有者崩溃（锁过期）后自动接管。
SCHEDULER_LOCK_KEY = "fastapiadmin:scheduler:lock"
SCHEDULER_LOCK_TTL = 30  # 锁有效期（秒）；须大于续期间隔，否则锁在续期前就过期
SCHEDULER_RENEW_INTERVAL = 10  # 持有者续期间隔
SCHEDULER_POLL_INTERVAL = 5  # 候选进程争抢间隔；越小接管越快，Redis 压力越大

# 系统级周期任务注册与任务失败落库由 api 层登记注入（core 不反向依赖 app.api.* 的 ORM/Service）。
# - 登记回调在本进程取得调度器持有权、本地 start 后调用（幂等，replace_existing 兜底）；
# - 失败落库接收 core 已组装好的记录 dict，仅负责持久化。
SystemJobRegistrar = Callable[[], None]
JobFailureRecorder = Callable[[dict[str, Any]], None]

_system_job_registrar: SystemJobRegistrar | None = None
_job_failure_recorder: JobFailureRecorder | None = None


def set_scheduler_backends(
    *,
    system_job_registrar: SystemJobRegistrar | None = None,
    job_failure_recorder: JobFailureRecorder | None = None,
) -> None:
    """登记调度器所需的 api 层能力（应用启动时由 api 层调用）。"""
    global _system_job_registrar, _job_failure_recorder
    _system_job_registrar = system_job_registrar
    _job_failure_recorder = job_failure_recorder

scheduler = AsyncIOScheduler()
scheduler.configure(
    jobstores={
        "default": RedisJobStore(
            host=settings.REDIS_HOST,
            port=int(settings.REDIS_PORT),
            username=settings.REDIS_USER or None,
            password=settings.REDIS_PASSWORD or None,
            db=int(settings.REDIS_DB_NAME),
        ),
        "sqlalchemy": SQLAlchemyJobStore(url=settings.DB_URI, engine=engine),
        "memory": MemoryJobStore(),
    },
    executors={
        "default": AsyncIOExecutor(),
        "threadpool": ThreadPoolExecutor(max_workers=10),
        "processpool": ProcessPoolExecutor(max_workers=1),
    },
    job_defaults={
        "coalesce": True,
        "max_instances": 5,
    },
    timezone="Asia/Shanghai",
)


class SchedulerUtil:
    """定时任务 SDK — 仅封装 APScheduler 核心操作，不含业务逻辑（无 ORM/实体引用）。"""

    redis_instance: Redis | None = None
    # 多 worker 选主状态：_redis 为空视为单机直跑；_leader_token 非空表示本进程持有调度锁
    _redis: Redis | None = None
    _leader_token: str | None = None
    _maintain_task: asyncio.Task | None = None

    # ------------------------------------------------------------------ #
    # 生命周期（多 worker 下仅持有分布式锁的进程真正运行调度器）
    # ------------------------------------------------------------------ #
    @classmethod
    async def init_scheduler(cls, redis: Redis | None = None) -> None:
        """应用启动时初始化定时任务调度器（含系统级周期任务注册）。

        多 worker 部署（WORKERS>1）时各进程共享 RedisJobStore，若各自 start，
        同一任务会被多个进程重复执行。这里用分布式锁选主：本进程抢到锁就启动
        调度器；抢不到则转后台候选，持有者异常退出后自动接管。
        Redis 不可用（None）时退化为本进程直接运行，等价于单机行为。

        返回:
        - None
        """
        try:
            if redis:
                cls.redis_instance = redis
                cls._redis = redis
            if await cls._ensure_scheduler_running():
                logger.info("✅ 本进程持有调度器锁，定时任务调度器已启动")
            else:
                logger.info("🔄 调度器由其它进程持有，本进程转为候选（异常退出后自动接管）")
        except Exception as e:
            logger.error(f"❌ 定时任务调度器初始化失败: {e}")
            raise

    @classmethod
    async def _ensure_scheduler_running(cls) -> bool:
        """确保调度器在运行：抢到锁则本地启动并登记后台维护协程；否则登记候选协程。

        返回:
        - bool: 本进程是否真正运行着调度器。
        """
        if scheduler.running:
            return True
        if cls._redis is None:
            cls._start_scheduler_local()
            return True
        from app.core.redis_crud import RedisCURD

        acquired, token = await RedisCURD(cls._redis).lock(key=SCHEDULER_LOCK_KEY, expire=SCHEDULER_LOCK_TTL)
        if acquired:
            cls._leader_token = token
            cls._start_scheduler_local()
        cls._spawn_maintain()
        return acquired

    @classmethod
    async def _maintain_loop(cls) -> None:
        """后台维护循环：持有者周期续期锁，锁丢失（崩溃/长时间阻塞）则让位转候选。

        候选进程周期争抢锁，抢到即接管调度器。
        """
        if cls._redis is None:
            return
        from app.core.redis_crud import RedisCURD

        crud = RedisCURD(cls._redis)
        try:
            while True:
                if cls._leader_token:
                    await asyncio.sleep(SCHEDULER_RENEW_INTERVAL)
                    renewed = await crud.renew_lock(
                        key=SCHEDULER_LOCK_KEY, expire=SCHEDULER_LOCK_TTL, value=cls._leader_token
                    )
                    if renewed:
                        continue
                    # 续期失败：先确认锁是否真丢（也可能只是 Redis 瞬时抖动）
                    if await crud.get(key=SCHEDULER_LOCK_KEY) == cls._leader_token:
                        continue
                    logger.error("调度器持有锁已丢失，本进程停机让位，等待候选接管")
                    cls._leader_token = None
                    cls._stop_scheduler_local()
                else:
                    await asyncio.sleep(SCHEDULER_POLL_INTERVAL)
                    acquired, token = await crud.lock(
                        key=SCHEDULER_LOCK_KEY, expire=SCHEDULER_LOCK_TTL
                    )
                    if not acquired:
                        continue
                    cls._leader_token = token
                    cls._start_scheduler_local()
                    logger.info("✅ 本进程接管调度器持有权，定时任务调度器已启动")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("调度器维护协程异常退出: {}", e)

    @classmethod
    def _start_scheduler_local(cls) -> None:
        """本地启动调度器并注册系统级周期任务（幂等）。"""
        if scheduler.running:
            return
        scheduler.start()
        scheduler.add_listener(cls._dispatch_job_event, EVENT_ALL)
        scheduler.resume()

        if _system_job_registrar is not None:
            _system_job_registrar()
            logger.info("✅ 系统级定时任务已注册")
        else:
            logger.warning("⚠️ 系统级周期任务注册器未登记，跳过系统任务注册")

    @classmethod
    def _stop_scheduler_local(cls) -> None:
        """本地停止调度器（幂等）。"""
        if scheduler.running:
            scheduler.shutdown(wait=False)

    @classmethod
    def _spawn_maintain(cls) -> None:
        """启动（或替换）后台维护协程。"""
        if cls._maintain_task is not None and not cls._maintain_task.done():
            return
        cls._maintain_task = asyncio.create_task(cls._maintain_loop(), name="scheduler-maintain")

    @classmethod
    def register_system_job(cls, job_id: str, func: Callable, trigger: Any, name: str) -> None:
        """外部注册系统级定时任务。"""
        scheduler.add_job(func, trigger=trigger, id=job_id, name=name, replace_existing=True)

    @classmethod
    async def start(cls, paused: bool = False) -> bool:
        """确保调度器运行（页面「启动调度器」入口）：持有锁则本地启动，否则转候选。

        返回:
        - bool: 调度器是否已由本进程（或其它持有进程）恢复运行。
        """
        if scheduler.running:
            return True
        await cls._ensure_scheduler_running()
        return scheduler.running or cls._redis is not None

    @classmethod
    def shutdown(cls, wait: bool = False) -> None:
        """停止本进程调度器并释放持有权；多 worker 下其它候选进程会自动接管。

        APScheduler 的暂停/停止是进程内状态，跨 worker 的手动编排不在 SDK 职责内。
        """
        if cls._maintain_task is not None and not cls._maintain_task.done():
            cls._maintain_task.cancel()
            cls._maintain_task = None
        cls._leader_token = None
        cls._stop_scheduler_local()

    @classmethod
    def _get_trigger_type(cls, job_id: str) -> str:
        """获取任务的触发类型"""
        job = cls.get_job(job_id=job_id)
        if not job:
            return "manual"
        trigger = job.trigger
        if isinstance(trigger, CronTrigger):
            return "cron"
        if isinstance(trigger, IntervalTrigger):
            return "interval"
        if isinstance(trigger, DateTrigger):
            if trigger.run_date:
                now = datetime.now(trigger.run_date.tzinfo)
                diff = abs((trigger.run_date - now).total_seconds())
                if diff < 60:
                    return "manual"
            return "date"
        return "manual"

    @classmethod
    def _dispatch_job_event(cls, event: JobEvent) -> None:
        """APScheduler 事件统一处理（注册为 EVENT_ALL 回调），仅错误事件写入 DB。"""
        job_id = str(event.job_id) if hasattr(event, "job_id") else None
        if not job_id:
            return

        if event.code == EVENT_JOB_ERROR:
            exception = getattr(event, "exception", None)
            logger.error(f"任务 {job_id} 执行失败: {exception!s}")
            if _job_failure_recorder is None:
                logger.warning("任务失败落库记录器未登记，跳过失败记录: job_id={}", job_id)
                return
            try:
                job = SchedulerUtil.get_job(job_id=job_id)
                _job_failure_recorder(
                    {
                        "job_id": job_id,
                        "job_name": job.name if job else None,
                        "trigger_type": SchedulerUtil._get_trigger_type(job_id) if job else "manual",
                        "status": JOB_STATUS_FAILED,
                        "error": str(exception),
                        "next_run_time": str(job.next_run_time) if job and job.next_run_time else None,
                        "job_state": SchedulerUtil._get_job_state(job) if job else None,
                    }
                )
            except Exception as e:
                logger.error(f"记录失败日志出错: job_id={job_id}, error={e}", exc_info=True)
        elif event.code == EVENT_JOB_MISSED:
            logger.warning(f"任务 {job_id} 错过执行时间")
        elif event.code == EVENT_JOB_EXECUTED:
            logger.info(f"任务 {job_id} 执行成功")
        elif event.code == EVENT_JOB_SUBMITTED:
            logger.info(f"任务 {job_id} 已提交执行")
        elif event.code == EVENT_JOB_REMOVED:
            logger.info(f"任务 {job_id} 已移除")
        elif event.code == EVENT_JOB_ADDED:
            logger.info(f"任务 {job_id} 已添加")
        elif event.code == EVENT_ALL_JOBS_REMOVED:
            logger.info("所有任务已从调度器中移除")

    @classmethod
    def pause(cls) -> None:
        scheduler.pause()

    @classmethod
    def resume(cls) -> None:
        scheduler.resume()

    @classmethod
    def is_running(cls) -> bool:
        return scheduler.running

    @classmethod
    def get_scheduler_state(cls) -> int:
        return scheduler.state

    @classmethod
    def get_job(cls, job_id: str | int, jobstore: str | None = None) -> Job | None:
        return scheduler.get_job(str(job_id), jobstore)

    @classmethod
    def get_jobs(cls, jobstore: str | None = None) -> list[Job]:
        return scheduler.get_jobs(jobstore)

    @classmethod
    def remove_job(cls, job_id: str | int, jobstore: str | None = None) -> None:
        scheduler.remove_job(str(job_id), jobstore)

    @classmethod
    def clear_jobs(cls) -> None:
        scheduler.remove_all_jobs()

    @classmethod
    def print_jobs(cls, jobstore: str | None = None) -> str:
        import io
        output = io.StringIO()
        scheduler.print_jobs(jobstore=jobstore, out=output)
        return output.getvalue()

    @classmethod
    def pause_job(cls, job_id: str | int, jobstore: str | None = None) -> Job | None:
        return scheduler.pause_job(str(job_id), jobstore)

    @classmethod
    def resume_job(cls, job_id: str | int, jobstore: str | None = None) -> Job | None:
        return scheduler.resume_job(str(job_id), jobstore)

    @classmethod
    def modify_job(cls, job_id: str | int, jobstore: str | None = None, **changes) -> Job | None:
        return scheduler.modify_job(str(job_id), jobstore, **changes)

    @classmethod
    def get_job_status(cls, job_id: str | int) -> int:
        """获取单个任务的当前状态。0=运行中 1=暂停中 2=已停止 3=未知"""
        job = cls.get_job(job_id=str(job_id))
        if not job:
            return 3
        if job.next_run_time is None:
            return 1
        if scheduler.state == 0:
            return 2
        return 0

    @classmethod
    def run_job_now(cls, job_id: str | int, jobstore: str | None = None) -> Job | None:
        """立即执行任务（通过临时 Job，不修改原任务 trigger）。"""
        from datetime import timedelta

        job = cls.get_job(job_id=job_id, jobstore=jobstore)
        if not job:
            return None

        temp_job_id = f"{job_id}_run_now_{datetime.now().timestamp()}"

        trigger = DateTrigger(run_date=datetime.now() + timedelta(seconds=0.1), timezone="Asia/Shanghai")
        temp_job = scheduler.add_job(
            func=job.func,
            trigger=trigger,
            args=job.args,
            kwargs=job.kwargs,
            id=temp_job_id,
            name=f"{job.name}(立即执行)",
            jobstore=jobstore or "default",
            executor=job.executor,
            max_instances=1,
        )
        logger.info(f"任务 {job_id} 已触发立即执行，临时任务 ID: {temp_job_id}")
        return temp_job

    @classmethod
    def _task_wrapper(cls, job_id: str | int, code_block: str | None, *args, **kwargs):
        """任务执行包装器，执行自定义代码块（同步版本，用于 ThreadPoolExecutor）

        安全提示：code_block 来自页面提交，exec 等同给所有能创建任务的人
        服务器代码执行权限。生产环境应设置 SCHEDULER_ALLOW_CODE_EXEC=False
        关闭该能力，仅保留内置函数型任务。
        """
        if code_block and code_block.strip() and not settings.SCHEDULER_ALLOW_CODE_EXEC:
            message = f"任务 {job_id} 含用户提交代码块，已因 SCHEDULER_ALLOW_CODE_EXEC=False 拒绝执行"
            logger.error(message)
            raise RuntimeError(message)

        import types

        def run_sync_handler():
            if not code_block:
                return None
            module = types.ModuleType(f"node_task_{job_id}")
            module.__dict__["__builtins__"] = __builtins__
            exec(code_block, module.__dict__)
            handler = module.__dict__.get("handler")
            if handler and callable(handler):
                return handler(*args, **kwargs)
            raise ValueError("代码块必须定义 handler(*args, **kwargs) 函数")

        try:
            return run_sync_handler()
        except Exception as e:
            logger.error(f"任务 {job_id} 执行失败: {e!s}")
            raise

    @classmethod
    def _get_job_state(cls, job) -> str | None:
        """获取任务状态（解析为可读的JSON格式）"""
        import pickle

        if not job:
            return None
        state = job.__getstate__()

        def serialize_value(obj):
            if obj is None:
                return None
            if isinstance(obj, (str, int, float, bool)):
                return obj
            if isinstance(obj, bytes):
                try:
                    return serialize_value(pickle.loads(obj))
                except Exception:
                    return obj.decode("utf-8", errors="replace")
            if isinstance(obj, dict):
                return {k: serialize_value(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [serialize_value(item) for item in obj]
            if hasattr(obj, "__dict__"):
                obj_dict = {}
                for k, v in obj.__dict__.items():
                    if not k.startswith("_"):
                        obj_dict[k] = serialize_value(v)
                return {"__class__": obj.__class__.__name__, **obj_dict}
            try:
                return str(obj)
            except Exception:
                return f"<{type(obj).__name__}>"

        return json.dumps(serialize_value(state), ensure_ascii=False, indent=2)
