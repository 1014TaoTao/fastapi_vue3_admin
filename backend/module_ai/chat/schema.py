from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.base_schema import BaseQueryParam, UserByQueryParam


class ChatQuerySchema(BaseModel):
    """WebSocket聊天查询模型"""

    message: str | None = Field("", description="消息内容（停止时可为空）")
    session_id: str | None = Field(None, description="会话ID")
    files: list[dict[str, Any]] | None = Field(None, description="文件信息")
    action: str | None = Field(None, description="动作类型：stop=停止生成 | None=对话")


class ChatSessionCreateSchema(BaseModel):
    """创建会话模型"""

    title: str = Field(..., min_length=1, max_length=200, description="会话标题")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1 or len(v) > 200:
            raise ValueError("会话标题长度必须在1-200个字符之间")
        return v


class ChatSessionUpdateSchema(BaseModel):
    """更新会话模型"""

    title: str = Field(..., min_length=1, max_length=200, description="会话标题")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1 or len(v) > 200:
            raise ValueError("会话标题长度必须在1-200个字符之间")
        return v


class ChatSessionMessageSchema(BaseModel):
    """会话消息模型"""

    id: str = Field(..., description="消息ID")
    role: str = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    created_at: int | None = Field(None, description="创建时间(Unix时间戳)")

    model_config = ConfigDict(from_attributes=True)


class ChatSessionQueryParam(BaseQueryParam, UserByQueryParam):
    """会话查询参数"""

    title: str | None = Field(None, description="会话标题")




class AiChatRequestSchema(BaseModel):
    """AI 对话请求模型（非流式）"""

    message: str = Field(..., min_length=1, description="用户消息内容")
    session_id: str | None = Field(None, description="会话ID，不传则创建新会话")

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1:
            raise ValueError("用户消息内容不能为空")
        return v


class AiChatResponseSchema(BaseModel):
    """AI 对话响应模型（非流式）"""

    response: str = Field(..., description="AI 回复内容")
    session_id: str = Field(..., description="会话ID")
    function_calls: list[dict[str, Any]] | None = Field(None, description="函数调用信息")
    action: dict[str, Any] | None = Field(None, description="建议执行的操作")


class AiModelConfigSchema(BaseModel):
    """AI 模型配置项"""

    name: str = Field(..., min_length=1, max_length=50, description="配置名称（用户可读）")
    base_url: str = Field(..., min_length=1, max_length=500, description="API Base URL，如 https://api.openai.com/v1")
    api_key: str = Field(..., min_length=1, max_length=500, description="API 密钥")
    model_id: str = Field(..., min_length=1, max_length=100, description="模型 ID")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度参数")

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        if not v.startswith(("http://", "https://")):
            raise ValueError("Base URL 必须以 http:// 或 https:// 开头")
        return v

    @field_validator("model_id")
    @classmethod
    def validate_model_id(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("模型 ID 不能为空")
        return v


class AiModelConfigItemSchema(AiModelConfigSchema):
    """带 ID 的模型配置项（存储与返回）"""

    id: str = Field(..., min_length=1, max_length=64, description="配置项唯一 ID")
    created_time: str | None = Field(None, description="创建时间（ISO 字符串）")


class AiModelConfigUpdateSchema(AiModelConfigSchema):
    """更新 AI 模型配置（与创建结构相同，不含 id）"""


class AiModelConfigListResponse(BaseModel):
    """模型配置列表响应"""

    items: list[AiModelConfigItemSchema] = Field(default_factory=list, description="配置项列表")
    active_id: str | None = Field(None, description="当前激活的配置项 ID；为空表示使用系统默认")
