import asyncio
from collections.abc import Iterable

from alembic import context
from alembic.operations import MigrationScript
from alembic.runtime.migration import MigrationContext
from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.config.path_conf import ALEMBIC_VERSION_DIR
from app.config.setting import settings
from app.core.base_model import MappedBase
from app.core.logger import logger
from app.utils.import_util import ImportUtil

ALEMBIC_VERSION_DIR.mkdir(parents=True, exist_ok=True)

ImportUtil.find_models(MappedBase)

alembic_config = context.config

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
    if url is None:
        raise ValueError("数据库URL未正确配置，请检查环境配置文件")

    connectable = create_async_engine(url, poolclass=pool.NullPool)

    async def run_async_migrations() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()

    def do_run_migrations(connection: Connection) -> None:
        if connection.dialect.name == "mysql":
            connection.execute(text("SET FOREIGN_KEY_CHECKS=0"))

        def process_revision_directives(
            context: MigrationContext,
            revision: str | Iterable[str | None] | Iterable[str],
            directives: list[MigrationScript],
        ) -> None:
            script = directives[0]

            # 检查所有操作集是否为空
            # 注意：清空 directives 与 `alembic check` 命令（1.9+）互斥——check 会取
            # generated_revisions[-1] 而崩溃。官方已知限制；本项目用 dev 启动时的
            # revision + 文件 diff 做等价检查，不依赖 alembic check。
            all_empty = all(ops.is_empty() for ops in script.upgrade_ops_list)

            if all_empty:
                # 如果没有实际变更，不生成迁移文件
                directives[:] = []
                logger.info("❎️ 未检测到模型变更，不生成迁移文件")
            else:
                logger.info("✅️ 检测到模型变更，生成迁移文件")

        def include_name(name, type_, parent_names) -> bool:
            # 只对 MappedBase 中存在的表做 autogenerate 对比（官方推荐范式：
            # 用 schema_qualified_table_name 全名匹配），自动忽略数据库中的
            # 非模型表（apscheduler_jobs、alembic_version 及未来新增的任何非模型表），
            # 避免被误判为多余表而生成 DROP。注意 include_name 仅作用于反射侧对象。
            if type_ == "table":
                return parent_names["schema_qualified_table_name"] in target_metadata.tables
            return True

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # compare_type 自 Alembic 1.12 起默认开启，无需显式传入
            compare_server_default=True,  # 默认关闭的可选增强；MySQL 下简单场景可靠，若出现误报移除本行即可
            render_as_batch=True,  # SQLite 不支持部分 ALTER，须走 batch 重建；对 MySQL/PG 无影响
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
