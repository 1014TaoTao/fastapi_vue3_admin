from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import WorkflowFlowModel
from .schema import WorkflowFlowCreateSchema, WorkflowFlowUpdateSchema


class WorkflowFlowCRUD(CRUDBase[WorkflowFlowModel, WorkflowFlowCreateSchema, WorkflowFlowUpdateSchema]):
    """传输流程数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=WorkflowFlowModel, auth=auth, db=db)
