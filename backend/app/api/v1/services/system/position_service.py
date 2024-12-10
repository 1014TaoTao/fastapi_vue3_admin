# -*- coding: utf-8 -*-

from typing import Any, Dict, List

from app.api.v1.cruds.system.position_crud import PositionCRUD
from app.api.v1.schemas.system.auth_schema import AuthSchema
from app.api.v1.schemas.system.position_schema import (
    PositionCreateSchema,
    PositionUpdateSchema,
    PositionOutSchema,
)
from app.core.base_schema import BatchSetAvailable
from app.utils.excel_util import ExcelUtil
from app.api.v1.params.system.position_param import PositionQueryParams

class PositionService:
    """岗位模块服务层"""

    @classmethod
    async def get_position_detail(cls, auth: AuthSchema, id: int) -> Dict:
        """获取岗位详情"""
        position = await PositionCRUD(auth).get_position_by_id(id=id)
        return PositionOutSchema.model_validate(position).model_dump()

    @classmethod
    async def get_position_list(cls, auth: AuthSchema, search: PositionQueryParams, order_by: List[Dict] = None) -> List[Dict]:
        """获取岗位列表"""
        order_by = order_by if order_by else [{"order": "asc"}]
        position_list = await PositionCRUD(auth).get_position_list(search=search.__dict__, order_by=order_by)
        return [PositionOutSchema.model_validate(position).model_dump() for position in position_list]

    @classmethod
    async def create_position(cls, auth: AuthSchema, data: PositionCreateSchema) -> Dict:
        """创建岗位"""
        new_position = await PositionCRUD(auth).create(data=data)
        return PositionOutSchema.model_validate(new_position).model_dump()

    @classmethod
    async def update_position(cls, auth: AuthSchema, data: PositionUpdateSchema) -> Dict:
        """更新岗位"""
        updated_position = await PositionCRUD(auth).update(id=data.id, data=data)
        return PositionOutSchema.model_validate(updated_position).model_dump()

    @classmethod
    async def delete_position(cls, auth: AuthSchema, id: int) -> None:
        """删除岗位"""
        await PositionCRUD(auth).delete(ids=[id])

    @classmethod
    async def set_position_available(cls, auth: AuthSchema, data: BatchSetAvailable) -> None:
        """设置岗位状态"""
        await PositionCRUD(auth).set_position_available(ids=data.ids, available=data.available)

    @classmethod
    async def export_post_list(cls, post_list: List[Dict[str, Any]]) -> bytes:
        """导出岗位列表"""
        mapping_dict = {
            'id': '岗位编号',
            'name': '岗位名称', 
            'order': '显示顺序',
            'available': '状态',
            'creator': '创建者',
            'create_datetime': '创建时间',
            'modifier': '更新者',
            'update_datetime': '更新时间',
            'description': '备注',
        }

        # 复制数据并转换状态
        data = post_list.copy()
        for item in data:
            item['available'] = '正常' if item.get('available') else '停用'

        # 转换为中文键
        new_data = [
            {mapping_dict.get(key): value for key, value in item.items() if mapping_dict.get(key)} 
            for item in data
        ]

        return ExcelUtil.export_list2excel(list_data=new_data)