from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import MappedBase, ModelMixin, UserMixin

if TYPE_CHECKING:
    from app.modules.system.dept.model import DeptModel
    from app.modules.system.menu.model import MenuModel
    from app.modules.system.user.model import UserModel


class RoleMenusModel(MappedBase):
    """角色菜单关联表

    定义角色与菜单的多对多关系，用于权限控制
    """

    __tablename__: str = "sys_role_menus"
    __table_args__: dict[str, str] = {"comment": "角色菜单关联表"}

    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_role.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        comment="角色ID",
    )
    menu_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_menu.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        comment="菜单ID",
    )


class RoleDeptsModel(MappedBase):
    """角色部门关联表

    定义角色与部门的多对多关系，用于数据权限控制
    仅当角色的data_scope=5(自定义数据权限)时使用此表
    """

    __tablename__: str = "sys_role_depts"
    __table_args__: dict[str, str] = {"comment": "角色部门关联表"}

    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_role.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        comment="角色ID",
    )
    dept_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_dept.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        comment="部门ID",
    )


class RoleModel(ModelMixin, UserMixin):
    """角色模型"""

    __tablename__: str = "sys_role"
    __table_args__: dict[str, str] = {"comment": "角色表"}

    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="角色名称")
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="角色编码")
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=999, comment="显示排序")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:启动 1:停用)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")
    data_scope: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="数据权限范围(1:仅本人 2:本部门及以下 3:全部)")

    menus: Mapped[list["MenuModel"]] = relationship(secondary="sys_role_menus", back_populates="roles", order_by="MenuModel.order")
    depts: Mapped[list["DeptModel"]] = relationship(secondary="sys_role_depts", back_populates="roles")
    users: Mapped[list["UserModel"]] = relationship(secondary="sys_user_roles", back_populates="roles")
