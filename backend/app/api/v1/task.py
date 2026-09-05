"""task 路由清单：仅聚合路由，不含业务逻辑。"""

from fastapi import APIRouter

from app.modules.task.cronjob.job.controller import JobRouter
from app.modules.task.cronjob.node.controller import NodeRouter

task_router = APIRouter(prefix="/task")

task_router.include_router(JobRouter)
task_router.include_router(NodeRouter)
