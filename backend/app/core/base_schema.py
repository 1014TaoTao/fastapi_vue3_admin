# -*- coding: utf-8 -*-

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.validator import DateTimeStr


class UserInfoSchema(BaseModel):
    """用户信息模型"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="用户ID")
    name: str = Field(description="用户姓名")
    username: str = Field(description="用户名")


class BaseSchema(BaseModel):
    """通用输出模型，包含基础字段和审计字段"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="主键ID")
    created_at: DateTimeStr = Field(description="创建时间")
    updated_at: DateTimeStr = Field(description="更新时间")
    creator_id: Optional[str] = Field(default=None, description="创建人ID")
    creator: Optional[UserInfoSchema] = Field(default=None, description="创建人信息")


class BatchSetAvailable(BaseModel):
    """批量设置可用状态的请求模型"""
    ids: List[str] = Field(default_factory=list, description="ID列表")
    available: bool = Field(default=True, description="是否可用")


class UploadResponseSchema(BaseModel):
    """
    上传响应模型
    """

    model_config = ConfigDict(from_attributes=True)

    file_path: Optional[str] = Field(default=None, description='新文件映射路径')
    file_name: Optional[str] = Field(default=None, description='新文件名称') 
    origin_name: Optional[str] = Field(default=None, description='原文件名称')
    file_url: Optional[str] = Field(default=None, description='新文件访问地址')
