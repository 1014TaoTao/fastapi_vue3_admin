# -*- coding: utf-8 -*-

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

from app.core.base_schema import BaseSchema


class JobCreateSchema(BaseModel):
    """
    定时任务调度表对应pydantic模型
    """

    name: Optional[str] = Field(default=None, max_length=64, description='任务名称')
    func: str = Field(..., description='任务函数')
    trigger: str = Field(..., description='触发器:控制此作业计划的 trigger 对象')
    args: Optional[str] = Field(default=None, description='位置参数')
    kwargs: Optional[str] = Field(default=None, description='关键字参数')
    coalesce: Optional[bool] = Field(default=False, description='是否合并运行:是否在多个运行时间到期时仅运行作业一次')
    max_instances: Optional[int] = Field(default=1, ge=1, description='最大实例数:允许的最大并发执行实例数')
    jobstore: Optional[str] = Field(default='default', max_length=64, description='任务存储')
    executor: Optional[str] = Field(default='default', max_length=64, description='任务执行器:将运行此作业的执行程序的名称')
    trigger_args: Optional[str] = Field(default=None, description='触发器参数')
    start_date: Optional[str] = Field(default=None, description='开始时间')
    end_date: Optional[str] = Field(default=None, description='结束时间')
    description: Optional[str] = Field(default=None, description='备注说明')
    status: Optional[bool] = Field(default=False, description='任务状态:启动,停止')
    message: Optional[str] = Field(default=None, max_length=500, description='日志信息')

class JobUpdateSchema(JobCreateSchema):
    """定时任务更新模型"""
    ...
    id: str = Field(..., description="ID")
    

class JobOutSchema(JobCreateSchema, BaseSchema):
    """定时任务响应模型"""
    model_config = ConfigDict(from_attributes=True)
    ...
    