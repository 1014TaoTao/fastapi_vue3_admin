"""健康检查服务：仅探测 DB / Redis 网络连通（SELECT 1 / PING）。"""

import asyncio
from typing import Any

from sqlalchemy import text

from app.config.setting import settings
from app.core.database import async_db_session
from app.core.logger import logger

from .schema import ServiceInfoOut


class HealthService:
    """健康检查服务：探测 DB / Redis 网络连通并组装状态。"""

    @classmethod
    async def check_database(cls) -> int:
        """数据库连通：SELECT 1 成功返回 1，失败返回 0。"""
        try:
            async with async_db_session() as session:
                await session.execute(text("SELECT 1"))
            return 1
        except Exception as e:
            logger.warning(f"数据库连通检查失败: {e}")
            return 0

    @classmethod
    async def check_redis(cls, redis: Any | None) -> int:
        """Redis 连通：PING 成功返回 1，失败返回 0。"""
        if redis is None:
            return 0
        try:
            await redis.ping()
            return 1
        except Exception as e:
            logger.warning(f"Redis 连通检查失败: {e}")
            return 0

    @classmethod
    async def collect(cls, redis: Any | None) -> ServiceInfoOut:
        """并行探活 DB / Redis，组装健康状态。"""
        db_status, redis_status = await asyncio.gather(
            cls.check_database(),
            cls.check_redis(redis),
        )
        return ServiceInfoOut(
            name=settings.TITLE,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT.value,
            db_status=db_status,
            redis_status=redis_status,
        )
