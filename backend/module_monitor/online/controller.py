from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, Security
from fastapi.responses import JSONResponse
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.request import PaginationService
from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter, get_current_user, redis_getter
from app.core.router_class import OperationLogRoute

from .schema import DashboardStatsSchema, OnlineOutSchema, OnlineQueryParam
from .service import OnlineService

OnlineRouter = APIRouter(route_class=OperationLogRoute, prefix="/online", tags=["在线用户"])


@OnlineRouter.get("/list", summary="获取在线用户列表", response_model=ResponseSchema[list[OnlineOutSchema]], dependencies=[Security(AuthPermission(["module_monitor:online:query"]))])
async def get_online_list_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[OnlineQueryParam, Query()],
) -> JSONResponse:
    result_dict_list = await OnlineService.get_online_list(redis=redis, search=search)
    result_dict = await PaginationService.paginate(
        data_list=result_dict_list,
        page_no=page.page_no,
        page_size=page.page_size,
    )
    return SuccessResponse(data=result_dict, msg="获取成功")


@OnlineRouter.get("/current", summary="获取当前用户的在线会话", response_model=ResponseSchema[list[OnlineOutSchema]], dependencies=[Depends(get_current_user)])
async def get_current_online_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    auth: Annotated[AuthSchema, Depends(get_current_user)],
) -> JSONResponse:
    sessions = await OnlineService.get_current_user_sessions(redis=redis, user_id=auth.user.id)
    return SuccessResponse(data=sessions, msg="获取当前用户在线会话成功")


@OnlineRouter.delete("/delete", summary="强制下线", response_model=ResponseSchema[None], dependencies=[Security(AuthPermission(["module_monitor:online:delete"]))])
async def delete_online_controller(
    session_id: Annotated[str, Body(description="会话编号")],
    redis: Annotated[Redis, Depends(redis_getter)],
) -> JSONResponse:
    await OnlineService.delete_online(redis=redis, session_id=session_id)
    return SuccessResponse(msg="强制下线成功")


@OnlineRouter.delete("/clear", summary="清除所有在线用户", response_model=ResponseSchema[None], dependencies=[Security(AuthPermission(["module_monitor:online:delete"]))])
async def clear_online_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
) -> JSONResponse:
    await OnlineService.clear_online(redis=redis)
    return SuccessResponse(msg="清除所有在线用户成功")


@OnlineRouter.get("/stats", summary="获取仪表盘统计数据", response_model=ResponseSchema[DashboardStatsSchema])
async def get_dashboard_stats_controller(
    db: Annotated[AsyncSession, Depends(db_getter)],
    redis: Annotated[Redis, Depends(redis_getter)],
    _auth: Annotated[AuthSchema, Security(AuthPermission(["module_monitor:dashboard:query"]))],
) -> JSONResponse:
    data = await OnlineService.get_dashboard_stats(db=db, redis=redis)
    return SuccessResponse(data=data, msg="获取仪表盘统计成功")
