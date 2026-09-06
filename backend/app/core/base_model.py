from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, MetaData, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column, relationship

from app.utils.common_util import uuid4_str

# 官方 autogenerate 最佳实践：约束显式命名（匿名 FK 在 MySQL 落库为 ibfk_1 这类自动名，
# 跨方言渲染/对比/batch 重建均不可靠）。ix 与 SQLAlchemy 默认模板一致，显式声明便于阅读。
# uq 特意不配置：MySQL 下 unique=True 渲染为列名 unique index（如 `code`），一旦命名（uq_sys_dept_code）
# 会与存量库名字不匹配，autogenerate 生成 remove_index+add_uq 迁移，又被 dev 启动的 DROP 拦截机制
# 删除而永远无法自动应用，故保持默认匿名渲染。
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class MappedBase(AsyncAttrs, DeclarativeBase):
    """声明式基类

    `AsyncAttrs <https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.AsyncAttrs>`__

    `DeclarativeBase <https://docs.sqlalchemy.org/en/20/orm/declarative_config.html>`__

    `mapped_column() <https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.mapped_column>`__

    兼容 SQLite、MySQL 和 PostgreSQL
    """

    __abstract__: bool = True
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class ModelMixin(MappedBase):
    """模型混入类 - 提供通用字段和功能

    基础模型混合类 Mixin: 一种面向对象编程概念, 使结构变得更加清晰

    数据隔离设计原则：
    ==================
    数据权限 (created_id/updated_id):
        - 配合角色的data_scope字段实现精细化权限控制
        - 1:仅本人
        - 2:本部门
        - 3:本部门及以下
        - 4:全部数据
        - 5:自定义

    SQLAlchemy加载策略说明:
    - select(默认): 延迟加载,访问时单独查询
    - joined: 使用LEFT JOIN预加载
    - selectin: 使用IN查询批量预加载(推荐用于一对多)
    - subquery: 使用子查询预加载
    - raise/raise_on_sql: 禁止加载
    - noload: 不加载,返回None
    - immediate: 立即加载
    - write_only: 只写不读
    - dynamic: 返回查询对象,支持进一步过滤
    """

    __abstract__: bool = True

    @declared_attr.directive
    def __table_args__(cls) -> tuple:
        table_name = cls.__tablename__ if hasattr(cls, '__tablename__') else cls.__name__.lower()
        return (
            Index(f"ix_{table_name}_status_deleted", "status", "is_deleted"),
            Index(f"ix_{table_name}_created_deleted", "created_time", "is_deleted"),
        )

    # 基础字段
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="主键ID",
        index=True,
    )
    uuid: Mapped[str] = mapped_column(
        String(64),
        default=uuid4_str,
        nullable=False,
        unique=True,
        comment="UUID全局唯一标识",
        index=True,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已删除(0:未删除 1:已删除)",
        index=True,
    )
    created_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        comment="创建时间",
        index=True,
    )
    updated_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
        comment="更新时间",
    )
    deleted_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
        comment="删除时间",
    )


class UserMixin(MappedBase):
    """用户审计字段 Mixin

    CRUD（base_crud.py）会自动检测并预加载 created_by/updated_by（使用 joinedload，一对一关系最高效），
    无需在 service 层显式声明。deleted_by 仅在回收站等特定场景需要时通过 preload 参数显式获取。
    """

    __abstract__: bool = True

    created_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sys_user.id", ondelete="SET NULL", onupdate="CASCADE"),
        default=None,
        nullable=True,
        index=True,
        comment="创建人ID",
    )
    updated_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sys_user.id", ondelete="SET NULL", onupdate="CASCADE"),
        default=None,
        nullable=True,
        index=True,
        comment="更新人ID",
    )

    deleted_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sys_user.id", ondelete="SET NULL", onupdate="CASCADE"),
        default=None,
        nullable=True,
        index=True,
        comment="删除人ID",
    )

    @declared_attr
    def created_by(self):
        """创建人关联关系"""
        return relationship(
            "UserModel",
            foreign_keys=lambda: self.created_id,  # pyright: ignore[reportArgumentType]
            uselist=False,
        )

    @declared_attr
    def updated_by(self):
        """更新人关联关系"""
        return relationship(
            "UserModel",
            foreign_keys=lambda: self.updated_id,  # pyright: ignore[reportArgumentType]
            uselist=False,
        )

    @declared_attr
    def deleted_by(self):
        """删除人关联关系"""
        return relationship(
            "UserModel",
            foreign_keys=lambda: self.deleted_id,  # pyright: ignore[reportArgumentType]
            uselist=False,
        )
