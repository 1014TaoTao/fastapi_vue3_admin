from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import ModelMixin, UserMixin

if TYPE_CHECKING:
    from app.modules.system.user.model import UserModel


class PositionModel(ModelMixin, UserMixin):
    """岗位模型"""

    __tablename__: str = "sys_position"
    __table_args__: dict[str, str] = {"comment": "岗位表"}

    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="岗位名称")
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="岗位编码")
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="显示排序")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:启动 1:停用)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")

    # 关联关系
    users: Mapped[list["UserModel"]] = relationship(secondary="sys_user_positions", back_populates="positions")
