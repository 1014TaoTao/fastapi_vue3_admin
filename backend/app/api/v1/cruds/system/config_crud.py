# -*- coding: utf-8 -*-

from typing import Dict, List, Optional, Sequence

from app.core.base_crud import CRUDBase
from app.api.v1.models.system.config_model import ConfigModel
from app.api.v1.schemas.system.config_schema import ConfigCreateSchema,ConfigUpdateSchema
from app.api.v1.schemas.system.auth_schema import AuthSchema


class ConfigCRUD(CRUDBase[ConfigModel, ConfigCreateSchema, ConfigUpdateSchema]):
    """配置管理数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """初始化配置CRUD"""
        self.auth = auth
        super().__init__(model=ConfigModel, auth=auth)
    
    async def get_obj_by_id_crud(self, id: int) -> Optional[ConfigModel]:
        """获取配置管理型详情"""
        return await self.get(id=id)
    
    async def get_obj_by_key_crud(self, key: str) -> Optional[ConfigModel]:
        """根据key获取配置管理型详情"""
        return await self.get(key=key)
    
    async def get_obj_list_crud(self, search: Dict = None, order_by: List[Dict[str, str]] = None) -> Sequence[ConfigModel]:
        """获取配置管理型列表"""
        return await self.list(search=search, order_by=order_by)
    
    async def create_obj_crud(self, data: ConfigCreateSchema) -> Optional[ConfigModel]:
        """创配置管理型"""
        return await self.create(data=data)
    
    async def update_obj_crud(self, id: int, data: ConfigUpdateSchema) -> Optional[ConfigModel]:
        """更新配置管理型"""
        return await self.update(id=id, data=data)
    
    async def delete_obj_crud(self, ids: List[str]) -> None:
        """删除配置管理型"""
        return await self.delete(ids=ids)
