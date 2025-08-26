# -*- coding: utf-8 -*-

import json
import uuid
from typing import Dict, Union, NewType
from fastapi import Request
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from user_agents import parse

from app.common.enums import RedisInitKeyConfig
from app.core.logger import logger
from app.config.setting import settings
from app.core.exceptions import CustomException
from app.api.v1.schemas.monitor.online_schema import OnlineOutSchema
from app.utils.common_util import get_random_character
from app.utils.captcha_util import CaptchaUtil
from app.api.v1.cruds.system.user_crud import UserCRUD
from app.api.v1.models.system.user_model import UserModel
from app.api.v1.schemas.system.auth_schema import (
    JWTPayloadSchema,
    JWTOutSchema,
    AuthSchema,
    CaptchaOutSchema,
    LogoutPayloadSchema,
    RefreshTokenPayloadSchema
)
from app.core.hash_bcrpy import PwdUtil
from app.core.security import (
    CustomOAuth2PasswordRequestForm,
    create_access_token,
    decode_access_token
)
from app.utils.ip_local_util import IpLocalUtil
from app.core.redis_crud import RedisCURD

CaptchaKey = NewType('CaptchaKey', str)
CaptchaBase64 = NewType('CaptchaBase64', str)


class LoginService:
    """登录认证服务"""

    @classmethod
    async def authenticate_user_service(cls, request: Request, redis: Redis, login_form: CustomOAuth2PasswordRequestForm, db: AsyncSession) -> JWTOutSchema:
        """
        用户认证
        
        Args:
            request: 请求对象
            login_form: 登录表单
            db: 数据库会话
            
        Returns:
            UserModel: 认证通过的用户对象
            
        Raises:
            CustomException: 认证失败时抛出异常
        """
        # 判断是否来自API文档
        referer = request.headers.get('referer', '')
        request_from_docs = referer.endswith(('docs', 'redoc'))
        
        # 验证码校验
        if settings.CAPTCHA_ENABLE and not request_from_docs:
            await CaptchaService.check_captcha_service(redis=redis, key=login_form.captcha_key, captcha=login_form.captcha)

        # 用户认证
        auth = AuthSchema(db=db)
        user = await UserCRUD(auth).get_by_username_crud(username=login_form.username)

        if not user:
            raise CustomException(msg="用户不存在")

        if not PwdUtil.verify_password(plain_password=login_form.password, password_hash=user.password):
            raise CustomException(msg="账号或密码错误")

        if not user.status:
            raise CustomException(msg="用户已被停用")
        
        # 更新最后登录时间
        user = await UserCRUD(auth).update_last_login_crud(id=user.id)

        # 创建token
        token = await cls.create_token_service(request=request, redis=redis, user=user, login_type=login_form.login_type)

        return token

    @classmethod
    async def create_token_service(cls, request: Request, redis: Redis, user: UserModel, login_type: str) -> JWTOutSchema:
        """
        创建访问令牌和刷新令牌
        
        Args:
            username: 用户名
            request: 请求对象
            
        Returns:
            JWTOutSchema: 包含访问令牌和刷新令牌的响应对象
        """
        # 生成会话编号
        session_id = str(uuid.uuid4())
        request.scope["session_id"] = session_id

        user_agent = parse(request.headers.get("user-agent"))
        request_ip = None
        x_forwarded_for = request.headers.get('X-Forwarded-For')
        if x_forwarded_for:
            # 取第一个 IP 地址，通常为客户端真实 IP
            request_ip = x_forwarded_for.split(',')[0].strip()
        else:
            # 若没有 X-Forwarded-For 头，则使用 request.client.host
            request_ip = request.client.host
        login_location = await IpLocalUtil.get_ip_location(request_ip)
        request.scope["login_location"] = login_location
        
        # 确保在请求上下文中设置用户名
        request.scope["user_username"] = user.username

        access_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        
        now = datetime.now()
        session_info=OnlineOutSchema(
            session_id=session_id,
            user_id=user.id, 
            name=user.name,
            user_name=user.username,
            ipaddr=request_ip,
            login_location=login_location,
            os=user_agent.os.family,
            browser = user_agent.browser.family,
            login_time=user.last_login.isoformat() if isinstance(user.last_login, datetime) else str(user.last_login),
            login_type=login_type
        ).model_dump_json()

        access_token = create_access_token(payload=JWTPayloadSchema(
            sub=session_info,
            is_refresh=False,
            exp=now + access_expires,
        ))
        refresh_token = create_access_token(payload=JWTPayloadSchema(
            sub=session_info,
            is_refresh=True,
            exp=now + refresh_expires,
        ))

        # 设置新的token
        await RedisCURD(redis).set(
            key=f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}',
            value=access_token,
            expire=int(access_expires.total_seconds())
        )

        await RedisCURD(redis).set(
            key=f'{RedisInitKeyConfig.REFRESH_TOKEN.key}:{session_id}',
            value=refresh_token,
            expire=int(refresh_expires.total_seconds())
        )

        return JWTOutSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=access_expires.total_seconds(),
            token_type=settings.TOKEN_TYPE
        )

    @classmethod
    async def refresh_token_service(cls, db: AsyncSession, redis: Redis, request: Request, refresh_token: RefreshTokenPayloadSchema) -> JWTOutSchema:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            JWTOutSchema: 新的令牌对象
            
        Raises:
            CustomException: 刷新令牌无效时抛出异常
        """
        token_payload: JWTPayloadSchema = decode_access_token(token = refresh_token.refresh_token)
        if not token_payload.is_refresh:
            raise CustomException(msg="非法凭证，请传入刷新令牌")
        
        # 去 Redis 查完整信息
        session_info = json.loads(token_payload.sub)
        session_id = session_info.get("session_id")
        user_id = session_info.get("user_id")

        if not session_id or not user_id:
            raise CustomException(msg="非法凭证,无法获取会话编号或用户ID")

        # 用户认证
        auth = AuthSchema(db=db)
        user = await UserCRUD(auth).get_by_id_crud(id=user_id)

        # 设置新的 token
        access_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        now = datetime.now()

        session_info_json = json.dumps(session_info)

        access_token = create_access_token(payload=JWTPayloadSchema(
            sub=session_info_json,
            is_refresh=False,
            exp=now + access_expires,
        ))

        refresh_token_new = create_access_token(payload=JWTPayloadSchema(
            sub=session_info_json,
            is_refresh=True,
            exp=now + refresh_expires,
        ))
        
        # 覆盖写入 Redis
        await RedisCURD(redis).set(
            key=f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}',
            value=access_token,
            expire=int(access_expires.total_seconds())
        )

        await RedisCURD(redis).set(
            key=f'{RedisInitKeyConfig.REFRESH_TOKEN.key}:{session_id}',
            value=refresh_token_new,
            expire=int(refresh_expires.total_seconds())
        )

        return JWTOutSchema(
            access_token=access_token,
            refresh_token=refresh_token_new,
            expires_in=access_expires.total_seconds(),
            token_type=settings.TOKEN_TYPE
        )

    @classmethod
    async def logout_services_service(cls, redis: Redis, token: LogoutPayloadSchema) -> bool:
        """
        退出登录
        
        Args:
            request: 请求对象
            token: 令牌
            
        Returns:
            bool: 退出成功返回True
        """
        payload: JWTPayloadSchema = decode_access_token(token=token.token)
        session_info = json.loads(payload.sub)
        session_id = session_info.get("session_id")
        
        if not session_id:
            raise CustomException(msg="非法凭证,无法获取会话编号")

        # 删除Redis中的在线用户、访问令牌、刷新令牌
        await RedisCURD(redis).delete(f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}")
        await RedisCURD(redis).delete(f"{RedisInitKeyConfig.REFRESH_TOKEN.key}:{session_id}")
        
        logger.info(f"用户退出登录成功,会话编号:{session_id}")

        return True


class CaptchaService:
    """验证码服务"""

    @classmethod
    async def get_captcha_service(cls, redis: Redis) -> Dict[str, Union[CaptchaKey, CaptchaBase64]]:
        """
        获取验证码
        
        Args:
            request: 请求对象
            
        Returns:
            Dict: 包含验证码key和base64图片的字典
            
        Raises:
            CustomException: 验证码服务未启用时抛出异常
        """
        if not settings.CAPTCHA_ENABLE:
            raise CustomException(msg="未开启验证码服务")

        # 生成验证码图片和值
        captcha_base64, captcha_value = CaptchaUtil.captcha_arithmetic()
        captcha_key = get_random_character()

        # 保存到Redis并设置过期时间
        redis_key = f"{RedisInitKeyConfig.CAPTCHA_CODES.key}:{captcha_key}"
        await RedisCURD(redis).set(
            key=redis_key,
            value=captcha_value,
            expire=settings.CAPTCHA_EXPIRE_SECONDS
        )

        logger.info(f"生成验证码成功,验证码:{captcha_value}")

        # 返回验证码信息
        return CaptchaOutSchema(
            enable=settings.CAPTCHA_ENABLE,
            key=CaptchaKey(captcha_key),
            img_base=CaptchaBase64(f"data:image/png;base64,{captcha_base64}")
        ).model_dump()

    @classmethod
    async def check_captcha_service(cls, redis: Redis, key: str, captcha: str) -> bool:
        """
        校验验证码
        
        Args:
            request: 请求对象
            key: 验证码key
            captcha: 用户输入的验证码
            
        Returns:
            bool: 验证通过返回True
            
        Raises:
            CustomException: 验证码无效或错误时抛出异常
        """
        if not captcha:
            raise CustomException(msg="验证码不能为空")

        # 获取Redis中存储的验证码
        redis_key = f'{RedisInitKeyConfig.CAPTCHA_CODES.key}:{key}'
        
        captcha_value = await RedisCURD(redis).get(redis_key)
        if not captcha_value:
            logger.warning('验证码已过期或不存在')
            raise CustomException(msg="验证码已过期")

        # 验证码不区分大小写比对
        if captcha.lower() != captcha_value.lower():
            logger.warning(f'验证码错误,用户输入:{captcha},正确值:{captcha_value}')
            raise CustomException(msg="验证码错误")

        # 验证成功后删除验证码,避免重复使用
        await RedisCURD(redis).delete(redis_key)
        logger.info(f'验证码校验成功,key:{key}')
        return True
