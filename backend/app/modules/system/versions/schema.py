from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.base_schema import BaseQueryParam
from app.core.validator import DateTimeStr


class VersionCreateSchema(BaseModel):
    """版本创建模型"""

    version: str = Field(..., description="版本号")
    title: str = Field(..., description="更新标题")
    date: str = Field(..., description="发布日期")
    content: str | None = Field(default=None, description="更新内容(富文本HTML)")
    description: str | None = Field(default=None, description="备注")
    sort: int = Field(default=0, description="排序")
    status: int = Field(default=0, description="状态: 0=草稿,1=已发布,2=已回滚")
    require_re_login: bool = Field(default=False, description="是否需要重新登录")


class VersionUpdateSchema(VersionCreateSchema):
    """版本更新模型"""


class VersionOutSchema(VersionCreateSchema):
    """版本响应模型"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="主键ID")
    created_time: DateTimeStr | None = Field(default=None, description="创建时间")
    updated_time: DateTimeStr | None = Field(default=None, description="更新时间")


class VersionStatusSchema(BaseModel):
    """版本状态更新模型"""

    status: int = Field(..., description="状态: 0=草稿,1=已发布,2=已回滚")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: int) -> int:
        if v not in (0, 1, 2):
            raise ValueError("status must be 0, 1, or 2")
        return v


class VersionQueryParam(BaseQueryParam):
    """版本查询参数"""

    status: int | None = Field(default=None, description="状态: 0=草稿,1=已发布,2=已回滚", json_schema_extra={"q": "eq"})
