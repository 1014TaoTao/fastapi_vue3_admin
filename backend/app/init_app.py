import asyncio
from collections.abc import AsyncGenerator
from time import monotonic
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .common.enums import EnvironmentEnum
from .config import path_conf
from .config.setting import settings
from .core.exceptions import handle_exception
from .core.logger import logger
from .utils.common_util import import_module
from .utils.console import console_end, console_start

if TYPE_CHECKING:
    from .core.redis_crud import RedisCURD

# 启动初始化单飞（WORKERS > 1 时避免多进程并发建库/迁移/预热）
BOOTSTRAP_LOCK_KEY = "fastapiadmin:bootstrap:lock"
BOOTSTRAP_DONE_KEY = "fastapiadmin:bootstrap:done"
BOOTSTRAP_LOCK_TTL = 300  # 持锁进程崩溃后的锁自动释放时间
BOOTSTRAP_DONE_TTL = 120  # 同批次启动的其它进程在此窗口内跳过重复初始化
BOOTSTRAP_WAIT_SECONDS = 60  # 等待其它进程完成初始化的最长时间


async def _run_bootstrap(app: FastAPI) -> None:
    """执行建库迁移、种子数据与 Redis 缓存预热。"""
    from app.api.v1.module_system.dict.service import DictDataService
    from app.api.v1.module_system.params.service import ParamsService
    from app.scripts.initialize import InitializeData

    await InitializeData().init_db()
    logger.info("✅ {}数据库初始化完成", settings.DATABASE_TYPE)
    await ParamsService.init_cache(redis=app.state.redis)
    logger.info("✅ Redis系统参数初始化完成")
    await DictDataService.init_cache(redis=app.state.redis)
    logger.info("✅ Redis数据字典初始化完成")


async def _wait_for_bootstrap(crud: "RedisCURD") -> bool:
    """等待持锁进程完成初始化；返回 True 表示已完成，False 表示需要自行执行。"""
    deadline = monotonic() + BOOTSTRAP_WAIT_SECONDS
    while monotonic() < deadline:
        if await crud.get(key=BOOTSTRAP_DONE_KEY):
            return True
        if not await crud.get(key=BOOTSTRAP_LOCK_KEY):
            return False  # 持锁进程已退出且未标记完成（多半失败），交由本进程重试
        await asyncio.sleep(0.5)
    return False


async def _bootstrap(app: FastAPI) -> None:
    """全局初始化：多 worker 部署时仅由抢到 Redis 锁的进程执行一次。"""
    from app.core.redis_crud import RedisCURD

    crud = RedisCURD(app.state.redis)
    acquired, token = await crud.lock(key=BOOTSTRAP_LOCK_KEY, expire=BOOTSTRAP_LOCK_TTL)
    if acquired:
        try:
            await _run_bootstrap(app)
            await crud.set(key=BOOTSTRAP_DONE_KEY, value=token, expire=BOOTSTRAP_DONE_TTL)
        finally:
            await crud.unlock(key=BOOTSTRAP_LOCK_KEY, value=token)
        return

    if await _wait_for_bootstrap(crud):
        logger.info("✅ 其它进程已完成数据库与缓存初始化，本进程跳过")
        return

    logger.warning("⚠️ 未等到其它进程完成初始化，本进程自行执行一次")
    await _run_bootstrap(app)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    from app.core.ap_scheduler import SchedulerUtil
    from app.core.database import async_engine, redis_connect

    await redis_connect(app, status=True)
    logger.info("✅ Redis 连接初始化完成")
    await _bootstrap(app)

    await SchedulerUtil.init_scheduler(redis=app.state.redis)
    logger.info("✅ 定时任务调度器初始化完成")

    # 生产环境未显式配置 CORS 域名时给出安全告警（此时 ALLOW_ORIGINS 回退为 "*"）
    if settings.ENVIRONMENT == EnvironmentEnum.PROD and not settings.PROD_CORS_ORIGINS:
        logger.warning("⚠️ 生产环境未配置 PROD_CORS_ORIGINS，CORS 允许所有来源；建议配置具体域名列表")

    console_start(
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        database_type=settings.DATABASE_TYPE,
        database_ready=True,
        redis_ready=True,
        scheduler_ready=SchedulerUtil.is_running(),
    )

    yield

    try:
        # 先停跨进程订阅协程，避免 Redis 关闭后其 listen 循环抛错刷日志
        from app.core.ws_manager import stop_ws_relays

        stop_ws_relays()
        SchedulerUtil.shutdown(wait=True)
        logger.info("✅ 定时任务调度器已关闭")
        await redis_connect(app, status=False)
        logger.info("✅ Redis 连接已关闭")
        await async_engine.dispose()
        logger.info("✅ 数据库引擎连接池已释放")
        console_end()
    except Exception as e:
        logger.error("❌ 应用关闭过程中发生错误: {}", e)
        raise SystemExit(1)


def register_middlewares(app: FastAPI) -> None:
    for middleware in settings.MIDDLEWARE_LIST[::-1]:
        if not middleware:
            continue
        middleware = import_module(middleware, desc="中间件")
        app.add_middleware(middleware)


def register_exceptions(app: FastAPI) -> None:
    handle_exception(app)


def register_routers(app: FastAPI) -> None:
    from app.api.v1.module_ai import ai_router
    from app.api.v1.module_common import common_router
    from app.api.v1.module_generator import generator_router
    from app.api.v1.module_monitor import monitor_router
    from app.api.v1.module_system import system_router
    from app.api.v1.module_task import task_router

    app.include_router(common_router)
    app.include_router(monitor_router)
    app.include_router(system_router)
    app.include_router(ai_router)
    app.include_router(generator_router)
    app.include_router(task_router)

    # 组合根：业务模块已就绪，把 api 层能力登记进 core 注入点（core 保持纯基础层）
    from app.api.v1.core_backends import register_core_backends

    register_core_backends()

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
    async def custom_redoc_html():
        return get_redoc_html(
            openapi_url=root_openapi_url,
            title=app.title + " - ReDoc",
            redoc_js_url=settings.REDOC_JS_URL,
            redoc_favicon_url=settings.FAVICON_URL,
        )


def register_frontend(app: FastAPI) -> None:
    if path_conf.FRONTEND_DIST_DIR.exists():
        app.mount("/web", StaticFiles(directory=str(path_conf.FRONTEND_DIST_DIR), html=True), name="frontend")
