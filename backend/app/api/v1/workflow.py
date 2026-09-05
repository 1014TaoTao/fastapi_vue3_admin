"""workflow 路由清单：仅聚合路由，不含业务逻辑。"""

from fastapi import APIRouter

from app.modules.workflow.flow.controller import WorkflowFlowRouter
from app.modules.workflow.source.controller import StorageSourceRouter
from app.modules.workflow.storage.controller import StorageFileRouter
from app.modules.workflow.transfer.controller import StorageTransferRouter

workflow_router = APIRouter(prefix="/workflow")

workflow_router.include_router(StorageSourceRouter)
workflow_router.include_router(StorageFileRouter)
workflow_router.include_router(StorageTransferRouter)
workflow_router.include_router(WorkflowFlowRouter)
