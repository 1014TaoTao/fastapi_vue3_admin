# -*- coding: utf-8 -*-
"""
基础模型模块
提供跨数据库兼容的基础模型类和类型装饰器
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

import json
from sqlalchemy import Boolean, String, Integer, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, declared_attr, mapped_column
from sqlalchemy.types import TypeDecorator


class MappedBase(AsyncAttrs, DeclarativeBase):
    """
    声明式基类

    兼容 SQLite、MySQL 和 PostgreSQL
    """

    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """生成表名"""
        return cls.__name__.lower()

    @declared_attr.directive
    def __table_args__(cls) -> dict:
        """表配置"""
        return {'comment': cls.__doc__ or ''}


class ModelMixin(MappedBase):
    """
    基础模型混合类
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    status: Mapped[bool] = mapped_column(Boolean(), default=True, nullable=False, comment="是否启用(True:启用 False:禁用)")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注说明")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment='创建时间')
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')


class CreatorMixin(ModelMixin):
    """
    创建人混合类
    """
    __abstract__ = True

    creator_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True, comment="创建人ID")

    @declared_attr
    def creator(cls) -> Mapped[Optional["UserModel"]]:
        """创建人关联关系（延迟加载，避免循环依赖）"""
        return relationship(
            "UserModel",
            primaryjoin=f"{cls.__name__}.creator_id == UserModel.id",
            lazy="selectin",
            foreign_keys=[cls.creator_id],
            viewonly=True
        )