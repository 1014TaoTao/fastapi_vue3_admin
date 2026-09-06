from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import MappedBase, ModelMixin, UserMixin

if TYPE_CHECKING:
    from app.modules.system.dept.model import DeptModel
    from app.modules.system.position.model import PositionModel
    from app.modules.system.role.model import RoleModel


class UserRolesModel(MappedBase):
    """用户角色关联表

    定义用户与角色的多对多关系
    """

    __tablename__: str = "sys_user_roles"
    __table_args__: dict[str, str] = {"comment": "用户角色关联表"}

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_user.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        comment="用户ID",
    )
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_role.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        comment="角色ID",
    )


class UserPositionsModel(MappedBase):
    """用户岗位关联表

    定义用户与岗位的多对多关系
    """

    __tablename__: str = "sys_user_positions"
    __table_args__: dict[str, str] = {"comment": "用户岗位关联表"}

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_user.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        comment="用户ID",
    )
    position_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_position.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        comment="岗位ID",
    )


class UserModel(ModelMixin, UserMixin):
    """用户模型
    """

    __tablename__: str = "sys_user"
    __table_args__: dict[str, str] = {"comment": "用户表"}

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="用户名/登录账号")
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    name: Mapped[str] = mapped_column(String(32), nullable=False, comment="昵称")
    mobile: Mapped[str | None] = mapped_column(String(11), nullable=True, index=True, comment="手机号")
    email: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True, comment="邮箱")
    gender: Mapped[str | None] = mapped_column(String(1), default="2", nullable=True, comment="性别(0:男 1:女 2:未知)")
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="头像URL地址")
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否超管")
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="最后登录时间")
    gitee_login: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="Gitee登录")
    github_login: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="Github登录")
    wx_login: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="微信登录")
    qq_login: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="QQ登录")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:启动 1:停用)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")

    dept_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sys_dept.id", ondelete="SET NULL", onupdate="CASCADE", use_alter=True), nullable=True, index=True, comment="部门ID")
    dept: Mapped["DeptModel | None"] = relationship(back_populates="users", foreign_keys=[dept_id])
    roles: Mapped[list["RoleModel"]] = relationship(secondary="sys_user_roles", back_populates="users")
    positions: Mapped[list["PositionModel"]] = relationship(secondary="sys_user_positions", back_populates="users")
    created_by: Mapped["UserModel | None"] = relationship("UserModel", foreign_keys="UserModel.created_id", remote_side="UserModel.id", uselist=False, viewonly=True)
    updated_by: Mapped["UserModel | None"] = relationship("UserModel", foreign_keys="UserModel.updated_id", remote_side="UserModel.id", uselist=False, viewonly=True)
    deleted_by: Mapped["UserModel | None"] = relationship("UserModel", foreign_keys="UserModel.deleted_id", remote_side="UserModel.id", uselist=False, viewonly=True)
