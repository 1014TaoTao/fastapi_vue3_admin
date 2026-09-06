from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.base_schema import BaseQueryParam, BaseSchema, UserByQueryParam, UserBySchema


class PositionCreateSchema(BaseModel):
    """岗位创建模型"""

    name: str = Field(..., min_length=1, max_length=64, description="岗位名称")
    code: str = Field(..., min_length=1, max_length=64, description="岗位编码")
    order: int = Field(default=1, ge=0, description="显示排序")
    status: int = Field(default=0, ge=0, le=1, description="状态(0:启动 1:停用)")
    description: str | None = Field(default=None, max_length=255, description="描述")

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("岗位名称不能为空")
        return v

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("岗位编码不能为空")
        return v


class PositionUpdateSchema(PositionCreateSchema):
    """岗位更新模型"""


class PositionOutSchema(PositionCreateSchema, BaseSchema, UserBySchema):
    """岗位信息响应模型"""

    model_config = ConfigDict(from_attributes=True)


class PositionQueryParam(BaseQueryParam, UserByQueryParam):
    """岗位管理查询参数"""

    name: str | None = Field(None, description="岗位名称", json_schema_extra={"q": "like"})
    status: int | None = Field(None, ge=0, le=1, description="状态(0:启动 1:停用)", json_schema_extra={"q": "eq"})
