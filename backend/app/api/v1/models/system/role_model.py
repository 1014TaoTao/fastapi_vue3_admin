# -*- coding: utf-8 -*-

from sqlalchemy import Boolean, Column, ForeignKey, String, Integer, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.base_model import ModelBase


class RoleMenusModel(ModelBase):
    """
    角色菜单关联表 - 用于存储角色与菜单的多对多关系
    """

    __tablename__ = "system_role_menus"
    __table_args__ = ({'comment': '角色菜单关联表'})

    role_id = Column(
        String(36),
        ForeignKey("system_role.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        comment="角色ID",
        index=True
    )
    menu_id = Column(
        String(36),
        ForeignKey("system_menu.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        comment="菜单ID",
        index=True
    )


class RoleDeptsModel(ModelBase):
    """
    角色数据权限部门关联表 - 用于存储角色与部门的多对多关系(数据权限)
    """

    __tablename__ = "system_role_depts"
    __table_args__ = ({'comment': '角色部门关联表'})

    role_id = Column(
        String(36),
        ForeignKey("system_role.id"),
        primary_key=True,
        comment="角色ID",
        index=True
    )
    dept_id = Column(
        String(36),
        ForeignKey("system_dept.id"),
        primary_key=True,
        comment="部门ID",
        index=True
    )


class RoleModel(ModelBase):
    """
    角色表 - 用于存储系统角色信息
    data_scope 数据权限范围说明:
    1: 仅本人数据权限
    2: 本部门数据权限  
    3: 本部门及以下数据权限
    4: 全部数据权限
    5: 自定义数据权限
    """

    __tablename__ = "system_role"
    __table_args__ = ({'comment': '角色表'})

    # 基础字段
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False, unique=True, comment='主键ID')
    name = Column(String(40), nullable=False, comment="角色名称", unique=True)
    order = Column(Integer, nullable=False, default=1, comment="显示排序")

    # 权限相关
    data_scope = Column(Integer, nullable=False, default=1, comment="数据权限范围")
    available = Column(Boolean, default=True, nullable=False, comment="是否启用(True:启用 False:禁用)")

    # 关联关系
    menus = relationship(
        "MenuModel",
        secondary=RoleMenusModel.__tablename__,
        lazy="joined",
        cascade="all, delete",
        passive_deletes=True,
        post_update=True,
        uselist=True
    )
    depts = relationship(
        "DeptModel",
        secondary=RoleDeptsModel.__tablename__,
        lazy="joined",
        cascade="all, delete",
        passive_deletes=True,
        post_update=True,
        uselist=True
    )

    # 审计字段
    description = Column(Text, nullable=True, comment="备注说明")
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    creator_id = Column(
        String(36),
        ForeignKey("system_users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
        comment="创建人ID"
    )
    creator = relationship(
        "UserModel", 
        foreign_keys=creator_id, 
        lazy="joined",
        post_update=True,
        uselist=False
    )
