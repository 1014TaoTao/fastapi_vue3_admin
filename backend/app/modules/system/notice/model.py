from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class NoticeModel(ModelMixin, UserMixin):
    """通知公告表"""

    __tablename__: str = "sys_notice"
    __table_args__: dict[str, str] = {"comment": "通知公告表"}

    notice_title: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="公告标题")
    notice_type: Mapped[str] = mapped_column(String(1), nullable=False, index=True, comment="公告类型(1通知 2公告)")
    notice_content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="公告内容")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:草稿 1:已发布 2:已归档)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")
