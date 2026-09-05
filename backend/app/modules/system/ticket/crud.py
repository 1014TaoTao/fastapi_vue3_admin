from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import TicketCommentModel, TicketModel
from .schema import TicketCommentCreateSchema, TicketCreateSchema, TicketUpdateSchema


class TicketCRUD(CRUDBase[TicketModel, TicketCreateSchema, TicketUpdateSchema]):
    """工单 CRUD"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=TicketModel, auth=auth, db=db)


class TicketCommentCRUD(CRUDBase[TicketCommentModel, TicketCommentCreateSchema, Any]):
    """工单评论 CRUD"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=TicketCommentModel, auth=auth, db=db)
