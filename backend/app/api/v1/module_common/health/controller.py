import asyncio
from collections.abc import AsyncIterable
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.sse import EventSourceResponse, ServerSentEvent

from app.common.enums import RET
from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.config.setting import settings
from app.core.router_class import OperationLogRoute

from .schema import HealthOut, ReadinessOut
from .service import HEALTH_STREAM_INTERVAL, HealthService

HealthRouter = APIRouter(route_class=OperationLogRoute, prefix="/health", tags=["健康检查"])


@HealthRouter.get("/check", summary="健康检查", response_model=ResponseSchema[HealthOut])
async def health_check() -> JSONResponse:
    """基础健康检查

    参数:
    - 无

    返回:
    - SuccessResponse: 包含进程存活状态、启动时间、版本号的 JSON 响应。
    """
    return SuccessResponse(
        data=HealthOut(
            status=1,
            timestamp=datetime.now().isoformat(),
            version=settings.VERSION,
            uptime_seconds=HealthService.get_uptime(),
        ),
        msg="系统健康",
    )


@HealthRouter.get("/live", summary="存活探针", response_model=ResponseSchema[HealthOut])
async def liveness_check() -> JSONResponse:
    """存活探针

    参数:
    - 无

    返回:
    - SuccessResponse: 包含进程存活状态、启动时间、版本号的 JSON 响应。
    """
    return SuccessResponse(
        data=HealthOut(
            status=1,
            timestamp=datetime.now().isoformat(),
            version=settings.VERSION,
            uptime_seconds=HealthService.get_uptime(),
        ),
        msg="进程存活",
    )


@HealthRouter.get("/ready", summary="就绪探针", response_model=ResponseSchema[ReadinessOut])
async def readiness_check(request: Request) -> JSONResponse:
    """就绪探针

    参数:
    - request (Request): FastAPI 请求对象，用于获取 Redis 客户端。

    返回:
    - SuccessResponse | ErrorResponse: 依赖就绪时返回 200，未就绪返回 503。
    """
    redis = getattr(request.app.state, "redis", None)
    dependencies = await HealthService.check_dependencies(redis)

    # 判断总体状态
    all_ok = all(d.status == 1 for d in dependencies.values())

    payload = ReadinessOut(
        status=1 if all_ok else 0,
        timestamp=datetime.now().isoformat(),
        version=settings.VERSION,
        uptime_seconds=HealthService.get_uptime(),
        dependencies=dependencies,
        disk_usage=HealthService.get_disk_usage(),
    )

    if all_ok:
        return SuccessResponse(data=payload, msg="依赖就绪")

    return ErrorResponse(
        data=payload,
        msg="依赖未就绪",
        code=RET.SERVICE_UNAVAILABLE.code,
        status_code=503,
        success=False,
    )


# ============================================================
# SSE 健康状态实时推送
# ============================================================


@HealthRouter.get("/stream", summary="健康状态实时推送", response_class=EventSourceResponse)
async def health_stream(request: Request) -> AsyncIterable[ServerSentEvent]:
    """SSE 实时推送健康状态，每 30 秒推送一次，客户端无需轮询 /ready。"""
    redis = getattr(request.app.state, "redis", None)
    yield ServerSentEvent(data=await HealthService.collect_status(redis), event="health")

    while True:
        await asyncio.sleep(HEALTH_STREAM_INTERVAL)
        yield ServerSentEvent(data=await HealthService.collect_status(redis), event="health")
