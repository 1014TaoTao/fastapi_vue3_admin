# -*- coding: utf-8 -*-

import time
from typing import Dict, List, Union
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp
from starlette.requests import Request
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.base import Response, BaseHTTPMiddleware, RequestResponseEndpoint

from app.common.response import ErrorResponse
from app.config.setting import settings
from app.core.logger import logger
from app.core.exceptions import CustomException


class CustomCORSMiddleware(CORSMiddleware):
    """CORS跨域中间件"""
    def __init__(self, app: ASGIApp) -> None:
        CORSMiddlewareConfig: Dict[str, Union[List[str], bool]] = {
            "allow_origins": settings.ALLOW_ORIGINS,
            "allow_methods": settings.ALLOW_METHODS,
            "allow_headers": settings.ALLOW_HEADERS,
            "allow_credentials": settings.ALLOW_CREDENTIALS
        }
        super().__init__(app, **CORSMiddlewareConfig)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    记录请求日志中间件: 提供一个基础的中间件类，允许你自定义请求和响应处理逻辑。
    """
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()

        logger.info(
            f"请求来源: {request.client.host}, "
            f"请求方法: {request.method}, "
            f"请求路径: {request.url.path}, "
            f"客户端IP: {request.client.host}"
        )
        
        try:
            response = await call_next(request)
            process_time = round(time.time() - start_time, 5)
            response.headers["X-Process-Time"] = str(process_time)
            
            logger.info(
                f"会话ID: {request.scope.get('session_id')}, "
                f"响应状态: {response.status_code}, "
                f"响应内容长度: {response.headers.get('content-length', '0')}, "
                f"处理时间: {process_time}s"
            )
            
            return response
        
        except CustomException as e:
            logger.error(f"系统异常: {str(e)}")
            return ErrorResponse(msg=f"系统异常，请联系管理员: {str(e)}")


class DemoEnvMiddleware(BaseHTTPMiddleware):
    """演示环境中间件"""
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        
        if settings.DEMO_ENABLE and request.method != "GET":
            path = request.scope.get("path")
            client_ip = request.client.host
            user_username = request.scope.get("user_username")

            # 检查IP是否在白名单，或路径是否在白名单，或用户是否在白名单
            if (client_ip in settings.DEMO_IP_WHITE_LIST or 
                path in settings.DEMO_WHITE_LIST_PATH or 
                (user_username and user_username in settings.DEMO_USER_WHITE_LIST)):
                return await call_next(request)
            
            else:
                try:
                    response = await call_next(request)
                    
                    # 现在检查用户是否有权限执行操作
                    user_username = request.scope.get("user_username")
                    if user_username and user_username not in settings.DEMO_USER_WHITE_LIST:
                        # 如果用户没有权限，返回错误响应
                        return ErrorResponse(msg="演示环境，禁止操作")
                    
                    return response
                except Exception as e:
                    # 处理可能的异常
                    raise e

        return await call_next(request)


class CustomGZipMiddleware(GZipMiddleware):
    """GZip压缩中间件"""
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(
            app,
            minimum_size=settings.GZIP_MIN_SIZE,
            compresslevel=settings.GZIP_COMPRESS_LEVEL
        )

