from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Security
from fastapi.responses import JSONResponse
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema
from app.core.dependencies import AuthPermission, db_getter, redis_getter
from app.core.router_class import OperationLogRoute

from .schema import ParamsOutSchema, ParamsUpdateSchema
from .service import ParamsService

ParamsRouter = APIRouter(route_class=OperationLogRoute, prefix="/param", tags=["参数管理"])


@ParamsRouter.put("/update/{id}", summary="修改参数", response_model=ResponseSchema[ParamsOutSchema])
async def update_param_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:param:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(description="参数ID", ge=1)],
    data: Annotated[ParamsUpdateSchema, Body(description="参数修改参数")],
) -> JSONResponse:
    result_dict: ParamsOutSchema = await ParamsService(auth, db).update(redis=redis, id=id, data=data)
    return SuccessResponse(data=result_dict, msg="更新参数成功")


@ParamsRouter.get("/info", summary="获取初始化缓存参数", response_model=ResponseSchema[list[ParamsOutSchema]])
async def get_init_config_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
) -> JSONResponse:
    result_dict: list[dict[str, Any]] = await ParamsService.get_init_cache(redis=redis)
    return SuccessResponse(data=result_dict, msg="获取初始化缓存参数成功")
