"""FastapiAdmin 应用工厂：唯一的应用构建与生命周期定义点。"""

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import path_conf
from .config.setting import settings
from .core.exceptions import handle_exception
from .core.logger import logger
from .utils.common_util import import_module
from .utils.console import console_end, console_start


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    from app.core.ap_scheduler import SchedulerUtil
    from app.core.database import async_engine
    from app.core.redis_crud import redis_connect
    from app.modules.system.dict.service import DictDataService
    from app.modules.system.params.service import ParamsService
    from app.scripts.initialize import InitializeData

    await InitializeData().init_db()
    logger.info(f"✅ {settings.DATABASE_TYPE} 连接初始化完成")
    await redis_connect(app, status=True)
    logger.info("✅ Redis 连接初始化完成")
    await ParamsService.init_cache(redis=app.state.redis)
    logger.info("✅ Redis系统参数 初始化完成")
    await DictDataService.init_cache(redis=app.state.redis)
    logger.info("✅ Redis数据字典 初始化完成")
    await SchedulerUtil.init_scheduler(redis=app.state.redis)
    logger.info("✅ 定时任务调度器 初始化完成")

    console_start(
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        database_type=settings.DATABASE_TYPE,
        database_ready=True,
        redis_ready=True,
        scheduler_ready=SchedulerUtil.is_scheduler_ready(),
    )

    yield

    try:
        await SchedulerUtil.shutdown(wait=True)
        logger.info("✅ 定时任务调度器已关闭")
        await redis_connect(app, status=False)
        logger.info("✅ redis 连接已关闭")
        await async_engine.dispose()
        logger.info(f"✅ {settings.DATABASE_TYPE} 连接已关闭")
    except Exception as e:
        logger.error("❌ 应用关闭过程中发生错误: {}", e)
        raise SystemExit(1)
    finally:
        console_end()


def register_middlewares(app: FastAPI) -> None:
    for middleware in settings.MIDDLEWARE_LIST[::-1]:
        if not middleware:
            continue
        middleware = import_module(middleware, desc="中间件")
        app.add_middleware(middleware)


def register_exceptions(app: FastAPI) -> None:
    handle_exception(app)


def register_routers(app: FastAPI) -> None:
    from app.api.v1.routers import api_v1
    app.include_router(api_v1)

    from app.core.discover import dynamic_router
    dynamic_router.init_app(app)


def register_static(app: FastAPI) -> None:
    """注册静态文件路由。"""
    path_conf.STATIC_DIR.mkdir(parents=True, exist_ok=True)
    app.mount(path=settings.STATIC_URL, app=StaticFiles(directory=path_conf.STATIC_DIR), name=path_conf.STATIC_DIR.name)


def register_docs(app: FastAPI) -> None:
    """注册文档路由。"""
    swagger_ui_redirect_url = str(app.swagger_ui_oauth2_redirect_url)
    root_openapi_url = str(app.root_path) + str(app.openapi_url)

    @app.get(swagger_ui_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @app.get(settings.DOCS_URL, include_in_schema=False)
    async def custom_swagger_ui_html() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url=root_openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url=settings.SWAGGER_JS_URL,
            swagger_css_url=settings.SWAGGER_CSS_URL,
            swagger_favicon_url=settings.FAVICON_URL,
        )

    @app.get(settings.REDOC_URL, include_in_schema=False)
    async def custom_redoc_html() -> HTMLResponse:
        return get_redoc_html(
            openapi_url=root_openapi_url,
            title=app.title + " - ReDoc",
            redoc_js_url=settings.REDOC_JS_URL,
            redoc_favicon_url=settings.FAVICON_URL,
        )


def register_frontend(app: FastAPI) -> None:
    if path_conf.FRONTEND_DIST_DIR.exists():
        app.mount("/web", StaticFiles(directory=str(path_conf.FRONTEND_DIST_DIR), html=True), name="frontend")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例并完成日志、中间件、路由与静态资源注册。

    返回:
    - FastAPI: 已配置生命周期的应用对象。
    """

    # 创建FastAPI应用
    app = FastAPI(**settings.FASTAPI_CONFIG, lifespan=lifespan)
    # 注册异常处理器
    register_exceptions(app)
    # 注册中间件
    register_middlewares(app)
    # 注册路由
    register_routers(app)
    # 注册静态文件
    register_static(app)
    # 注册API文档（豁免限流）
    register_docs(app)
    # 注册前端
    register_frontend(app)
    return app
