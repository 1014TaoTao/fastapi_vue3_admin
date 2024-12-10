# -*- coding: utf-8 -*-

from typing import Any, List, Dict

from app.api.v1.schemas.system.auth_schema import AuthSchema
from app.api.v1.schemas.system.notice_schema import NoticeCreateSchema, NoticeUpdateSchema, NoticeOutSchema
from app.core.base_schema import BatchSetAvailable
from app.api.v1.params.system.notice_param import NoticeQueryParams
from app.api.v1.cruds.system.notice_crud import NoticeCRUD
from app.utils.excel_util import ExcelUtil


class NoticeService:
    """
    公告管理模块服务层
    """
    
    @classmethod
    async def get_notice_detail_services(cls, auth: AuthSchema, id: int) -> Dict:
        config_obj = await NoticeCRUD(auth).get_notice_by_id(id=id)
        return NoticeOutSchema.model_validate(config_obj).model_dump()
    
    @classmethod
    async def get_notice_list_services(cls, auth: AuthSchema, search: NoticeQueryParams = None, order_by: List[Dict[str, str]] = None) -> List[Dict]:
        config_obj_list = await NoticeCRUD(auth).get_notice_list(search=search.__dict__, order_by=order_by)
        return [NoticeOutSchema.model_validate(config_obj).model_dump() for config_obj in config_obj_list]
    
    @classmethod
    async def create_notice_services(cls, auth: AuthSchema, data: NoticeCreateSchema) -> Dict:
        config_obj = await NoticeCRUD(auth).create_notice(data=data)
        return NoticeOutSchema.model_validate(config_obj).model_dump()
    
    @classmethod
    async def update_notice_services(cls, auth: AuthSchema, data: NoticeUpdateSchema) -> Dict:
        config_obj = await NoticeCRUD(auth).update_notice(id=data.id, data=data)
        return NoticeOutSchema.model_validate(config_obj).model_dump()
    
    @classmethod
    async def delete_notice_services(cls, auth: AuthSchema, id: int) -> None:
        await NoticeCRUD(auth).delete_notice(ids=[id])
    
    @classmethod
    async def set_notice_available_services(cls, auth: AuthSchema, data: BatchSetAvailable) -> None:
        await NoticeCRUD(auth).set_notice_available(ids=data.ids, available=data.available)
    
    @classmethod
    async def export_notice_services(cls, notice_list: List[Dict[str, Any]]) -> bytes:
        """导出公告列表"""
        mapping_dict = {
            'id': '公告编号',
            'notice_title': '公告标题', 
            'notice_type': '公告类型（1通知 2公告）',
            'notice_content': '公告内容',
            'available': '状态',
            'description': '备注',
            'created_at': '创建时间',
            'updated_at': '更新时间',
            'creator_id': '创建者ID',
            'creator': '创建者',
        }

        # 复制数据并转换状态
        data = notice_list.copy()
        for item in data:
            item['available'] = '正常' if item.get('available') else '停用'

        # 转换为中文键
        new_data = [
            {mapping_dict.get(key): value for key, value in item.items() if mapping_dict.get(key)} 
            for item in data
        ]

        return ExcelUtil.export_list2excel(list_data=new_data)