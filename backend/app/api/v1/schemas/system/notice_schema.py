# -*- coding: utf-8 -*-

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.base_schema import BaseSchema


class NoticeCreateSchema(BaseModel):
    """公告通知创建模型"""
    notice_title: str = Field(..., max_length=50, description='公告标题')
    notice_type: str = Field(..., description='公告类型（1通知 2公告）')
    notice_content: str = Field(..., description='公告内容')
    available: bool = Field(True, description="是否启用(True:启用 False:禁用)")
    description: Optional[str] = Field(None, max_length=255, description="公告描述")


class NoticeUpdateSchema(NoticeCreateSchema):
    """公告通知更新模型"""
    id: str = Field(..., description="公告通知ID")


class NoticeOutSchema(NoticeCreateSchema, BaseSchema):
    """公告通知响应模型"""
    model_config = ConfigDict(from_attributes=True)
