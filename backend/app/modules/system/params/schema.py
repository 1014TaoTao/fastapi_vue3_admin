import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.base_schema import BaseSchema


class ParamsBaseSchema(BaseModel):
    """参数基础字段
    """

    config_name: str = Field(..., min_length=1, max_length=64, description="参数名称")
    config_key: str = Field(..., min_length=1, max_length=500, description="参数键名（小写字母开头，仅允许字母数字_.-）")
    config_value: str | None = Field(default=None, description="参数键值")
    config_type: bool = Field(default=False, description="是否系统内置(True:是 False:否)")
    status: int = Field(default=0, ge=0, le=1, description="状态(0:正常 1:停用)")
    description: str | None = Field(default=None, max_length=500, description="参数描述")

    @field_validator("config_key")
    @classmethod
    def _validate_config_key(cls, v: str) -> str:
        """校验参数键名：小写字母开头，仅含字母/数字/_ . -"""
        v = v.strip().lower()
        if not re.match(r"^[a-z][a-z0-9_.-]*$", v):
            raise ValueError("参数键名必须以小写字母开头，仅允许小写字母、数字、_ . -")
        return v


class ParamsUpdateSchema(ParamsBaseSchema):
    """参数更新模型
    """


class ParamsOutSchema(ParamsBaseSchema, BaseSchema):
    """参数响应模型
    """

    model_config = ConfigDict(from_attributes=True)
