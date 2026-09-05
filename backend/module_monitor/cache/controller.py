from typing import Annotated

from fastapi import APIRouter, Depends, Path, Security
from fastapi.responses import JSONResponse
from redis.asyncio.client import Redis

from app.api.v1.module_monitor.cache.schema import CacheInfoSchema, CacheMonitorSchema
from app.common.response import ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission, redis_getter
from app.core.router_class import OperationLogRoute

from .service import CacheService

CacheRouter = APIRouter(route_class=OperationLogRoute, prefix="/cache", tags=["缓存监控"])


@CacheRouter.get("/info", summary="获取缓存监控信息", response_model=ResponseSchema[CacheMonitorSchema], dependencies=[Security(AuthPermission(["module_monitor:cache:query"]))])
async def get_monitor_cache_info_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
) -> JSONResponse:
    result = await CacheService.get_monitor_statistical_info(redis=redis)
    return SuccessResponse(data=result, msg="获取缓存监控信息成功")


@CacheRouter.get("/get/names", summary="获取缓存名称列表", response_model=ResponseSchema[list[CacheInfoSchema]], dependencies=[Security(AuthPermission(["module_monitor:cache:query"]))])
async def get_monitor_cache_name_controller() -> JSONResponse:
    result = await CacheService.get_monitor_cache_names()
    return SuccessResponse(data=result, msg="获取缓存名称列表成功")


@CacheRouter.get("/get/keys/{cache_name}", summary="获取缓存键名列表", response_model=ResponseSchema[list[CacheInfoSchema]], dependencies=[Security(AuthPermission(["module_monitor:cache:query"]))])
async def get_monitor_cache_key_controller(cache_name: Annotated[str, Path(description="缓存名称")], redis: Annotated[Redis, Depends(redis_getter)]) -> JSONResponse:
    result = await CacheService.get_monitor_cache_keys(redis=redis, cache_name=cache_name)
    return SuccessResponse(data=result, msg=f"获取缓存{cache_name}的键名列表成功")


@CacheRouter.get("/get/value/{cache_name}/{cache_key}", summary="获取缓存值", response_model=ResponseSchema[CacheInfoSchema], dependencies=[Security(AuthPermission(["module_monitor:cache:query"]))])
async def get_monitor_cache_value_controller(
    cache_name: Annotated[str, Path(description="缓存名称")],
    cache_key: Annotated[str, Path(description="缓存键名")],
    redis: Annotated[Redis, Depends(redis_getter)],
) -> JSONResponse:
    result = await CacheService.get_monitor_cache_value(redis=redis, cache_name=cache_name, cache_key=cache_key)
    return SuccessResponse(data=result, msg=f"获取缓存{cache_name}:{cache_key}的值成功")


@CacheRouter.delete("/delete/name/{cache_name}", summary="清除指定缓存名称的所有缓存", response_model=ResponseSchema[None], dependencies=[Security(AuthPermission(["module_monitor:cache:delete"]))])
async def clear_monitor_cache_name_controller(cache_name: Annotated[str, Path(description="缓存名称")], redis: Annotated[Redis, Depends(redis_getter)]) -> JSONResponse:
    result = await CacheService.clear_monitor_cache_by_name(redis=redis, cache_name=cache_name)
    return SuccessResponse(msg=f"{cache_name}对应键值清除成功", data=result)


@CacheRouter.delete("/delete/key/{cache_key}", summary="清除指定缓存键", response_model=ResponseSchema[None], dependencies=[Security(AuthPermission(["module_monitor:cache:delete"]))])
async def clear_monitor_cache_key_controller(cache_key: Annotated[str, Path(description="缓存键名")], redis: Annotated[Redis, Depends(redis_getter)]) -> JSONResponse:
    result = await CacheService.clear_monitor_cache_by_key(redis=redis, cache_key=cache_key)
    return SuccessResponse(msg=f"{cache_key}清除成功", data=result)


@CacheRouter.delete("/clear", summary="清除所有缓存", response_model=ResponseSchema[None], dependencies=[Security(AuthPermission(["module_monitor:cache:delete"]))])
async def clear_monitor_cache_all_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
) -> JSONResponse:
    result = await CacheService.clear_monitor_cache_all(redis=redis)
    return SuccessResponse(msg="所有缓存清除成功", data=result)
