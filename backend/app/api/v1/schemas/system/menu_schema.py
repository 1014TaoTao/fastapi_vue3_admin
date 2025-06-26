# -*- coding: utf-8 -*-

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.validator import menu_request_validator
from app.core.base_schema import BaseSchema


class MenuCreateSchema(BaseModel):
    """菜单创建模型"""
    name: str = Field(..., max_length=50, description="菜单名称")
    type: int = Field(..., ge=1, le=3, description="菜单类型(1:目录 2:菜单 3:按钮)")
    icon: Optional[str] = Field(default=None, max_length=100, description="菜单图标")
    order: int = Field(default=1, ge=0, description="显示顺序")
    permission: Optional[str] = Field(default=None, max_length=100, description="权限标识")
    route_name: Optional[str] = Field(default=None, max_length=100, description="路由名称")
    route_path: Optional[str] = Field(default=None, max_length=200, description="路由地址")
    component_path: Optional[str] = Field(default=None, max_length=255, description="组件路径")
    redirect: Optional[str] = Field(default=None, max_length=200, description="重定向地址")
    available: bool = Field(default=True, description="是否启用(True:启用 False:禁用)")
    cache: bool = Field(default=True, description="是否缓存(True:是 False:否)")
    hidden: bool = Field(default=False, description="是否隐藏(True:是 False:否)")
    parent_id: Optional[str] = Field(default=None, description="父菜单ID")
    description: Optional[str] = Field(default=None, max_length=500, description="备注说明")

    @classmethod
    @model_validator(mode='after')
    def validate_fields(cls, data):
        return menu_request_validator(data)


class MenuUpdateSchema(MenuCreateSchema):
    """菜单更新模型"""
    id: str = Field(..., description="菜单ID")
    parent_name: Optional[str] = Field(default=None, max_length=50, description="父菜单名称")


class MenuOutSchema(MenuCreateSchema, BaseSchema):
    """菜单响应模型"""
    model_config = ConfigDict(from_attributes=True)
    parent_name: Optional[str] = Field(default=None, max_length=50, description="父菜单名称")