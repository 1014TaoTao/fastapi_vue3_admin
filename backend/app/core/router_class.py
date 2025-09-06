# -*- coding: utf-8 -*-

import time
from typing import Any, Callable, Coroutine
from fastapi import Request, Response
from fastapi.routing import APIRoute
from user_agents import parse
import json

from app.core.database import session_connect
from app.config.setting import settings
from app.utils.ip_local_util import IpLocalUtil
from app.api.v1.module_system.auth.schema import AuthSchema
from app.api.v1.module_system.log.schema import OperationLogCreateSchema
from app.api.v1.module_system.log.service import OperationLogService

"""
在 FastAPI 中，route_class 参数用于自定义路由的行为。
通过设置 route_class，你可以定义一个自定义的路由类，从而在每个路由处理之前或之后执行特定的操作。
这对于日志记录、权限验证、性能监控等场景非常有用。
"""
class OperationLogRoute(APIRoute):
    """操作日志路由装饰器"""
    
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            start_time = time.time()
            # 请求前的处理
            response: Response = await original_route_handler(request)
            
            # 请求后的处理
            if not settings.OPERATION_LOG_RECORD:
                return response
            if request.method not in settings.OPERATION_RECORD_METHOD:
                return response
            route: APIRoute = request.scope.get("route")
            if route.name in settings.IGNORE_OPERATION_FUNCTION:
                return response
            
            user_agent = parse(request.headers.get("user-agent"))
            payload = b"{}"
            req_content_type = request.headers.get("Content-Type", "")
            
            if req_content_type and (
                req_content_type.startswith('multipart/form-data') or req_content_type.startswith('application/x-www-form-urlencoded')
            ):
                form_data = await request.form()
                oper_param = '\n'.join([f'{k}: {v}' for k, v in form_data.items()])
                payload = oper_param  # 直接使用字符串格式的参数
            else:
                payload = await request.body()
                path_params = request.path_params
                oper_param = {}
                
                # 处理请求体数据
                if payload:
                    try:
                        oper_param['body'] = json.loads(payload.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        oper_param['body'] = payload.decode('utf-8', errors='ignore')
                
                # 处理路径参数
                if path_params:
                    oper_param['path_params'] = dict(path_params)
                
                payload = json.dumps(oper_param, ensure_ascii=False)
                # payload = str(oper_param)

                # 日志表请求参数字段长度最大为2000，因此在此处判断长度
                if len(payload) > 2000:
                    payload = '请求参数过长'
            
            response_data = response.body if "application/json" in response.headers.get("Content-Type", "") else b"{}"
            process_time = f"{(time.time() - start_time):.4f}s"

            # 获取当前用户ID,如果是登录接口则为空
            log_type = 1 # 1:登录日志 2:操作日志
            current_user_id = None
            if "user_id" in request.scope:
                current_user_id = request.scope.get("user_id")
                log_type = 2
            
            request_ip = None
            x_forwarded_for = request.headers.get('X-Forwarded-For')
            if x_forwarded_for:
                # 取第一个 IP 地址，通常为客户端真实 IP
                request_ip = x_forwarded_for.split(',')[0].strip()
            else:
                # 若没有 X-Forwarded-For 头，则使用 request.client.host
                request_ip = request.client.host
            
            login_location = await IpLocalUtil.get_ip_location(request_ip)
            
            # 判断请求是否来自api文档
            request_from_swagger = (
                request.headers.get('referer').endswith('docs') if request.headers.get('referer') else False
            )
            request_from_redoc = (
                request.headers.get('referer').endswith('redoc') if request.headers.get('referer') else False
            )
            
            if request_from_swagger or request_from_redoc:
                pass
            else:
                async with session_connect() as session:
                    async with session.begin():
                        auth = AuthSchema(db=session)
                        
                        await OperationLogService.create_log_service(data=OperationLogCreateSchema(
                            type = log_type,
                            request_path = request.url.path,
                            request_method = request.method,
                            request_payload = payload,
                            request_ip = request_ip,
                            login_location=login_location,
                            request_os = user_agent.os.family,
                            request_browser = user_agent.browser.family,
                            response_code = response.status_code,
                            response_json = response_data.decode(),
                        process_time = process_time,
                        description = route.summary,
                        creator_id = current_user_id
                    ), auth = auth) 
            
            return response

        return custom_route_handler
