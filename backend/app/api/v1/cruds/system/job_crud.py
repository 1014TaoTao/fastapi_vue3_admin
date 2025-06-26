# -*- coding: utf-8 -*-

from typing import Dict, List, Optional, Sequence

from app.core.base_crud import CRUDBase
from app.api.v1.models.system.job_model import JobModel
from app.api.v1.schemas.system.job_schema import JobCreateSchema,JobUpdateSchema
from app.api.v1.schemas.system.auth_schema import AuthSchema


class JobCRUD(CRUDBase[JobModel, JobCreateSchema, JobUpdateSchema]):
    """定时任务数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """初始化定时任务CRUD"""
        self.auth = auth
        super().__init__(model=JobModel, auth=auth)

    async def get_obj_by_id_crud(self, id: int) -> Optional[JobModel]:
        """获取定时任务详情"""
        return await self.get(id=id)
    
    async def get_obj_list_crud(self, search: Dict = None, order_by: List[Dict[str, str]] = None) -> Sequence[JobModel]:
        """获取定时任务列表"""
        return await self.list(search=search, order_by=order_by)
    
    async def create_obj_crud(self, data: JobCreateSchema) -> Optional[JobModel]:
        """创定时任务"""
        return await self.create(data=data)
    
    async def update_obj_crud(self, id: int, data: JobUpdateSchema) -> Optional[JobModel]:
        """更新定时任务"""
        return await self.update(id=id, data=data)
    
    async def delete_obj_crud(self, ids: List[str]) -> None:
        """删除定时任务"""
        return await self.delete(ids=ids)
    
    async def set_obj_field_crud(self, ids: List[str], **kwargs) -> None:
        """设置定时任务的可用状态"""
        return await self.set(ids=ids, **kwargs)
    
    async def clear_obj_crud(self) -> None:
        """清除定时任务日志"""
        return await self.clear()

