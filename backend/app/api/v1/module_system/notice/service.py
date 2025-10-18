# -*- coding: utf-8 -*-

from typing import Any, List, Dict, Optional


from app.core.base_schema import BatchSetAvailable
from app.core.exceptions import CustomException
from app.utils.excel_util import ExcelUtil
from ..auth.schema import AuthSchema
from .schema import NoticeCreateSchema, NoticeUpdateSchema, NoticeOutSchema
from .param import NoticeQueryParam
from .crud import NoticeCRUD


class NoticeService:
    """
    公告管理模块服务层
    """
    
    @classmethod
    async def get_notice_detail_service(cls, auth: AuthSchema, id: int) -> Dict:
        """
        获取公告详情。
        
        参数:
        - auth (AuthSchema): 认证信息模型。
        - id (int): 公告ID。
        
        返回:
        - Dict: 公告详情字典。
        """
        notice_obj = await NoticeCRUD(auth).get_by_id_crud(id=id)
        return NoticeOutSchema.model_validate(notice_obj).model_dump()
    
    @classmethod
    async def get_notice_list_available_service(cls, auth: AuthSchema) -> List[Dict]:
        """
        获取可用的公告列表。
        
        参数:
        - auth (AuthSchema): 认证信息模型。
        
        返回:
        - List[Dict]: 可用公告详情字典列表。
        """
        notice_obj_list = await NoticeCRUD(auth).get_list_crud(search={'status': True})
        return [NoticeOutSchema.model_validate(notice_obj).model_dump() for notice_obj in notice_obj_list]

    @classmethod
    async def get_notice_list_service(cls, auth: AuthSchema, search: Optional[NoticeQueryParam] = None, order_by: Optional[List[Dict[str, str]]] = None) -> List[Dict]:
        """
        获取公告列表。
        
        参数:
        - auth (AuthSchema): 认证信息模型。
        - search (Optional[NoticeQueryParam]): 查询参数模型。
        - order_by (Optional[List[Dict[str, str]]]): 排序参数列表。
        
        返回:
        - List[Dict]: 公告详情字典列表。
        """
        notice_obj_list = await NoticeCRUD(auth).get_list_crud(search=search.__dict__, order_by=order_by)
        return [NoticeOutSchema.model_validate(notice_obj).model_dump() for notice_obj in notice_obj_list]
    
    @classmethod
    async def create_notice_service(cls, auth: AuthSchema, data: NoticeCreateSchema) -> Dict:
        """
        创建公告。
        
        参数:
        - auth (AuthSchema): 认证信息模型。
        - data (NoticeCreateSchema): 创建公告负载模型。
        
        返回:
        - Dict: 创建的公告详情字典。
        
        异常:
        - CustomException: 创建失败，该公告通知已存在。
        """
        notice = await NoticeCRUD(auth).get(notice_title=data.notice_title)
        if notice:
            raise CustomException(msg='创建失败，该公告通知已存在')
        notice_obj = await NoticeCRUD(auth).create_crud(data=data)
        return NoticeOutSchema.model_validate(notice_obj).model_dump()
    
    @classmethod
    async def update_notice_service(cls, auth: AuthSchema, id: int, data: NoticeUpdateSchema) -> Dict:
        """
        更新公告。
        
        参数:
        - auth (AuthSchema): 认证信息模型。
        - id (int): 公告ID。
        - data (NoticeUpdateSchema): 更新公告负载模型。
        
        返回:
        - Dict: 更新的公告详情字典。
        
        异常:
        - CustomException: 更新失败，该公告通知不存在或公告通知标题重复。
        """
        notice = await NoticeCRUD(auth).get_by_id_crud(id=id)
        if not notice:
            raise CustomException(msg='更新失败，该公告通知不存在')
        exist_notice = await NoticeCRUD(auth).get(notice_title=data.notice_title)
        if exist_notice and exist_notice.id != id:
            raise CustomException(msg='更新失败，公告通知标题重复')
        notice_obj = await NoticeCRUD(auth).update_crud(id=id, data=data)
        return NoticeOutSchema.model_validate(notice_obj).model_dump()
    
    @classmethod
    async def delete_notice_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        """
        删除公告。
        
        参数:
        - auth (AuthSchema): 认证信息模型。
        - ids (list[int]): 删除的ID列表。
        
        异常:
        - CustomException: 删除失败，删除对象不能为空或该公告通知不存在。
        """ 
        if len(ids) < 1:
            raise CustomException(msg='删除失败，删除对象不能为空')
        for id in ids:
            notice = await NoticeCRUD(auth).get_by_id_crud(id=id)
            if not notice:
                raise CustomException(msg='删除失败，该公告通知不存在')
        await NoticeCRUD(auth).delete_crud(ids=ids)
    
    @classmethod
    async def set_notice_available_service(cls, auth: AuthSchema, data: BatchSetAvailable) -> None:
        """
        批量设置公告状态。
        
        参数:
        - auth (AuthSchema): 认证信息模型。
        - data (BatchSetAvailable): 批量设置可用负载模型。
        
        异常:
        - CustomException: 批量设置失败，该公告通知不存在。
        """ 
        await NoticeCRUD(auth).set_available_crud(ids=data.ids, status=data.status)
    
    @classmethod
    async def export_notice_service(cls, notice_list: List[Dict[str, Any]]) -> bytes:
        """
        导出公告列表。
        
        参数:
        - notice_list (List[Dict[str, Any]]): 公告详情字典列表。
        
        返回:
        - bytes: Excel 文件的字节流。
        """
        mapping_dict = {
            'id': '编号',
            'notice_title': '公告标题', 
            'notice_type': '公告类型（1通知 2公告）',
            'notice_content': '公告内容',
            'status': '状态',
            'description': '备注',
            'created_at': '创建时间',
            'updated_at': '更新时间',
            'creator_id': '创建者ID',
            'creator': '创建者',
        }

        # 复制数据并转换状态
        data = notice_list.copy()
        for item in data:
            # 处理状态
            item['status'] = '正常' if item.get('status') else '停用'
            # 处理公告类型
            item['notice_type'] = '通知' if item.get('notice_type') == '1' else '公告'
            item['creator'] = item.get('creator', {}).get('name', '未知') if isinstance(item.get('creator'), dict) else '未知'

        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)