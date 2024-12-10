# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, String, Integer, Text, DateTime
from sqlalchemy.orm import relationship

from app.core.base_model import ModelBase


class DeptModel(ModelBase):
    """
    部门表 - 用于存储组织架构中的部门信息
    """
    __tablename__ = "system_dept"
    __table_args__ = ({'comment': '部门表'})

    # 基础字段
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, comment='主键ID')
    name = Column(String(40), nullable=False, comment="部门名称", unique=True)
    order = Column(Integer, nullable=False, default=1, comment="显示排序")
    
    # 层级关系
    parent_id = Column(
        Integer, 
        ForeignKey("system_dept.id", ondelete="SET NULL", onupdate="CASCADE"), 
        nullable=True, 
        index=True, 
        comment="父级部门ID"
    )
    parent = relationship(
        "DeptModel", 
        remote_side=[id], 
        backref="children", 
        lazy="selectin", 
        uselist=False
    )
    
    # 状态字段
    available = Column(Boolean, default=True, nullable=False, comment="是否启用(True:启用 False:禁用)")
    
    # 关联关系
    users = relationship(
        "UserModel",
        back_populates="dept",
        foreign_keys="UserModel.dept_id",
        lazy="selectin"
    )
    
    roles = relationship(
        "RoleModel",
        secondary="system_role_depts",
        back_populates="depts",
        lazy="selectin"
    )
    
    # 审计字段
    description = Column(Text, nullable=True, comment="备注说明")
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    creator_id = Column(
        Integer, 
        ForeignKey("system_user.id", ondelete="SET NULL", onupdate="CASCADE"), 
        nullable=True, 
        index=True, 
        comment="创建人ID"
    )
    creator = relationship(
        "UserModel", 
        foreign_keys=[creator_id], 
        lazy="joined",
        post_update=True,
        uselist=False
    )
