"""第三方 OAuth2 登录（微信开放平台扫码、QQ、GitHub、Gitee）。

各平台需在开放平台登记「授权回调域 / redirect_uri」为：
  {API}/system/auth/oauth/{provider}/callback
例如：https://your-domain.com/api/v1/system/auth/oauth/github/callback

环境变量见 Settings 中 OAUTH_* 字段。
"""

import json
import secrets
from typing import Any, Literal
from urllib.parse import quote, urlencode

import httpx
from fastapi import BackgroundTasks, Request
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_system.user.crud import UserCRUD
from app.api.v1.module_system.user.model import UserModel
from app.config.setting import settings
from app.core.base_schema import AuthSchema, JWTOutSchema
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.core.redis_crud import RedisCURD

from .service import LoginService, auto_register_login_user, sanitize_login_name

OAuthProvider = Literal["wechat", "qq", "github", "gitee"]

STATE_PREFIX = "oauth_state:"


def _callback_url(request: Request, provider: OAuthProvider) -> str:
    root = str(request.base_url).rstrip("/")
    # 域名白名单校验：防止 Host 头注入攻击重定向到恶意域名
    allowed_hosts = settings.OAUTH_ALLOWED_HOSTS
    if allowed_hosts and allowed_hosts != ["*"]:
        host = request.url.hostname
        if host is None or not any(host == allowed_host or host.endswith("." + allowed_host) for allowed_host in allowed_hosts):
            raise CustomException(msg="非法的 OAuth 回调域名")
    return f"{root}/system/auth/oauth/{provider}/callback"


def _frontend_error_redirect(frontend_base: str, message: str) -> str:
    sep = "&" if "?" in frontend_base else "?"
    return f"{frontend_base}{sep}oauth_error={quote(message, safe='')}"


def _frontend_success_redirect(frontend_base: str, access_token: str, refresh_token: str, token_type: str) -> str:
    q = urlencode(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": token_type,
        },
    )
    sep = "&" if "?" in frontend_base else "?"
    return f"{frontend_base}{sep}{q}"


def _require_credentials(provider: OAuthProvider) -> tuple[str, str]:
    if provider == "github":
        cid, sec = settings.OAUTH_GITHUB_CLIENT_ID, settings.OAUTH_GITHUB_CLIENT_SECRET
    elif provider == "gitee":
        cid, sec = settings.OAUTH_GITEE_CLIENT_ID, settings.OAUTH_GITEE_CLIENT_SECRET
    elif provider == "wechat":
        cid, sec = settings.OAUTH_WECHAT_OPEN_APP_ID, settings.OAUTH_WECHAT_OPEN_APP_SECRET
    elif provider == "qq":
        cid, sec = settings.OAUTH_QQ_APP_ID, settings.OAUTH_QQ_APP_SECRET
    else:
        raise CustomException(msg="不支持的 OAuth 渠道")
    if not cid or not sec:
        raise CustomException(msg=f"{provider} OAuth 未配置（客户端密钥为空）")
    return cid, sec


def build_authorize_url(
    *,
    provider: OAuthProvider,
    callback_url: str,
    state: str,
) -> str:
    """构造跳转至第三方授权页的 URL。"""
    cid, _ = _require_credentials(provider)

    if provider == "github":
        params = {
            "client_id": cid,
            "redirect_uri": callback_url,
            "scope": "user:email",
            "state": state,
        }
        return "https://github.com/login/oauth/authorize?" + urlencode(params)

    if provider == "gitee":
        params = {
            "client_id": cid,
            "redirect_uri": callback_url,
            "response_type": "code",
            "state": state,
        }
        return "https://gitee.com/oauth/authorize?" + urlencode(params)

    if provider == "wechat":
        params = {
            "appid": cid,
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": "snsapi_login",
            "state": state,
        }
        return "https://open.weixin.qq.com/connect/qrconnect?" + urlencode(params) + "#wechat_redirect"

    if provider == "qq":
        params = {
            "response_type": "code",
            "client_id": cid,
            "redirect_uri": callback_url,
            "state": state,
            "scope": "get_user_info",
        }
        return "https://graph.qq.com/oauth2.0/authorize?" + urlencode(params)

    raise CustomException(msg="不支持的 OAuth 渠道")


async def _http_json(method: str, url: str, **kwargs: Any) -> Any:
    timeout = getattr(settings, "HTTPX_DEFAULT_TIMEOUT", 15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.request(method, url, **kwargs)
        r.raise_for_status()
        try:
            return r.json()
        except json.JSONDecodeError:
            text = r.text
            logger.error(f"OAuth 非 JSON 响应: {text[:500]}")
            raise CustomException(msg="OAuth 接口返回异常")


async def _http_text(method: str, url: str, **kwargs: Any) -> str:
    timeout = getattr(settings, "HTTPX_DEFAULT_TIMEOUT", 15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.request(method, url, **kwargs)
        r.raise_for_status()
        return r.text


async def exchange_github_token(client_id: str, client_secret: str, code: str, redirect_uri: str) -> str:
    data = await _http_json(
        "POST",
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        },
    )
    if not isinstance(data, dict):
        raise CustomException(msg="GitHub token 响应格式错误")
    token = data.get("access_token")
    if not token:
        raise CustomException(msg=data.get("error_description") or "GitHub 换取令牌失败")
    return str(token)


async def exchange_gitee_token(client_id: str, client_secret: str, code: str, redirect_uri: str) -> str:
    qs = urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        },
    )
    data = await _http_json("GET", f"https://gitee.com/oauth/token?{qs}")
    if not isinstance(data, dict):
        raise CustomException(msg="Gitee token 响应格式错误")
    token = data.get("access_token")
    if not token:
        raise CustomException(msg=data.get("error_description") or "Gitee 换取令牌失败")
    return str(token)


async def exchange_wechat_token(app_id: str, secret: str, code: str) -> tuple[str, str]:
    qs = urlencode(
        {
            "appid": app_id,
            "secret": secret,
            "code": code,
            "grant_type": "authorization_code",
        },
    )
    data = await _http_json("GET", f"https://api.weixin.qq.com/sns/oauth2/access_token?{qs}")
    if not isinstance(data, dict):
        raise CustomException(msg="微信 token 响应格式错误")
    token = data.get("access_token")
    openid = data.get("openid")
    if not token or not openid:
        raise CustomException(msg=data.get("errmsg") or "微信换取令牌失败")
    return str(token), str(openid)


async def exchange_qq_token(client_id: str, client_secret: str, code: str, redirect_uri: str) -> tuple[str, str]:
    qs = urlencode(
        {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        },
    )
    text = await _http_text("GET", f"https://graph.qq.com/oauth2.0/token?{qs}")
    parts = dict(p.split("=", 1) for p in text.split("&") if "=" in p)
    token = parts.get("access_token")
    if not token:
        raise CustomException(msg="QQ 换取 access_token 失败")
    me = await _http_json(
        "GET",
        "https://graph.qq.com/oauth2.0/me",
        params={"access_token": token, "fmt": "json"},
    )
    if not isinstance(me, dict):
        raise CustomException(msg="QQ openid 响应格式错误")
    openid = me.get("openid")
    if not openid:
        raise CustomException(msg="QQ 获取 openid 失败")
    return str(token), str(openid)


async def fetch_github_profile(access_token: str) -> tuple[str, str, str | None]:
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    user = await _http_json("GET", "https://api.github.com/user", headers=headers)
    if not isinstance(user, dict):
        raise CustomException(msg="GitHub 用户信息格式错误")
    login = str(user.get("login") or "")
    name = str(user.get("name") or login or "github")
    email = user.get("email")
    if not email:
        emails = await _http_json("GET", "https://api.github.com/user/emails", headers=headers)
        if isinstance(emails, list):
            primary = next((e for e in emails if isinstance(e, dict) and e.get("primary")), None)
            if primary:
                email = primary.get("email")
    return login, name, email


async def fetch_gitee_profile(access_token: str) -> tuple[str, str, str | None]:
    user = await _http_json(
        "GET",
        "https://gitee.com/api/v5/user",
        params={"access_token": access_token},
    )
    if not isinstance(user, dict):
        raise CustomException(msg="Gitee 用户信息格式错误")
    login = str(user.get("login") or "")
    name = str(user.get("name") or login)
    email = user.get("email")
    return login, name, email


async def fetch_wechat_profile(access_token: str, openid: str) -> tuple[str, str]:
    qs = urlencode({"access_token": access_token, "openid": openid, "lang": "zh_CN"})
    user = await _http_json("GET", f"https://api.weixin.qq.com/sns/userinfo?{qs}")
    if not isinstance(user, dict):
        raise CustomException(msg="微信用户信息格式错误")
    nickname = str(user.get("nickname") or "wechat")
    unionid = user.get("unionid")
    oid = unionid or openid
    return str(oid), nickname


async def fetch_qq_profile(access_token: str, app_id: str, openid: str) -> tuple[str, str]:
    qs = urlencode(
        {
            "access_token": access_token,
            "oauth_consumer_key": app_id,
            "openid": openid,
        },
    )
    user = await _http_json("GET", f"https://graph.qq.com/user/get_user_info?{qs}")
    if not isinstance(user, dict):
        raise CustomException(msg="QQ 用户信息格式错误")
    if user.get("ret") not in (0, "0", None):
        raise CustomException(msg=user.get("msg") or "QQ 用户信息失败")
    nickname = str(user.get("nickname") or "qq")
    return openid, nickname


def _username_for_oauth(provider: OAuthProvider, unique_id: str) -> str:
    """生成符合注册规则的登录名：oauth_{provider}_{id}（清洗规则与微信小程序共用）。"""
    return sanitize_login_name(f"oauth_{provider}_{unique_id}")


async def ensure_oauth_user(
    *,
    db: AsyncSession,
    provider: OAuthProvider,
    unique_id: str,
    display_name: str,
) -> UserModel:
    auth = AuthSchema()
    username = _username_for_oauth(provider, unique_id)
    existing = await UserCRUD(auth, db).get(username=username)
    if existing:
        return existing
    user = await auto_register_login_user(
        db=db,
        username=username,
        display_name=display_name,
        fail_msg="OAuth 注册失败",
    )
    logger.info(f"OAuth 自动注册用户: {username} ({provider})")
    return user


async def complete_oauth_login(
    *,
    request: Request,
    redis: Redis,
    db: AsyncSession,
    provider: OAuthProvider,
    code: str,
    state: str,
    background_tasks: BackgroundTasks | None = None,
) -> tuple[JWTOutSchema, str]:
    rc = RedisCURD(redis)
    raw = await rc.get(f"{STATE_PREFIX}{state}")
    # 安全加固：state 一次性消费（read-then-delete）— 防止重放 / 跨上下文劫持
    await rc.delete(f"{STATE_PREFIX}{state}")
    if not raw:
        raise CustomException(msg="登录状态已失效，请重试")
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    payload = json.loads(raw)
    if payload.get("provider") != provider:
        raise CustomException(msg="OAuth 状态不匹配")

    frontend = str(payload.get("frontend_redirect") or "").strip()
    if not frontend:
        raise CustomException(msg="缺少前端回调地址")

    callback_url = _callback_url(request, provider)
    cid, csec = _require_credentials(provider)

    if provider == "github":
        access = await exchange_github_token(cid, csec, code, callback_url)
        login_k, name, _email = await fetch_github_profile(access)
        uid = login_k
    elif provider == "gitee":
        access = await exchange_gitee_token(cid, csec, code, callback_url)
        login_k, name, _email = await fetch_gitee_profile(access)
        uid = login_k
    elif provider == "wechat":
        access, openid = await exchange_wechat_token(cid, csec, code)
        uid, name = await fetch_wechat_profile(access, openid)
    elif provider == "qq":
        access, openid = await exchange_qq_token(cid, csec, code, callback_url)
        uid, name = await fetch_qq_profile(access, cid, openid)
    else:
        raise CustomException(msg="不支持的 OAuth 渠道")

    user = await ensure_oauth_user(db=db, provider=provider, unique_id=uid, display_name=name)
    try:
        user = await LoginService.prepare_user_for_login(db=db, user=user)
        login_type = f"oauth_{provider}"
        token = await LoginService.create_token(request=request, redis=redis, user=user, login_type=login_type, background_tasks=background_tasks)
        return token, frontend
    finally:
        await rc.delete(f"{STATE_PREFIX}{state}")


async def save_oauth_state(
    *,
    redis: Redis,
    state: str,
    provider: OAuthProvider,
    frontend_redirect: str,
) -> None:
    rc = RedisCURD(redis)
    ok = await rc.set(
        f"{STATE_PREFIX}{state}",
        json.dumps({"provider": provider, "frontend_redirect": frontend_redirect}),
        expire=settings.OAUTH_STATE_TTL,
    )
    if not ok:
        raise CustomException(msg="缓存 OAuth 状态失败")


async def _state_frontend_redirect(redis: Redis, state: str | None, fallback: str) -> str:
    """从缓存的 OAuth state 中还原前端回调地址；state 缺失/过期/损坏时回退默认值。"""
    if not state:
        return fallback
    raw = await RedisCURD(redis).get(f"{STATE_PREFIX}{state}")
    if not raw:
        return fallback
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return fallback
    return str(payload.get("frontend_redirect") or fallback).strip() or fallback


async def start_oauth_login(
    *,
    request: Request,
    redis: Redis,
    provider: OAuthProvider,
    redirect_uri: str | None,
) -> str:
    """OAuth 发起编排：生成一次性 state 并返回第三方授权页跳转地址。

    缺少 redirect_uri、渠道密钥未配置等异常时降级为错误重定向（回落到默认前端页），
    保证端点永远返回可跳转地址。
    """
    fallback = settings.OAUTH_FRONTEND_FALLBACK
    try:
        if not redirect_uri:
            raise CustomException(msg="缺少 redirect_uri 参数")
        state = secrets.token_urlsafe(32)
        await save_oauth_state(
            redis=redis,
            state=state,
            provider=provider,
            frontend_redirect=redirect_uri,
        )
        return build_authorize_url(
            provider=provider,
            callback_url=_callback_url(request, provider),
            state=state,
        )
    except CustomException as e:
        return _frontend_error_redirect(redirect_uri or fallback, e.msg)


async def finish_oauth_login(
    *,
    request: Request,
    redis: Redis,
    db: AsyncSession,
    provider: OAuthProvider,
    code: str | None,
    state: str | None,
    background_tasks: BackgroundTasks | None = None,
) -> str:
    """OAuth 回调编排：校验参数与 state → 换取令牌 → 查找/自动注册用户 → 签发登录态。

    返回浏览器最终跳转地址：成功回前端登录页并携带令牌；失败跳错误页
    （尽力还原发起时的前端地址，取不到则用系统默认值）。
    """
    fallback = settings.OAUTH_FRONTEND_FALLBACK

    async def _frontend() -> str:
        return await _state_frontend_redirect(redis=redis, state=state, fallback=fallback)

    if not code or not state:
        return _frontend_error_redirect(await _frontend(), "授权被取消或参数不完整")
    try:
        token, frontend = await complete_oauth_login(
            request=request,
            redis=redis,
            db=db,
            provider=provider,
            code=code,
            state=state,
            background_tasks=background_tasks,
        )
    except CustomException as e:
        return _frontend_error_redirect(await _frontend(), e.msg)
    return _frontend_success_redirect(
        frontend,
        token.access_token,
        token.refresh_token,
        token.token_type,
    )
