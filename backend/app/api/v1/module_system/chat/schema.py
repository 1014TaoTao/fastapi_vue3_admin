from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.base_schema import BaseSchema


class ChatMessageCreateSchema(BaseModel):
    """聊天消息创建模型"""

    conversation_type: int = Field(default=1, description="会话类型(1:私聊 2:群聊)")
    receiver_id: int = Field(..., gt=0, description="接收人ID(私聊:对方用户,群聊:群ID)")
    content: str = Field(..., min_length=1, max_length=2000, description="消息内容")

    @field_validator("conversation_type")
    @classmethod
    def _validate_conversation_type(cls, value: int):
        if value not in {1, 2}:
            raise ValueError("会话类型仅支持 1(私聊) 或 2(群聊)")
        return value

    @model_validator(mode="after")
    def _validate_after(self):
        if not self.content.strip():
            raise ValueError("消息内容不能为空")
        return self


class ChatMessageOutSchema(BaseSchema):
    """聊天消息响应模型"""

    model_config = ConfigDict(from_attributes=True)

    conversation_type: int = Field(description="会话类型(1:私聊 2:群聊)")
    sender_id: int = Field(description="发送人ID")
    receiver_id: int = Field(description="接收人ID(私聊:对方用户,群聊:群ID)")
    content: str = Field(description="消息内容")
    status: int = Field(description="消息状态(0:未读 1:已读,私聊使用)")
    sender_name: str | None = Field(default=None, description="发送人昵称")
    sender_avatar: str | None = Field(default=None, description="发送人头像URL")


class ChatMessagePageSchema(BaseModel):
    """历史消息分页结果"""

    items: list[ChatMessageOutSchema] = Field(default_factory=list, description="消息列表")
    has_more: bool = Field(default=False, description="是否还有更早的消息")


class ChatReadSchema(BaseModel):
    """标记已读模型"""

    conversation_type: int = Field(default=1, description="会话类型(1:私聊 2:群聊)")
    receiver_id: int = Field(..., gt=0, description="接收人ID(私聊:对方用户,群聊:群ID)")

    @field_validator("conversation_type")
    @classmethod
    def _validate_conversation_type(cls, value: int):
        if value not in {1, 2}:
            raise ValueError("会话类型仅支持 1(私聊) 或 2(群聊)")
        return value


class ChatUserItemSchema(BaseSchema):
    """会话成员/用户项模型"""

    model_config = ConfigDict(from_attributes=True)

    username: str = Field(description="用户名")
    name: str = Field(description="昵称")
    avatar: str | None = Field(default=None, description="头像URL")


class ChatConversationSchema(BaseModel):
    """会话列表项模型"""

    id: int | None = Field(description="会话ID(私聊:对端用户ID,群聊:群ID)")
    conversation_type: int = Field(description="会话类型(1:私聊 2:群聊)")
    name: str = Field(description="会话名称")
    avatar: str | None = Field(default=None, description="头像URL")
    online: bool = Field(default=False, description="是否在线(私聊)")
    member_count: int = Field(default=0, description="成员数(群聊)")
    last_message: str | None = Field(default=None, description="最后一条消息")
    last_time: str | None = Field(default=None, description="最后消息时间")
    unread: int = Field(default=0, description="未读数")


class ChatGroupCreateSchema(BaseModel):
    """聊天群组创建模型"""

    name: str = Field(..., min_length=1, max_length=64, description="群名称")
    avatar: str | None = Field(default=None, max_length=255, description="群头像URL")
    announcement: str | None = Field(default=None, max_length=1000, description="群公告")
    member_ids: list[int] = Field(default_factory=list, description="初始成员用户ID")

    @model_validator(mode="after")
    def _validate_after(self):
        if not self.name.strip():
            raise ValueError("群名称不能为空")
        if len(self.member_ids) > 500:
            raise ValueError("单次添加成员不能超过500人")
        return self


class ChatGroupUpdateSchema(BaseModel):
    """聊天群组更新模型"""

    name: str | None = Field(default=None, min_length=1, max_length=64, description="群名称")
    avatar: str | None = Field(default=None, max_length=255, description="群头像URL")
    announcement: str | None = Field(default=None, max_length=1000, description="群公告")

    @model_validator(mode="after")
    def _validate_after(self):
        if self.name is not None and not self.name.strip():
            raise ValueError("群名称不能为空")
        return self


class ChatGroupMemberSchema(BaseModel):
    """群成员操作模型"""

    member_ids: list[int] = Field(..., min_length=1, max_length=500, description="成员用户ID列表")


class ChatGroupDetailSchema(BaseSchema):
    """聊天群组详情模型"""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(description="群名称")
    avatar: str | None = Field(default=None, description="群头像URL")
    announcement: str | None = Field(default=None, description="群公告")
    owner_id: int = Field(description="群主ID")
    member_count: int = Field(default=0, description="成员数")
    members: list[ChatUserItemSchema] = Field(default_factory=list, description="成员列表")


class ChatGroupOutSchema(BaseSchema):
    """聊天群组响应模型"""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(description="群名称")
    avatar: str | None = Field(default=None, description="群头像URL")
    announcement: str | None = Field(default=None, description="群公告")
    owner_id: int = Field(description="群主ID")
    member_count: int = Field(default=0, description="成员数")
