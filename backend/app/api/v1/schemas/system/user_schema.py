# -*- coding: utf-8 -*-

from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator

from app.api.v1.schemas.system.position_schema import PositionOutSchema
from app.api.v1.schemas.system.role_schema import RoleOutSchema
from app.api.v1.schemas.system.dept_schema import DeptOutSchema
from app.core.validator import DateTimeStr, mobile_validator
from app.core.base_schema import BaseSchema


class CurrentUserUpdateSchema(BaseModel):
    """基础用户信息"""
    name: str = Field(default=None, max_length=15, description="名称")
    mobile: Optional[str] = Field(default=None, description="手机号")
    email: Optional[EmailStr] = Field(default=None, description="邮箱")
    gender: Optional[str] = Field(default=None, description="性别")
    avatar: Optional[str] = Field(default=None, description="头像")

    @classmethod
    @field_validator("mobile")
    def validate_mobile(cls, value: Optional[str]):
        return mobile_validator(value)


class UserRegisterSchema(BaseModel):
    """注册"""
    name: str = Field(default=None, max_length=15, description="名称")
    mobile: Optional[str] = Field(default=None, description="手机号")
    username: str = Field(default=None, max_length=15, description="账号")
    password: str = Field(default=None, max_length=128, description="密码哈希值")
    role_ids: Optional[List[str]] = Field(default=["dcfd6d46-5586-48d5-ba3e-f13415b87f06"], description='角色ID')
    creator_id: Optional[str] = Field(default=None, description='创建人ID')
    description: Optional[str] = Field(default=f'注册用户{username}', max_length=250, description="备注")


class UserForgetPasswordSchema(BaseModel):
    """忘记密码"""
    username: str = Field(default=None, max_length=15, description="用户名")
    mobile: Optional[str] = Field(default=None, description="手机号")
    new_password: str = Field(default=None, max_length=128, description="新密码")
    
    @classmethod
    @field_validator("mobile")
    def validate_mobile(cls, value: Optional[str]):
        return mobile_validator(value)


class UserChangePasswordSchema(BaseModel):
    """修改密码"""
    old_password: str = Field(default=None, max_length=128, description="旧密码")
    new_password: str = Field(default=None, max_length=128, description="新密码")


class UserCreateSchema(CurrentUserUpdateSchema):
    """新增"""
    model_config = ConfigDict(from_attributes=True)
    
    username: str = Field(default=None, max_length=15, description="用户名")
    password: Optional[str] = Field(default=None, max_length=128, description="密码哈希值")
    available: bool = Field(default=True, description="是否可用")
    is_superuser: bool = Field(default=False, description="是否超管")
    description: Optional[str] = Field(None, max_length=255, description="备注")
    
    dept_id: Optional[str] = Field(default=None, description='部门ID')
    role_ids: Optional[List[str]] = Field(default=[], description='角色ID')
    position_ids: Optional[List[str]] = Field(default=[], description='岗位ID')


class UserUpdateSchema(UserCreateSchema):
    """更新"""
    id: str = Field(..., description="主键ID")


class UserOutSchema(UserCreateSchema, BaseSchema):
    """响应"""
    model_config = ConfigDict(arbitrary_types_allowed=True, from_attributes=True)
    
    last_login: Optional[DateTimeStr] = Field(default=None, description="最后登录时间")
    dept_name: Optional[str] = Field(default=None, description='部门名称')
    dept: Optional[DeptOutSchema] = Field(default=None, description='部门')
    roles: List[RoleOutSchema] = Field(default=[], description='角色')
    positions: List[PositionOutSchema] = Field(default=[], description='岗位')
