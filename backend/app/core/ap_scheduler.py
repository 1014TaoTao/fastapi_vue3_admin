# -*- coding: utf-8 -*-

import json
import importlib
import datetime
import croniter
from typing import Union, List, Dict, Any, Optional, Callable, Coroutine
from asyncio import iscoroutinefunction
from apscheduler.job import Job
from apscheduler.events import JobExecutionEvent, JobSubmissionEvent, EVENT_ALL, JobEvent, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.jobstores.base import JobLookupError, ConflictingIdError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pymongo import MongoClient

from app.api.v1.schemas.system.auth_schema import AuthSchema
from app.config.setting import settings
from app.core.database import session_connect
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.api.v1.cruds.system.job_crud import JobCRUD
from app.api.v1.models.system.job_model import JobModel

# job 存储
# 处理Redis 5.0+ ACL格式的用户名:密码
redis_config = {
    'host': settings.REDIS_HOST,
    'port': settings.REDIS_PORT,
    'db': settings.REDIS_DB_NAME,
}

if settings.REDIS_PASSWORD:
    redis_config['password'] = settings.REDIS_PASSWORD
if settings.REDIS_USER:
    redis_config['username'] = settings.REDIS_USER

job_stores = {
    'default': MemoryJobStore(),
    'redis': RedisJobStore(**redis_config),
}
# 配置执行器
executors = {'default': AsyncIOExecutor(), 'processpool': ProcessPoolExecutor(5)}

job_defaults = {
    'coalesce': False,  # 是否合并执行
    'max_instances': 1,  # 最大实例数
}
# 配置调度器
scheduler = AsyncIOScheduler()
scheduler.configure(
    jobstores=job_stores, 
    executors=executors, 
    job_defaults=job_defaults,
    timezone='Asia/Shanghai'
)

class SchedulerUtil:
    """
    定时任务相关方法
    """

    @classmethod
    def scheduler_event_listener(cls, event: JobEvent | JobExecutionEvent):
        event_type = event.__class__.__name__
        status = True
        exception_info = ''
        if event_type == 'JobExecutionEvent' and event.exception:
            exception_info = str(event.exception)
            status = False
            if hasattr(event, 'job_id'):
                job_id = event.job_id
                query_job = cls.get_job(job_id=job_id)
                job_group = query_job._jobstore_alias # 获取任务组
                job_message = f"事件类型: {event_type}, 任务ID: {job_id}, 状态: {status}, 任务组: {job_group}, 错误详情: {exception_info}"
                logger.error(job_message)
                # JobCRUD(AuthSchema(db=session)).set_obj_field_crud(ids=[job_id], status=status, message=job_message)

    @classmethod
    async def init_system_scheduler(cls, db):
        """
        应用启动时初始化定时任务

        :return:
        """
        scheduler.add_listener(cls.scheduler_event_listener, EVENT_ALL)
        scheduler.start()

        auth = AuthSchema(db=db)
        job_list = await JobCRUD(auth).get_obj_list_crud()
        ids = []
        for item in job_list:
            ids.append(item.id)
            cls.remove_job(job_id=item.id)  # 删除旧任务
            cls.add_job(item)
        await JobCRUD(auth).set_obj_field_crud(ids=ids, status=True)  # 添加新任务

    @classmethod
    async def close_system_scheduler(cls):
        """
        关闭

        :return:
        """
        scheduler.shutdown(wait=False)
        logger.info('关闭定时任务成功')

    @classmethod
    def get_job(cls, job_id: Union[str, int]) -> Job:
        """
        获取

        :param job_id: 任务id
        :return: 任务对象
        """
        return scheduler.get_job(job_id=str(job_id))

    @classmethod
    def get_all_jobs(cls) -> List[Job]:
        """
        获取任务列表
        :return: 任务列表
        """
        return scheduler.get_jobs()

    @classmethod
    def add_job(cls, job_info: JobModel):
        """
        创建
        :param job_info: 任务对象信息
        :return:
        """
        try:
            # 动态导入模块
            # 1. 解析调用目标
            # app.module_task.scheduler_test.job
            module_path, func_name = job_info.func.rsplit('.', 1)
            module_path = "app.module_task." + module_path
            module = importlib.import_module(module_path)
            job_func = getattr(module, func_name)
            
            # 2. 确定执行器
            job_executor = job_info.executor
            if iscoroutinefunction(job_func):
                job_executor = 'default'
            if job_info.trigger == 'date':
                trigger = DateTrigger(run_date=job_info.trigger_args)
            elif job_info.trigger == 'interval':
                # 将传入的 interval 表达式拆分为不同的字段
                fields = job_info.trigger_args.strip().split()
                if len(fields) != 5:
                    raise ValueError("无效的 interval 表达式")
                second, minute, hour, day, week = tuple([int(field) if field != '*' else 0 for field in fields])
                # 秒、分、时、天、周（* * * * 1）
                trigger = IntervalTrigger(
                    weeks=week,
                    days=day,
                    hours=hour,
                    minutes=minute,
                    seconds=second,
                    start_date=job_info.start_date,
                    end_date=job_info.end_date,
                    timezone='Asia/Shanghai',
                    jitter=None
                )
            elif job_info.trigger == 'cron':
                # 秒、分、时、天、月、星期几、年 ()
                fields = job_info.trigger_args.strip().split()
                if len(fields) not in (6, 7):
                    raise ValueError("无效的 Cron 表达式")

                parsed_fields = [None if field in ('*', '?') else field for field in fields]
                if len(fields) == 6:
                    parsed_fields.append(None)

                second, minute, hour, day, month, day_of_week, year = tuple(parsed_fields)
                trigger = CronTrigger(
                    second=second,
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                    year=year,
                    start_date=job_info.start_date,
                    end_date=job_info.end_date,
                    timezone='Asia/Shanghai'
                )
            else:
                raise ValueError("无效的 trigger 触发器")

            # 3. 添加任务
            job = scheduler.add_job(
                func=job_func,  # 直接使用函数对象
                trigger=trigger,
                args=job_info.args.split(',') if job_info.args else None,
                kwargs=json.loads(job_info.kwargs) if job_info.kwargs else None,
                id=str(job_info.id),
                name=job_info.name,
                coalesce=job_info.coalesce,
                max_instances=job_info.max_instances,
                jobstore=job_info.jobstore,
                executor=job_executor,
            )
            return job
        except ModuleNotFoundError:
            raise ValueError(f"未找到该模块：{module_path}")
        except AttributeError:
            raise ValueError(f"未找到该模块下的方法：{func_name}")
        except Exception as e:
            raise CustomException(msg=f"添加任务失败: {str(e)}")

    @classmethod
    def remove_job(cls, job_id: Union[str, int]) -> None:
        """
        删除

        :param job_id: 任务id
        :return: None
        """
        query_job = cls.get_job(job_id=str(job_id))
        if query_job:
            scheduler.remove_job(job_id=str(job_id))
        

    @classmethod
    def clear_jobs(cls):
        """
        删除
        :param job_group: 任务组名
        :return:
        """
        scheduler.remove_all_jobs()

    @classmethod
    def modify_job(cls, job_id: Union[str, int]) -> Job:
        """
        更新（如果是运行中，则是下次次执行生效）
        :param job_id: 任务id
        :return: 更新后的任务对象
        """
        query_job = cls.get_job(job_id=str(job_id)) 
        if not query_job:
            raise CustomException(msg=f"未找到该任务：{job_id}")
        return scheduler.modify_job(job_id=str(job_id))

    @classmethod
    def pause_job(cls, job_id: Union[str, int]):
        """
        暂停（只有状态是运行中时才可以暂停， 已终止不可以）
        :param job_id: 任务id
        :return:
        """
        logger.info(f"开始获取全部任务：{cls.get_all_jobs()}， 状态： {cls.get_job_status()}")
        query_job = cls.get_job(job_id=str(job_id))
        if not query_job:
            raise ValueError(f"未找到该任务：{job_id}")
        scheduler.pause_job(job_id=str(job_id))
        logger.info(f"查看获取全部任务：{cls.get_all_jobs()}， 状态： {cls.get_job_status()}")

    @classmethod
    def resume_job(cls, job_id: Union[str, int]):
        """
        恢复（只有状态是暂停中时才可以恢复， 已终止不可以）
        :param job_id: 任务id
        :return:
        """
        
        logger.info(f"开始获取全部任务：{cls.get_all_jobs()}， 状态： {cls.get_job_status()}")
        query_job = cls.get_job(job_id=str(job_id))
        if not query_job:
            raise ValueError(f"未找到该任务：{job_id}")
        scheduler.resume_job(job_id=str(job_id))
        logger.info(f"查看获取全部任务：{cls.get_all_jobs()}， 状态： {cls.get_job_status()}")

    @classmethod
    def reschedule_job(cls, job_id: Union[str, int]) -> Job:
        """
        重启
        :param job_id: 任务id
        :return: 重启后的任务对象
        """
        logger.info(f"开始获取全部任务：{cls.get_all_jobs()}， 状态： {cls.get_job_status()}")
        query_job = cls.get_job(job_id=str(job_id))
        if not query_job:
            raise CustomException(msg=f"未找到该任务：{job_id}")
        scheduler.reschedule_job(job_id=str(job_id))
        logger.info(f"查看获取全部任务：{cls.get_all_jobs()}， 状态： {cls.get_job_status()}")

    @classmethod
    def export_jobs(cls):
        scheduler.export_jobs("/tmp/jobs.json")

    @classmethod
    def import_jobs(cls):
        scheduler.import_jobs("/tmp/jobs.json")

    @classmethod
    def print_jobs(cls,jobstore: Any | None = None, out: Any | None = None):
        """
        打印
        :return:
        """
        scheduler.print_jobs(jobstore=jobstore, out=out)

    @classmethod
    def get_job_status(cls) -> str:
        """
        获取调度器的当前状态
        
        :return: 状态字符串 ('stopped', 'running', 'paused')
        """
        #: constant indicating a scheduler's stopped state
        STATE_STOPPED = 0
        #: constant indicating a scheduler's running state (started and processing jobs)
        STATE_RUNNING = 1
        #: constant indicating a scheduler's paused state (started but not processing jobs)
        STATE_PAUSED = 2
        if scheduler.state == STATE_STOPPED:
            return 'stopped'
        elif scheduler.state == STATE_RUNNING:
            return 'running'
        elif scheduler.state == STATE_PAUSED:
            return 'paused'
        else:
            return 'unknown'