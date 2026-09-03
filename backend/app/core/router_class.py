import json
import time
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any

from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.background import BackgroundTask

from app.config.setting import settings
from app.core.logger import logger
from app.utils.ip_local_util import get_client_ip

# 操作日志落库实现由 api 层登记注入（core 不反向依赖 app.api.*）
OperationLogWriter = Callable[[dict[str, Any]], Awaitable[None]]
_operation_log_writer: OperationLogWriter | None = None


def set_operation_log_writer(writer: OperationLogWriter) -> None:
    """登记操作日志落库实现（应用启动时由 api 层调用）。"""
    global _operation_log_writer
    _operation_log_writer = writer

_WRITE_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

# 操作日志脱敏：命中键名（不区分大小写）的值替换为掩码，防止凭据明文入库。
# 有日志查看权限的人不应因此获得全员密码/token。
_SENSITIVE_KEYS = {
    "password",
    "passwd",
    "old_password",
    "new_password",
    "confirm_password",
    "captcha_key",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "secret",
    "client_secret",
    "secret_key",
    "authorization",
}
_REDACTED = "******"


def _redact_sensitive(obj: Any) -> Any:
    """递归脱敏 dict/list 中的敏感字段（键名匹配不区分大小写）。"""
    if isinstance(obj, dict):
        return {k: (_REDACTED if str(k).lower() in _SENSITIVE_KEYS else _redact_sensitive(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact_sensitive(item) for item in obj]
    return obj

# （通常在登录前调用，没有 JWT token）
_PUBLIC_WRITE_PATHS: set[str] = {
    "/auth/login",
    "/auth/token/refresh",
    "/auth/captcha/slider/complete",
    "/auth/user/register",
}


async def _write_operation_log_async(log_data: dict) -> None:
    """委托已登记的写入器落库操作日志（未登记时降级为告警，不阻塞响应）。"""
    if _operation_log_writer is None:
        logger.warning("操作日志写入器未登记，跳过落库: path={}", log_data.get("request_path"))
        return
    try:
        await _operation_log_writer(log_data)
    except Exception:
        logger.exception("操作日志写入失败: path={}", log_data.get("request_path"))


class OperationLogRoute(APIRoute):
    """操作日志路由 — 自动记录请求/响应并后台异步写入。

    根据 HTTP 方法判断：
    - 写方法 (POST/PUT/DELETE/PATCH)：注入租户写权限检查
    - 读方法 (GET/HEAD/OPTIONS)：不注入
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        methods = getattr(self, "methods", set())
        if methods & _WRITE_METHODS and self.path not in _PUBLIC_WRITE_PATHS:
            if self.dependencies is None:
                self.dependencies = []

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            start = time.perf_counter()
            response: Response = await original_route_handler(request)

            if request.method not in settings.OPERATION_RECORD_METHOD:
                return response
            route: APIRoute = request.scope.get("route", None)

            try:
                oper_param: dict[str, Any] = {}
                content_type = request.headers.get("Content-Type", "")
                if content_type.startswith(("multipart/form-data", "application/x-www-form-urlencoded")):
                    try:
                        form_data = await request.form()
                        # 过滤 UploadFile 对象并脱敏凭据字段
                        oper_param["form"] = {
                            k: (_REDACTED if k.lower() in _SENSITIVE_KEYS else v)
                            for k, v in form_data.items()
                            if not hasattr(v, "read")
                        }
                    except Exception:
                        oper_param["form"] = {}
                else:
                    payload = await request.body()
                    if payload:
                        try:
                            oper_param["body"] = _redact_sensitive(json.loads(payload.decode()))
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            oper_param["body"] = payload.decode("utf-8", errors="ignore")

                if request.path_params:
                    oper_param["path_params"] = dict(request.path_params)

                log_payload = json.dumps(oper_param, ensure_ascii=False)
                if len(log_payload) > 2000:
                    log_payload = "请求参数过长"

                is_json = "application/json" in response.headers.get("Content-Type", "")
                if is_json:
                    # 响应体同样脱敏：登录/刷新响应含 access_token，明文入库等于 token 泄露
                    try:
                        response_data = json.dumps(_redact_sensitive(json.loads(response.body.decode())), ensure_ascii=False).encode()
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        response_data = b"{}"
                else:
                    response_data = b"{}"

                log_data: dict[str, Any] = {
                    "username": getattr(getattr(request.state, "ctx", None), "user_username", "unknown"),
                    "request_path": request.url.path,
                    "request_method": request.method,
                    "request_payload": log_payload,
                    "response_code": response.status_code,
                    "response_json": bytes(response_data).decode(),
                    "process_time": f"{(time.perf_counter() - start):.2f}s",
                    "description": route.summary if route else "",
                    "request_ip": get_client_ip(request),
                }
                response.background = BackgroundTask(_write_operation_log_async, log_data)
            except Exception:
                logger.warning("操作日志采集异常: {}", request.url.path, exc_info=True)
            return response

        return custom_route_handler
