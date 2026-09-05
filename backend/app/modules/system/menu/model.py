from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import ModelMixin

if TYPE_CHECKING:
    from app.modules.system.role.model import RoleModel


class MenuModel(ModelMixin):
    """菜单表 - 用于存储系统菜单资源定义

    菜单类型说明:
    - 1: 目录(一级菜单)
    - 2: 菜单(二级菜单)
    - 3: 按钮/权限(页面内按钮权限)
    - 4: 外部链接
    """

    __tablename__: str = "sys_menu"
    __table_args__: dict[str, str] = {"comment": "系统菜单表"}

    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="菜单名称")
    type: Mapped[int] = mapped_column(Integer, nullable=False, default=2, comment="菜单类型(1:目录 2:菜单 3:按钮 4:链接)")
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=999, index=True, comment="显示排序")
    permission: Mapped[str | None] = mapped_column(String(100), comment="权限标识(如:module_system:user:query)")
    icon: Mapped[str | None] = mapped_column(String(50), comment="菜单图标")
    route_name: Mapped[str | None] = mapped_column(String(100), comment="路由名称")
    route_path: Mapped[str | None] = mapped_column(String(200), index=True, comment="路由路径")
    component_path: Mapped[str | None] = mapped_column(String(200), comment="组件路径")
    redirect: Mapped[str | None] = mapped_column(String(200), comment="重定向地址")
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否隐藏(True:隐藏 False:显示)")
    keep_alive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="是否缓存(True:是 False:否)")
    always_show: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否始终显示(True:是 False:否)")
    title: Mapped[str | None] = mapped_column(String(50), comment="菜单标题")
    params: Mapped[list[dict[str, str]] | None] = mapped_column(JSON, comment="路由参数(JSON对象)")
    affix: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否固定标签页(True:是 False:否)")
    link: Mapped[str | None] = mapped_column(String(500), comment="外链地址(仅type=4)")
    is_iframe: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否嵌入iframe(True:是 False:否)")
    is_hide_tab: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否隐藏标签页(True:是 False:否)")
    active_path: Mapped[str | None] = mapped_column(String(200), comment="激活菜单路径(用于高亮父级)")
    show_badge: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否显示红点角标(True:是 False:否)")
    show_text_badge: Mapped[str | None] = mapped_column(String(20), comment="文字角标内容")
    scope: Mapped[str] = mapped_column(String(20), nullable=False, default="web", server_default="web", comment="菜单可见范围(web:管理端 desktop app:移动端)")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:启动 1:停用)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sys_menu.id", ondelete="SET NULL"), default=None, index=True, comment="父菜单ID")
    parent: Mapped["MenuModel | None"] = relationship(back_populates="children", remote_side="MenuModel.id", foreign_keys="MenuModel.parent_id", uselist=False)
    children: Mapped[list["MenuModel"] | None] = relationship(back_populates="parent", foreign_keys="MenuModel.parent_id", order_by="MenuModel.order")
    roles: Mapped[list["RoleModel"]] = relationship(secondary="sys_role_menus", back_populates="menus")
