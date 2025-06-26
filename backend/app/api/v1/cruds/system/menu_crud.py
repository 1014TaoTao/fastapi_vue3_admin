# -*- coding: utf-8 -*-

from typing import Dict, List, Optional, Sequence

from app.core.base_crud import CRUDBase
from app.api.v1.models.system.menu_model import MenuModel
from app.api.v1.schemas.system.menu_schema import MenuCreateSchema, MenuUpdateSchema
from app.api.v1.schemas.system.auth_schema import AuthSchema


class MenuCRUD(CRUDBase[MenuModel, MenuCreateSchema, MenuUpdateSchema]):
    """菜单模块数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """初始化菜单CRUD"""
        self.auth = auth
        super().__init__(model=MenuModel, auth=auth)

    async def get_by_id_crud(self, id: int) -> Optional[MenuModel]:
        """
        根据id获取菜单信息
        
        :param id: 菜单ID
        :return: 菜单信息
        """
        obj = await self.get(id=id)
        if not obj:
            return None
            
        if obj.parent_id:
            parent = await self.get(id=obj.parent_id)
            if parent:
                obj.parent_name = parent.name
        return obj

    async def get_list_crud(self, search: Dict = None, order_by: List[Dict[str, str]] = None) -> Sequence[MenuModel]:
        """
        获取菜单列表
        
        :param search: 搜索条件
        :param order_by: 排序字段
        :return: 菜单列表
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
        批量设置菜单可用状态
        
        :param ids: 菜单ID列表
        :param available: 可用状态
        """
        await self.set(ids=ids, available=available)
