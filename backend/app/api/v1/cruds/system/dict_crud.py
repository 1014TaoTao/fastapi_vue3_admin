# -*- coding: utf-8 -*-

from typing import Dict, List, Optional, Sequence

from app.core.base_crud import CRUDBase
from app.api.v1.models.system.dict_model import DictDataModel, DictTypeModel
from app.api.v1.schemas.system.dict_schema import DictDataCreateSchema, DictDataUpdateSchema, DictTypeCreateSchema, DictTypeUpdateSchema
from app.api.v1.schemas.system.auth_schema import AuthSchema


class DictTypeCRUD(CRUDBase[DictTypeModel, DictTypeCreateSchema, DictTypeUpdateSchema]):
    """数据字典类型数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """初始化数据字典类型CRUD"""
        self.auth = auth
        super().__init__(model=DictTypeModel, auth=auth)

    async def get_obj_by_id_crud(self, id: int) -> Optional[DictTypeModel]:
        """获取数据字典类型详情"""
        return await self.get(id=id)
    
    async def get_obj_list_crud(self, search: Dict = None, order_by: List[Dict[str, str]] = None) -> Sequence[DictTypeModel]:
        """获取数据字典类型列表"""
        return await self.list(search=search, order_by=order_by)
    
    async def create_obj_crud(self, data: DictTypeCreateSchema) -> Optional[DictTypeModel]:
        """创数据字典类型"""
        return await self.create(data=data)
    
    async def update_obj_crud(self, id: int, data: DictTypeUpdateSchema) -> Optional[DictTypeModel]:
        """更新数据字典类型"""
        return await self.update(id=id, data=data)
    
    async def delete_obj_crud(self, ids: List[str]) -> None:
        """删除数据字典类型"""
        return await self.delete(ids=ids)
    
    async def set_obj_available_crud(self, ids: List[str], available: bool) -> None:
        """设置数据字典类型的可用状态"""
        return await self.set(ids=ids, available=available)


class DictDataCRUD(CRUDBase[DictDataModel, DictDataCreateSchema, DictDataUpdateSchema]):
    """数据字典数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """初始化数据字典数据CRUD"""
        self.auth = auth
        super().__init__(model=DictDataModel, auth=auth)

    async def get_obj_by_id_crud(self, id: int) -> Optional[DictDataModel]:
        """获取数据字典数据详情"""
        return await self.get(id=id)
    
    async def get_obj_list_crud(self, search: Dict = None, order_by: List[Dict[str, str]] = None) -> Sequence[DictDataModel]:
        """获取数据字典数据列表"""
        return await self.list(search=search, order_by=order_by)
    
    async def create_obj_crud(self, data: DictDataCreateSchema) -> Optional[DictDataModel]:
        """创建数据字典数据"""
        return await self.create(data=data)
    
    async def update_obj_crud(self, id: int, data: DictDataUpdateSchema) -> Optional[DictDataModel]:
        """更新数据字典数据"""
        return await self.update(id=id, data=data)
    
    async def delete_obj_crud(self, ids: List[str]) -> None:
        """删除数据字典数据"""
        return await self.delete(ids=ids)
    
    async def set_obj_available_crud(self, ids: List[str], available: bool) -> None:
        """设置数据字典数据的可用状态"""
        return await self.set(ids=ids, available=available)