# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import Boolean, Column, String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
import uuid

from app.core.base_model import ModelBase


class MenuModel(ModelBase):
    """
    菜单表 - 用于存储系统菜单信息
    type 菜单类型说明:
    1: 目录
    2: 菜单 
    3: 按钮/权限
    """
    __tablename__ = "system_menu"
    __table_args__ = ({'comment': '菜单表'})

    # 基础字段
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False, unique=True, comment='主键ID')
    name = Column(String(50), nullable=False, comment="菜单名称", unique=True)
    type = Column(Integer, nullable=False, default=2, comment="菜单类型")
    order = Column(Integer, nullable=False, default=1, comment="显示排序")
    
    # 权限相关
    permission = Column(String(100), nullable=True, comment="权限标识(如：system:user:list)")
    available = Column(Boolean, default=True, nullable=False, comment="是否启用(True:启用 False:禁用)")
    
    # 前端路由相关
    icon = Column(String(50), nullable=True, comment="菜单图标")
    route_name = Column(String(100), nullable=True, comment="路由名称")
    route_path = Column(String(200), nullable=True, comment="路由路径")
    component_path = Column(String(200), nullable=True, comment="组件路径")
    redirect = Column(String(200), nullable=True, comment="重定向地址")
    hidden = Column(Boolean, default=False, nullable=False, comment="是否隐藏(True:隐藏 False:显示)")
    cache = Column(Boolean, default=True, nullable=False, comment="是否缓存(True:是 False:否)")
    
    # 层级关系
    parent_id = Column(
        String(36),
        ForeignKey("system_menu.id"),
        nullable=True,
        index=True,
        comment="父级菜单ID"
    )
    parent = relationship(
        "MenuModel", 
        cascade='all, delete-orphan',
        primaryjoin="MenuModel.parent_id == MenuModel.id",
        uselist=False
    )
    
    # 审计字段
    description = Column(Text, nullable=True, comment="备注说明")
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

