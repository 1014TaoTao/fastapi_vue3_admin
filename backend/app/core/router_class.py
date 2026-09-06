import json
import time
from collections.abc import Callable, Coroutine
from typing import Any, TypedDict

from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.background import BackgroundTask

from app.config.setting import settings
from app.core.database import async_db_session
from app.core.logger import logger
from app.utils.ip_local_util import get_client_ip

_SENSITIVE_KEYS: set[str] = {
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


class OperationLogRecord(TypedDict):
    """操作日志落库记录（字段与 OperationLogModel 对应，定义与消费同处）。"""

    username: str
    request_path: str
    request_method: str
    request_payload: str
    response_code: int
    response_json: str
    process_time: str
    description: str
    request_ip: str


async def _write_operation_log_async(log_data: OperationLogRecord) -> None:
    """落库操作日志（BackgroundTask 中执行；失败仅告警，不影响响应）。"""
    from app.modules.system.log.model import OperationLogModel  # 延迟导入：core 导入期不依赖业务层（守卫不变式 3）

    try:
        async with async_db_session() as session, session.begin():
            session.add(OperationLogModel(**log_data))
    except Exception:
        logger.exception("操作日志写入失败: path={}", log_data.get("request_path"))


class OperationLogRoute(APIRoute):
    """操作日志路由 — 按配置的 HTTP 方法自动记录请求/响应并后台异步写入。"""

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
                        oper_param["form"] = {k: (_REDACTED if k.lower() in _SENSITIVE_KEYS else v) for k, v in form_data.items() if not hasattr(v, "read")}
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
                        response_data = json.dumps(_redact_sensitive(json.loads(bytes(response.body).decode())), ensure_ascii=False).encode()
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        response_data = b"{}"
                else:
                    response_data = b"{}"

                log_data: OperationLogRecord = {
                    "username": str(getattr(getattr(request.state, "ctx", None), "user_username", None) or "unknown"),
                    "request_path": request.url.path,
                    "request_method": request.method,
                    "request_payload": log_payload,
                    "response_code": response.status_code,
                    "response_json": bytes(response_data).decode(),
                    "process_time": f"{(time.perf_counter() - start):.2f}s",
                    "description": (route.summary or "") if route else "",
                    "request_ip": get_client_ip(request),
                }
                response.background = BackgroundTask(_write_operation_log_async, log_data)
            except Exception:
                logger.warning("操作日志采集异常: {}", request.url.path, exc_info=True)
            return response

        return custom_route_handler
