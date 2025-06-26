# -*- coding: utf-8 -*-

from typing import Dict, List, Optional, Sequence

from app.core.base_crud import CRUDBase
from app.api.v1.models.system.operation_log_model import OperationLogModel
from app.api.v1.schemas.system.operation_log_schema import OperationLogCreateSchema
from app.api.v1.schemas.system.auth_schema import AuthSchema


class OperationLogCRUD(CRUDBase[OperationLogModel, OperationLogCreateSchema, None]):
    """操作日志数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """初始化操作日志CRUD"""
        self.auth = auth
        super().__init__(model=OperationLogModel, auth=auth)

    async def create_crud(self, data: OperationLogCreateSchema) -> Optional[OperationLogModel]:
        """
        创建操作日志记录
        
        :param data: 操作日志创建模型
        :return: 操作日志记录
        """
        return await self.create(data=data.model_dump())

    async def get_by_id_crud(self, id: str) -> Optional[OperationLogModel]:
        """
        根据ID获取操作日志详情
        
        :param id: 操作日志ID
        :return: 操作日志记录
        """
        return await self.get(id=id)

    async def get_list_crud(self, search: Dict = None, order_by: List[Dict[str, str]] = None) -> Sequence[OperationLogModel]:
        """
        获取操作日志列表
        
        :param search: 搜索条件
        :param order_by: 排序字段
        :return: 操作日志列表
        """
        return await self.list(search=search, order_by=order_by)

