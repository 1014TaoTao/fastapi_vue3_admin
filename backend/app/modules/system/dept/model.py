from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import ModelMixin, UserMixin

if TYPE_CHECKING:
    from app.modules.system.role.model import RoleModel
    from app.modules.system.user.model import UserModel


class DeptModel(ModelMixin, UserMixin):
    """部门模型"""

    __tablename__: str = "sys_dept"
    __table_args__: dict[str, str] = {"comment": "部门表"}

    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="部门名称")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:启动 1:停用)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=999, index=True, comment="显示排序")
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="部门编码")
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sys_dept.id", ondelete="SET NULL", onupdate="CASCADE"),
        default=None,
        index=True,
        comment="父级部门ID",
    )
    parent: Mapped["DeptModel | None"] = relationship(
        back_populates="children",
        remote_side="DeptModel.id",
        foreign_keys=[parent_id],
        uselist=False,
    )
    children: Mapped[list["DeptModel"]] = relationship(back_populates="parent", foreign_keys=[parent_id])
    roles: Mapped[list["RoleModel"]] = relationship(secondary="sys_role_depts", back_populates="depts")
    users: Mapped[list["UserModel"]] = relationship(back_populates="dept", foreign_keys="UserModel.dept_id")
