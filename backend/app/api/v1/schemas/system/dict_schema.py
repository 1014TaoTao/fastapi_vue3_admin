from pydantic import BaseModel, ConfigDict, Field
from pydantic_validation_decorator import NotBlank, Pattern, Size
from typing import Optional

from app.core.base_schema import BaseSchema


class DictTypeCreateSchema(BaseModel):
    """
    字典类型表对应pydantic模型
    """

    dict_name: Optional[str] = Field(default=None, description='字典名称')
    dict_type: Optional[str] = Field(default=None, description='字典类型')
    available: Optional[bool] = Field(default=None, description='状态（0正常 1停用）')
    description: Optional[str] = Field(None, max_length=255, description="描述")

    @NotBlank(field_name='dict_name', message='字典名称不能为空')
    @Size(field_name='dict_name', min_length=0, max_length=100, message='字典类型名称长度不能超过100个字符')
    def get_dict_name(self):
        return self.dict_name

    @NotBlank(field_name='dict_type', message='字典类型不能为空')
    @Size(field_name='dict_type', min_length=0, max_length=100, message='字典类型类型长度不能超过100个字符')
    @Pattern(
        field_name='dict_type',
        regexp='^[a-z][a-z0-9_]*$',
        message='字典类型必须以字母开头，且只能为（小写字母，数字，下滑线）',
    )
    def get_dict_type(self):
        return self.dict_type

    def validate_fields(self):
        self.get_dict_name()
        self.get_dict_type()


class DictTypeUpdateSchema(DictTypeCreateSchema):
    """字典类型更新模型"""
    id: str = Field(..., description="字典类型ID")


class DictTypeOutSchema(DictTypeCreateSchema, BaseSchema):
    """字典类型响应模型"""
    model_config = ConfigDict(from_attributes=True)



class DictDataCreateSchema(BaseModel):
    """
    字典数据表对应pydantic模型
    """

    dict_sort: Optional[int] = Field(default=None, description='字典排序')
    dict_label: Optional[str] = Field(default=None, description='字典标签')
    dict_value: Optional[str] = Field(default=None, description='字典键值')
    dict_type: Optional[str] = Field(default=None, description='字典类型')
    css_class: Optional[str] = Field(default=None, description='样式属性（其他样式扩展）')
    list_class: Optional[str] = Field(default=None, description='表格回显样式')
    is_default: Optional[bool] = Field(default=None, description='是否默认（Y是 N否）')
    available: Optional[bool] = Field(default=None, description='状态（0正常 1停用）')
    description: Optional[str] = Field(default=None, max_length=255, description="描述")

    @NotBlank(field_name='dict_label', message='字典标签不能为空')
    @Size(field_name='dict_label', min_length=0, max_length=100, message='字典标签长度不能超过100个字符')
    def get_dict_label(self):
        return self.dict_label

    @NotBlank(field_name='dict_value', message='字典键值不能为空')
    @Size(field_name='dict_value', min_length=0, max_length=100, message='字典键值长度不能超过100个字符')
    def get_dict_value(self):
        return self.dict_value

    @NotBlank(field_name='dict_type', message='字典类型不能为空')
    @Size(field_name='dict_type', min_length=0, max_length=100, message='字典类型长度不能超过100个字符')
    def get_dict_type(self):
        return self.dict_type

    @Size(field_name='css_class', min_length=0, max_length=100, message='样式属性长度不能超过100个字符')
    def get_css_class(self):
        return self.css_class

    def validate_fields(self):
        self.get_dict_label()
        self.get_dict_value()
        self.get_dict_type()
        self.get_css_class()


class DictDataUpdateSchema(DictDataCreateSchema):
    """字典数据更新模型"""
    id: str = Field(..., description="字典数据ID")


class DictDataOutSchema(DictDataCreateSchema, BaseSchema):
    """字典数据响应模型"""
    model_config = ConfigDict(from_attributes=True)
