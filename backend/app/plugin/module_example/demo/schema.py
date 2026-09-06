from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.core.base_schema import BaseQueryParam, BaseSchema, UserByQueryParam, UserBySchema
from app.core.validator import DateStr, DateTimeStr, TimeStr


class DemoCreateSchema(BaseModel):
    """新增模型"""

    name: str = Field(..., min_length=2, max_length=50, description="名称")
    status: int = Field(default=0, ge=0, le=1, description="状态(0:正常 1:停用)")
    description: str | None = Field(default=None, max_length=255, description="描述")
    int_val: int | None = Field(default=None, description="整数")
    bigint_val: int | None = Field(default=None, description="大整数")
    float_val: float | None = Field(default=None, description="浮点数")
    bool_val: bool = Field(default=True, description="布尔型")
    date_val: DateStr | None = Field(default=None, description="日期")
    time_val: TimeStr | None = Field(default=None, description="时间")
    datetime_val: DateTimeStr | None = Field(default=None, description="日期时间")
    text_val: str | None = Field(default=None, description="长文本")
    json_val: dict | None = Field(default=None, description="元数据(JSON格式)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证名称字段的格式和内容。

        参数:
        - v (str): 原始名称。

        返回:
        - str: 去空白后的名称。

        异常:
        - ValueError: 名称为空时抛出。
        """
        # 去除首尾空格
        v = v.strip()
        if not v:
            raise ValueError("名称不能为空")
        return v

    @model_validator(mode="after")
    def validate_name_format(self):
        """核心业务规则校验
        """
        # 格式校验：名称只能包含字母、数字、下划线和中划线
        if not all(c.isalnum() or c in "-_" for c in self.name):
            raise ValueError("名称只能包含字母、数字、下划线和中划线")
        return self


class DemoUpdateSchema(BaseModel):
    """更新模型"""

    name: str | None = Field(default=None, min_length=2, max_length=50, description="名称")
    status: int | None = Field(default=None, ge=0, le=1, description="状态(0:正常 1:停用)")
    description: str | None = Field(default=None, max_length=255, description="描述")
    int_val: int | None = Field(default=None, description="整数")
    bigint_val: int | None = Field(default=None, description="大整数")
    float_val: float | None = Field(default=None, description="浮点数")
    bool_val: bool | None = Field(default=None, description="布尔型")
    date_val: DateStr | None = Field(default=None, description="日期")
    time_val: TimeStr | None = Field(default=None, description="时间")
    datetime_val: DateTimeStr | None = Field(default=None, description="日期时间")
    text_val: str | None = Field(default=None, description="长文本")
    json_val: dict | None = Field(default=None, description="元数据(JSON格式)")


class DemoOutSchema(DemoCreateSchema, BaseSchema, UserBySchema):
    """响应模型"""

    model_config = ConfigDict(from_attributes=True)


class DemoQueryParam(BaseQueryParam, UserByQueryParam):
    """示例查询参数（演示 Mixin 继承用法）"""

    name: str | None = Field(None, description="名称", json_schema_extra={"q": "like"})
    description: str | None = Field(None, description="描述", json_schema_extra={"q": "like"})
    status: int | None = Field(None, description="状态(0:正常 1:停用)", json_schema_extra={"q": "eq"})
