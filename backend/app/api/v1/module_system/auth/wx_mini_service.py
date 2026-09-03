"""微信小程序后端服务。

提供以下能力：
1. code2Session — 用前端 uni.login 返回的 code 换取 openid + session_key
2. get_phone_number — 用 getPhoneNumber 回调返回的 code 换取手机号（2023+ 新 API，无需 AES 解密）
3. get_qrcode — 调用 getwxacodeunlimit 生成小程序码
4. ensure_wx_user — 通过 openid 查找或自动注册用户
5. wx_mini_login / wx_mini_phone_login — 登录编排（code → openid/手机号 → 用户 → JWT）

所有微信 API 调用统一走 httpx.AsyncClient，access_token 通过 Redis 缓存（TTL < 7200s）。
"""

import json
import secrets
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import BackgroundTasks, Request
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_system.user.crud import UserCRUD
from app.api.v1.module_system.user.model import UserModel
from app.common.enums import RedisInitKeyConfig
from app.config.setting import settings
from app.core.base_schema import AuthSchema
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.core.redis_crud import RedisCURD

from .schema import LoginOutSchema
from .service import LoginService, auto_register_login_user, sanitize_login_name

# 微信 API 基础地址
_WX_API_BASE = "https://api.weixin.qq.com"

# code2Session 接口
_CODE2SESSION_URL = f"{_WX_API_BASE}/sns/jscode2session"

# 获取 access_token（稳定版，推荐）
_ACCESS_TOKEN_URL = f"{_WX_API_BASE}/cgi-bin/stable_token"

# 获取手机号（2023+ 新 API）
_GET_PHONE_URL = f"{_WX_API_BASE}/wxa/business/getuserphonenumber"

# 生成无限制小程序码
_GET_QRCODE_URL = f"{_WX_API_BASE}/wxa/getwxacodeunlimit"


def _require_mini_credentials() -> tuple[str, str]:
    """校验小程序 AppID / AppSecret 是否已配置。"""
    app_id = settings.WX_MINI_APP_ID
    app_secret = settings.WX_MINI_APP_SECRET
    if not app_id or not app_secret:
        raise CustomException(msg="微信小程序未配置（AppID / AppSecret 为空）")
    return app_id, app_secret


async def _http_json(method: str, url: str, **kwargs: Any) -> dict:
    """发起 HTTP 请求并解析 JSON 响应。"""
    timeout = settings.HTTPX_DEFAULT_TIMEOUT
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.request(method, url, **kwargs)
        r.raise_for_status()
        try:
            return r.json()
        except json.JSONDecodeError:
            logger.error(f"微信 API 非 JSON 响应: {r.text[:500]}")
            raise CustomException(msg="微信接口返回异常")


async def _get_access_token(redis: Redis) -> str:
    """获取微信小程序 access_token，优先从 Redis 缓存读取。

    微信 access_token 有效期 7200 秒，多实例共享同一 token，必须通过中央存储（Redis）缓存。
    使用 stable_token 接口（比 cgi-bin/token 更稳定，不会因并发请求导致 token 互相覆盖）。
    """
    rc = RedisCURD(redis)
    cache_key = f"{RedisInitKeyConfig.WX_MINI_ACCESS_TOKEN.key}"
    cached = await rc.get(cache_key)
    if cached:
        if isinstance(cached, bytes):
            cached = cached.decode("utf-8")
        return str(cached)

    app_id, app_secret = _require_mini_credentials()
    data = await _http_json(
        "POST",
        _ACCESS_TOKEN_URL,
        json={
            "grant_type": "client_credential",
            "appid": app_id,
            "secret": app_secret,
            "force_refresh": False,
        },
    )
    token = data.get("access_token")
    if not token:
        errmsg = data.get("errmsg") or "未知错误"
        errcode = data.get("errcode")
        raise CustomException(msg=f"获取微信 access_token 失败: [{errcode}] {errmsg}")

    # 缓存到 Redis，TTL 比微信上限少 200 秒留余量
    ttl = settings.WX_MINI_ACCESS_TOKEN_CACHE_TTL
    await rc.set(key=cache_key, value=str(token), expire=ttl)
    logger.info(f"微信小程序 access_token 已缓存，TTL={ttl}s")
    return str(token)


def _check_wx_error(data: dict, action: str) -> None:
    """统一检查微信 API 返回的 errcode。"""
    errcode = data.get("errcode")
    if errcode and errcode != 0:
        errmsg = data.get("errmsg") or "未知错误"
        raise CustomException(msg=f"微信{action}失败: [{errcode}] {errmsg}")


async def code2session(code: str) -> dict:
    """用 uni.login 返回的 code 换取 openid + session_key。

    参数:
    - code (str): 前端 uni.login 返回的临时登录凭证

    返回:
    - dict: {"openid": str, "session_key": str, "unionid": str | None}
    """
    app_id, app_secret = _require_mini_credentials()
    qs = urlencode(
        {
            "appid": app_id,
            "secret": app_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }
    )
    data = await _http_json("GET", f"{_CODE2SESSION_URL}?{qs}")
    _check_wx_error(data, "code2Session")

    openid = data.get("openid")
    session_key = data.get("session_key")
    if not openid or not session_key:
        raise CustomException(msg="微信 code2Session 返回数据不完整")

    return {
        "openid": str(openid),
        "session_key": str(session_key),
        "unionid": str(data["unionid"]) if data.get("unionid") else None,
    }


async def get_phone_number(redis: Redis, code: str) -> str:
    """用 getPhoneNumber 回调返回的 code 换取手机号。

    2023+ 微信推荐方案：前端 <button open-type="getPhoneNumber"> 回调 e.detail.code，
    后端调用此接口直接获取手机号，无需 AES 解密 encryptedData。

    参数:
    - redis (Redis): Redis 连接
    - code (str): getPhoneNumber 回调返回的动态令牌

    返回:
    - str: 纯手机号（如 13800138000）
    """
    access_token = await _get_access_token(redis)
    data = await _http_json(
        "POST",
        f"{_GET_PHONE_URL}?access_token={access_token}",
        json={"code": code},
    )
    _check_wx_error(data, "获取手机号")

    phone_info = data.get("phone_info")
    if not phone_info or not phone_info.get("phoneNumber"):
        raise CustomException(msg="微信返回手机号为空")

    return str(phone_info["phoneNumber"])


async def get_qrcode(redis: Redis, scene: str, page: str | None = None, width: int = 430) -> bytes:
    """生成无限制小程序码。

    调用 getwxacodeunlimit 接口，返回 PNG 图片二进制数据。
    注意：该接口返回的是图片二进制，不是 JSON。

    参数:
    - redis (Redis): Redis 连接
    - scene (str): 场景参数（最大 32 字符，如 "invite=abc123"）
    - page (str | None): 小程序页面路径，为空则默认主页
    - width (int): 图片宽度，默认 430px

    返回:
    - bytes: PNG 图片二进制
    """
    access_token = await _get_access_token(redis)
    payload: dict[str, Any] = {
        "scene": scene,
        "width": width,
        "auto_color": False,
        "is_hyaline": False,
    }
    if page:
        payload["page"] = page

    timeout = settings.HTTPX_DEFAULT_TIMEOUT
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(
            f"{_GET_QRCODE_URL}?access_token={access_token}",
            json=payload,
        )
        r.raise_for_status()

        # 微信接口在出错时返回 JSON（Content-Type: application/json），
        # 成功时返回 image（Content-Type: image/png 或类似）
        content_type = r.headers.get("content-type", "")
        if "json" in content_type.lower():
            # 出错了，解析错误信息
            try:
                err_data = r.json()
                _check_wx_error(err_data, "生成小程序码")
            except json.JSONDecodeError:
                pass
            raise CustomException(msg="生成小程序码失败")

        return r.content


def _username_for_wx_mini(openid: str) -> str:
    """生成符合注册规则的登录名：wxmini_{openid前20位}（清洗规则与 OAuth 共用）。"""
    # openid 取前 20 位，保证长度在 32 以内且生成规则长期稳定
    return sanitize_login_name(f"wxmini_{openid[:20]}")


async def ensure_wx_user(
    *,
    db: AsyncSession,
    openid: str,
    nickname: str | None = None,
    avatar: str | None = None,
    mobile: str | None = None,
) -> UserModel:
    """通过 openid 查找或自动注册用户。

    用户名规则：wxmini_{openid前20位}，与 OAuth 模块保持一致的风格。
    如果用户已存在但提供了新的手机号/昵称/头像，则更新这些字段。

    参数:
    - db (AsyncSession): 数据库会话
    - openid (str): 微信小程序用户唯一标识
    - nickname (str | None): 昵称
    - avatar (str | None): 头像 URL
    - mobile (str | None): 手机号

    返回:
    - UserModel: 用户对象
    """
    auth = AuthSchema()
    username = _username_for_wx_mini(openid)
    existing = await UserCRUD(auth, db).get(username=username)

    if existing:
        # 已有用户：按需更新手机号 / 昵称 / 头像（仅当新值非空且与当前不同）
        updated = False
        if mobile and existing.mobile != mobile:
            existing.mobile = mobile
            updated = True
        if nickname and existing.name != nickname:
            existing.name = nickname[:32]
            updated = True
        if avatar and existing.avatar != avatar:
            existing.avatar = avatar
            updated = True
        if updated:
            await db.flush()
        return existing

    # 自动注册新用户（随机密码 + 默认角色，与 OAuth 注册共用同一入口）
    user = await auto_register_login_user(
        db=db,
        username=username,
        display_name=nickname or username,
        mobile=mobile,
        avatar=avatar,
        fail_msg="微信小程序用户注册失败",
    )
    logger.info(f"微信小程序自动注册用户: {username}")
    return user


async def get_wx_login_user(
    *,
    db: AsyncSession,
    openid: str,
    nickname: str | None = None,
    avatar: str | None = None,
) -> UserModel:
    """小程序登录用户准备入口：查找/注册用户 + 状态校验 + 更新最后登录时间。"""
    user = await ensure_wx_user(db=db, openid=openid, nickname=nickname, avatar=avatar)
    return await LoginService.prepare_user_for_login(db=db, user=user)


async def get_wx_phone_login_user(*, db: AsyncSession, phone: str) -> UserModel:
    """手机号登录用户准备入口：查找用户（不存在则自动注册）+ 状态校验 + 更新最后登录时间。"""
    user = await UserCRUD(AuthSchema(), db).get(mobile=phone)

    if not user:
        # 未找到用户 → 自动注册（以手机号派生唯一登录名）
        username = sanitize_login_name(f"wxphone_{phone[-4:]}_{secrets.token_hex(4)}")
        user = await auto_register_login_user(
            db=db,
            username=username,
            display_name=f"用户{phone[-4:]}",
            mobile=phone,
            fail_msg="手机号用户注册失败",
        )
        logger.info(f"微信手机号自动注册用户: {username}")

    return await LoginService.prepare_user_for_login(db=db, user=user)


async def wx_mini_login(
    *,
    request: Request,
    redis: Redis,
    db: AsyncSession,
    code: str,
    nickname: str | None = None,
    avatar: str | None = None,
    background_tasks: BackgroundTasks,
) -> LoginOutSchema:
    """小程序登录编排：code → openid → 查找/自动注册用户 → 签发 JWT。

    登录类型记为 wx_mini；归属地为待解析时由后台任务补全会话登录地点。
    """
    session_data = await code2session(code=code)
    openid = session_data["openid"]
    user = await get_wx_login_user(db=db, openid=openid, nickname=nickname, avatar=avatar)
    token = await LoginService.create_token(
        request=request,
        redis=redis,
        user=user,
        login_type="wx_mini",
        background_tasks=background_tasks,
    )
    logger.info(f"微信小程序用户登录成功: {user.username}")
    return LoginService.build_login_out(token=token, user=user)


async def wx_mini_phone_login(
    *,
    request: Request,
    redis: Redis,
    db: AsyncSession,
    code: str,
    background_tasks: BackgroundTasks,
) -> LoginOutSchema:
    """小程序手机号登录编排：code → 手机号 → 查找/自动注册用户 → 签发 JWT。

    登录类型记为 wx_mini_phone；响应额外携带手机号字段 mobile。
    """
    phone = await get_phone_number(redis=redis, code=code)
    user = await get_wx_phone_login_user(db=db, phone=phone)
    token = await LoginService.create_token(
        request=request,
        redis=redis,
        user=user,
        login_type="wx_mini_phone",
        background_tasks=background_tasks,
    )
    logger.info(f"微信手机号用户登录成功: {user.username}")
    return LoginService.build_login_out(token=token, user=user, with_mobile=True)


# =================================================== #
# *************** 订阅消息发送能力 ******************* #
# =================================================== #

# 订阅消息发送接口
_SUBSCRIBE_SEND_URL = f"{_WX_API_BASE}/cgi-bin/message/subscribe/send"


def extract_openid_from_username(username: str) -> str | None:
    """从微信小程序用户登录名中提取 openid。

    登录名规则：wxmini_{openid前20位}（见 _username_for_wx_mini）。
    由于只保留了前 20 位，无法还原完整 openid —— 该提取结果仅用于
    与「再次登录时的用户名」匹配判断，不作为真实 openid 使用。

    实际发送订阅消息时应使用登录时缓存的完整 openid（TODO：扩展用户表字段）。
    """
    prefix = "wxmini_"
    if username and username.startswith(prefix):
        return username[len(prefix) :]
    return None


async def send_subscribe_message(
    redis: Redis,
    *,
    openid: str,
    template_id: str,
    page: str | None = None,
    data: dict[str, dict[str, str]] | None = None,
) -> bool:
    """发送微信订阅消息（模板消息）。

    订阅消息必须由用户主动授权（前端 wx.requestSubscribeMessage）后才能下发；
    未授权 / 未配置模板 / 未配置 AppID 时静默跳过，不抛异常（避免影响业务主流程）。

    参数:
    - redis (Redis): Redis 连接
    - openid (str): 接收者 openid
    - template_id (str): 订阅消息模板 ID（微信公众平台申请）
    - page (str | None): 点击消息跳转的小程序页面路径
    - data (dict | None): 模板字段值，如 {"thing1": {"value": "工单已更新"}}

    返回:
    - bool: 是否发送成功（未配置/未授权返回 False，不视为错误）
    """
    # 防御性校验：未配置 AppID 或模板 ID 为空 → 静默跳过
    if not settings.WX_MINI_APP_ID or not settings.WX_MINI_APP_SECRET:
        logger.debug("订阅消息发送跳过：小程序未配置 AppID/AppSecret")
        return False
    if not template_id:
        logger.debug("订阅消息发送跳过：模板 ID 为空")
        return False
    if not openid:
        return False

    try:
        access_token = await _get_access_token(redis)
        payload: dict[str, Any] = {
            "touser": openid,
            "template_id": template_id,
            "data": data or {},
        }
        if page:
            payload["page"] = page

        resp = await _http_json(
            "POST",
            f"{_SUBSCRIBE_SEND_URL}?access_token={access_token}",
            json=payload,
        )
        errcode = resp.get("errcode")
        if errcode and errcode != 0:
            errmsg = resp.get("errmsg") or "未知错误"
            # 43101: 用户未订阅该模板（正常业务场景，不告警）
            if errcode == 43101:
                logger.debug(f"订阅消息发送跳过：用户未订阅模板 {template_id}")
            else:
                logger.warning(f"订阅消息发送失败: [{errcode}] {errmsg}")
            return False
        logger.info(f"订阅消息发送成功: template={template_id}, touser={openid[:8]}...")
        return True
    except Exception as e:
        # 静默失败：订阅消息属于增值能力，失败不影响业务主流程
        logger.warning(f"订阅消息发送异常: {e}")
        return False
