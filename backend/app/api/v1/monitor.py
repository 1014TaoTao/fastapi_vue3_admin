"""monitor 路由清单：仅聚合路由，不含业务逻辑。"""

from fastapi import APIRouter

from app.modules.monitor.cache.controller import CacheRouter
from app.modules.monitor.health.controller import HealthRouter
from app.modules.monitor.online.controller import OnlineRouter
from app.modules.monitor.server.controller import ServerRouter

monitor_router = APIRouter(prefix="/monitor")

monitor_router.include_router(CacheRouter)
monitor_router.include_router(HealthRouter)
monitor_router.include_router(OnlineRouter)
monitor_router.include_router(ServerRouter)
