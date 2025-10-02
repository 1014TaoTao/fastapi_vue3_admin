# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Optional

from app.core.base_schema import BatchSetAvailable
from app.core.exceptions import CustomException
from app.utils.excel_util import ExcelUtil
from ..auth.schema import AuthSchema
from .param import PositionQueryParam
from .crud import PositionCRUD
from .schema import (
    PositionCreateSchema,
    PositionUpdateSchema,
    PositionOutSchema,
)


class PositionService:
    """岗位模块服务层"""

    @classmethod
    async def get_position_detail_service(cls, auth: AuthSchema, id: int) -> Dict:
        """获取岗位详情"""
        position = await PositionCRUD(auth).get_by_id_crud(id=id)
        return PositionOutSchema.model_validate(position).model_dump()

    @classmethod
    async def get_position_list_service(cls, auth: AuthSchema, search: Optional[PositionQueryParam] = None, order_by: Optional[List[Dict[str, str]]] = None) -> List[Dict]:
        """获取岗位列表"""
        position_list = await PositionCRUD(auth).get_list_crud(search=search.__dict__, order_by=order_by)
        return [PositionOutSchema.model_validate(position).model_dump() for position in position_list]

    @classmethod
    async def create_position_service(cls, auth: AuthSchema, data: PositionCreateSchema) -> Dict:
        """创建岗位"""
        position = await PositionCRUD(auth).get(name=data.name)
        if position:
            raise CustomException(msg='创建失败，该岗位已存在')
        new_position = await PositionCRUD(auth).create(data=data)
        return PositionOutSchema.model_validate(new_position).model_dump()

    @classmethod
    async def update_position_service(cls, auth: AuthSchema, id:int, data: PositionUpdateSchema) -> Dict:
        """更新岗位"""
        position = await PositionCRUD(auth).get_by_id_crud(id=id)
        if not position:
            raise CustomException(msg='更新失败，该岗位不存在')
        exist_position = await PositionCRUD(auth).get(name=data.name)
        if exist_position and exist_position.id != id:
            raise CustomException(msg='更新失败，岗位名称重复')
        updated_position = await PositionCRUD(auth).update(id=id, data=data)
        return PositionOutSchema.model_validate(updated_position).model_dump()

    @classmethod
    async def delete_position_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        """删除岗位"""
        if len(ids) < 1:
            raise CustomException(msg='删除失败，删除对象不能为空')
        for id in ids:
            position = await PositionCRUD(auth).get_by_id_crud(id=id)
            if not position:
                raise CustomException(msg='删除失败，该岗位不存在')
        await PositionCRUD(auth).delete(ids=ids)

    @classmethod
    async def set_position_available_service(cls, auth: AuthSchema, data: BatchSetAvailable) -> None:
        """设置岗位状态"""
        await PositionCRUD(auth).set_available_crud(ids=data.ids, status=data.status)

    @classmethod
    async def export_position_list_service(cls, position_list: List[Dict[str, Any]]) -> bytes:
        """导出岗位列表"""
        mapping_dict = {
            'id': '编号',
            'name': '岗位名称', 
            'order': '显示顺序',
            'status': '状态',
            'description': '备注',
            'created_at': '创建时间',
            'updated_at': '更新时间',
            'creator_id': '创建者ID',
            'creator': '创建者',
        }

        # 复制数据并转换状态
        data = position_list.copy()
        for item in data:
            item['status'] = '正常' if item.get('status') else '停用'
            item['creator'] = item.get('creator', {}).get('name', '未知') if isinstance(item.get('creator'), dict) else '未知'

        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)