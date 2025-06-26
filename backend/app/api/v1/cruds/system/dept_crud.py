# -*- coding: utf-8 -*-

from typing import Dict, List, Optional, Sequence

from app.core.base_crud import CRUDBase
from app.api.v1.models.system.dept_model import DeptModel
from app.api.v1.schemas.system.dept_schema import DeptCreateSchema, DeptUpdateSchema
from app.api.v1.schemas.system.auth_schema import AuthSchema


class DeptCRUD(CRUDBase[DeptModel, DeptCreateSchema, DeptUpdateSchema]):
    """部门模块数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """初始化部门CRUD"""
        self.auth = auth
        super().__init__(model=DeptModel, auth=auth)

    async def get_by_id_crud(self, id: int) -> Optional[DeptModel]:
        """
        根据id获取部门信息
        
        :param id: 部门ID
        :return: 部门信息
        """
        obj = await self.get(id=id)
        if not obj:
            return None
            
        if obj.parent_id:
            parent = await self.get(id=obj.parent_id)
            if parent:
                obj.parent_name = parent.name
        return obj

    async def get_list_crud(self, search: Dict = None, order_by: List[Dict[str, str]] = None) -> Sequence[DeptModel]:
        """
        获取部门列表
        
        :param search: 搜索条件
        :param order_by: 排序字段
        :return: 部门列表
        """
        obj_list = await self.list(search=search, order_by=order_by)
        parent_ids = [obj.parent_id for obj in obj_list if obj.parent_id]
        if parent_ids:
            parents = await self.list(search={"id": ("in", parent_ids)})
            parent_map = {p.id: p.name for p in parents}
            for obj in obj_list:
                if obj.parent_id:
                    obj.parent_name = parent_map.get(obj.parent_id)
        return obj_list

    async def set_available_crud(self, ids: List[str], available: bool) -> None:
        """
        批量设置部门可用状态
        
        :param ids: 部门ID列表
        :param available: 可用状态
        """
        await self.set(ids=ids, available=available)

    async def get_name_crud(self, id: int) -> Optional[str]:
        """
        根据id获取部门名称
        """
        obj = await self.get(id=id)
        return obj.name if obj else None
