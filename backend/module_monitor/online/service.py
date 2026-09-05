import json
from datetime import date, datetime, timedelta

from redis.asyncio.client import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_system.log.model import LoginLogModel
from app.api.v1.module_system.user.model import UserModel
from app.common.enums import RedisInitKeyConfig
from app.core.logger import logger
from app.core.redis_crud import RedisCURD
from app.core.security import decode_access_token

from .schema import DashboardStatsSchema, LoginTrendItem, OnlineQueryParam, RecentLoginItem


class OnlineService:
    """在线用户管理模块服务层"""

    @staticmethod
    async def get_online_list(redis: Redis, search: OnlineQueryParam | None = None) -> list[dict]:
        keys = await RedisCURD(redis).scan_keys(f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:*")
        tokens = await RedisCURD(redis).mget(keys)

        online_users = []
        for key, token in zip(keys, tokens, strict=True):
            if not token:
                continue
            try:
                payload = decode_access_token(token=token)
                session_id = payload.sub

                # 从 Redis 读取完整会话信息
                raw = await RedisCURD(redis).get(f"{RedisInitKeyConfig.USER_SESSION.key}:{session_id}")
                if not raw:
                    continue
                session_info = json.loads(raw)

                # 内联搜索匹配逻辑
                if search:
                    if search.name and search.name[1]:
                        kw = search.name[1].strip("%")
                        if kw.lower() not in session_info.get("name", "").lower():
                            continue
                    if search.ipaddr and search.ipaddr[1]:
                        kw = search.ipaddr[1].strip("%")
                        if kw not in session_info.get("ipaddr", ""):
                            continue
                    if search.login_location and search.login_location[1]:
                        kw = search.login_location[1].strip("%")
                        if kw.lower() not in session_info.get("login_location", "").lower():
                            continue

                online_users.append(session_info)
            except Exception:
                # token 已过期或无效，清理 Redis 中的脏数据
                key_str = key.decode() if isinstance(key, bytes) else key
                session_id = key_str.split(":")[-1]
                await RedisCURD(redis).delete(key_str)
                await RedisCURD(redis).delete(f"{RedisInitKeyConfig.REFRESH_TOKEN.key}:{session_id}")
                await RedisCURD(redis).delete(f"{RedisInitKeyConfig.USER_SESSION.key}:{session_id}")
                continue

        online_users.sort(key=lambda x: x.get("login_time", ""), reverse=True)
        return online_users

    @staticmethod
    async def get_current_user_sessions(redis: Redis, user_id: int) -> list[dict]:
        """获取当前用户的在线会话列表"""
        all_online = await OnlineService.get_online_list(redis)
        return [s for s in all_online if s.get("user_id") == user_id]

    @staticmethod
    async def delete_online(redis: Redis, session_id: str) -> None:
        await RedisCURD(redis).delete(f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}")
        await RedisCURD(redis).delete(f"{RedisInitKeyConfig.REFRESH_TOKEN.key}:{session_id}")
        await RedisCURD(redis).delete(f"{RedisInitKeyConfig.USER_SESSION.key}:{session_id}")
        logger.info(f"强制下线用户会话: {session_id}")

    @staticmethod
    async def clear_online(redis: Redis) -> None:
        await RedisCURD(redis).clear(f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:*")
        await RedisCURD(redis).clear(f"{RedisInitKeyConfig.REFRESH_TOKEN.key}:*")
        await RedisCURD(redis).clear(f"{RedisInitKeyConfig.USER_SESSION.key}:*")
        logger.info("清除所有在线用户会话成功")

    @staticmethod
    async def get_dashboard_stats(db: AsyncSession, redis: Redis) -> DashboardStatsSchema:
        """获取仪表盘统计数据"""
        today_start = datetime.combine(date.today(), datetime.min.time())
        week_start = today_start - timedelta(days=7)

        online_count = len(await OnlineService.get_online_list(redis))

        users_sql = select(func.count()).select_from(UserModel).where(UserModel.is_deleted.is_(False))
        user_count = (await db.execute(users_sql)).scalar() or 0

        users_week_sql = (
            select(func.count()).select_from(UserModel)
            .where(UserModel.is_deleted.is_(False), UserModel.created_time >= week_start)
        )
        user_week_count = (await db.execute(users_week_sql)).scalar() or 0

        today_login_sql = (
            select(func.count()).select_from(LoginLogModel)
            .where(LoginLogModel.created_time >= today_start)
        )
        today_login_count = (await db.execute(today_login_sql)).scalar() or 0

        today_unique_sql = (
            select(func.count(func.distinct(LoginLogModel.username)))
            .select_from(LoginLogModel)
            .where(LoginLogModel.created_time >= today_start)
        )
        today_unique_count = (await db.execute(today_unique_sql)).scalar() or 0

        recent_stmt = (
            select(LoginLogModel.username, LoginLogModel.status, LoginLogModel.created_time,
                   LoginLogModel.login_ip, LoginLogModel.login_location)
            .where(LoginLogModel.is_deleted.is_(False))
            .order_by(LoginLogModel.created_time.desc())
            .limit(10)
        )
        recent_rows = (await db.execute(recent_stmt)).all()
        recent_logins = [
            RecentLoginItem(username=r.username, status=r.status, login_time=r.created_time,
                            login_ip=r.login_ip, login_location=r.login_location)
            for r in recent_rows
        ]

        # 近 7 天登录趋势：按天聚合登录次数 / 独立用户 / 新增用户（含今天，共 7 天）
        login_trend = await OnlineService._build_login_trend(db, today_start=today_start, week_start=week_start)

        result = DashboardStatsSchema(
            online_users=online_count,
            total_users=user_count,
            today_login_count=today_login_count,
            today_unique_users=today_unique_count,
            week_user_created=user_week_count,
            login_trend=login_trend,
            recent_logins=recent_logins,
        )
        return result

    @staticmethod
    async def _build_login_trend(db: AsyncSession, *, today_start: datetime, week_start: datetime) -> list[LoginTrendItem]:
        """构建近 7 天登录趋势（含今天，共 7 天，按日期倒序填充缺口为 0）。

        参数:
        - db (AsyncSession): 数据库会话
        - today_start (datetime): 今天零点
        - week_start (datetime): 7 天前零点

        返回:
        - list[LoginTrendItem]: 按日期升序的 7 天趋势
        """
        # 查询 7 天内每天登录次数与独立用户数
        login_sql = (
            select(
                func.date(LoginLogModel.created_time).label("day"),
                func.count().label("logins"),
                func.count(func.distinct(LoginLogModel.username)).label("unique_users"),
            )
            .where(
                LoginLogModel.is_deleted.is_(False),
                LoginLogModel.status == 1,  # 仅统计成功登录
                LoginLogModel.created_time >= week_start,
            )
            .group_by(func.date(LoginLogModel.created_time))
        )
        login_rows = (await db.execute(login_sql)).all()
        login_map = {str(r.day): (r.logins, r.unique_users) for r in login_rows}

        # 查询 7 天内每天新增用户数
        new_user_sql = (
            select(
                func.date(UserModel.created_time).label("day"),
                func.count().label("new_users"),
            )
            .where(
                UserModel.is_deleted.is_(False),
                UserModel.created_time >= week_start,
            )
            .group_by(func.date(UserModel.created_time))
        )
        new_rows = (await db.execute(new_user_sql)).all()
        new_map = {str(r.day): r.new_users for r in new_rows}

        # 生成连续 7 天日期序列（升序），缺口补 0
        trend: list[LoginTrendItem] = []
        for offset in range(7):
            d = week_start.date() + timedelta(days=offset)
            day_str = d.isoformat()
            logins, unique_users = login_map.get(day_str, (0, 0))
            trend.append(
                LoginTrendItem(
                    day=day_str,
                    logins=int(logins or 0),
                    unique_users=int(unique_users or 0),
                    new_users=int(new_map.get(day_str, 0) or 0),
                )
            )
        return trend
