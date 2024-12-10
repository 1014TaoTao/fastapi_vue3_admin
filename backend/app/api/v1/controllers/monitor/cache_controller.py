# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.core.dependencies import AuthPermission
from app.api.v1.services.monitor.cache_service import CacheService
from app.core.logger import logger
from app.common.response import SuccessResponse
from app.core.exceptions import CustomException
from app.core.router_class import OperationLogRoute


router = APIRouter(route_class=OperationLogRoute)


@router.get(
    '/info',
    dependencies=[Depends(AuthPermission(permissions=['monitor:cache:query']))],
    summary="获取缓存监控信息",
    description="获取缓存监控信息"
)
async def get_monitor_cache_info(request: Request) -> JSONResponse:
    """获取缓存监控统计信息"""
    result = await CacheService.get_cache_monitor_statistical_info_services(request)
    logger.info('获取缓存监控信息成功')
    return SuccessResponse(data=result, msg='获取缓存监控信息成功')


@router.get(
    '/get/names',
    dependencies=[Depends(AuthPermission(permissions=['monitor:cache:query']))],
    summary="获取缓存名称列表",
    description="获取缓存名称列表"
)
async def get_monitor_cache_name() -> JSONResponse:
    """获取缓存名称列表"""
    result = await CacheService.get_cache_monitor_cache_name_services()
    logger.info('获取缓存名称列表成功')
    return SuccessResponse(data=result, msg='获取缓存名称列表成功')


@router.get(
    '/get/keys/{cache_name}',
    dependencies=[Depends(AuthPermission(permissions=['monitor:cache:query']))],
    summary="获取缓存键名列表",
    description="获取缓存键名列表"
)
async def get_monitor_cache_key(request: Request, cache_name: str) -> JSONResponse:
    """获取指定缓存名称下的键名列表"""
    result = await CacheService.get_cache_monitor_cache_key_services(request, cache_name)
    logger.info(f'获取缓存{cache_name}的键名列表成功')
    return SuccessResponse(data=result, msg=f'获取缓存{cache_name}的键名列表成功')


@router.get(
    '/get/value/{cache_name}/{cache_key}',
    dependencies=[Depends(AuthPermission(permissions=['monitor:cache:query']))],
    summary="获取缓存值",
    description="获取缓存值"
)
async def get_monitor_cache_value(request: Request, cache_name: str, cache_key: str) -> JSONResponse:
    """获取指定缓存键的值"""
    result = await CacheService.get_cache_monitor_cache_value_services(request, cache_name, cache_key)
    logger.info(f'获取缓存{cache_name}:{cache_key}的值成功')
    return SuccessResponse(data=result, msg=f'获取缓存{cache_name}:{cache_key}的值成功')


@router.delete(
    '/delete/name/{cache_name}',
    dependencies=[Depends(AuthPermission(permissions=['monitor:cache:delete']))],
    summary="清除指定缓存名称的所有缓存",
    description="清除指定缓存名称的所有缓存"
)
async def clear_monitor_cache_name(request: Request, cache_name: str) -> JSONResponse:
    """清除指定缓存名称下的所有缓存"""
    result = await CacheService.clear_cache_monitor_cache_name_services(request, cache_name)
    if not result:
        raise CustomException(message='清除缓存失败', data=result)
    logger.info(f'清除缓存{cache_name}成功')
    return SuccessResponse(msg=f'{cache_name}对应键值清除成功', data=result)


@router.delete(
    '/delete/key/{cache_key}',
    dependencies=[Depends(AuthPermission(permissions=['monitor:cache:delete']))],
    summary="清除指定缓存键",
    description="清除指定缓存键"
)
async def clear_monitor_cache_key(request: Request, cache_key: str) -> JSONResponse:
    """清除指定缓存键"""
    result = await CacheService.clear_cache_monitor_cache_key_services(request, cache_key)
    if not result:
        raise CustomException(message='清除缓存失败', data=result)
    logger.info(f'清除缓存键{cache_key}成功')
    return SuccessResponse(msg=f'{cache_key}清除成功', data=result)


@router.delete(
    '/delete/all',
    dependencies=[Depends(AuthPermission(permissions=['monitor:cache:delete']))],
    summary="清除所有缓存",
    description="清除所有缓存"
)
async def clear_monitor_cache_all(request: Request) -> JSONResponse:
    """清除所有缓存"""
    result = await CacheService.clear_cache_monitor_all_services(request)
    if not result:
        raise CustomException(message='清除缓存失败', data=result)
    logger.info('清除所有缓存成功')
    return SuccessResponse(msg='所有缓存清除成功', data=result)
