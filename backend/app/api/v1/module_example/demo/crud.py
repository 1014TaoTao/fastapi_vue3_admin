# -*- coding: utf-8 -*-

from typing import Dict, List, Optional, Sequence

from app.core.base_crud import CRUDBase
from app.api.v1.module_system.auth.schema import AuthSchema
from .model import DemoModel
from .schema import DemoCreateSchema, DemoUpdateSchema


class DemoCRUD(CRUDBase[DemoModel, DemoCreateSchema, DemoUpdateSchema]):
    """示例数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """初始化CRUD"""
        super().__init__(model=DemoModel, auth=auth)

    async def get_by_id_crud(self, id: int) -> Optional[DemoModel]:
        """详情"""
        return await self.get(id=id)
    
    async def get_list_crud(self, search: Optional[Dict] = None, order_by: Optional[List[Dict[str, str]]] = None) -> Sequence[DemoModel]:
        """列表查询"""
        return await self.list(search=search, order_by=order_by)
    
    async def create_crud(self, data: DemoCreateSchema) -> Optional[DemoModel]:
        """创建"""
        return await self.create(data=data)
    
    async def update_crud(self, id: int, data: DemoUpdateSchema) -> Optional[DemoModel]:
        """更新"""
        return await self.update(id=id, data=data)
    
    async def delete_crud(self, ids: List[int]) -> None:
        """批量删除"""
        return await self.delete(ids=ids)
    
    async def set_available_crud(self, ids: List[int], status: bool) -> None:
        """批量设置可用状态"""
        return await self.set(ids=ids, status=status)