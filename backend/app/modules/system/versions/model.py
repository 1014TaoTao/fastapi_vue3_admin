from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class VersionModel(ModelMixin, UserMixin):
    """版本管理（平台级）"""

    __tablename__: str = "sys_version"
    __table_args__: dict[str, str] = {"comment": "版本管理表"}

    version: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, comment="版本号")
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="版本标题")
    date: Mapped[str] = mapped_column(String(50), nullable=False, comment="发布日期")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, default=None, comment="版本富文本内容")
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="排序")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态: 0=草稿,1=已发布,2=已回滚")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None, comment="备注")
    require_re_login: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否需要重新登录")
