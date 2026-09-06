from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import NoticeModel
from .schema import NoticeCreateSchema, NoticeUpdateSchema


class NoticeCRUD(CRUDBase[NoticeModel, NoticeCreateSchema, NoticeUpdateSchema]):
    """公告数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=NoticeModel, auth=auth, db=db)
