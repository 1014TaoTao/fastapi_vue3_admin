# -*- coding: utf-8 -*-

import time
from typing import Union, Dict
from fastapi import APIRouter, Depends, Request, BackgroundTasks, WebSocket
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from aioredis import Redis

from app.config.setting import settings
from app.common.response import ErrorResponse, SuccessResponse
from app.api.v1.services.system.auth_service import LoginService, CaptchaService
from app.api.v1.schemas.system.auth_schema import (
    CaptchaOutSchema,
    JWTOutSchema,
    RefreshTokenPayloadSchema,
    LogoutPayloadSchema,
)
from app.core.dependencies import db_getter, get_current_user, redis_getter
from app.core.router_class import OperationLogRoute
from app.core.security import CustomOAuth2PasswordRequestForm
from app.core.logger import logger


router = APIRouter(route_class=OperationLogRoute)


@router.post("/login", summary="登录", description="登录", response_model=JWTOutSchema)
async def login_for_access_token_controller(
    request: Request,
    redis: Redis = Depends(redis_getter),
    login_form: CustomOAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(db_getter),
) -> Union[JSONResponse, Dict]:
    login_token = await LoginService.authenticate_user_service(
        request=request, redis=redis, login_form=login_form, db=db
    )

    logger.info(f"用户{login_form.username}登录成功")

    # 如果是文档请求，则不记录日志:http://localhost:8000/api/v1/docs
    if settings.DOCS_URL in request.headers.get("referer", ""):
        return login_token.model_dump()
    return SuccessResponse(data=login_token.model_dump(), msg="登录成功")


@router.post(
    "/token/refresh",
    summary="刷新token",
    description="刷新token",
    response_model=JWTOutSchema,
    dependencies=[Depends(get_current_user)],
)
async def get_new_token_controller(
    request: Request,
    payload: RefreshTokenPayloadSchema,
    db: AsyncSession = Depends(db_getter),
    redis: Redis = Depends(redis_getter),
) -> JSONResponse:
    # 解析当前的访问Token以获取用户名
    new_token = await LoginService.refresh_token_service(
        db=db, request=request, redis=redis, refresh_token=payload
    )
    token_dict = new_token.model_dump()
    logger.info(f"刷新token成功: {token_dict}")
    return SuccessResponse(data=token_dict, msg="刷新成功")


@router.post(
    "/captcha/get",
    summary="获取验证码",
    description="获取登录验证码",
    response_model=CaptchaOutSchema,
)
async def get_captcha_for_login_controller(
    redis: Redis = Depends(redis_getter),
) -> JSONResponse:
    # 获取验证码
    captcha = await CaptchaService.get_captcha_service(redis=redis)
    logger.info(f"获取验证码成功")
    return SuccessResponse(data=captcha, msg="获取验证码成功")


@router.post(
    "/logout",
    summary="退出登录",
    description="退出登录",
    dependencies=[Depends(get_current_user)],
)
async def logout_controller(
    payload: LogoutPayloadSchema, redis: Redis = Depends(redis_getter)
) -> JSONResponse:
    if await LoginService.logout_services_service(redis=redis, token=payload):
        logger.info("退出成功")
        return SuccessResponse(msg="退出成功")
    return ErrorResponse(msg="退出失败")


# 以下接口为预留，后期会用
@router.post("/background_tasks", summary="模拟fastapi自带后台任务-模拟流式响应")
async def stream_response__controller(background_tasks: BackgroundTasks, message: str):
    def task(message):
        for i in range(5):
            yield f"睡眠 {message} {i}\n"
            time.sleep(1)

    background_tasks.add_task(task, message)

    return StreamingResponse(
        data=task(message),
        headers={"X-Custom-Header": "Streaming-Response"},
        media_type="text/plain",
    )


@router.websocket("/ws", name="websocket")
async def websocket_endpoint_controller(websocket: WebSocket):
    # ws://127.0.0.1:8000/ws
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
