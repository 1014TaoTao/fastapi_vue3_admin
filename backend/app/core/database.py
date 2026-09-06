from sqlalchemy import Engine, create_engine, event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config.setting import settings
from app.core.base_model import MappedBase
from app.core.logger import logger


def create_sync_engine(db_url: str = settings.DB_URI) -> Engine:
    """创建同步数据库引擎。

    同步引擎仅供同步组件使用：APScheduler SQLAlchemyJobStore、代码生成器 Inspector
    （后者经 asyncio.to_thread 在线程池中调用，见 gencode/crud.py 的 _sync_* 方法）。
    请求侧一律走异步会话，勿在事件循环内直接使用本引擎。

    参数:
    - db_url (str): 数据库连接URL,默认从配置中获取。

    返回:
    - Engine: 同步数据库引擎。
    """
    try:
        engine: Engine = create_engine(
            url=db_url,
            echo=settings.DATABASE_ECHO,
            pool_pre_ping=settings.POOL_PRE_PING,
            pool_recycle=settings.POOL_RECYCLE,
        )
    except Exception as e:
        logger.error(f"❌ 数据库连接失败 {e}")
        raise
    return engine


def create_async_engine_and_session(db_url: str = settings.ASYNC_DB_URI) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """获取异步数据库会话连接。

    参数:
    - db_url (str): 异步数据库 URL，默认取配置项 ASYNC_DB_URI。

    返回:
    - tuple[AsyncEngine, async_sessionmaker[AsyncSession]]: 异步数据库引擎和会话工厂。
    """
    try:
        # 异步数据库引擎
        if settings.DATABASE_TYPE == "sqlite":
            async_engine = create_async_engine(
                url=db_url,
                echo=settings.DATABASE_ECHO,
                echo_pool=settings.ECHO_POOL,
                pool_pre_ping=settings.POOL_PRE_PING,
                pool_recycle=settings.POOL_RECYCLE,
                connect_args={"timeout": 30},  # 等待锁释放，避免并发写立即报 database is locked
            )

            @event.listens_for(async_engine.sync_engine, "connect")
            def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
                """SQLite 启用 WAL + busy_timeout，提升读写并发（后台任务与请求并存时尤为必要）。"""
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA busy_timeout=30000")
                cursor.close()
        else:
            async_engine = create_async_engine(
                url=db_url,
                echo=settings.DATABASE_ECHO,
                echo_pool=settings.ECHO_POOL,
                pool_pre_ping=settings.POOL_PRE_PING,
                pool_recycle=settings.POOL_RECYCLE,
                pool_size=settings.POOL_SIZE,
                max_overflow=settings.MAX_OVERFLOW,
                pool_timeout=settings.POOL_TIMEOUT,
                pool_use_lifo=settings.POOL_USE_LIFO,
            )
    except Exception as e:
        logger.error(f"❌ 数据库连接失败 {e}")
        raise
    else:
        # 异步数据库会话工厂
        AsyncSessionLocal = async_sessionmaker[AsyncSession](
            bind=async_engine,
            autocommit=settings.AUTOCOMMIT,
            autoflush=settings.AUTOFLUSH if settings.AUTOFETCH is None else settings.AUTOFETCH,
            expire_on_commit=settings.EXPIRE_ON_COMMIT,
            class_=AsyncSession,
        )
        return async_engine, AsyncSessionLocal


engine = create_sync_engine()
async_engine, async_db_session = create_async_engine_and_session()

async def create_tables() -> None:
    """创建数据库表（根据 ORM metadata）。

    返回:
    - None
    """
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(MappedBase.metadata.create_all)
    except Exception as e:
        logger.error(f"❌ 数据库表结构初始化失败: {e}")
        raise


async def drop_tables() -> None:
    """删除数据库表（根据 ORM metadata）。

    返回:
    - None
    """
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(MappedBase.metadata.drop_all)
    except Exception as e:
        logger.error(f"❌ 数据库表结构删除失败: {e}")
        raise
