# -*- coding: utf-8 -*-

from typing import Any, List, Dict

from app.api.v1.schemas.system.auth_schema import AuthSchema
from app.core.ap_scheduler import SchedulerUtil
from app.core.exceptions import CustomException
from app.utils.cron_util import CronUtil
from app.utils.excel_util import ExcelUtil
from app.api.v1.schemas.system.job_schema import JobCreateSchema, JobUpdateSchema, JobOutSchema
from app.api.v1.params.system.job_param import JobQueryParams
from app.api.v1.cruds.system.job_crud import JobCRUD


class JobService:
    """
    定时任务管理模块服务层
    """
    
    @classmethod
    async def get_job_detail_service(cls, auth: AuthSchema, id: int) -> Dict:
        obj = await JobCRUD(auth).get_obj_by_id_crud(id=id)
        return JobOutSchema.model_validate(obj).model_dump()
    
    @classmethod
    async def get_job_list_service(cls, auth: AuthSchema, search: JobQueryParams = None, order_by: List[Dict[str, str]] = None) -> List[Dict]:
        if order_by:
            order_by = eval(order_by)
        obj_list = await JobCRUD(auth).get_obj_list_crud(search=search.__dict__, order_by=order_by)
        return [JobOutSchema.model_validate(obj).model_dump() for obj in obj_list]
    
    @classmethod
    async def create_job_service(cls, auth: AuthSchema, data: JobCreateSchema) -> Dict:
        exist_obj = await JobCRUD(auth).get(name=data.name)
        if exist_obj:
            raise CustomException(msg='创建失败，该定时任务已存在')
        if data.trigger == 'cron' and not CronUtil.validate_cron_expression(data.trigger_args):
            raise CustomException(msg=f'新增定时任务{data.name}失败, Cron表达式不正确')
        
        obj = await JobCRUD(auth).create_obj_crud(data=data)
        SchedulerUtil().add_job(job_info=obj)
        return JobOutSchema.model_validate(obj).model_dump()
    
    @classmethod
    async def update_job_service(cls, auth: AuthSchema, data: JobUpdateSchema) -> Dict:
        exist_obj = await JobCRUD(auth).get_obj_by_id_crud(id=data.id)
        if not exist_obj:
            raise CustomException(msg='更新失败，该定时任务不存在')
        if data.trigger == 'cron' and not CronUtil.validate_cron_expression(data.trigger_args):
            raise CustomException(msg=f'新增定时任务{data.name}失败, Cron表达式不正确')
        obj = await JobCRUD(auth).update_obj_crud(id=data.id, data=data)
        SchedulerUtil().modify_job(job_id=obj.id)
        return JobOutSchema.model_validate(obj).model_dump()
    
    @classmethod
    async def delete_job_service(cls, auth: AuthSchema, id: int) -> None:
        exist_obj = await JobCRUD(auth).get_obj_by_id_crud(id=id)
        if not exist_obj:
            raise CustomException(msg='删除失败，该数据定时任务不存在')
        await JobCRUD(auth).delete_obj_crud(ids=[id])
        SchedulerUtil.remove_job(job_id=id)

    @classmethod
    async def clear_job_service(cls, auth: AuthSchema) -> None:
        SchedulerUtil().clear_jobs()
        await JobCRUD(auth).clear_obj_crud()

    @classmethod
    async def option_job_service(cls, auth: AuthSchema, id: int, option: int) -> None:
        # 1: 暂停 2: 恢复 3: 重启
        obj = await JobCRUD(auth).get_obj_by_id_crud(id=id)
        if not obj:
            raise CustomException(msg='操作失败，该数据定时任务不存在')
        if option == 1:
            SchedulerUtil().pause_job(job_id=id)
            await JobCRUD(auth).set_obj_field_crud(ids=[id], status=False)
        elif option == 2:
            SchedulerUtil().resume_job(job_id=id)
            await JobCRUD(auth).set_obj_field_crud(ids=[id], status=True)
        # elif option == 3:
        #     SchedulerUtil().reschedule_job(job_id=id)
        #     await JobCRUD(auth).set_obj_field_crud(ids=[id], status=False)

    @classmethod
    async def export_job_service(cls, data_list: List[Dict[str, Any]]) -> bytes:
        """导出公告列表"""
        mapping_dict = {
            'id': '编号',
            'name': '任务名称',
            'func': '任务函数',
            'trigger': '触发器',
            'args': '位置参数',
            'kwargs': '关键字参数',
            'coalesce': '是否合并运行',
            'max_instances': '最大实例数',
            'jobstore': '任务存储',
            'executor': '任务执行器',
            'trigger_args': '触发器参数',
            'status': '任务状态',
            'message': '日志信息',
            'description': '备注',
            'created_at': '创建时间',
            'updated_at': '更新时间',
            'creator_id': '创建者ID',
            'creator': '创建者',
        }

        # 复制数据并转换状态
        data = data_list.copy()
        for item in data:
            item['status'] = '已完成' if item['status'] == 0 else '运行中' if item['status'] == 1 else '暂停'

        return ExcelUtil.export_list2excel(list_data=data_list, mapping_dict=mapping_dict)
    