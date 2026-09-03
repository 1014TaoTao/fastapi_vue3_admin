from fastapi import FastAPI
from redis import exceptions
from redis.asyncio import Redis
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config.setting import settings
from app.core.base_model import MappedBase
from app.core.logger import logger


def create_engine_and_session(db_url: str = settings.DB_URI) -> tuple[Engine, sessionmaker]:
    """创建同步数据库引擎和会话工厂。

    参数:
    - db_url (str): 数据库连接URL,默认从配置中获取。

    返回:
    - tuple[Engine, sessionmaker]: 同步数据库引擎和会话工厂。
    """
    try:
        # 同步数据库引擎
        engine: Engine = create_engine(
            url=db_url,
            echo=settings.DATABASE_ECHO,
            pool_pre_ping=settings.POOL_PRE_PING,
            pool_recycle=settings.POOL_RECYCLE,
        )
    except Exception as e:
        logger.error(f"❌ 数据库连接失败 {e}")
        raise
    else:
        # 同步数据库会话工厂
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return engine, SessionLocal


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
                future=settings.FUTURE,
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
                future=settings.FUTURE,
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


engine, db_session = create_engine_and_session()
async_engine, async_db_session = create_async_engine_and_session()

async def check_db() -> None:
    """检查数据库连接是否正常。"""

    try:
        with engine.connect():
            pass
        logger.info("✅ 数据库连接正常")
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        raise e


async def create_tables() -> None:
    """创建数据库表（根据 ORM metadata）。

    返回:
    - None
    """
    try:
        async with async_engine.begin() as coon:
            await coon.run_sync(MappedBase.metadata.create_all)
    except Exception as e:
        logger.error(f"❌ 数据库表结构初始化失败: {e}")
        raise e


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
        raise e


async def redis_connect(app: FastAPI, status: bool) -> Redis | None:
    """创建或关闭Redis连接。

    连接失败时直接抛出异常（fail-fast）：Redis 承载会话/参数缓存/调度 jobstore，
    静默降级会导致应用带病运行、请求期随机 500，宁可启动即失败。

    参数:
    - app (FastAPI): FastAPI应用实例。
    - status (bool): 连接状态,True为创建连接,False为关闭连接。

    返回:
    - Redis | None: Redis连接实例（status=False 时返回 None）。
    """
    if status:
        try:
            rd = await Redis.from_url(
                url=settings.REDIS_URI,
                encoding="utf-8",
                decode_responses=True,
                health_check_interval=settings.REDIS_HEALTH_CHECK_INTERVAL,
                max_connections=settings.POOL_SIZE,
                socket_timeout=settings.POOL_TIMEOUT,
            )
            app.state.redis = rd
            if await rd.ping():  # pyright: ignore[reportGeneralTypeIssues]
                return rd
            msg = "Redis ping 返回 False，连接不可用"
            raise exceptions.ConnectionError(msg)
        except exceptions.RedisError as e:
            logger.error(f"❌ Redis 连接失败: {e}")
            raise
    else:
        await app.state.redis.close()
        logger.info("✅️ Redis连接已关闭")
