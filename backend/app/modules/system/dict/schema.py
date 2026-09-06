import re

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.core.base_schema import BaseQueryParam, BaseSchema


class DictTypeCreateSchema(BaseModel):
    """字典类型表对应pydantic模型
    """

    dict_name: str = Field(..., min_length=1, max_length=64, description="字典名称")
    dict_type: str = Field(..., min_length=1, max_length=255, description="字典类型编码")
    status: int = Field(default=0, ge=0, le=1, description="状态(0:正常 1:停用)")
    description: str | None = Field(default=None, max_length=255, description="描述")

    @field_validator("dict_name")
    @classmethod
    def validate_dict_name(cls, value: str):
        """校验字典名称为非空字符串。

        参数:
        - value (str): 字典名称。

        返回:
        - str: 去首尾空格后的字典名称。

        异常:
        - ValueError: 字典名称为空时抛出。
        """
        if not value or value.strip() == "":
            raise ValueError("字典名称不能为空")
        return value.strip()

    @field_validator("dict_type")
    @classmethod
    def validate_dict_type(cls, value: str):
        """校验字典类型：小写字母开头，仅包含小写字母/数字/下划线。

        参数:
        - value (str): 字典类型。

        返回:
        - str: 去首尾空格后的字典类型。

        异常:
        - ValueError: 字典类型为空或不满足格式要求时抛出。
        """
        if not value or value.strip() == "":
            raise ValueError("字典类型不能为空")
        regexp = r"^[a-z][a-z0-9_]*$"
        if not re.match(regexp, value):
            raise ValueError("字典类型必须以字母开头，且只能为（小写字母，数字，下滑线）")
        return value.strip()


class DictTypeUpdateSchema(DictTypeCreateSchema):
    """字典类型更新模型"""


class DictTypeOutSchema(DictTypeCreateSchema, BaseSchema):
    """字典类型响应模型"""

    model_config = ConfigDict(from_attributes=True)


class DictTypeQueryParam(BaseQueryParam):
    """字典类型查询参数"""

    dict_name: str | None = Field(default=None, description="字典名称", max_length=100, json_schema_extra={"q": "like"})
    dict_type: str | None = Field(default=None, description="字典类型", max_length=100, json_schema_extra={"q": "eq"})
    status: int | None = Field(default=None, ge=0, le=1, description="状态(0:启动 1:停用)", json_schema_extra={"q": "eq"})


class DictDataCreateSchema(BaseModel):
    """字典数据表对应pydantic模型
    """

    dict_sort: int = Field(..., ge=1, le=999, description="排序")
    dict_label: str = Field(..., min_length=1, max_length=255, description="字典标签")
    dict_value: str = Field(..., min_length=1, max_length=255, description="字典键值")
    dict_type: str = Field(..., max_length=255, description="字典类型")
    dict_type_id: int = Field(..., gt=0, description="字典类型ID")
    css_class: str | None = Field(default=None, max_length=255, description="样式属性")
    list_class: str | None = Field(default=None, max_length=255, description="表格回显样式")
    is_default: bool = Field(default=False, description="是否默认")
    status: int = Field(default=0, ge=0, le=1, description="状态(0:正常 1:停用)")
    description: str | None = Field(default=None, max_length=255, description="描述")

    @model_validator(mode="after")
    def validate_after(self):
        """校验并规范化字典数据字段（标签/键值/类型/类型ID）。

        返回:
        - DictDataCreateSchema: 校验与去空格后的同一实例。

        异常:
        - ValueError: 必填字段为空或类型ID非法时抛出。
        """
        if not self.dict_label or not self.dict_label.strip():
            raise ValueError("字典标签不能为空")
        if not self.dict_value or not self.dict_value.strip():
            raise ValueError("字典键值不能为空")
        if not self.dict_type or not self.dict_type.strip():
            raise ValueError("字典类型不能为空")
        if not hasattr(self, "dict_type_id") or self.dict_type_id <= 0:
            raise ValueError("字典类型ID不能为空且必须大于0")

        # 确保字符串字段被正确处理
        self.dict_label = self.dict_label.strip()
        self.dict_value = self.dict_value.strip()
        self.dict_type = self.dict_type.strip()

        return self


class DictDataUpdateSchema(DictDataCreateSchema):
    """字典数据更新模型"""


class DictDataOutSchema(DictDataCreateSchema, BaseSchema):
    """字典数据响应模型"""

    model_config = ConfigDict(from_attributes=True)


class DictDataQueryParam(BaseQueryParam):
    """字典数据查询参数"""

    dict_label: str | None = Field(default=None, description="字典标签", max_length=255, json_schema_extra={"q": "like"})
    dict_type: str | None = Field(default=None, description="字典类型", max_length=255, json_schema_extra={"q": "eq"})
    dict_type_id: int | None = Field(default=None, description="字典类型ID", json_schema_extra={"q": "eq"})
    status: int | None = Field(default=None, ge=0, le=1, description="状态(0:启动 1:停用)", json_schema_extra={"q": "eq"})
