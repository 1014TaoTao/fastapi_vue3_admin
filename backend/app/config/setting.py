# -*- coding: utf-8 -*-

import os
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Union
from pydantic import MongoDsn, RedisDsn, MySQLDsn, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from uvicorn.config import LifespanType

from app.common.enums import EnvironmentEnum


class Settings(BaseSettings):
    """系统配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    ENVIRONMENT: str

    BANNER: ClassVar[str] = """
     ______        _                  _ 
    |  ____|      | |     /\         (_)
    | |__ __ _ ___| |_   /  \   _ __  _ 
    |  __/ _` / __| __| / /\ \ | '_ \| |
    | | | (_| \__ \ |_ / ____ \| |_) | |
    |_|  \__,_|___/\__/_/    \_\ .__/|_|
                               | |      
                               |_|
    """
    # ================================================= #
    # ******************* 项目配置 ****************** #
    # ================================================= #
    # 项目根目录
    BASE_DIR: Path = Path(__file__).parent.parent.parent

    # ================================================= #
    # ******************* 服务器配置 ****************** #
    # ================================================= #
    SERVER_HOST: str  # 允许访问的IP地址
    SERVER_PORT: int  # 服务端口
    RELOAD: bool  # 是否自动重启
    FACTORY: bool  # 是否使用异步模式
    LIFESPAN: LifespanType  # 生命周期模式
    WORKERS: int  # 启动进程数
    LIMIT_CONCURRENCY: int  # 最大并发连接数
    BACKLOG: int  # 等待队列最大连接数
    LIMIT_MAX_REQUESTS: int  # HTTP最大请求数
    TIMEOUT_KEEP_ALIVE: int  # 保持连接时间(秒)

    # ================================================= #
    # ******************* API文档配置 ****************** #
    # ================================================= #
    DEBUG: bool  # 调试模式
    TITLE: str  # 文档标题
    VERSION: str  # 版本号
    DESCRIPTION: str  # 文档描述
    SUMMARY: str | None  # 文档概述
    DOCS_URL: str | None  # Swagger UI路径
    REDOC_URL: str | None  # ReDoc路径
    ROOT_PATH: str  # API路由前缀

    # ================================================= #
    # ******************** 跨域配置 ******************** #
    # ================================================= #
    CORS_ORIGIN_ENABLE: bool = True  # 是否启用跨域
    ALLOW_ORIGINS: List[str] = ["*"]  # 允许的域名列表
    ALLOW_METHODS: List[str] = ["*"]  # 允许的HTTP方法
    ALLOW_HEADERS: List[str] = ["*"]  # 允许的请求头
    ALLOW_CREDENTIALS: bool = True  # 是否允许携带cookie

    # ================================================= #
    # ******************* 登录认证配置 ****************** #
    # ================================================= #
    SECRET_KEY: str = "vgb0tnl9d58+6n-6h-ea&u^1#s0ccp!794=krylxcjq75vzps$"  # JWT密钥
    ALGORITHM: str = "HS256"  # JWT算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # access_token过期时间(分钟)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # refresh_token过期时间(分钟)
    TOKEN_TYPE: str = "bearer"  # token类型

    # ================================================= #
    # ******************** 数据库配置 ******************* #
    # ================================================= #
    SQL_DB_ENABLE: bool = True  # 是否启用数据库
    DATABASE_ECHO: bool = False  # 是否显示SQL日志
    ECHO_POOL: bool = False  # 是否显示连接池日志
    POOL_SIZE: int = 20  # 连接池大小
    MAX_OVERFLOW: int = 10  # 最大溢出连接数
    POOL_TIMEOUT: int = 30  # 连接超时时间(秒)
    POOL_RECYCLE: int = 1800  # 连接回收时间(秒)
    POOL_PRE_PING: bool = True  # 是否开启连接预检
    FUTURE: bool = True  # 是否使用SQLAlchemy 2.0特性
    AUTOCOMMIT: bool = False  # 是否自动提交
    AUTOFETCH: bool = False  # 是否自动获取
    EXPIRE_ON_COMMIT: bool = False  # 是否在提交时过期

    # ORM数据库连接
    ORM_DB_DRIVER: str
    ORM_DB_ENABLE: bool
    ORM_DB_HOST: str
    ORM_DB_USER: str
    ORM_DB_PASSWORD: str
    ORM_DB_PORT: int
    ORM_DB_NAME: str

    # ================================================= #
    # ******************** MongoDB配置 ******************* #
    # ================================================= #
    MONGO_DB_ENABLE: bool  # 是否启用MongoDB
    MONGO_DB_USER: str
    MONGO_DB_PASSWORD: str
    MONGO_DB_HOST: str
    MONGO_DB_PORT: int
    MONGO_DB_NAME: str

    # ================================================= #
    # ******************** Redis配置 ******************* #
    # ================================================= #
    REDIS_ENABLE: bool  # 是否启用Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB_NAME: int
    REDIS_USER: str
    REDIS_PASSWORD: str

    # ================================================= #
    # ******************** 验证码配置 ******************* #
    # ================================================= #
    CAPTCHA_ENABLE: bool = True  # 是否启用验证码
    CAPTCHA_EXPIRE_SECONDS: int = 60  # 验证码过期时间(秒)
    CAPTCHA_FONT_SIZE: int = 40  # 字体大小
    CAPTCHA_FONT_PATH: Path = "static/assets/font/Arial.ttf"  # 字体路径

    # ================================================= #
    # ********************* 日志配置 ******************* #
    # ================================================= #
    LOGGER_LEVEL: str  # 日志级别
    LOGGER_NAME: str = date.today().strftime(r"%Y-%m-%d.log")  # 日志文件名
    LOGGER_DIR: Path = BASE_DIR.joinpath("logs")
    if not LOGGER_DIR.exists():
        LOGGER_DIR.mkdir(parents=True, exist_ok=True)
    LOGGER_FILEPATH: Path = LOGGER_DIR.joinpath(LOGGER_NAME)  # 日志文件路径
    BACKUPCOUNT: int = 10  # 日志文件备份数
    WHEN: str = "MIDNIGHT"  # 日志分割时间
    INTERVAL: int = 1  # 日志分割间隔
    ENCODING: str = "utf-8"  # 日志编码
    LOGGER_FORMAT: str = "%(asctime)s - %(levelname)s - [%(name)s:%(filename)s:%(funcName)s:%(lineno)d] %(message)s"  # 日志格式
    OPERATION_LOG_RECORD: bool = True  # 是否记录操作日志
    OPERATION_RECORD_METHOD: List[str] = [
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "HEAD",
        "OPTIONS",
    ]  # 需要记录的请求方法
    IGNORE_OPERATION_FUNCTION: List[str] = ["get_captcha_for_login"]  # 忽略记录的函数

    # ================================================= #
    # ******************* Gzip压缩配置 ******************* #
    # ================================================= #
    GZIP_ENABLE: bool = True  # 是否启用Gzip
    GZIP_MIN_SIZE: int = 1000  # 最小压缩大小(字节)
    GZIP_COMPRESS_LEVEL: int = 9  # 压缩级别(1-9)

    # ================================================= #
    # ***************** 演示模型配置 ***************** #
    # ================================================= #
    DEMO_ENABLE: bool  # 是否开启演示模式
    DEMO_WHITE_LIST_PATH: List[str] = [  # 演示白名单
        "/api/v1/system/auth/login",
        "/api/v1/system/auth/token/refresh",
        "/api/v1/system/auth/captcha/get",
        "/api/v1/system/auth/logout",
    ]
    DEMO_BLACK_LIST_PATH: List[str] = [  # 演示黑名单
        "/auth/login"
    ]

    # ================================================= #
    # ***************** 静态文件配置 ***************** #
    # ================================================= #
    STATIC_ENABLE: bool = True  # 是否启用静态文件
    STATIC_URL: str = "/static"  # 访问路由
    STATIC_DIR: str = "static"  # 目录名
    STATIC_ROOT: Path = BASE_DIR.joinpath(STATIC_DIR)  # 绝对路径

    # ================================================= #
    # ***************** 动态文件配置 ***************** #
    # ================================================= #
    UPLOAD_FILE_PATH: Path = "static/upload"  # 上传目录
    UPLOAD_MACHINE: str = "A"  # 上传机器标识
    ALLOWED_EXTENSIONS: list[str] = [  # 允许的文件类型
        # 图片
        ".bmp",
        ".gif",
        ".jpg",
        ".jpeg",
        ".png",
        ".ico",
        # 文档
        ".csv",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".html",
        ".htm",
        ".txt",
        ".pdf",
        # 压缩包
        ".rar",
        ".zip",
        ".gz",
        ".bz2",
        # 视频
        ".mp4",
        ".avi",
        ".rmvb",
    ]
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 最大文件大小(10MB)

    # ================================================= #
    # ***************** Swagger配置 ***************** #
    # ================================================= #
    SWAGGER_CSS_URL: Path = "static/swagger/swagger-ui/swagger-ui.css"
    SWAGGER_JS_URL: Path = "static/swagger/swagger-ui/swagger-ui-bundle.js"
    REDOC_JS_URL: Path = "static/swagger/redoc/bundles/redoc.standalone.js"
    FAVICON_URL: Path = "static/swagger/favicon.png"

    # ================================================= #
    # ******************* 初始化数据 ****************** #
    # ================================================= #
    SCRIPT_DIR: Path = BASE_DIR.joinpath("app/scripts/data")  # 管理员路由目录

    # ================================================= #
    # ******************* 其他配置 ******************* #
    # ================================================= #
    @property
    def MIDDLEWARE_LIST(self) -> List[Optional[str]]:
        """获取项目根目录"""
        # 中间件列表
        MIDDLEWARES: List[Optional[str]] = [
            "app.core.middlewares.CustomCORSMiddleware"
            if self.CORS_ORIGIN_ENABLE
            else None,
            "app.core.middlewares.RequestLogMiddleware"
            if self.OPERATION_LOG_RECORD
            else None,
            "app.core.middlewares.CustomGZipMiddleware" if self.GZIP_ENABLE else None,
            "app.core.middlewares.DemoEnvMiddleware" if self.DEMO_ENABLE else None,
        ]
        return MIDDLEWARES

    @property
    def EVENT_LIST(self) -> List[Optional[str]]:
        # 事件列表
        EVENTS: List[Optional[str]] = [
            "app.core.database.mongodb_connect" if self.MONGO_DB_ENABLE else None,
            "app.core.database.redis_connect" if self.REDIS_ENABLE else None,
        ]
        return EVENTS

    @property
    def DB_URI(self) -> str:
        """获取数据库连接"""
        supported_db_drivers = ("sqlite", "mysql", "sqlserver", "postgresql")
        if settings.ORM_DB_DRIVER not in supported_db_drivers:
            raise ValueError(
                f"数据库驱动不支持: {settings.ORM_DB_DRIVER}, 请选择 {supported_db_drivers}"
            )
        if settings.ORM_DB_DRIVER == "mysql":
            MYSQL_URI: MySQLDsn = f"mysql+asyncmy://{settings.ORM_DB_USER}:{settings.ORM_DB_PASSWORD}@{settings.ORM_DB_HOST}:{settings.ORM_DB_PORT}/{settings.ORM_DB_NAME}?charset=utf8mb4"
            return MYSQL_URI
        elif settings.ORM_DB_DRIVER == "sqlserver":
            SQLSERVER_URI: str = f"mssql+aioodbc://{settings.ORM_DB_USER}:{settings.ORM_DB_PASSWORD}@{settings.ORM_DB_HOST}:{settings.ORM_DB_PORT}/{settings.ORM_DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server"
            return SQLSERVER_URI
        elif settings.ORM_DB_DRIVER == "postgresql":
            POSTGRESQL_URI: PostgresDsn = f"postgresql+asyncpg://{settings.ORM_DB_USER}:{settings.ORM_DB_PASSWORD}@{settings.ORM_DB_HOST}:{settings.ORM_DB_PORT}/{settings.ORM_DB_NAME}"
            return POSTGRESQL_URI
        else:
            SQLITE_URI: str = f"sqlite+aiosqlite:///{settings.BASE_DIR.joinpath(settings.ORM_DB_NAME)}.db?characterEncoding=UTF-8"
            return SQLITE_URI

    @property
    def DATABASES_URI(self) -> str:
        """获取数据库连接"""
        supported_db_drivers = ("sqlite", "mysql")
        if settings.DB_DRIVER not in supported_db_drivers:
            raise ValueError(
                f"数据库驱动不支持: {settings.DB_DRIVER}, 请选择 {supported_db_drivers}"
            )
        if settings.DB_DRIVER == "mysql":
            MYSQL_URI: MySQLDsn = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB_NAME}?charset=utf8mb4"
            return MYSQL_URI
        else:
            SQLITE_URI: str = f"sqlite:///{settings.BASE_DIR.joinpath(settings.SQLITE_DB_NAME)}?characterEncoding=UTF-8"
            return SQLITE_URI

    @property
    def MONGO_DB_URI(self) -> MongoDsn:
        """获取MongoDB连接"""
        if settings.MONGO_DB_USER and settings.MONGO_DB_PASSWORD:
            return f"mongodb://{settings.MONGO_DB_USER}:{settings.MONGO_DB_PASSWORD}@{settings.MONGO_DB_HOST}:{settings.MONGO_DB_PORT}/{settings.MONGO_DB_NAME}"
        else:
            return f"mongodb://{settings.MONGO_DB_HOST}:{settings.MONGO_DB_PORT}/{settings.MONGO_DB_NAME}"

    @property
    def REDIS_URI(self) -> RedisDsn:
        """获取Redis连接"""
        return f"redis://{settings.REDIS_USER}:{self.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB_NAME}"

    @property
    def FASTAPI_CONFIG(self) -> Dict[str, Union[str, bool, None]]:
        """获取FastAPI应用属性"""
        return {
            "debug": self.DEBUG,
            "title": self.TITLE,
            "version": self.VERSION,
            "description": self.DESCRIPTION,
            "summary": self.SUMMARY,
            "docs_url": None,
            "redoc_url": None,
            "root_path": self.ROOT_PATH,
        }

    @property
    def UVICORN_CONFIG(self) -> Dict[str, Any]:
        """获取Uvicorn配置"""
        return {
            "host": self.SERVER_HOST,
            "port": self.SERVER_PORT,
            "reload": self.RELOAD,
            "log_config": {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "()": "uvicorn.logging.DefaultFormatter",
                        "fmt": self.LOGGER_FORMAT,
                        "use_colors": None,
                    },
                    "access": {
                        "()": "uvicorn.logging.AccessFormatter",
                        "fmt": self.LOGGER_FORMAT,
                    },
                },
                "handlers": {
                    "console": {
                        "formatter": "default",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stderr",
                    },
                    "access_console": {
                        "formatter": "access",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                    },
                    "file": {
                        "formatter": "default",
                        "class": "logging.handlers.TimedRotatingFileHandler",
                        "filename": self.LOGGER_FILEPATH,
                        "when": self.WHEN,
                        "backupCount": self.BACKUPCOUNT,
                        "encoding": self.ENCODING,
                    },
                },
                "loggers": {
                    "uvicorn": {
                        "handlers": ["file", "console"],
                        "level": self.LOGGER_LEVEL,
                        "propagate": False,
                    },
                    "uvicorn.error": {
                        "handlers": ["file", "console"],
                        "level": self.LOGGER_LEVEL,
                        "propagate": False,
                    },
                    "uvicorn.access": {
                        "handlers": ["file", "access_console"],
                        "level": self.LOGGER_LEVEL,
                        "propagate": False,
                    },
                },
            },
            "workers": self.WORKERS,
            "limit_concurrency": self.LIMIT_CONCURRENCY,
            "backlog": self.BACKLOG,
            "limit_max_requests": self.LIMIT_MAX_REQUESTS,
            "timeout_keep_alive": self.TIMEOUT_KEEP_ALIVE,
            "lifespan": self.LIFESPAN,
            "factory": self.FACTORY,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取配置实例"""
    env = os.getenv("ENVIRONMENT", EnvironmentEnum.DEV.value)
    if env not in [e.value for e in EnvironmentEnum]:
        raise ValueError(f"无效的环境配置: {env}")

    env_file = Path(__file__).parent.parent.parent / "env" / f".env.{env}"

    if not env_file.exists():
        raise FileNotFoundError(f"环境配置文件不存在: {env_file}")

    return Settings(_env_file=env_file)


settings = get_settings()
