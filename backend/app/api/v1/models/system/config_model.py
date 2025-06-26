# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
import uuid

from app.core.base_model import ModelBase


class ConfigModel(ModelBase):
    """
    配置表 - 用于存储组织架构中的配置信息
    """
    __tablename__ = "system_config"
    __table_args__ = ({'comment': '配置表'})

    # 基础字段
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False, unique=True, comment='主键ID')
    config_name = Column(String(500), nullable=True, unique=True, default='', comment='参数名称')
    config_key = Column(String(500), nullable=True, unique=True, default='', comment='参数键名')
    config_value = Column(String(500), nullable=True, default='', comment='参数键值')
    config_type = Column(Boolean, default=False, nullable=False, comment="系统内置((True:是 False:否))")

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
