# -*- coding: utf-8 -*-

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.validator import menu_request_validator
from app.core.base_schema import BaseSchema


class MenuCreateSchema(BaseModel):
    """菜单创建模型"""
    name: str = Field(..., max_length=50, description="菜单名称")
    type: Optional[int] = Field(default=None, ge=1, le=4, description="菜单类型(1:目录 2:菜单 3:按钮 4:外链)")
    icon: Optional[str] = Field(default=None, max_length=100, description="菜单图标")
    order: int = Field(..., ge=1, description="显示顺序")
    permission: Optional[str] = Field(default=None, max_length=100, description="权限标识")
    route_name: Optional[str] = Field(default=None, max_length=100, description="路由名称")
    route_path: Optional[str] = Field(default=None, max_length=200, description="路由地址")
    component_path: Optional[str] = Field(default=None, max_length=255, description="组件路径")
    redirect: Optional[str] = Field(default=None, max_length=200, description="重定向地址")
    status: bool = Field(default=True, description="是否启用(True:启用 False:禁用)")
    keep_alive: bool = Field(default=True, description="是否缓存(True:是 False:否)")
    hidden: bool = Field(default=False, description="是否隐藏(True:是 False:否)")
    always_show: bool = Field(default=False, description="是否始终显示(True:是 False:否)")
    title: Optional[str] = Field(default=None, max_length=50, description="菜单标题")
    params: Optional[list[dict[str, str]]] = Field(default=None, description="路由参数，格式为[{key: string, value: string}]")
    affix: bool = Field(default=False, description="是否固定标签页(True:是 False:否)")
    parent_id: Optional[int] = Field(default=None, ge=1, description="父菜单ID")
    description: Optional[str] = Field(default=None, max_length=500, description="备注说明")

    @model_validator(mode='after')
    def validate_fields(self):
        return menu_request_validator(self)


class MenuUpdateSchema(MenuCreateSchema):
    """菜单更新模型"""
    id: int = Field(..., ge=1, description="菜单ID")
    parent_name: Optional[str] = Field(default=None, max_length=50, description="父菜单名称")


class MenuOutSchema(MenuCreateSchema, BaseSchema):
    """菜单响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    parent_name: Optional[str] = Field(default=None, max_length=50, description="父菜单名称")