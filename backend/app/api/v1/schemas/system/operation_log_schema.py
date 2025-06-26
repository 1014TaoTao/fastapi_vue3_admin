# -*- coding: utf-8 -*-

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.base_schema import BaseSchema


class OperationLogCreateSchema(BaseModel):
    """日志创建模型"""
    request_path: Optional[str] = Field(default=None, description="请求路径")
    request_method: Optional[str] = Field(default=None, description="请求方法")
    request_payload: Optional[str] = Field(default=None, description="请求负载")
    request_ip: Optional[str] = Field(default=None, description="请求 IP 地址")
    login_location: Optional[str] = Field(default=None, description="登录位置")
    request_os: Optional[str] = Field(default=None, description="请求操作系统")
    request_browser: Optional[str] = Field(default=None, description="请求浏览器")
    response_code: Optional[int] = Field(default=None, description="响应状态码")
    response_json: Optional[str] = Field(default=None, description="响应 JSON 数据")
    process_time: Optional[float] = Field(default=None, description="处理时间")
    description: Optional[str] = Field(default=None, max_length=255, description="备注")
    creator_id: Optional[str] = Field(default=None, description="创建人ID")


class OperationLogOutSchema(OperationLogCreateSchema, BaseSchema):
    """日志响应模型"""
    model_config = ConfigDict(from_attributes=True)
