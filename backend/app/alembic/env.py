import asyncio
import warnings
from collections.abc import Iterable

from alembic import context
from alembic.operations import MigrationScript
from alembic.runtime.migration import MigrationContext
from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SAWarning
from sqlalchemy.ext.asyncio import create_async_engine

from app.config.path_conf import ALEMBIC_VERSION_DIR
from app.config.setting import settings
from app.core.base_model import MappedBase
from app.utils.import_util import ImportUtil

ALEMBIC_VERSION_DIR.mkdir(parents=True, exist_ok=True)

print("🔍 开始查找模型...")
found_models = ImportUtil.find_models(MappedBase)
print(f"📊 找到 {len(found_models)} 个有效模型")

alembic_config = context.config

warnings.filterwarnings(
    "ignore",
    message=r"Cannot correctly sort tables.*",
    category=SAWarning,
)

target_metadata = MappedBase.metadata
alembic_config.set_main_option("sqlalchemy.url", settings.ASYNC_DB_URI)


def run_migrations_offline() -> None:
    """离线模式运行迁移
    """
    url = alembic_config.get_main_option("sqlalchemy.url")
    # 确保URL不为None
    if url is None:
        raise ValueError("数据库URL未正确配置，请检查环境配置文件")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """异步模式运行迁移
    """
    url = alembic_config.get_main_option("sqlalchemy.url")
    # 确保URL不为None
    if url is None:
        raise ValueError("数据库URL未正确配置，请检查环境配置文件")

    connectable = create_async_engine(url, poolclass=pool.NullPool)

    async def run_async_migrations() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()

    def do_run_migrations(connection: Connection) -> None:
        # MySQL 建表时外键引用的表必须已存在；sys_dept/sys_user 循环外键（互相引用）无法顺序建表，
        # PG/SQLite 支持 forward reference 无此限制。执行迁移时对 MySQL 临时关闭外键检查，
        # 该变量为会话级，连接关闭后自动恢复，不影响运行时。
        if connection.dialect.name == "mysql":
            connection.execute(text("SET FOREIGN_KEY_CHECKS=0"))

        def process_revision_directives(
            context: MigrationContext,
            revision: str | Iterable[str | None] | Iterable[str],
            directives: list[MigrationScript],
        ) -> None:
            script = directives[0]

            # 检查所有操作集是否为空
            all_empty = all(ops.is_empty() for ops in script.upgrade_ops_list)

            if all_empty:
                # 如果没有实际变更，不生成迁移文件
                directives[:] = []
                print("❎️ 未检测到模型变更，不生成迁移文件")
            else:
                print("✅️ 检测到模型变更，生成迁移文件")

        def include_name(name, type_, parent_names) -> bool:
            # 只对 MappedBase 中存在的表做 autogenerate 对比，自动忽略数据库中的非模型表
            # （apscheduler_jobs、alembic_version 及未来新增的任何非模型表），
            # 避免被误判为多余表而生成 DROP。官方推荐范式（include_name 过滤表名），
            # 优于逐个硬编码排除。
            if type_ == "table":
                return name in target_metadata.tables
            return True

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            transaction_per_migration=True,
            include_name=include_name,
            process_revision_directives=process_revision_directives,
        )


        context.run_migrations()
        connection.commit()

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
