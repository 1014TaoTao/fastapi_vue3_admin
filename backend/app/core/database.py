# -*- coding: utf-8 -*-

import aioredis
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
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
    InvalidRequestError,
)

from app.core.logger import logger
from app.config.setting import settings
from app.core.exceptions import CustomException


def async_db_engine() -> AsyncEngine:
    """创建异步数据库引擎"""
    # 创建数据库引擎
    async_engine = create_async_engine(
        url=settings.DB_URI,
        echo=settings.DATABASE_ECHO,
        echo_pool=settings.ECHO_POOL,
        pool_pre_ping=settings.POOL_PRE_PING,
        future=settings.FUTURE,
        pool_recycle=settings.POOL_RECYCLE,
        # pool_size=settings.POOL_SIZE,  # sqlite 不支持
        # max_overflow=settings.MAX_OVERFLOW,  # sqlite 不支持
        # pool_timeout=settings.POOL_TIMEOUT,  # sqlite 不支持
    )

    return async_engine


# 创建会话工厂
async_session = async_sessionmaker(
    bind=async_db_engine(),
    autocommit=settings.AUTOCOMMIT,
    autoflush=settings.AUTOFETCH,
    expire_on_commit=settings.EXPIRE_ON_COMMIT,
    class_=AsyncSession,
)


def session_connect() -> AsyncSession:
    """获取数据库会话"""
    try:
        if not settings.SQL_DB_ENABLE:
            raise CustomException(
                msg="请先开启数据库连接",
                data="请启用 app/config/setting.py: SQL_DB_ENABLE",
            )
        return async_session()
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise CustomException(msg=f"数据库连接失败: {e}")


async def test_db_connection(session: AsyncSession) -> bool:
    try:
        # 执行简单查询测试连接是否真实可用
        await session.execute(text("SELECT 1"))
        return True
    except OperationalError:
        logger.error("数据库操作失败，请检查数据库服务是否正常运行")
        raise CustomException(msg="数据库操作失败，请检查数据库服务是否正常运行")
    except TimeoutError:
        logger.error("数据库连接超时，请检查网络连接或增加连接超时时间")
        raise CustomException(msg="数据库连接超时，请检查网络连接或增加连接超时时间")
    except DisconnectionError as e:
        logger.error(f"数据库连接中断: {e}")
        raise CustomException(msg="数据库连接中断，请检查数据库服务状态")
    except InterfaceError as e:
        logger.error(f"数据库接口错误: {e}")
        raise CustomException(msg="数据库接口错误，请检查数据库驱动配置")
    except ProgrammingError as e:
        logger.error(f"SQL语句错误: {e}")
        raise CustomException(msg="SQL语句错误，请检查SQL语法")
    except IntegrityError as e:
        logger.error(f"数据完整性错误: {e}")
        raise CustomException(msg="数据完整性错误，请检查数据约束条件")
    except DataError as e:
        logger.error(f"数据类型错误: {e}")
        raise CustomException(msg="数据类型错误，请检查数据格式")
    except InternalError as e:
        logger.error(f"数据库内部错误: {e}")
        raise CustomException(msg="数据库内部错误，请联系数据库管理员")
    except NotSupportedError as e:
        logger.error(f"数据库不支持的操作: {e}")
        raise CustomException(msg="数据库不支持该操作，请检查数据库版本")
    except InvalidRequestError as e:
        logger.error(f"无效的数据库请求: {e}")
        raise CustomException(msg="无效的数据库请求，请检查请求参数")
    except Exception as e:
        logger.error(f"数据库操作异常: {e}")
        raise CustomException(msg="数据库操作异常，请联系管理员")


async def redis_connect(app: FastAPI, status: bool) -> aioredis.Redis:
    """创建或关闭Redis连接"""
    if not settings.REDIS_ENABLE:
        raise CustomException(
            msg="请先开启Redis连接", data="请启用 app/core/config.py: REDIS_ENABLE"
        )

    if status:
        try:
            rd = await aioredis.from_url(
                url=settings.REDIS_URI,
                encoding="utf-8",
                decode_responses=True,
                health_check_interval=20,
                max_connections=settings.POOL_SIZE,
                socket_timeout=settings.POOL_TIMEOUT,
            )
            app.state.redis = rd
            if await rd.ping():
                logger.info("Redis连接成功...")
                return rd
            raise CustomException(msg="Redis连接失败")
        except aioredis.AuthenticationError as e:
            logger.error(f"Redis认证失败: {e}")
            raise aioredis.AuthenticationError(f"Redis认证失败: {e}")
        except aioredis.TimeoutError as e:
            logger.error(f"Redis连接超时: {e}")
            raise aioredis.TimeoutError(f"Redis连接超时: {e}")
        except aioredis.RedisError as e:
            logger.error(f"Redis连接错误: {e}")
            raise aioredis.RedisError(f"Redis连接错误: {e}")
    else:
        await app.state.redis.close()
        logger.info("Redis连接已关闭")


async def mongodb_connect(app: FastAPI, status: bool) -> AsyncIOMotorClient:
    """创建或关闭MongoDB连接"""
    if not settings.MONGO_DB_ENABLE:
        raise CustomException(
            msg="请先开启MongoDB连接", data="请启用 app/core/config.py: MONGO_DB_ENABLE"
        )

    if status:
        try:
            client = AsyncIOMotorClient(
                settings.MONGO_DB_URI,
                maxPoolSize=settings.POOL_SIZE,
                minPoolSize=settings.MAX_OVERFLOW,
                serverSelectionTimeoutMS=settings.POOL_TIMEOUT * 1000,
            )
            app.state.mongo_client = client
            app.state.mongo = client[settings.MONGO_DB_NAME]
            data = await client.server_info()
            logger.info("MongoDB连接成功", data)
            return data
        except Exception as e:
            logger.error(f"MongoDB连接失败: {e}")
            raise ValueError(f"MongoDB连接失败: {e}")
    else:
        app.state.mongo_client.close()
        logger.info("MongoDB连接已关闭")
