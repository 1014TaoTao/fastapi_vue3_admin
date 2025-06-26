# -*- coding: utf-8 -*-

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api.v1.schemas.system.dept_schema import DeptOutSchema
from app.api.v1.schemas.system.menu_schema import MenuOutSchema
from app.core.base_schema import BaseSchema
from app.core.validator import role_permission_request_validator


class RoleCreateSchema(BaseModel):
    """角色创建模型"""
    name: str = Field(default=None, max_length=15, description="角色名称")
    order: Optional[int] = Field(default=1, ge=1, description='显示排序')
    data_scope: Optional[int] = Field(default=1, ge=1, le=5, description='数据权限范围')
    available: bool = Field(default=True, description="是否启用")
    description: Optional[str] = Field(None, max_length=255, description="角色描述")


class RolePermissionSettingSchema(BaseModel):
    """角色权限配置模型"""
    data_scope: int = Field(default=1, ge=1, le=5, description='数据权限范围')
    role_ids: List[str] = Field(default_factory=list, description='角色ID列表')
    menu_ids: List[str] = Field(default_factory=list, description='菜单ID列表')
    dept_ids: List[str] = Field(default_factory=list, description='部门ID列表')
    
    @classmethod
    @model_validator(mode='after')
    def validate_fields(cls, data):
        """验证权限配置字段"""
        return role_permission_request_validator(data)


class RoleUpdateSchema(RoleCreateSchema):
    """角色更新模型"""
    id: str = Field(..., description="角色ID")


class RoleOutSchema(RoleCreateSchema, BaseSchema):
    """角色信息响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    menus: List[MenuOutSchema] = Field(default_factory=list, description='角色菜单列表')
    depts: List[DeptOutSchema] = Field(default_factory=list, description='角色部门列表')
