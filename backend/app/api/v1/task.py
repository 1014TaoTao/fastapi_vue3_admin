from fastapi import APIRouter

from app.modules.task.cronjob.job.controller import CornJobRouter
from app.modules.task.cronjob.node.controller import CornJobNodeRouter
from app.modules.task.storage.browse.controller import StorageBrowseRouter
from app.modules.task.storage.node.controller import StorageNodeRouter
from app.modules.task.storage.transfer.controller import StorageTransferRouter
from app.modules.task.storage.workflow.controller import StorageWorkflowRouter

task_router = APIRouter(prefix="/task")

task_router.include_router(CornJobRouter)
task_router.include_router(CornJobNodeRouter)
task_router.include_router(StorageNodeRouter)
task_router.include_router(StorageBrowseRouter)
task_router.include_router(StorageTransferRouter)
task_router.include_router(StorageWorkflowRouter)
