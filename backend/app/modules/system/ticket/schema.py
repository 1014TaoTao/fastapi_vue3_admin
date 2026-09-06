from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.enums import TicketTypeEnum
from app.core.base_schema import (
    BaseQueryParam,
    BaseSchema,
    CommonSchema,
    UserByQueryParam,
    UserBySchema,
)


class TicketCreateSchema(BaseModel):
    """创建工单"""

    title: str = Field(..., min_length=1, max_length=200, description="工单标题")
    ticket_content: str = Field(default="", description="工单内容（富文本）")
    summary: str | None = Field(default=None, description="工单内容（纯文本摘要）")
    ticket_type: TicketTypeEnum = Field(default=TicketTypeEnum.SUGGESTION, description="工单类型(suggestion/bug/optimize/other)")
    images: str | None = Field(default=None, description="图片URL列表(JSON数组)")
    description: str | None = Field(default=None, max_length=255, description="工单描述")

    @field_validator("title")
    @classmethod
    def _validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("工单标题不能为空")
        return v


class TicketUpdateSchema(BaseModel):
    """更新工单"""

    title: str | None = Field(default=None, max_length=200, description="工单标题")
    ticket_content: str | None = Field(default=None, description="工单内容（富文本）")
    summary: str | None = Field(default=None, description="工单内容（纯文本摘要）")
    ticket_type: TicketTypeEnum | None = Field(default=None, description="工单类型")
    status: int | None = Field(default=None, ge=0, le=3, description="状态(0:待处理 1:处理中 2:已完成 3:已关闭)")
    reply: str | None = Field(default=None, description="回复内容")
    assigned_id: int | None = Field(default=None, gt=0, description="处理人ID")
    description: str | None = Field(default=None, max_length=255, description="工单描述")


class TicketOutSchema(BaseSchema, UserBySchema):
    """工单响应"""

    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., description="工单标题")
    ticket_content: str | None = Field(default=None, description="工单内容")
    summary: str | None = Field(default=None, description="摘要")
    ticket_type: TicketTypeEnum = Field(..., description="工单类型")
    status: int = Field(..., description="状态(0:待处理 1:处理中 2:已完成 3:已关闭)")
    images: str | None = Field(default=None, description="图片")
    reply: str | None = Field(default=None, description="回复内容")
    assigned_id: int | None = Field(default=None, description="指派人ID")
    assigned_by: CommonSchema | None = Field(default=None, description="指派人")


class TicketBatchSchema(BaseModel):
    """批量更新工单"""

    ids: list[int] = Field(..., min_length=1, description="工单ID列表")
    status: int = Field(..., ge=0, le=3, description="状态(0:待处理 1:处理中 2:已完成 3:已关闭)")


class TicketQueryParam(BaseQueryParam, UserByQueryParam):
    """工单查询参数"""

    title: str | None = Field(None, description="工单标题", json_schema_extra={"q": "like"})
    ticket_type: str | None = Field(None, description="工单类型", json_schema_extra={"q": "eq"})
    assigned_id: int | None = Field(None, description="处理人ID", json_schema_extra={"q": "eq"})
    status: int | None = Field(None, ge=0, le=3, description="状态(0:待处理 1:处理中 2:已完成 3:已关闭)", json_schema_extra={"q": "eq"})


class TicketCommentCreateSchema(BaseModel):
    """创建评论"""
    content: str = Field(..., min_length=1, description="评论内容")


class TicketCommentOutSchema(BaseSchema, UserBySchema):
    """评论响应"""
    model_config = ConfigDict(from_attributes=True)
    ticket_id: int
    content: str
    created_by_name: str | None = None
