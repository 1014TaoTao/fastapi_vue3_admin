# -*- coding: utf-8 -*-

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.base_schema import BaseSchema


class ConfigCreateSchema(BaseModel):
    """配置创建模型"""
    config_name: str = Field(..., max_length=500, description="参数名称")
    config_key: str = Field(..., max_length=500, description="参数键名")
    config_value: str = Field(..., max_length=500, description="参数键值")
    config_type: bool = Field(..., description="系统内置((True:是 False:否))")
    description: Optional[str] = Field(None, max_length=500, description="备注说明")


class ConfigUpdateSchema(ConfigCreateSchema):
    """配置更新模型"""
    id: str = Field(description="主键ID")


class ConfigOutSchema(ConfigCreateSchema, BaseSchema):
    """配置响应模型"""
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(description="主键ID")


class UpdataSystemConfigSchema(BaseSchema):
    """更新系统配置"""
    sys_web_title: str = Field(description="网站标题") 
    sys_web_description:  str = Field(description="网站描述")
    sys_web_favicon: str = Field(description="网站图标")
    sys_web_logo: str = Field(description="网站logo")
    sys_login_background:  str = Field(description="登录背景")
    sys_web_copyright:  str = Field(description="版权信息")
    sys_keep_record: str = Field(description="备案号")
    sys_help_doc: str = Field(description="帮助文档")
    sys_web_privacy: str = Field(description="隐私条款")
    sys_web_clause: str = Field(description="用户协议")
    sys_git_code: str = Field(description="源码地址")