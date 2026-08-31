from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column, relationship

from app.utils.common_util import uuid4_str


def _merge_base_indexes(args: Any, table_name: str, *, has_status: bool) -> Any:
    """把 ``ModelMixin`` 的通用软删除索引合并进子类声明的 ``__table_args__``。

    ``status`` 列由各模型自行声明（**不在 ``ModelMixin`` 中**），因此只对确实有该列的表
    补 ``ix_{表}_status_deleted``；``created_time`` / ``is_deleted`` 由 ``ModelMixin`` 提供，恒可补。

    Args:
        args: 子类声明的 ``__table_args__``（dict 或 tuple）。
        table_name: 表名，用于生成索引名。
        has_status: 该模型是否声明了 ``status`` 列。

    Returns:
        合并后的 ``__table_args__``（dict/tuple 形态与入参一致）。
    """
    indexes: tuple[Index, ...] = (Index(f"ix_{table_name}_created_deleted", "created_time", "is_deleted"),)
    if has_status:
        indexes = (Index(f"ix_{table_name}_status_deleted", "status", "is_deleted"), *indexes)

    if isinstance(args, dict):
        # 字典形式（如 {"comment": "..."}）：索引在前、字典结尾（SQLAlchemy 约定）
        return (*indexes, args)
    if isinstance(args, tuple):
        # 元组形式：按索引名去重，避免与子类自定义索引重名导致重复创建
        existing = {idx.name for idx in args if isinstance(idx, Index)}
        missing = tuple(idx for idx in indexes if idx.name not in existing)
        return (*missing, *args)
    return args


class _DeclarativeMeta(type(DeclarativeBase)):
    """在 declarative 扫描**之前**合并通用索引。

    为何必须用元类而不是 ``__init_subclass__``：SQLAlchemy 的 declarative 读取的是
    传给元类的 ``namespace`` 字典来构建 Table；而 ``__init_subclass__`` 在
    ``type.__new__`` 末尾才触发，此时表结构已按原值构建完毕——实测在
    ``__init_subclass__`` 里改写 ``cls.__table_args__`` 无效（``__dict__`` 已是新值，
    但 ``__table__.indexes`` 里没有索引）。

    同理，``declared_attr.directive`` 也无法自行合并：子类一旦声明了自己的
    ``__table_args__``，mixin 的 directive 根本不会被调用。
    """

    def __new__(mcls, name: str, bases: tuple[type, ...], namespace: dict[str, Any], **kwargs: Any) -> type:
        args = namespace.get("__table_args__")
        if args is None:
            return super().__new__(mcls, name, bases, namespace, **kwargs)
        # 未显式声明 __tablename__ 时，与 MappedBase 的默认规则保持一致（类名小写）
        table_name = namespace.get("__tablename__") or name.lower()
        # 只处理继承 ModelMixin 的模型：纯关联表（仅继承 MappedBase）没有
        # created_time / is_deleted 列，补索引会因列不存在而建表失败。
        has_soft_delete = "created_time" in namespace or any("created_time" in getattr(b, "__dict__", {}) for b in bases)
        # status 列由各模型自行声明（Mixin 中没有），据此决定是否补 status 索引，
        # 避免给无该列的表（如 ChatGroupModel）建出引用不存在列的索引。
        has_status = "status" in namespace or any("status" in getattr(b, "__dict__", {}) for b in bases)
        skip = namespace.get("__table_args_skip_base_index__")
        if table_name and has_soft_delete and not skip:
            namespace["__table_args__"] = _merge_base_indexes(args, table_name, has_status=has_status)
        return super().__new__(mcls, name, bases, namespace, **kwargs)


class MappedBase(AsyncAttrs, DeclarativeBase, metaclass=_DeclarativeMeta):
    """声明式基类

    `AsyncAttrs <https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.AsyncAttrs>`__

    `DeclarativeBase <https://docs.sqlalchemy.org/en/20/orm/declarative_config.html>`__

    `mapped_column() <https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.mapped_column>`__

    兼容 SQLite、MySQL 和 PostgreSQL
    """

    __abstract__: bool = True

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
