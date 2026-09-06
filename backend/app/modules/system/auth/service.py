import json
import secrets
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, NewType

import ua_parser
from fastapi import BackgroundTasks, Request
from redis.asyncio.client import Redis
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import EnvironmentEnum, RedisInitKeyConfig
from app.config.setting import settings
from app.core.base_schema import AuthSchema, JWTOutSchema, JWTPayloadSchema
from app.core.database import async_db_session
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.core.redis_crud import RedisCURD
from app.core.security import (
    CustomOAuth2PasswordRequestForm,
    create_access_token,
    decode_access_token,
)
from app.modules.system.log.crud import LoginLogCRUD
from app.modules.system.log.model import LoginLogModel
from app.modules.system.log.schema import LoginLogCreateSchema
from app.modules.system.user.crud import UserCRUD
from app.modules.system.user.model import UserModel
from app.modules.system.user.schema import UserCreateSchema
from app.modules.system.user.service import UserService
from app.utils.common_util import get_random_character
from app.utils.ip_local_util import IpLocalUtil, get_client_fingerprint, get_client_ip
from app.utils.password_util import PwdUtil

from .schema import (
    CaptchaOutSchema,
    LoginOutSchema,
)

CaptchaKey = NewType("CaptchaKey", str)
CaptchaBase64 = NewType("CaptchaBase64", str)


def sanitize_login_name(raw: str) -> str:
    """把外部唯一标识清洗为符合注册规则的登录名（字母开头、3-32 位、仅字母数字/_.-）。

    供微信小程序 / OAuth 自动注册生成登录名共用。注意：生成规则一旦变更会导致
    历史用户无法命中，需保持稳定，确有调整要走用户表数据迁移。
    """
    name = "".join(c if c.isalnum() or c in "_-." else "_" for c in raw)[:32]
    if len(name) < 3:
        name = (name + "usr")[:32]
    return name if name[0].isalpha() else "u" + name[:31]


async def auto_register_login_user(
    *,
    db: AsyncSession,
    username: str,
    display_name: str,
    mobile: str | None = None,
    avatar: str | None = None,
    fail_msg: str,
) -> UserModel:
    """自动注册第三方登录用户：随机密码 + 默认角色（OAUTH_DEFAULT_ROLE_IDS）。

    并发创建触发唯一约束等异常时，回退为按登录名再查一次（登录场景以拿到用户为准）。
    """
    auth = AuthSchema()
    reg = UserCreateSchema(
        username=username,
        password=secrets.token_urlsafe(24),
        name=(display_name or username)[:32],
        mobile=mobile,
        avatar=avatar,
        role_ids=list(settings.OAUTH_DEFAULT_ROLE_IDS),
    )
    try:
        await UserService(auth, db).create(data=reg)
    except Exception:
        existing = await UserCRUD(auth, db).get(username=username)
        if existing:
            return existing
        raise CustomException(msg=fail_msg)
    user = await UserCRUD(auth, db).get(username=username)
    if not user:
        raise CustomException(msg=fail_msg)
    return user


async def _write_login_log(
    username: str,
    status: int,
    login_ip: str | None = None,
    login_location: str | None = None,
    request_os: str | None = None,
    request_browser: str | None = None,
    msg: str | None = None,
) -> int | None:
    """写入登录日志；返回日志 ID（用于后台补全归属地）。"""
    try:
        async with async_db_session() as session, session.begin():
            _auth = AuthSchema()
            obj = await LoginLogCRUD(_auth, session).create(
                data=LoginLogCreateSchema(
                    username=username,
                    status=status,
                    login_ip=login_ip,
                    login_location=login_location,
                    request_os=request_os,
                    request_browser=request_browser,
                    msg=msg,
                ),
            )
            return obj.id if obj else None
    except Exception:
        # 登录日志失败不影响主流程，但静默吞会丢失审计线索——至少留应用日志
        logger.warning(f"登录审计日志写入失败: username={username}, msg={msg}", exc_info=True)
        return None


async def _async_fill_login_location(redis, login_log_id: int, ip: str | None) -> None:
    """后台异步补全登录日志的归属地。"""
    if not ip:
        return
    try:
        location = await IpLocalUtil.resolve_location_async(redis, ip)
        logger.info(f"异步解析IP归属地结果: ip={ip}, log_id={login_log_id}, location={location}")
        if location == "归属地查询中" or not location:
            return
        async with async_db_session() as session, session.begin():
            await session.execute(sa_update(LoginLogModel).where(LoginLogModel.id == login_log_id).values(login_location=location))
            logger.info(f"登录日志归属地已更新: log_id={login_log_id}, location={location}")
    except Exception as e:
        logger.warning(f"异步补全登录归属地失败: {e}")


async def _async_fill_session_location(redis, session_id: str, ip: str | None) -> None:
    """后台异步补全会话缓存中的归属地（微信/OAuth 登录不写登录日志，需单独更新 Redis 会话）。"""
    if not ip:
        return
    try:
        location = await IpLocalUtil.resolve_location_async(redis, ip)
        logger.info(f"异步解析IP归属地结果: ip={ip}, session_id={session_id}, location={location}")
        if location == "归属地查询中" or not location:
            return
        key = f"{RedisInitKeyConfig.USER_SESSION.key}:{session_id}"
        raw = await RedisCURD(redis).get(key)
        if not raw:
            return
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        session_dict = json.loads(raw)
        session_dict["login_location"] = location
        ttl = await RedisCURD(redis).ttl(key)
        # 原子替换：会话在此期间被删除(登出)或改写时不落盘，避免复活已登出的会话
        updated = await RedisCURD(redis).compare_and_set(
            key=key,
            expected=raw,
            value=json.dumps(session_dict, default=str),
            expire=max(int(ttl), 1),
        )
        if updated:
            logger.info(f"会话归属地已更新: session_id={session_id}, location={location}")
    except Exception as e:
        logger.warning(f"异步补全会话归属地失败: {e}")


class LoginService:
    """登录认证服务"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    @staticmethod
    def _collect_permissions(
        user: UserModel,
    ) -> tuple[list[str], list[int]]:
        """收集用户角色下的权限和菜单 ID

        参数:
        - user (UserModel): 用户对象

        返回:
        - tuple[list[str], list[int]]: (permissions, menu_ids)
        """
        permissions: list[str] = []
        menu_ids: list[int] = []
        if not user.is_superuser and hasattr(user, "roles"):
            for role in user.roles:
                if role and role.status == 0:
                    if hasattr(role, "menus"):
                        for menu in role.menus:
                            if menu and menu.status == 0:
                                menu_ids.append(menu.id)
                                if menu.permission:
                                    permissions.append(menu.permission)
        return permissions, menu_ids

    @staticmethod
    async def _check_login_rate_limit(redis: Redis, request_ip: str | None) -> None:
        """登录限流（Redis 固定窗口）：防账号密码无限爆破。

        爆破类攻击必须高频请求，窗口阈值取正常用户不可能达到的次数，
        误伤概率极低；Redis 异常时放行（认证主流程优先），与全局限流策略一致。
        """
        if not request_ip or request_ip in ("unknown", "127.0.0.1", "localhost"):
            return
        key = f"login_rate_limit:{request_ip}"
        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)
            if count > settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
                raise CustomException(msg="登录尝试过于频繁，请稍后再试")
        except CustomException:
            raise
        except Exception as e:
            logger.warning(f"登录限流检查异常（已放行）: {e}")

    @classmethod
    async def authenticate_user(
        cls,
        request: Request,
        background_tasks: BackgroundTasks,
        redis: Redis,
        login_form: CustomOAuth2PasswordRequestForm,
        db: AsyncSession,
    ) -> LoginOutSchema:
        """用户认证"""
        ua_result = ua_parser.parse(request.headers.get("user-agent") or "")
        request_ip = get_client_ip(request)
        await cls._check_login_rate_limit(redis=redis, request_ip=request_ip)
        login_location = await IpLocalUtil.resolve_location_for_log(redis, request_ip)
        _login_os = ua_result.os.family if ua_result.os else "Unknown"
        _login_browser = ua_result.user_agent.family if ua_result.user_agent else "Unknown"
        _login_username = login_form.username

        referer = request.headers.get("referer", "")
        # docs 豁免仅限非生产环境：Referer 完全由客户端控制，不能作为生产环境的安全边界
        request_from_docs = settings.ENVIRONMENT != EnvironmentEnum.PROD and referer.endswith(("docs", "redoc"))

        if settings.CAPTCHA_ENABLE and not request_from_docs:
            if not login_form.captcha_key:
                raise CustomException(msg="验证码不能为空")
            # 滑块模式：slider_complete 已验证身份，此处仅校验状态
            await CaptchaService.check_captcha(
                redis=redis,
                request=request,
                key=login_form.captcha_key,
            )

        auth = AuthSchema()
        user = await UserCRUD(auth, db).get(username=login_form.username, preload=["roles", "roles.menus"])

        if not user:
            await _write_login_log(
                username=_login_username,
                status=2,
                login_ip=request_ip,
                login_location=login_location,
                request_os=_login_os,
                request_browser=_login_browser,
                msg="用户不存在",
            )
            raise CustomException(msg="用户不存在")

        if not await PwdUtil.averify_password(plain_password=login_form.password, password_hash=user.password):
            await _write_login_log(
                username=_login_username,
                status=2,
                login_ip=request_ip,
                login_location=login_location,
                request_os=_login_os,
                request_browser=_login_browser,
                msg="账号或密码错误",
            )
            raise CustomException(msg="账号或密码错误")
        if user.status == 1:
            await _write_login_log(
                username=_login_username,
                status=2,
                login_ip=request_ip,
                login_location=login_location,
                request_os=_login_os,
                request_browser=_login_browser,
                msg="用户已被停用",
            )
            raise CustomException(msg="用户已被停用")

        user = await UserCRUD(auth, db).update_last_login(id=user.id)
        if not user:
            raise CustomException(msg="用户不存在")
        if not login_form.login_type:
            raise CustomException(msg="登录类型不能为空")

        token = await cls.create_token(
            request=request,
            redis=redis,
            user=user,
            login_type=login_form.login_type,
        )

        log_id = await _write_login_log(
            username=user.username,
            status=1,
            login_ip=request_ip,
            login_location=login_location,
            request_os=_login_os,
            request_browser=_login_browser,
            msg="登录成功",
        )
        # 登录成功后异步补全归属地，不阻塞返回
        if log_id and login_location == "归属地查询中":
            background_tasks.add_task(_async_fill_login_location, redis, log_id, request_ip)

        return cls.build_login_out(token=token, user=user)

    @staticmethod
    async def prepare_user_for_login(db: AsyncSession, user: UserModel) -> UserModel:
        """登录前可用性校验并刷新最后登录时间（微信小程序 / OAuth 自动注册登录共用）。"""
        if user.status == 1:
            raise CustomException(msg="用户已被停用")
        refreshed = await UserCRUD(AuthSchema(), db).update_last_login(id=user.id)
        if not refreshed:
            raise CustomException(msg="用户不存在")
        return refreshed

    @staticmethod
    def build_login_out(token: JWTOutSchema, user: UserModel, *, with_mobile: bool = False) -> LoginOutSchema:
        """组装登录响应：令牌 + 用户基础信息（手机号登录场景额外携带 mobile）。"""
        user_info: dict[str, Any] = {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "avatar": user.avatar,
            "is_superuser": user.is_superuser,
        }
        if with_mobile:
            user_info["mobile"] = user.mobile
        return LoginOutSchema(
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            expires_in=token.expires_in,
            token_type=token.token_type,
            user_info=user_info,
        )

    @staticmethod
    def _build_session_dict(
        user: UserModel,
        session_id: str,
        permissions: list[str],
        menu_ids: list[int],
        request_ip: str,
        login_location: str | None,
        ua_result: Any,
        login_type: str,
    ) -> dict:
        """构建会话信息字典

        参数:
        - user (UserModel): 用户对象
        - session_id (str): 会话ID
        - permissions (list[str]): 权限标识列表
        - menu_ids (list[int]): 菜单ID列表
        - request_ip (str): 请求IP
        - login_location (str): 登录地点
        - ua_result: User-Agent 解析结果
        - login_type (str): 登录类型

        返回:
        - dict: 会话信息字典
        """
        return {
            "session_id": session_id,
            "user_id": user.id,
            "is_superuser": user.is_superuser,
            "user_status": user.status,
            "name": user.name,
            "user_name": user.username,
            "dept_id": user.dept_id,
            "mobile": user.mobile,
            "email": user.email,
            "gender": user.gender,
            "avatar": user.avatar,
            "permissions": permissions,
            "menu_ids": menu_ids,
            "ipaddr": request_ip,
            "login_location": login_location,
            "os": ua_result.os.family if ua_result.os else "Unknown",
            "browser": ua_result.user_agent.family if ua_result.user_agent else "Unknown",
            "login_time": user.last_login,
            "login_type": login_type,
        }

    @classmethod
    async def create_token(
        cls,
        request: Request,
        redis: Redis,
        user: UserModel,
        login_type: str,
        background_tasks: BackgroundTasks | None = None,
    ) -> JWTOutSchema:
        """创建访问令牌和刷新令牌"""
        session_id = str(uuid.uuid4())
        ua_result = ua_parser.parse(request.headers.get("user-agent") or "")
        request_ip = get_client_ip(request)

        login_location = await IpLocalUtil.resolve_location_for_log(redis, request_ip)

        access_expires = timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
        refresh_expires = timedelta(seconds=settings.REFRESH_TOKEN_EXPIRE_SECONDS)

        now = datetime.now()

        permissions, menu_ids = LoginService._collect_permissions(user)

        session_dict = LoginService._build_session_dict(
            user=user,
            session_id=session_id,
            permissions=permissions,
            menu_ids=menu_ids,
            request_ip=request_ip,
            login_location=login_location,
            ua_result=ua_result,
            login_type=login_type,
        )
        # 会话创建时间（UTC）：滑动续期的绝对存活上限判据，见 dependencies._authenticate
        session_dict["created_at"] = datetime.now(UTC).isoformat()
        session_info = json.dumps(session_dict, default=str)

        # 会话信息存 Redis（完整 JSON），JWT sub 仅含 session_id
        await RedisCURD(redis).set(
            key=f"{RedisInitKeyConfig.USER_SESSION.key}:{session_id}",
            value=session_info,
            expire=int(refresh_expires.total_seconds()),
        )

        access_token = create_access_token(
            payload=JWTPayloadSchema(
                sub=session_id,
                is_refresh=False,
                exp=now + access_expires,
            ),
        )
        refresh_token = create_access_token(
            payload=JWTPayloadSchema(
                sub=session_id,
                is_refresh=True,
                exp=now + refresh_expires,
            ),
        )

        await RedisCURD(redis).set(
            key=f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}",
            value=access_token,
            expire=int(access_expires.total_seconds()),
        )

        await RedisCURD(redis).set(
            key=f"{RedisInitKeyConfig.REFRESH_TOKEN.key}:{session_id}",
            value=refresh_token,
            expire=int(refresh_expires.total_seconds()),
        )

        # 归属地为待解析时后台补全会话中的 login_location（微信/OAuth 登录路径）
        if background_tasks and login_location == "归属地查询中":
            background_tasks.add_task(_async_fill_session_location, redis, session_id, request_ip)

        return JWTOutSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_expires.total_seconds()),
            token_type=settings.TOKEN_TYPE,
        )

    @classmethod
    async def refresh_token(
        cls,
        db: AsyncSession,
        redis: Redis,
        refresh_token: str,
    ) -> JWTOutSchema:
        """刷新访问令牌"""
        token_payload: JWTPayloadSchema = decode_access_token(token=refresh_token)
        if not token_payload.is_refresh:
            raise CustomException(msg="非法凭证，请传入刷新令牌")

        session_id = token_payload.sub
        session_key = f"{RedisInitKeyConfig.USER_SESSION.key}:{session_id}"
        session_info = await RedisCURD(redis).get(session_key)
        if not session_info:
            raise CustomException(msg="会话已过期，请重新登录")

        # refresh token 轮换校验：必须与会话当前有效的 refresh token 一致，
        # 旧 token 被再次使用视为泄露/重放 → 撤销整个会话，强制重新登录
        crud = RedisCURD(redis)
        refresh_key = f"{RedisInitKeyConfig.REFRESH_TOKEN.key}:{session_id}"
        stored_refresh = await crud.get(refresh_key)
        if isinstance(stored_refresh, bytes):
            stored_refresh = stored_refresh.decode()
        if not stored_refresh or stored_refresh != refresh_token:
            await crud.delete(
                session_key,
                refresh_key,
                f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}",
            )
            logger.warning(f"检测到疑似 refresh token 重放，已撤销会话: {session_id}")
            raise CustomException(msg="刷新凭证已失效，请重新登录")

        user_id = json.loads(session_info).get("user_id")

        if not session_id or not user_id:
            raise CustomException(msg="非法凭证,无法获取会话编号或用户ID")

        auth = AuthSchema()
        user = await UserCRUD(auth, db).get(id=user_id)
        if not user:
            raise CustomException(msg="刷新token失败，用户不存在")
        if user.status == 1:
            raise CustomException(msg="用户已被停用")

        access_expires = timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
        refresh_expires = timedelta(seconds=settings.REFRESH_TOKEN_EXPIRE_SECONDS)
        now = datetime.now()

        # 延长会话信息 Redis TTL
        await RedisCURD(redis).expire(
            key=f"{RedisInitKeyConfig.USER_SESSION.key}:{session_id}",
            expire=int(refresh_expires.total_seconds()),
        )

        access_token = create_access_token(
            payload=JWTPayloadSchema(
                sub=session_id,
                is_refresh=False,
                exp=now + access_expires,
            ),
        )

        refresh_token_new = create_access_token(
            payload=JWTPayloadSchema(
                sub=session_id,
                is_refresh=True,
                exp=now + refresh_expires,
            ),
        )

        await RedisCURD(redis).set(
            key=f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}",
            value=access_token,
            expire=int(access_expires.total_seconds()),
        )

        await RedisCURD(redis).set(
            key=f"{RedisInitKeyConfig.REFRESH_TOKEN.key}:{session_id}",
            value=refresh_token_new,
            expire=int(refresh_expires.total_seconds()),
        )

        return JWTOutSchema(
            access_token=access_token,
            refresh_token=refresh_token_new,
            token_type=settings.TOKEN_TYPE,
            expires_in=int(access_expires.total_seconds()),
        )

    @staticmethod
    async def logout(redis: Redis, token: str) -> bool:
        """退出登录"""
        payload: JWTPayloadSchema = decode_access_token(token=token)
        session_id = payload.sub

        if not session_id:
            raise CustomException(msg="非法凭证,无法获取会话编号")

        await RedisCURD(redis).delete(f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}")
        await RedisCURD(redis).delete(f"{RedisInitKeyConfig.REFRESH_TOKEN.key}:{session_id}")
        await RedisCURD(redis).delete(f"{RedisInitKeyConfig.USER_SESSION.key}:{session_id}")

        logger.info(f"用户退出登录成功,会话编号:{session_id}")

        return True


class CaptchaService:
    """验证码服务 — 滑块拖动模式

    滑块是纯前端交互，服务端拿不到任何可信的人机证据（拖动轨迹可以伪造），
    因此这里只能把「一次验证码」的可用范围收窄到签发它的那个来源：
    - 来源指纹绑定（IP + UA）：key 无法被批量预取后投毒给其它请求；
    - 最小驻留时长：签发后立刻回交 complete 的脚本会被拒；
    - 一次性消费：校验通过即删除，杜绝重放。
    需要真正的防机器能力，应改为服务端出题的图形/行为验证码（需前端配合）。
    """

    PENDING = "pending"
    VERIFIED = "verified"

    @staticmethod
    def _redis_key(captcha_key: str) -> str:
        return f"{RedisInitKeyConfig.CAPTCHA_CODES.key}:{captcha_key}"

    @staticmethod
    async def _read_state(redis: Redis, captcha_key: str) -> dict:
        """读取验证码状态；升级前签发的在途纯字符串状态按「无指纹、零耗时」兼容处理。"""
        raw = await RedisCURD(redis).get(CaptchaService._redis_key(captcha_key))
        if not raw:
            raise CustomException(msg="验证码已过期，请刷新")
        if isinstance(raw, bytes):
            raw = raw.decode()
        try:
            state = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return {"status": raw, "fingerprint": "", "issued_at": 0.0}
        if not isinstance(state, dict):
            return {"status": "", "fingerprint": "", "issued_at": 0.0}
        return {"status": state.get("status", ""), "fingerprint": state.get("fingerprint", ""), "issued_at": float(state.get("issued_at") or 0.0)}

    @staticmethod
    async def _write_state(redis: Redis, captcha_key: str, status: str, fingerprint: str, issued_at: float) -> None:
        await RedisCURD(redis).set(
            key=CaptchaService._redis_key(captcha_key),
            value=json.dumps({"status": status, "fingerprint": fingerprint, "issued_at": issued_at}),
            expire=settings.CAPTCHA_EXPIRE_SECONDS,
        )

    @staticmethod
    def _matches(state: dict, request: Request) -> bool:
        """来源是否与签发时一致（历史无指纹状态一律放行）。"""
        return not state["fingerprint"] or state["fingerprint"] == get_client_fingerprint(request)

    @staticmethod
    async def get_captcha(redis: Redis, request: Request) -> CaptchaOutSchema:
        """获取验证码（滑块模式：仅生成 key，无需算术图片）"""
        if not settings.CAPTCHA_ENABLE:
            raise CustomException(msg="未开启验证码服务")

        captcha_key = get_random_character()
        # 存储滑块状态：pending（待验证）/ verified（已验证通过）
        await CaptchaService._write_state(
            redis=redis,
            captcha_key=captcha_key,
            status=CaptchaService.PENDING,
            fingerprint=get_client_fingerprint(request),
            issued_at=time.time(),
        )

        return CaptchaOutSchema(
            enable=settings.CAPTCHA_ENABLE,
            key=CaptchaKey(captcha_key),
            img_base=CaptchaBase64(""),
        )

    @staticmethod
    async def slider_complete(redis: Redis, request: Request, captcha_key: str) -> dict:
        """标记滑块验证完成"""
        if not captcha_key:
            raise CustomException(msg="验证码标识不能为空")

        state = await CaptchaService._read_state(redis=redis, captcha_key=captcha_key)
        if state["status"] == CaptchaService.VERIFIED:
            raise CustomException(msg="验证码已使用")
        if state["status"] != CaptchaService.PENDING:
            raise CustomException(msg="验证码状态异常，请刷新重试")
        if not CaptchaService._matches(state, request):
            logger.warning("滑块验证来源与签发来源不一致，已拒绝: key={}", captcha_key)
            raise CustomException(msg="验证码无效，请刷新重试")
        # 签发与完成可能落在不同进程/不同主机，只能用墙钟；出现负值说明时钟回拨，放行以免误伤
        elapsed = time.time() - state["issued_at"]
        if 0 <= elapsed < settings.CAPTCHA_MIN_VERIFY_SECONDS:
            raise CustomException(msg="验证过于频繁，请完成滑块后重试")

        # 标记为已验证（保留签发时间与指纹，供登录时二次确认来源）
        await CaptchaService._write_state(
            redis=redis,
            captcha_key=captcha_key,
            status=CaptchaService.VERIFIED,
            fingerprint=state["fingerprint"] or get_client_fingerprint(request),
            issued_at=state["issued_at"],
        )

        return {"captcha_key": captcha_key, "verified": True}

    @staticmethod
    async def check_captcha(redis: Redis, request: Request, key: str) -> bool:
        """校验滑块验证码：检查 key 状态是否为 verified 并确认来源一致，通过后立即消费。"""
        state = await CaptchaService._read_state(redis=redis, captcha_key=key)
        if state["status"] != CaptchaService.VERIFIED:
            raise CustomException(msg="请先完成滑块验证")
        await RedisCURD(redis).delete(CaptchaService._redis_key(key))
        if not CaptchaService._matches(state, request):
            logger.warning("登录使用的验证码与签发来源不一致: key={}", key)
            raise CustomException(msg="验证码无效，请刷新重试")
        return True
