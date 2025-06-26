# -*- coding: utf-8 -*-

from typing import Dict, List, Optional, Sequence

from app.core.base_crud import CRUDBase
from app.api.v1.models.system.position_model import PositionModel
from app.api.v1.schemas.system.position_schema import PositionCreateSchema, PositionUpdateSchema
from app.api.v1.schemas.system.auth_schema import AuthSchema


class PositionCRUD(CRUDBase[PositionModel, PositionCreateSchema, PositionUpdateSchema]):
    """岗位模块数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """初始化岗位CRUD"""
        self.auth = auth
        super().__init__(model=PositionModel, auth=auth)

    async def get_by_id_crud(self, id: int) -> Optional[PositionModel]:
        """
        根据id获取岗位信息
        
        :param id: 岗位ID
        :return: 岗位信息
        """
        return await self.get(id=id)

    async def get_list_crud(self, search: Dict = None, order_by: List[Dict[str, str]] = None) -> Sequence[PositionModel]:
        """
        获取岗位列表
        
        :param search: 搜索条件
        :param order_by: 排序字段
        :return: 岗位列表
        """
        return await self.list(search=search, order_by=order_by)

    async def set_available_crud(self, ids: List[str], available: bool) -> None:
        """
        批量设置岗位可用状态
        
        :param ids: 岗位ID列表
        :param available: 可用状态
        """
        await self.set(ids=ids, available=available)

    async def get_name_crud(self, ids: List[str]) -> Optional[str]:
        """
        根据id列表获取岗位名称
        """
        position_names = []
        for id in ids:
            obj = await self.get(id=id)
            if obj:
                position_names.append(obj.name)
        return position_names
