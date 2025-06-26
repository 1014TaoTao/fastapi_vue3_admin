# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, String, Text, DateTime
from sqlalchemy.orm import relationship
import uuid

from app.core.base_model import ModelBase


class NoticeModel(ModelBase):
    """
    通知公告表 - 用于公告发布
    """
    __tablename__ = "system_notice"
    __table_args__ = ({'comment': '通知公告表'})

    # 基础字段
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False, unique=True, comment='主键ID')
    notice_title = Column(String(50), nullable=False, comment='公告标题')
    notice_type = Column(String(50), nullable=False, comment='公告类型（1通知 2公告）')
    notice_content = Column(Text, comment='公告内容')

    # 状态字段
    available = Column(Boolean, default=True, nullable=False, comment="是否启用(True:启用 False:禁用)")

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
