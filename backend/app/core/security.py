from datetime import datetime

import jwt
from fastapi import Form, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param

from app.common.enums import RET
from app.config.setting import settings
from app.core.base_schema import JWTPayloadSchema
from app.core.exceptions import CustomException


class CustomOAuth2PasswordBearer(OAuth2PasswordBearer):
    """自定义OAuth2认证类,继承自OAuth2PasswordBearer"""

    def __init__(
        self,
        token_url: str,
        scheme_name: str | None = None,
        scopes: dict[str, str] | None = None,
        description: str | None = None,
        auto_error: bool = True,
    ) -> None:
        super().__init__(
            tokenUrl=token_url,
            scheme_name=scheme_name,
            scopes=scopes,
            description=description,
            auto_error=auto_error,
        )

    async def __call__(self, request: Request) -> str | None:
        """重写认证方法,校验token

        参数:
        - request (Request): FastAPI请求对象。

        返回:
        - str | None: 校验通过的token,如果校验失败则返回None。

        异常:
        - CustomException: 认证失败时抛出,状态码为401。
        """
        authorization = request.headers.get("Authorization")
        scheme, token = get_authorization_scheme_param(authorization)

        if not authorization or scheme.lower() != settings.TOKEN_TYPE.lower():
            if self.auto_error:
                raise CustomException(msg="认证失败,请登录后再试", code=RET.TOKEN_EXPIRED.code, status_code=401)
            return None
        return token


class CustomOAuth2PasswordRequestForm(OAuth2PasswordRequestForm):
    """自定义登录表单,扩展验证码等字段

    参数:
    - grant_type (str | None): 授权类型,默认值为None,正则表达式为'password'。
    - scope (str): 作用域,默认值为空字符串。
    - client_id (str | None): 客户端ID,默认值为None。
    - client_secret (str | None): 客户端密钥,默认值为None。
    - username (str): 用户名。
    - password (str): 密码。
    - captcha_key (str | None): 验证码键,默认值为空字符串。
    - captcha (str | None): 验证码值,默认值为空字符串。
    - login_type (str | None): 登录类型,默认值为"PC端",描述为"PC端 | 移动端"。
    """

    def __init__(
        self,
        grant_type: str | None = Form(default=None, pattern="password"),
        scope: str = Form(default=""),
        client_id: str | None = Form(default=None),
        client_secret: str | None = Form(default=None),
        username: str = Form(),
        password: str = Form(),
        captcha_key: str | None = Form(default=""),
        captcha: str | None = Form(default=""),
        login_type: str | None = Form(default="PC端", description="PC端 | 移动端"),
    ) -> None:
        super().__init__(
            grant_type=grant_type,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
        )
        self.captcha_key = captcha_key
        self.captcha = captcha
        self.login_type = login_type


# OAuth2认证配置
OAuth2Schema = CustomOAuth2PasswordBearer(token_url="system/auth/login", description="认证")


def create_access_token(payload: JWTPayloadSchema) -> str:
    """生成JWT访问令牌

    参数:
    - payload (JWTPayloadSchema): JWT有效载荷,包含用户信息等。

    返回:
    - str: 生成的JWT访问令牌。
    """
    payload_dict = payload.model_dump(exclude_none=False)
    # PyJWT 2.x 不支持 datetime 对象，需转为 Unix 时间戳
    if isinstance(payload_dict.get("exp"), datetime):
        payload_dict["exp"] = int(payload_dict["exp"].timestamp())
    return jwt.encode(
        payload=payload_dict,
        key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str, verify_exp: bool = True) -> JWTPayloadSchema:
    """解析JWT访问令牌

    参数:
    - token (str): JWT访问令牌字符串。
    - verify_exp (bool): 是否校验 exp 声明。滑动续期场景设为 False，由 Redis session 决定有效期。

    返回:
    - JWTPayloadSchema: 解析后的JWT有效载荷,包含用户信息等。

    异常:
    - CustomException: 解析失败时抛出,状态码为401。
    """
    if not token:
        raise CustomException(msg="认证不存在,请重新登录", code=RET.TOKEN_EXPIRED.code, status_code=401)

    try:
        options: dict = {}
        if not verify_exp:
            options["verify_exp"] = False
        payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options=options)  # type: ignore[arg-type]

        online_user_info = payload.get("sub")
        if not online_user_info:
            raise CustomException(msg="无效认证,请重新登录", code=RET.TOKEN_EXPIRED.code, status_code=401)

        return JWTPayloadSchema(**payload)

    except (jwt.InvalidSignatureError, jwt.DecodeError):
        raise CustomException(msg="无效认证,请重新登录", code=RET.TOKEN_EXPIRED.code, status_code=401)

    except jwt.ExpiredSignatureError:
        raise CustomException(msg="认证已过期,请重新登录", code=RET.TOKEN_EXPIRED.code, status_code=401)

    except jwt.InvalidTokenError:
        raise CustomException(msg="token已失效,请重新登录", code=RET.TOKEN_EXPIRED.code, status_code=401)
