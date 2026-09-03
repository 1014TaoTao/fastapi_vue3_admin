from fastapi import APIRouter

from .cache.controller import CacheRouter
from .online.controller import OnlineRouter
from .server.controller import ServerRouter

monitor_router = APIRouter(prefix="/monitor")

monitor_router.include_router(CacheRouter)
monitor_router.include_router(OnlineRouter)
monitor_router.include_router(ServerRouter)
