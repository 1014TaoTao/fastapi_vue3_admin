from redis.asyncio.client import Redis

from app.common.enums import RedisInitKeyConfig
from app.core.redis_crud import RedisCURD

from .schema import CacheInfoSchema, CacheMonitorSchema


class CacheService:
    """缓存监控模块服务层"""

    @staticmethod
    async def get_monitor_statistical_info(redis: Redis) -> CacheMonitorSchema:
        info = await RedisCURD(redis).info()
        db_size = await RedisCURD(redis).db_size()
        command_stats_dict = await RedisCURD(redis).commandstats()

        command_stats = [{"name": key.split("_")[1], "value": str(value.get("calls"))} for key, value in command_stats_dict.items()]
        return CacheMonitorSchema(command_stats=command_stats, db_size=db_size, info=info)

    @staticmethod
    async def get_monitor_cache_names() -> list[CacheInfoSchema]:
        return [
            CacheInfoSchema(
                cache_key="",
                cache_name=key_config.key,
                cache_value="",
                remark=key_config.remark,
            )
            for key_config in RedisInitKeyConfig
        ]

    @staticmethod
    async def get_monitor_cache_keys(redis: Redis, cache_name: str) -> list:
        cache_keys = await RedisCURD(redis).get_keys(f"{cache_name}*")
        return [key.split(":", 1)[1] for key in cache_keys if key.startswith(f"{cache_name}:")]

    @staticmethod
    async def get_monitor_cache_value(redis: Redis, cache_name: str, cache_key: str) -> CacheInfoSchema:
        cache_value = await RedisCURD(redis).get(f"{cache_name}:{cache_key}")
        return CacheInfoSchema(
            cache_key=cache_key,
            cache_name=cache_name,
            cache_value=cache_value,
            remark="",
        )

    @staticmethod
    async def clear_monitor_cache_by_name(redis: Redis, cache_name: str) -> bool:
        cache_keys = await RedisCURD(redis).get_keys(f"{cache_name}*")
        if cache_keys:
            await RedisCURD(redis).delete(*cache_keys)
        return True

    @staticmethod
    async def clear_monitor_cache_by_key(redis: Redis, cache_key: str) -> bool:
        cache_keys = await RedisCURD(redis).get_keys(f"*{cache_key}")
        if cache_keys:
            await RedisCURD(redis).delete(*cache_keys)
        return True

    @staticmethod
    async def clear_monitor_cache_all(redis: Redis) -> bool:
        cache_keys = await RedisCURD(redis).get_keys()
        if cache_keys:
            await RedisCURD(redis).delete(*cache_keys)
        return True
