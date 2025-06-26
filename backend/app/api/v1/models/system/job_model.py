# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
import uuid

from app.core.base_model import ModelBase


class JobModel(ModelBase):
    """
    定时任务调度表
    """

    __tablename__ = 'system_job'
    __table_args__ = ({'comment': '定时任务调度表'})

    id=Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False, unique=True, comment='任务ID')
    name=Column(String(64), nullable=True, default='', comment='任务名称')
    jobstore=Column(String(64), nullable=True, default='default', comment='存储器')
    executor=Column(String(64), nullable=True, default='default', comment='执行器:将运行此作业的执行程序的名称')
    trigger=Column(String(64), nullable=False, comment='触发器:控制此作业计划的 trigger 对象')
    trigger_args=Column(Text, nullable=True, comment='触发器参数')
    func = Column(Text, nullable=False, comment='任务函数')
    args=Column(Text, nullable=True, comment='位置参数')
    kwargs=Column(Text, nullable=True, comment='关键字参数')
    coalesce=Column(Boolean, nullable=True, default=False, comment='是否合并运行:是否在多个运行时间到期时仅运行作业一次')
    max_instances=Column(Integer, nullable=True, default=1, comment='最大实例数:允许的最大并发执行实例数 工作')
    start_date=Column(Text, default=None,  nullable=True, comment='开始时间')
    end_date=Column(Text, default=None, nullable=True, comment='结束时间')
    status = Column(Boolean, default=False, nullable=True, comment='任务状态:正常,停止')
    message = Column(String(500), default=None, nullable=True, comment='日志信息')
    
    # 审计字段
    description = Column(Text, nullable=True, comment="备注说明")
    created_at = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now, comment='更新时间')
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

