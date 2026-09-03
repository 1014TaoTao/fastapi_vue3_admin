import asyncio
import shutil
import time
from datetime import datetime
from typing import Any

from sqlalchemy import text

from app.core.database import async_db_session
from app.core.logger import logger

from .schema import DependencyStatus

# 应用启动时间戳
_start_time = datetime.now()

# 健康检查时间间隔
HEALTH_STREAM_INTERVAL = 30  # 秒


class HealthService:
    """健康检查服务：封装数据库 / Redis / 磁盘等依赖的探活逻辑。"""

    @staticmethod
    async def check_database() -> DependencyStatus:
        """检查数据库连接"""
        try:
            start = time.perf_counter()
            async with async_db_session() as session:
                await session.execute(text("SELECT 1"))
            latency = (time.perf_counter() - start) * 1000
            return DependencyStatus(status=1, latency_ms=round(latency, 2))
        except Exception as e:
            logger.warning(f"数据库健康检查失败: {e}")
            return DependencyStatus(status=0)

    @staticmethod
    async def check_redis(redis: Any | None) -> DependencyStatus:
        """检查 Redis 连接

        参数:
        - redis: Redis 客户端实例（由控制器从应用状态中取出注入）。
        """
        if redis is None:
            return DependencyStatus(status=0)
        try:
            start = time.perf_counter()
            await redis.ping()
            latency = (time.perf_counter() - start) * 1000
            return DependencyStatus(status=1, latency_ms=round(latency, 2))
        except Exception as e:
            logger.warning(f"Redis 健康检查失败: {e}")
            return DependencyStatus(status=0)

    @staticmethod
    async def check_dependencies(redis: Any | None) -> dict[str, DependencyStatus]:
        """并行探活全部依赖项。"""
        db_status, redis_status = await asyncio.gather(
            HealthService.check_database(),
            HealthService.check_redis(redis),
        )
        return {"database": db_status, "redis": redis_status}

    @staticmethod
    def get_disk_usage() -> float:
        """获取磁盘使用率"""
        try:
            usage = shutil.disk_usage("/")
            return round(usage.used / usage.total * 100, 1)
        except Exception:
            return -1.0

    @staticmethod
    def get_uptime() -> float:
        """进程运行时长（秒）"""
        return (datetime.now() - _start_time).total_seconds()

    @staticmethod
    async def collect_status(redis: Any | None) -> dict:
        """采集当前健康状态（供 SSE 实时推送）。"""
        dependencies = await HealthService.check_dependencies(redis)
        return {
            "status": 1 if all(d.status == 1 for d in dependencies.values()) else 0,
            "dependencies": {name: dep.model_dump() for name, dep in dependencies.items()},
            "disk_usage": HealthService.get_disk_usage(),
            "uptime_seconds": HealthService.get_uptime(),
            "timestamp": datetime.now().isoformat(),
        }
