# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
import uuid

from app.core.base_model import ModelBase


class DictTypeModel(ModelBase):
    """
    字典类型表
    """

    __tablename__ = "system_dict_type"
    __table_args__ = ({'comment': '数据字典类型表'})

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False, unique=True, comment='字典主键')
    dict_name = Column(String(100), nullable=True, unique=True, default='', comment='字典名称')
    dict_type = Column(String(100), nullable=True, unique=True, default='', comment='字典类型')
    available = Column(Boolean, nullable=True, default='0', comment='状态（0正常 1停用）')
    
    # 审计字段
    description = Column(Text, nullable=True, comment="备注说明")
    created_at = Column(DateTime, nullable=True,default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, nullable=True,default=datetime.now, onupdate=datetime.now, comment='更新时间')
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


class DictDataModel(ModelBase):
    """
    字典数据表
    """

    __tablename__ = 'system_dict_data'
    __table_args__ = ({'comment': '数据字典数据表'})

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False, unique=True, comment='字典编码')
    dict_sort = Column(Integer, nullable=True, default=0, comment='字典排序')
    dict_label = Column(String(100), nullable=True, default='', comment='字典标签')
    dict_value = Column(String(100), nullable=True, default='', comment='字典键值')
    dict_type = Column(String(100), nullable=True, default='', comment='字典类型')
    css_class = Column(String(100), nullable=True, default=None, comment='样式属性（其他样式扩展）')
    list_class = Column(String(100), nullable=True, default=None, comment='表格回显样式')
    is_default = Column(Boolean, nullable=True, default='N', comment='是否默认（Y是 N否）')
    available = Column(Boolean, nullable=True, default='0', comment='状态（0正常 1停用）')
    
    # 审计字段
    description = Column(Text, nullable=True, comment="备注说明")
    created_at = Column(DateTime, nullable=True,default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, nullable=True,default=datetime.now, onupdate=datetime.now, comment='更新时间')
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
