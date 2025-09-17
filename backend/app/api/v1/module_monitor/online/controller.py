# -*- coding: utf-8 -*-

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse
from redis.asyncio.client import Redis

from app.common.request import PaginationService
from app.common.response import SuccessResponse,ErrorResponse
from app.core.dependencies import AuthPermission, redis_getter
from app.core.base_params import PaginationQueryParam
from app.core.router_class import OperationLogRoute
from app.core.logger import logger
from .param import OnlineQueryParam
from .service import OnlineService


OnlineRouter = APIRouter(route_class=OperationLogRoute, prefix="/online", tags=["在线用户"])


@OnlineRouter.get(
    '/list', 
    dependencies=[Depends(AuthPermission(permissions=['monitor:online:query']))],
    summary="获取在线用户列表",
    description="获取在线用户列表"
)
async def get_online_list_controller(
    redis: Redis = Depends(redis_getter), 
    paging_query: PaginationQueryParam = Depends(),
    search: OnlineQueryParam = Depends()
)->JSONResponse:
    # 获取全量数据
    result_dict_list = await OnlineService.get_online_list_service(redis=redis, search=search)
    result_dict = await PaginationService.get_page_obj(data_list= result_dict_list, page_no= paging_query.page_no, page_size = paging_query.page_size)
    logger.info('获取成功')

    return SuccessResponse(data=result_dict,msg='获取成功')


@OnlineRouter.delete(
    '/delete', 
    dependencies=[Depends(AuthPermission(permissions=['monitor:online:delete']))],
    summary="强制下线",
    description="强制下线"
)
async def delete_online_controller(
    session_id: str = Body(..., description="会话编号"),
    redis: Redis = Depends(redis_getter),
)->JSONResponse:
    is_ok = await OnlineService.delete_online_service(redis=redis, session_id=session_id)
    if is_ok:
        logger.info("强制下线成功")
        return SuccessResponse(msg="强制下线成功")
    else:
        logger.info("强制下线失败")
        return ErrorResponse(msg="强制下线失败")

@OnlineRouter.delete(
    '/clear', 
    dependencies=[Depends(AuthPermission(permissions=['monitor:online:delete']))],
    summary="清除所有在线用户",
    description="清除所有在线用户"
)
async def clear_online_controller(
    redis: Redis = Depends(redis_getter),
)->JSONResponse:
    is_ok = await OnlineService.clear_online_service(redis=redis)
    if is_ok:
        logger.info("清除所有在线用户成功")
        return SuccessResponse(msg="清除所有在线用户成功")
    else:
        logger.info("清除所有在线用户失败")
        return ErrorResponse(msg="清除所有在线用户失败")