# -*- coding: utf-8 -*-

from typing import Dict, List, Optional, Sequence

from app.core.base_crud import CRUDBase
from app.api.v1.models.system.notice_model import NoticeModel
from app.api.v1.schemas.system.notice_schema import NoticeCreateSchema, NoticeUpdateSchema
from app.api.v1.schemas.system.auth_schema import AuthSchema


class NoticeCRUD(CRUDBase[NoticeModel, NoticeCreateSchema, NoticeUpdateSchema]):
    """操作日志数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """初始化操作日志CRUD"""
        self.auth = auth
        super().__init__(model=NoticeModel, auth=auth)

    async def get_by_id_crud(self, id: int) -> Optional[NoticeModel]:
        """获取公告详情"""
        return await self.get(id=id)
    
    async def get_list_crud(self, search: Dict = None, order_by: List[Dict[str, str]] = None) -> Sequence[NoticeModel]:
        """获取公告列表"""
        return await self.list(search=search, order_by=order_by)
    
    async def create_crud(self, data: NoticeCreateSchema) -> Optional[NoticeModel]:
        """创建公告"""
        return await self.create(data=data)
    
    async def update_crud(self, id: int, data: NoticeUpdateSchema) -> Optional[NoticeModel]:
        """更新公告"""
        return await self.update(id=id, data=data)
    
    async def delete_crud(self, ids: List[str]) -> None:
        """删除公告"""
        return await self.delete(ids=ids)
    
    async def set_available_crud(self, ids: List[str], available: bool) -> None:
        """设置公告的可用状态"""
        return await self.set(ids=ids, available=available)