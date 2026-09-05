import json
from collections.abc import Sequence

from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import RedisInitKeyConfig
from app.core.base_schema import AuthSchema
from app.core.database import async_db_session
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.core.redis_crud import RedisCURD

from .crud import ParamsCRUD
from .schema import ParamsOutSchema, ParamsUpdateSchema


class ParamsService:
    """参数管理服务"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def update(self, redis: Redis, id: int, data: ParamsUpdateSchema) -> ParamsOutSchema:
        """更新参数

        参数:
        - redis (Redis): Redis 客户端实例
        - id (int): 参数ID
        - data (ParamsUpdateSchema): 参数更新模型

        返回:
        - ParamsOutSchema: 更新后的参数响应模型
        """
        exist_obj = await ParamsCRUD(self.auth, self.db).get_or_404(id=id, msg="更新失败，该数据不存在")
        if exist_obj.config_key != data.config_key:
            raise CustomException(msg="更新失败，系统配置key不允许修改")

        new_obj = await ParamsCRUD(self.auth, self.db).update(id=id, data=data)
        if not new_obj:
            raise CustomException(msg="更新失败，系统配置不存在")
        out = ParamsOutSchema.model_validate(new_obj)
        redis_payload = out.model_dump(mode="json")

        # 同步redis
        user = self.auth.user
        if not user:
            raise CustomException(msg="未登录")
        redis_key = f"{RedisInitKeyConfig.SYSTEM_CONFIG.key}:{new_obj.config_key}"
        try:
            value = json.dumps(redis_payload, ensure_ascii=False)
            result = await RedisCURD(redis).set(
                key=redis_key,
                value=value,
                expire=None,
            )
            if not result:
                logger.error(f"同步配置到缓存失败: {out}")
                raise CustomException(msg="同步配置到缓存失败")
        except Exception as e:
            logger.error(f"更新系统配置失败: {e}")
            raise CustomException(msg="同步配置到缓存失败") from e

        return out

    @staticmethod
    async def _load_all_configs_from_db() -> Sequence[object]:
        async with async_db_session() as session, session.begin():
            init_auth = AuthSchema()
            return await ParamsCRUD(init_auth, session).get_list()

    @staticmethod
    async def _sync_configs_to_redis(redis: Redis, config_obj: Sequence) -> list[dict]:
        """将 DB 配置写入 Redis，返回对应的 dict 列表。"""
        configs: list[dict] = []
        for config in config_obj:
            redis_key = f"{RedisInitKeyConfig.SYSTEM_CONFIG.key}:{config.config_key}"
            out = ParamsOutSchema.model_validate(config)
            payload = out.model_dump(mode="json")
            try:
                await RedisCURD(redis).set(redis_key, json.dumps(payload, ensure_ascii=False))
                configs.append(out.model_dump())
            except Exception as e:
                logger.error(f"❌️ 缓存系统配置失败: {redis_key}: {e}")
        return configs

    @staticmethod
    async def init_cache(redis: Redis) -> None:
        """启动时初始化系统参数到 Redis。"""
        try:
            config_obj = await ParamsService._load_all_configs_from_db()
            if not config_obj:
                raise CustomException(msg="该数据不存在")
            await ParamsService._sync_configs_to_redis(redis, config_obj)
        except Exception as e:
            logger.error(f"❌️ 初始化系统参数到 Redis 失败: {e}")
            raise CustomException(msg="初始化系统参数到 Redis 失败") from e

    @staticmethod
    async def get_init_cache(redis: Redis) -> list[dict]:
        """从 Redis 读取系统配置；为空时自动回源 DB。"""
        redis_keys = await RedisCURD(redis).get_keys(f"{RedisInitKeyConfig.SYSTEM_CONFIG.key}:*")
        redis_configs = await RedisCURD(redis).mget(redis_keys)
        configs = []
        for raw in redis_configs:
            if not raw:
                continue
            try:
                configs.append(json.loads(raw))
            except Exception as e:
                logger.error(f"解析系统配置数据失败: {e}")

        if not configs:
            config_obj = await ParamsService._load_all_configs_from_db()
            if config_obj:
                configs = await ParamsService._sync_configs_to_redis(redis, config_obj)
        return configs
