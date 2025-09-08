# -*- coding: utf-8 -*-

from redis import asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)
from sqlalchemy.exc import (
    OperationalError,
    TimeoutError,
    DisconnectionError,
    InterfaceError,
    ProgrammingError,
    IntegrityError,
    DataError,
    InternalError,
    NotSupportedError,
    InvalidRequestError
)

from app.core.logger import logger
from app.config.setting import settings
from app.core.exceptions import CustomException

# 同步数据库引擎
engine = create_engine(
    url=settings.DB_URI,
    echo=settings.DATABASE_ECHO,
)
# 同步数据库会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 异步数据库引擎
async_engine: AsyncEngine = create_async_engine(
    url=settings.ASYNC_DB_URI,
    echo=settings.DATABASE_ECHO,
    echo_pool=settings.ECHO_POOL,
    pool_pre_ping=settings.POOL_PRE_PING,
    future=settings.FUTURE,
    pool_recycle=settings.POOL_RECYCLE,
    # pool_size=settings.POOL_SIZE,  # sqlite 不支持
    # max_overflow=settings.MAX_OVERFLOW,  # sqlite 不支持
    # pool_timeout=settings.POOL_TIMEOUT,  # sqlite 不支持
)

# 异步数据库会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autocommit=settings.AUTOCOMMIT,
    autoflush=settings.AUTOFETCH,
    expire_on_commit=settings.EXPIRE_ON_COMMIT,
    class_=AsyncSession
)

def session_connect() -> AsyncSession:
    """获取数据库会话"""
    try:
        if not settings.SQL_DB_ENABLE:
            raise CustomException(msg="请先开启数据库连接", data="请启用 app/config/setting.py: SQL_DB_ENABLE")
        return AsyncSessionLocal()
    except Exception as e:
        raise CustomException(msg=f"数据库连接失败: {e}")

async def test_db_connection(session: AsyncSession) -> bool:
    try:
        # 执行简单查询测试连接是否真实可用
        await session.execute(text("SELECT 1"))
        return True
    except OperationalError as e:
        raise CustomException(msg=f"数据库操作失败: {e}，请检查数据库服务是否正常运行")
    except TimeoutError as e:
        raise CustomException(msg=f"数据库连接超时: {e}，请检查网络连接或增加连接超时时间")
    except DisconnectionError as e:
        raise CustomException(msg=f"数据库连接中断: {e}，请检查数据库服务状态")
    except InterfaceError as e:
        raise CustomException(msg=f"数据库接口错误: {e}，请检查数据库驱动配置")
    except ProgrammingError as e:
        raise CustomException(msg=f"SQL语句错误: {e}，请检查SQL语法")
    except IntegrityError as e:
        raise CustomException(msg=f"数据完整性错误: {e}，请检查数据约束条件")
    except DataError as e:
        raise CustomException(msg=f"数据类型错误: {e}，请检查数据格式")
    except InternalError as e:
        raise CustomException(msg=f"数据库内部错误: {e}，请联系数据库管理员")
    except NotSupportedError as e:
        raise CustomException(msg=f"数据库不支持该操作: {e}，请检查数据库版本")
    except InvalidRequestError as e:
        raise CustomException(msg=f"无效的数据库请求: {e}，请检查请求参数")
    except Exception as e:
        raise CustomException(msg=f"数据库操作异常: {e}，请联系管理员")

async def redis_connect(app: FastAPI, status: bool) -> aioredis.Redis:
    """创建或关闭Redis连接"""
    if not settings.REDIS_ENABLE:
        raise CustomException(msg="请先开启Redis连接", data="请启用 app/core/config.py: REDIS_ENABLE")

    if status:
        try:
            
            rd = await aioredis.from_url(
                url=settings.REDIS_URI,
                encoding='utf-8',
                decode_responses=True,
                health_check_interval=20,
                max_connections=settings.POOL_SIZE,
                socket_timeout=settings.POOL_TIMEOUT
            )
            app.state.redis = rd
            if await rd.ping():
                logger.info("Redis连接成功...")
                return rd
            raise CustomException(msg="Redis连接失败")
        except aioredis.AuthenticationError as e:
            raise aioredis.AuthenticationError(f"Redis认证失败: {e}")
        except aioredis.TimeoutError as e:
            raise aioredis.TimeoutError(f"Redis连接超时: {e}")
        except aioredis.RedisError as e:
            raise aioredis.RedisError(f"Redis连接错误: {e}")
    else:
        await app.state.redis.close()
        logger.info('Redis连接已关闭')

async def mongodb_connect(app: FastAPI, status: bool) -> AsyncIOMotorClient:
    """创建或关闭MongoDB连接"""
    if not settings.MONGO_DB_ENABLE:
        raise CustomException(msg="请先开启MongoDB连接", data="请启用 app/core/config.py: MONGO_DB_ENABLE")

    if status:
        try:
            
            client = AsyncIOMotorClient(
                settings.MONGO_DB_URI,
                maxPoolSize=settings.POOL_SIZE,
                minPoolSize=settings.MAX_OVERFLOW,
                serverSelectionTimeoutMS=settings.POOL_TIMEOUT * 1000
            )
            app.state.mongo_client = client
            app.state.mongo = client[settings.MONGO_DB_NAME]
            data = await client.server_info()
            logger.info("MongoDB连接成功...", data)
            return data
        except Exception as e:
            raise ValueError(f"MongoDB连接失败: {e}")
    else:
        app.state.mongo_client.close()
        logger.info("MongoDB连接已关闭")