from collections.abc import Sequence

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import WorkflowEdgeModel, WorkflowModel, WorkflowNodeModel
from .schema import WorkflowCreateSchema, WorkflowUpdateSchema


class WorkflowCRUD(CRUDBase[WorkflowModel, WorkflowCreateSchema, WorkflowUpdateSchema]):
    """传输流程数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=WorkflowModel, auth=auth, db=db)


class WorkflowNodeCRUD(CRUDBase[WorkflowNodeModel, object, object]):
    """流程节点明细数据层

    明细是 flow 的派生从属数据：随父流程全量覆写/删除，无独立数据权限主体，
    也没有回收站/软删消费场景。因此不沿用基类软删 delete（否则每次保存画布都会
    残留一套 is_deleted=1 的旧明细，无限累积），删除统一走下方物理删除方法。
    """

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=WorkflowNodeModel, auth=auth, db=db)

    async def hard_delete_by_flow_ids(self, flow_ids: Sequence[int]) -> None:
        """按 flow 物理删除明细（父流程行已过数据权限校验）。"""
        if not flow_ids:
            return
        _ = await self.db.execute(delete(WorkflowNodeModel).where(WorkflowNodeModel.flow_id.in_(flow_ids)))


class WorkflowEdgeCRUD(CRUDBase[WorkflowEdgeModel, object, object]):
    """流程连线明细数据层，删除语义同 WorkflowNodeCRUD"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=WorkflowEdgeModel, auth=auth, db=db)

    async def hard_delete_by_flow_ids(self, flow_ids: Sequence[int]) -> None:
        """按 flow 物理删除明细（父流程行已过数据权限校验）。"""
        if not flow_ids:
            return
        _ = await self.db.execute(delete(WorkflowEdgeModel).where(WorkflowEdgeModel.flow_id.in_(flow_ids)))
