import asyncio
from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.sse import EventSourceResponse, ServerSentEvent

from app.common.response import ResponseSchema, SuccessResponse
from app.config.setting import Settings, get_settings
from app.core.router_class import OperationLogRoute

from .schema import ServiceInfoOut
from .service import HealthService

HealthRouter = APIRouter(route_class=OperationLogRoute, prefix="/health", tags=["健康检查"])


@HealthRouter.get("/check", summary="健康检查", response_model=ResponseSchema[ServiceInfoOut])
async def health_check(request: Request, settings: Annotated[Settings, Depends(get_settings)]) -> JSONResponse:
    """健康检查：实时探测 DB / Redis 网络连通状态。"""
    redis: Any | None = getattr(request.app.state, "redis", None)
    info = await HealthService.collect(redis)
    ok = info.db_status == 1 and info.redis_status == 1
    return SuccessResponse(data=info, msg=f"系统健康-{settings.VERSION}" if ok else f"服务异常-{settings.VERSION}")



@HealthRouter.get("/stream", summary="健康检查实时流(SSE)", response_class=EventSourceResponse)
async def health_stream_controller(
    request: Request,
) -> AsyncGenerator[ServerSentEvent, None]:
    """健康检查实时流（SSE）：每 30s 实时探测 DB / Redis 后推送一帧。"""
    redis: Any | None = getattr(request.app.state, "redis", None)
    while True:
        info = await HealthService.collect(redis)
        yield ServerSentEvent(data=info.model_dump_json())
        await asyncio.sleep(30) # SSE 推送间隔（秒）

