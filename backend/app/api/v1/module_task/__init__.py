from fastapi import APIRouter

from .cronjob.job.controller import JobRouter
from .cronjob.node.controller import NodeRouter
from .workflow.flow.controller import WorkflowFlowRouter
from .workflow.node.controller import StorageSourceRouter
from .workflow.storage.controller import StorageFileRouter
from .workflow.transfer.controller import StorageTransferRouter

task_router = APIRouter(prefix="/task")

workflow_router = APIRouter(prefix="/workflow")
workflow_router.include_router(StorageSourceRouter)
workflow_router.include_router(StorageFileRouter)
workflow_router.include_router(StorageTransferRouter)
workflow_router.include_router(WorkflowFlowRouter)

task_router.include_router(JobRouter)
task_router.include_router(NodeRouter)
task_router.include_router(workflow_router)
