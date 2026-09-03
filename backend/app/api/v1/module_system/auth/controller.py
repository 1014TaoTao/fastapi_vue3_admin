"""认证控制器。

TODO(限流细化): /login、/oauth/*、/captcha/* 目前共享全局限流，建议为各端点配置
独立的 RateLimiter——登录按 IP+用户名限流防爆破、OAuth 与验证码按 IP 限流防遍历。
"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Path, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ErrorResponse, RedirectContentResponse, ResponseSchema, SuccessResponse
from app.config.setting import settings
from app.core.base_schema import JWTOutSchema
from app.core.dependencies import db_getter, get_current_user, redis_getter
from app.core.logger import logger
from app.core.router_class import OperationLogRoute
from app.core.security import CustomOAuth2PasswordRequestForm

from .oauth_service import OAuthProvider, finish_oauth_login, start_oauth_login
from .schema import (
    CaptchaOutSchema,
    LoginOutSchema,
    SliderCompleteOutSchema,
    SliderCompleteSchema,
    WxLoginSchema,
    WxPhoneLoginSchema,
    WxQrCodeOutSchema,
    WxQrCodeSchema,
)
from .service import (
    CaptchaService,
    LoginService,
)
from .wx_mini_service import get_qrcode, wx_mini_login, wx_mini_phone_login

AuthRouter = APIRouter(route_class=OperationLogRoute, prefix="/auth", tags=["认证授权"])


@AuthRouter.post("/login", summary="登录", response_model=LoginOutSchema)
async def login_for_access_token_controller(
    request: Request,
    background_tasks: BackgroundTasks,
    redis: Annotated[Redis, Depends(redis_getter)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    login_form: Annotated[CustomOAuth2PasswordRequestForm, Depends()],
) -> JSONResponse | LoginOutSchema:
    login_result = await LoginService.authenticate_user(request=request, redis=redis, login_form=login_form, db=db, background_tasks=background_tasks)

    logger.info(f"用户{login_form.username}登录成功")

    if settings.DOCS_URL in request.headers.get("referer", ""):
        return login_result
    return SuccessResponse(data=login_result, msg="登录成功")


@AuthRouter.post("/token/refresh", summary="刷新token", response_model=ResponseSchema[JWTOutSchema])
async def get_new_token_controller(
    db: Annotated[AsyncSession, Depends(db_getter)],
    redis: Annotated[Redis, Depends(redis_getter)],
    payload: Annotated[str, Body(description="刷新token参数")],
) -> JSONResponse:
    new_token = await LoginService.refresh_token(db=db, redis=redis, refresh_token=payload)
    return SuccessResponse(data=new_token, msg="刷新成功")


@AuthRouter.get("/captcha/get", summary="获取验证码", response_model=ResponseSchema[CaptchaOutSchema])
async def get_captcha_for_login_controller(
    request: Request,
    redis: Annotated[Redis, Depends(redis_getter)],
) -> JSONResponse:
    captcha = await CaptchaService.get_captcha(redis=redis, request=request)
    return SuccessResponse(data=captcha, msg="获取验证码成功")


@AuthRouter.post("/captcha/slider/complete", summary="滑块验证完成", response_model=ResponseSchema[SliderCompleteOutSchema])
async def slider_complete_controller(
    request: Request,
    redis: Annotated[Redis, Depends(redis_getter)],
    body: SliderCompleteSchema,
) -> JSONResponse:
    result = await CaptchaService.slider_complete(redis=redis, request=request, captcha_key=body.captcha_key)
    return SuccessResponse(data=result, msg="滑块验证成功")


@AuthRouter.post("/logout", summary="退出登录", response_model=ResponseSchema[None], dependencies=[Depends(get_current_user)])
async def logout_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    payload: Annotated[str, Body(description="退出登录参数")],
) -> JSONResponse:
    if await LoginService.logout(redis=redis, token=payload):
        logger.info("退出成功")
        return SuccessResponse(msg="退出成功")
    return ErrorResponse(msg="退出失败")


@AuthRouter.get("/oauth/{provider}/login", summary="第三方OAuth跳转")
async def oauth_login_redirect_controller(
    request: Request,
    redis: Annotated[Redis, Depends(redis_getter)],
    provider: Annotated[OAuthProvider, Path(description="wechat | qq | github | gitee")],
    redirect_uri: Annotated[str | None, Query(description="OAuth 完成后浏览器回到的前端登录页完整 URL")] = None,
) -> RedirectResponse:
    """跳转第三方授权页；入参缺失或渠道密钥未配置时自动降级为错误重定向。"""
    url = await start_oauth_login(
        request=request,
        redis=redis,
        provider=provider,
        redirect_uri=redirect_uri,
    )
    return RedirectContentResponse(url=url, status_code=302)


@AuthRouter.get("/oauth/{provider}/callback", summary="第三方OAuth回调", include_in_schema=False)
async def oauth_callback_controller(
    request: Request,
    background_tasks: BackgroundTasks,
    redis: Annotated[Redis, Depends(redis_getter)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    provider: Annotated[OAuthProvider, Path(description="wechat | qq | github | gitee")],
    code: Annotated[str | None, Query(description="OAuth 授权码")] = None,
    state: Annotated[str | None, Query(description="OAuth 状态参数")] = None,
) -> RedirectResponse:
    """处理第三方平台回调并回跳前端登录页（成功携带令牌 / 失败携带原因）。"""
    url = await finish_oauth_login(
        request=request,
        redis=redis,
        db=db,
        provider=provider,
        code=code,
        state=state,
        background_tasks=background_tasks,
    )
    return RedirectContentResponse(url=url, status_code=302)


# =================================================== #
# *************** 微信小程序登录端点 ***************** #
# =================================================== #


@AuthRouter.post("/wx-login", summary="微信小程序登录", response_model=ResponseSchema[LoginOutSchema])
async def wx_mini_login_controller(
    request: Request,
    redis: Annotated[Redis, Depends(redis_getter)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    body: WxLoginSchema,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """微信小程序登录：前端 uni.login 的 code 换取 openid 后签发 JWT。"""
    result = await wx_mini_login(
        request=request,
        redis=redis,
        db=db,
        code=body.code,
        nickname=body.nickname,
        avatar=body.avatar,
        background_tasks=background_tasks,
    )
    return SuccessResponse(data=result, msg="登录成功")


@AuthRouter.post("/wx-phone-login", summary="微信小程序手机号登录", response_model=ResponseSchema[LoginOutSchema])
async def wx_mini_phone_login_controller(
    request: Request,
    redis: Annotated[Redis, Depends(redis_getter)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    body: WxPhoneLoginSchema,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """微信小程序手机号登录：getPhoneNumber 回调的 code 换取手机号后签发 JWT。"""
    result = await wx_mini_phone_login(
        request=request,
        redis=redis,
        db=db,
        code=body.code,
        background_tasks=background_tasks,
    )
    return SuccessResponse(data=result, msg="登录成功")


@AuthRouter.post("/wx-qrcode/generate", summary="生成小程序码", response_model=ResponseSchema[WxQrCodeOutSchema])
async def wx_qrcode_generate_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    body: WxQrCodeSchema,
) -> JSONResponse:
    """生成无限制小程序码。

    调用微信 getwxacodeunlimit 接口生成小程序码图片，
    返回 base64 编码的图片数据，前端可直接用于 Canvas 绘制或显示。
    """
    import base64

    image_bytes = await get_qrcode(
        redis=redis,
        scene=body.scene,
        page=body.page,
        width=body.width,
    )

    # 转 base64 data URI，前端可直接作为图片 src 使用
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:image/png;base64,{b64}"

    return SuccessResponse(
        data=WxQrCodeOutSchema(url=data_uri),
        msg="生成成功",
    )
