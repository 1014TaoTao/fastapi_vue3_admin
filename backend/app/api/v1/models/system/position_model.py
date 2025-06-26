# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, String, Integer, Text, DateTime
from sqlalchemy.orm import relationship
import uuid

from app.core.base_model import ModelBase
from .user_model import UserPositionsModel


class PositionModel(ModelBase):
    """
    岗位表 - 用于存储组织架构中的岗位信息
    """
    __tablename__ = "system_position"
    __table_args__ = ({'comment': '岗位表'})

    # 基础字段
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False, unique=True, comment='主键ID')
    name = Column(String(40), nullable=False, comment="岗位名称", unique=True)
    order = Column(Integer, nullable=False, default=1, comment="显示排序")

    # 状态字段
    available = Column(Boolean, default=True, nullable=False, comment="是否启用(True:启用 False:禁用)")

    users = relationship(
        "UserModel", 
        secondary=UserPositionsModel.__tablename__, 
        back_populates='positions', 
        lazy="joined",
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
