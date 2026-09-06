import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.common.enums import EnvironmentEnum
from app.config.path_conf import ENV_DIR


class Settings(BaseSettings):
    """系统配置类"""

    model_config = SettingsConfigDict(
        env_file=ENV_DIR / f".env.{os.getenv('ENVIRONMENT')}",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,  # 区分大小写
    )

    # ================================================= #
    # ******************* 项目环境 ****************** #
    # ================================================= #
    ENVIRONMENT: EnvironmentEnum = EnvironmentEnum.DEV

    # ================================================= #
    # ******************* 服务器配置 ****************** #
    # ================================================= #
    SERVER_HOST: str = "0.0.0.0"  # 允许访问的IP地址
    SERVER_PORT: int = 8001  # 服务端口
    WORKERS: int = 1  # uvicorn worker 进程数（prod 环境可调大；>1 时需确保 Redis 共享 jobstore 不重复调度）

    # ================================================= #
    # ******************* API文档配置 ****************** #
    # ================================================= #
    DEBUG: bool = True  # 调试模式
    TITLE: str = "🎉 FastapiAdmin 🎉 "  # 文档标题
    VERSION: str = "3.0.0"  # 版本号
    DESCRIPTION: str = "一个基于fastapi、sqlalchemy、redis实现的轻量化框架"  # 文档描述
    SUMMARY: str = "接口汇总"  # 文档概述
    DOCS_URL: str = "/docs"  # Swagger UI路径
    REDOC_URL: str = "/redoc"  # ReDoc路径
    WEB_URL: str = "/web"  # 前端路径
    ROOT_PATH: str = "/api/v1"  # API路由前缀

    # ================================================= #
    # ******************** 日志配置 ******************** #
    # ================================================= #
    LOGGER_LEVEL: str = "DEBUG"  # 日志级别

    # ================================================= #
    # ******************** 跨域配置 ******************** #
    # ================================================= #
    PROD_CORS_ORIGINS: str = ""  # 生产环境允许的域名列表，逗号分隔，如 "https://admin.example.com,https://www.example.com"
    ALLOW_METHODS: list[str] = ["*"]  # 允许的HTTP方法
    ALLOW_HEADERS: list[str] = ["*"]  # 允许的请求头
    ALLOW_CREDENTIALS: bool = True  # 是否允许携带cookie
    CORS_EXPOSE_HEADERS: list[str] = ["X-Request-ID"]

    # ================================================= #
    # ******************* 登录认证配置 ****************** #
    # ================================================= #
    SECRET_KEY: str = "fastapiadmin-dev-secret-key-do-not-use-in-production"  # JWT密钥（必须通过环境变量 SECRET_KEY 设置，无默认值）
    ALGORITHM: str = "HS256"  # JWT算法
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 12  # access_token过期时间(秒)12 小时
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 12  # refresh_token过期时间(秒)12 小时
    TOKEN_TYPE: str = "Bearer"  # token类型（RFC 6750 标准大小写）
    TOKEN_SLIDING_EXPIRE: bool = True  # 是否启用滑动过期(用户操作时自动续期)
    SESSION_MAX_LIFETIME_SECONDS: int = 60 * 60 * 24 * 7  # 会话绝对存活上限(秒)，滑动续期不得超过该上限
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 60  # 登录限流窗口(秒)
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS: int = 10  # 限流窗口内单 IP 最大登录尝试次数

    # ================================================= #
    #  ****************** 数据加密配置 ***************** #
    # ================================================= #
    DATA_ENCRYPTION_KEY: str | None = None  # 数据加密主密钥(建议 openssl rand -hex 32)；未配置时由 SECRET_KEY 经 HKDF 派生
    DATA_ENCRYPTION_OLD_KEYS: str = ""  # 轮换后的旧主密钥列表(逗号分隔)，仅用于解密历史数据

    # ================================================= #
    # ******************** 数据库配置 ******************* #
    # ================================================= #
    DATABASE_ECHO: bool | Literal["debug"] = False  # 是否显示SQL日志
    ECHO_POOL: bool | Literal["debug"] = False  # 是否显示连接池日志
    POOL_SIZE: int = 10  # 连接池大小
    MAX_OVERFLOW: int = 20  # 最大溢出连接数
    POOL_TIMEOUT: int = 30  # 连接超时时间(秒)
    POOL_RECYCLE: int = 1800  # 连接回收时间(秒)
    POOL_USE_LIFO: bool = True  # 是否使用LIFO连接池
    POOL_PRE_PING: bool = True  # 是否开启连接预检
    AUTOCOMMIT: bool = False  # 是否自动提交（映射 SQLAlchemy sessionmaker(autocommit=...)）
    AUTOFLUSH: bool = False  # 是否自动刷新（映射 SQLAlchemy sessionmaker(autoflush=...)）
    AUTOFETCH: bool | None = None  # AUTOFLUSH 别名（优先级高于 AUTOFLUSH，兼容旧环境变量名）
    EXPIRE_ON_COMMIT: bool = False  # 是否在提交时过期

    # MySQL/PostgreSQL数据库连接
    DATABASE_TYPE: Literal["mysql", "postgres", "sqlite"] = "mysql"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str = ""
    DATABASE_NAME: str = "fastapiadmin"

    # ================================================= #
    # ******************** Redis配置 ******************* #
    # ================================================= #
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB_NAME: int = 1
    REDIS_USER: str = ""
    REDIS_PASSWORD: str = ""
    REDIS_HEALTH_CHECK_INTERVAL: int = 20  # Redis 健康检查间隔（秒，对应 async_pool 的 health_check_interval）
    REDIS_DEFAULT_CACHE_TTL: int = 86400  # RedisCURD.set() 默认 TTL（秒，24 小时）

    # ================================================= #
    # ******************** 验证码配置 ******************* #
    # ================================================= #
    CAPTCHA_ENABLE: bool = True  # 是否启用验证码
    CAPTCHA_EXPIRE_SECONDS: int = 60 * 1  # 验证码过期时间(秒) 1分钟
    CAPTCHA_MIN_VERIFY_SECONDS: float = 0.2

    # ================================================= #
    # ******************* 任务调度配置 ****************** #
    # ================================================= #
    SCHEDULER_ALLOW_CODE_EXEC: bool = True  # 是否允许定时任务执行用户提交的代码块(exec)。等同远程代码执行能力，生产环境强烈建议设为 False

    # ================================================= #
    # ******************* 口令策略配置 ****************** #
    # ================================================= #
    PASSWORD_MIN_LENGTH: int = 6
    PASSWORD_MAX_LENGTH: int = 128
    PASSWORD_IMPORT_DEFAULT: str = "123456"

    # ================================================= #
    # ***************** 第三方 OAuth 登录（可选）********* #
    # ================================================= #
    OAUTH_DEFAULT_ROLE_IDS: list[int] = [2]
    OAUTH_FRONTEND_FALLBACK: str = "http://127.0.0.1:5173/login"
    OAUTH_GITHUB_CLIENT_ID: str = ""
    OAUTH_GITHUB_CLIENT_SECRET: str = ""
    OAUTH_GITEE_CLIENT_ID: str = ""
    OAUTH_GITEE_CLIENT_SECRET: str = ""
    OAUTH_WECHAT_OPEN_APP_ID: str = ""
    OAUTH_WECHAT_OPEN_APP_SECRET: str = ""
    OAUTH_QQ_APP_ID: str = ""
    OAUTH_QQ_APP_SECRET: str = ""
    OAUTH_STATE_TTL: int = 600  # OAuth state 参数过期时间（秒）
    OAUTH_ALLOWED_HOSTS: list[str] = ["*"]

    # ================================================= #
    # *************** 微信小程序配置（可选）************** #
    # ================================================= #
    WX_MINI_APP_ID: str = ""  # 小程序 AppID
    WX_MINI_APP_SECRET: str = ""  # 小程序 AppSecret
    WX_MINI_ACCESS_TOKEN_CACHE_TTL: int = 7000  # access_token Redis 缓存秒数（微信上限 7200，留 200s 余量）

    # ================================================= #
    # ******************* 外部 HTTP（httpx）******************* #
    # ================================================= #
    HTTPX_DEFAULT_TIMEOUT: float = 10.0  # 对外 HTTP 请求默认超时（秒）
    IP_LOCATION_ENABLE: bool = True  # 是否启用 IP 归属地查询（登录时对外发起 HTTP 请求）
    IP_LOCATION_CACHE_TTL: int = 2592000  # IP 归属地缓存时间（秒，默认 30 天）
    IP_LOCATION_QUERY_TIMEOUT: float = 3.0  # IP 归属地查询单次 HTTP 超时（秒）

    # ================================================= #
    # ********************* 日志配置 ******************* #
    # ================================================= #
    OPERATION_RECORD_METHOD: list[str] = [
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "HEAD",
        "OPTIONS",
    ]  # 需要记录的请求方法

    # ================================================= #
    # ******************* Gzip压缩配置 ******************* #
    # ================================================= #
    GZIP_MIN_SIZE: int = 1000  # 最小压缩大小(字节)
    GZIP_COMPRESS_LEVEL: int = 9  # 压缩级别(1-9)

    # ================================================= #
    # ******************* 安全中间件配置 ****************** #
    # ================================================= #
    ALLOWED_HOSTS: list[str] = ["service.fastapiadmin.com", "*.fastapiadmin.com"]  # 允许访问的主机名列表

    # 接口白名单（无需认证即可访问的接口路径，支持 * 开头表示前缀匹配）
    WHITE_API_LIST_PATH: list[str] = [
        "/api/v1/system/auth/login",
        "/api/v1/system/auth/token/refresh",
        "/api/v1/system/auth/captcha/get",
        "/api/v1/system/auth/captcha/slider/complete",
        "/api/v1/system/auth/logout",
        "/api/v1/system/param/info",
        "/api/v1/system/dict/info",
        "/api/v1/system/user/current/info",
        "/api/v1/system/notice/available",
        "/api/v1/monitor/health",
        "/metrics",
    ]

    # ================================================= #
    # ***************** 静态文件配置 ***************** #
    # ================================================= #
    STATIC_URL: str = "/static"  # 访问路由

    # ================================================= #
    # ***************** 动态文件配置 ***************** #
    # ================================================= #
    UPLOAD_FILE_PATH: Path = Path("static/upload")  # 上传目录
    UPLOAD_MACHINE: str = "A"  # 上传机器标识
    ALLOWED_EXTENSIONS: list[str] = [  # 允许的文件类型
        ".gif",
        ".jpg",
        ".jpeg",
        ".png",
        ".ico",
        ".svg",
        ".xls",
        ".xlsx",
    ]
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 最大文件大小(10MB)

    # ================================================= #
    # ***************** Swagger配置 ***************** #
    # ================================================= #
    SWAGGER_CSS_URL: str = "static/swagger/swagger-ui/swagger-ui.css"
    SWAGGER_JS_URL: str = "static/swagger/swagger-ui/swagger-ui-bundle.js"
    REDOC_JS_URL: str = "static/swagger/redoc/bundles/redoc.standalone.js"
    FAVICON_URL: str = "static/image/favicon.ico"

    # ================================================= #
    # ******************* AI大模型配置 ****************** #
    # ================================================= #
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = ""
    OPENAI_BASE_URL: str = ""  # API Base URL，如 https://api.minimax.chat/v1

    # ================================================= #
    # ******************* 动态配置 ******************* #
    # ================================================= #
    @property
    def ALLOW_ORIGINS(self) -> list[str]:
        """根据环境动态返回 CORS 允许的域名列表。"""
        if self.ENVIRONMENT == EnvironmentEnum.PROD and self.PROD_CORS_ORIGINS:
            return [origin.strip() for origin in self.PROD_CORS_ORIGINS.split(",") if origin.strip()]
        return ["*"]

    # ================================================= #
    @property
    def REDIS_URI(self) -> str:
        """构建 Redis 连接 URI（供 slowapi / 其他模块复用）。"""
        auth_part = ""
        if self.REDIS_USER and self.REDIS_PASSWORD:
            auth_part = f"{self.REDIS_USER}:{self.REDIS_PASSWORD}@"
        elif self.REDIS_PASSWORD:
            auth_part = f":{self.REDIS_PASSWORD}@"
        return f"redis://{auth_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB_NAME}"

    @property
    def MIDDLEWARE_LIST(self) -> list[str | None]:
        MIDDLEWARES: list[str | None] = [
            "app.core.middlewares.CustomHTTPSRedirectMiddleware" if self.ENVIRONMENT == EnvironmentEnum.PROD else None,
            "app.core.middlewares.CustomTrustedHostMiddleware" if self.ENVIRONMENT == EnvironmentEnum.PROD else None,
            "app.core.middlewares.CustomCORSMiddleware",
            "app.core.middlewares.RequestLogMiddleware",
            "app.core.middlewares.CustomGZipMiddleware",
            "app.core.middlewares.CorrelationIdMiddleware",  # 请求上下文
        ]
        return MIDDLEWARES

    @property
    def ASYNC_DB_URI(self) -> str:
        if self.DATABASE_TYPE not in ("mysql", "postgres", "sqlite"):
            raise ValueError(f"数据库驱动不支持: {self.DATABASE_TYPE}, 异步数据库请选择 mysql、postgres、sqlite")
        db_connect: str = ""
        if self.DATABASE_TYPE == "mysql":
            db_connect = f"mysql+aiomysql://{self.DATABASE_USER}:{quote_plus(self.DATABASE_PASSWORD)}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}?charset=utf8mb4"
        elif self.DATABASE_TYPE == "postgres":
            db_connect = f"postgresql+asyncpg://{self.DATABASE_USER}:{quote_plus(self.DATABASE_PASSWORD)}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        else:
            name = self.DATABASE_NAME if self.DATABASE_NAME.endswith(".db") else f"{self.DATABASE_NAME}.db"
            db_connect = f"sqlite+aiosqlite:///{name}"
        return db_connect

    @property
    def DB_URI(self) -> str:
        if self.DATABASE_TYPE not in ("mysql", "postgres", "sqlite"):
            raise ValueError(f"数据库驱动不支持: {self.DATABASE_TYPE}, 同步数据库请选择 mysql、postgres、sqlite")
        db_connect: str = ""
        if self.DATABASE_TYPE == "mysql":
            db_connect = f"mysql+pymysql://{self.DATABASE_USER}:{quote_plus(self.DATABASE_PASSWORD)}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}?charset=utf8mb4"
        elif self.DATABASE_TYPE == "postgres":
            db_connect = f"postgresql+psycopg://{self.DATABASE_USER}:{quote_plus(self.DATABASE_PASSWORD)}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        else:
            name = self.DATABASE_NAME if self.DATABASE_NAME.endswith(".db") else f"{self.DATABASE_NAME}.db"
            db_connect = f"sqlite:///{name}"
        return db_connect

    @property
    def FASTAPI_CONFIG(self) -> dict[str, Any]:
        return {
            "debug": self.DEBUG,
            "title": self.TITLE,
            "version": self.VERSION,
            "description": self.DESCRIPTION,
            "summary": self.SUMMARY,
            "docs_url": None,
            "redoc_url": None,
            "root_path": self.ROOT_PATH,
            "responses": {
                200: {"description": "成功"},
                400: {"description": "请求参数错误"},
                401: {"description": "未认证"},
                403: {"description": "未授权"},
                404: {"description": "资源不存在"},
                422: {"description": "请求参数验证错误"},
                500: {"description": "服务器内部错误"},
            }
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(_env_file=ENV_DIR / f".env.{os.getenv('ENVIRONMENT', 'dev')}")  # pyright: ignore[reportCallIssue]


settings = get_settings()
