# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import Column, ForeignKey, String, Integer, Text, DateTime, Float
from sqlalchemy.orm import relationship
import uuid

from app.core.base_model import ModelBase


class OperationLogModel(ModelBase):
    """ 操作日志模型，用于记录系统的操作日志 """
    __tablename__ = "system_operation_log"
    __table_args__ = ({'comment': '操作日志表'})

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False, unique=True, comment='主键ID')
    request_path = Column(String(255), nullable=True, comment="请求路径", index=True)
    request_method = Column(String(10), nullable=True, comment="请求方式", index=True)
    request_payload = Column(Text, nullable=True, comment="请求体")
    request_ip = Column(String(50), nullable=True, comment="请求IP地址")
    login_location=Column(String(255), nullable=True, comment="登录位置")
    request_os = Column(String(64), nullable=True, comment="操作系统")
    request_browser = Column(String(64), nullable=True, comment="浏览器")
    response_code = Column(Integer, nullable=True, comment="响应状态码")
    response_json = Column(Text, nullable=True, comment="响应体")
    process_time = Column(Float, nullable=True, comment="处理时间")
    
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
