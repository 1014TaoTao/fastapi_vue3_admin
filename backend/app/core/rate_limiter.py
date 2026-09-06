"""全局 API 限流（fastapi-limiter 0.2.0 + pyrate-limiter）。

0.2.0 为破坏性重写：无 FastAPILimiter.init，直接构造 pyrate-limiter 的
Limiter（进程内内存桶，多 worker 时配额按进程独立）；默认按 IP+路由路径
计数，超限抛 HTTP 429。单路由可用 @skip_limiter 豁免（如监控探针）。

ApiRateLimiter 兼容修复：0.2.0 的 RateLimiter.__call__ 遍历 app.routes
并直接访问 route.path，而 FastAPI 0.138 include_router 的惰性挂载产物
_IncludedRouter 没有 path 属性，会抛 AttributeError——改为直接使用请求
scope 中的路径与端点，语义等价（IP + 完整路径计数、支持 _skip_limiter）。
"""

import json

from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter, WebSocketRateLimiter
from pyrate_limiter import Limiter, Rate
from starlette.websockets import WebSocket

from app.config.setting import settings

limiter = Limiter(Rate(settings.API_RATE_LIMIT_TIMES, settings.API_RATE_LIMIT_INTERVAL_MS))


class ApiRateLimiter(RateLimiter):
    """兼容 FastAPI 0.138 惰性路由挂载的限流依赖。"""

    async def __call__(self, request: Request, response: Response):
        endpoint = request.scope.get("endpoint")
        if endpoint is not None and getattr(endpoint, "_skip_limiter", False):
            return
        rate_key = await self.identifier(request)
        key = f"{rate_key}:{request.scope['path']}"
        success = await self.limiter.try_acquire_async(key, blocking=self.blocking)
        if not success:
            return await self.callback(request, response)


# 挂载点：api_v1 全局 dependencies（见 app/api/v1/routers.py）
api_rate_limiter = ApiRateLimiter(limiter=limiter)


async def ws_rate_limit_callback(ws: WebSocket) -> None:
    """WS 超限回调：WebSocket 中不能抛 HTTPException，改为下发提示并断开（1008 策略违规）。"""
    await ws.send_text(json.dumps({"type": "rate_limited", "message": "发送过于频繁，请稍后再试"}))
    await ws.close(code=1008, reason="rate limited")


# WS 聊天限流：每条对话消息在接收处调用一次（stop 等控制指令不限流）
ws_rate_limiter = WebSocketRateLimiter(
    limiter=Limiter(Rate(settings.WS_RATE_LIMIT_TIMES, settings.WS_RATE_LIMIT_INTERVAL_MS)),
    callback=ws_rate_limit_callback,
)
