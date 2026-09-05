from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.base_model import ModelMixin, UserMixin

if TYPE_CHECKING:
    from app.modules.system.user.model import UserModel


class TicketModel(ModelMixin, UserMixin):
    """工单模型 — 用户提交的建议和反馈
    status: 0=待处理 1=处理中 2=已完成 3=已关闭
    """

    __tablename__: str = "sys_ticket"
    __table_args__: dict[str, str] = {"comment": "工单表"}

    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="标题")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:待处理 1:处理中 2:已完成 3:已关闭)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")
    ticket_content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="工单内容（富文本）")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True, comment="工单内容（纯文本摘要）")
    ticket_type: Mapped[str] = mapped_column(String(20), nullable=False, default="suggestion", comment="工单类型(suggestion:建议 bug:缺陷 optimize:优化 other:其他)")
    images: Mapped[str | None] = mapped_column(Text, nullable=True, comment="图片URL列表(JSON数组)")
    reply: Mapped[str | None] = mapped_column(Text, nullable=True, comment="回复内容")
    assigned_id: Mapped[int | None] = mapped_column(ForeignKey("sys_user.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, index=True, comment="处理人ID")

    assigned_by: Mapped["UserModel | None"] = relationship("UserModel", foreign_keys=[assigned_id], uselist=False)

    @validates("title")
    def validate_title(self, key: str, title: str) -> str:
        if not title or not title.strip():
            raise ValueError("工单标题不能为空")
        return title.strip()

    @validates("summary", "ticket_content")
    def validate_content(self, key: str, content: str | None) -> str | None:
        if content and content.strip():
            return content.strip()
        return content


class TicketCommentModel(ModelMixin, UserMixin):
    """工单评论模型"""
    __tablename__: str = "sys_ticket_comment"
    __table_args__: dict[str, str] = {"comment": "工单评论表"}

    ticket_id: Mapped[int] = mapped_column(ForeignKey("sys_ticket.id", ondelete="CASCADE"), nullable=False, index=True, comment="工单ID")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="评论内容（富文本）")
