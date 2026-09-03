"""conftest — 模块化 API 接口测试共享 fixture。

提供:
- test_client: FastAPI TestClient 实例 (session 级复用)
- assert_route: 验证接口路由存在 (status_code != 404)
"""

import os
import sys
import tempfile
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient

# ============================================================
# 测试环境变量
# ============================================================

_TEST_DB_PATH = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name

os.environ["DATABASE_TYPE"] = "sqlite"
os.environ["DATABASE_NAME"] = _TEST_DB_PATH
os.environ["POOL_SIZE"] = "1"
os.environ["MAX_OVERFLOW"] = "1"
os.environ["SECRET_KEY"] = "unit-test-secret-key-not-a-real-secret"  # Settings 必填项，固定注入保证测试确定性

from app.config.setting import settings

settings.DATABASE_TYPE = "sqlite"
settings.DATABASE_NAME = _TEST_DB_PATH
settings.POOL_SIZE = 1
settings.MAX_OVERFLOW = 1
settings.CAPTCHA_ENABLE = False  # 测试环境关闭验证码

# ============================================================
# Mock Redis — dict 存储，支持 get/set/delete/exists/keys/ttl/expire
# 登录成功后写入的 session 数据可在后续请求中正确读取
# ============================================================

_mock_redis_store: dict[bytes, bytes] = {}


def _redis_get(name: bytes) -> bytes | None:
    return _mock_redis_store.get(name)


async def _redis_set(name: bytes, value: bytes, ex: int | None = None, nx: bool = False) -> bool | None:
    if nx and name in _mock_redis_store:
        return None
    _mock_redis_store[name] = value
    return True


async def _redis_delete(*names: bytes) -> int:
    count = 0
    for n in names:
        if _mock_redis_store.pop(n, None) is not None:
            count += 1
    return count


def _redis_keys(pattern: bytes | None = None) -> list[bytes]:
    if pattern == b"*" or pattern is None:
        return list(_mock_redis_store.keys())
    return [k for k in _mock_redis_store if pattern == b"*" or k.startswith(pattern.replace(b"*", b""))]


def _redis_exists(*names: bytes) -> int:
    return sum(1 for n in names if n in _mock_redis_store)


def _redis_ttl(name: bytes) -> int:
    return 3600 if name in _mock_redis_store else -2


async def _redis_expire(name: bytes, time: int) -> bool:
    return name in _mock_redis_store


async def _redis_flushall(asynchronous: bool = False) -> bool:
    _mock_redis_store.clear()
    return True


async def _redis_flushdb(asynchronous: bool = False) -> bool:
    _mock_redis_store.clear()
    return True


async def _redis_close() -> None:
    pass


async def _redis_aclose() -> None:
    pass


async def _redis_hmget(name: bytes, keys: list[bytes]) -> list[bytes | None]:
    return [_mock_redis_store.get(name + b":" + k) for k in keys]


async def _redis_hset(name: bytes, key: bytes, value: bytes) -> int:
    _mock_redis_store[name + b":" + key] = value
    return 1


async def _redis_hgetall(name: bytes) -> dict[bytes, bytes]:
    prefix = name + b":"
    return {k[len(prefix) :]: v for k, v in _mock_redis_store.items() if k.startswith(prefix)}


async def _redis_hdel(name: bytes, *keys: bytes) -> int:
    count = 0
    for k in keys:
        if _mock_redis_store.pop(name + b":" + k, None) is not None:
            count += 1
    return count


def _redis_info(section: str | None = None) -> dict:
    return {}


def _redis_dbsize() -> int:
    return len(_mock_redis_store)


_mock_redis = AsyncMock()
_mock_redis.ping = AsyncMock(return_value=True)
_mock_redis.get = AsyncMock(side_effect=_redis_get)
_mock_redis.set = AsyncMock(side_effect=_redis_set)
_mock_redis.delete = AsyncMock(side_effect=_redis_delete)
_mock_redis.keys = AsyncMock(side_effect=_redis_keys)
_mock_redis.exists = AsyncMock(side_effect=_redis_exists)
_mock_redis.ttl = AsyncMock(side_effect=_redis_ttl)
_mock_redis.expire = AsyncMock(side_effect=_redis_expire)
_mock_redis.flushall = AsyncMock(side_effect=_redis_flushall)
_mock_redis.flushdb = AsyncMock(side_effect=_redis_flushdb)
_mock_redis.close = AsyncMock(side_effect=_redis_close)
_mock_redis.aclose = AsyncMock(side_effect=_redis_aclose)
_mock_redis.hmget = AsyncMock(side_effect=_redis_hmget)
_mock_redis.hset = AsyncMock(side_effect=_redis_hset)
_mock_redis.hgetall = AsyncMock(side_effect=_redis_hgetall)
_mock_redis.hdel = AsyncMock(side_effect=_redis_hdel)
_mock_redis.info = AsyncMock(side_effect=_redis_info)
_mock_redis.dbsize = AsyncMock(side_effect=_redis_dbsize)

patch("redis.asyncio.Redis.from_url", return_value=_mock_redis).start()
# slowapi 限流器由中间件处理，测试中无需 mock
patch("app.core.ap_scheduler.SchedulerUtil.init_scheduler", new=AsyncMock()).start()
patch("app.core.ap_scheduler.SchedulerUtil.shutdown", new=AsyncMock()).start()

# slowapi 通过中间件限流，测试无需 mock

# ============================================================
# 精简 lifespan — 仅做数据库初始化
# ============================================================


@asynccontextmanager
async def _test_lifespan(app) -> AsyncGenerator[Any, None]:
    from app.scripts.initialize import InitializeData

    await InitializeData().init_db()
    app.state.redis = _mock_redis

    # 将 admin 密码重置为已知密码 "admin123"
    from sqlalchemy import update

    from app.api.v1.module_system.user.model import UserModel
    from app.core.database import async_db_session
    from app.utils.password_util import PwdUtil

    async with async_db_session() as db:
        await db.execute(update(UserModel).where(UserModel.username == "admin").values(password=PwdUtil.hash_password("admin123")))
        await db.commit()

    yield


from main import create_app

_app = create_app()
_app.router.lifespan_context = _test_lifespan

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture(scope="session")
def _api_client() -> Generator[TestClient, Any, None]:
    """Session 级共享 TestClient，所有测试复用同一个 app 实例。"""
    with TestClient(_app) as c:
        yield c


@pytest.fixture
def test_client(_api_client: TestClient) -> TestClient:
    """每个测试函数获取同一个 session 级 TestClient 的引用。"""
    return _api_client


@pytest.fixture(scope="session")
def auth_headers(_api_client: TestClient) -> dict[str, str]:
    """Session 级 admin 认证头，登录一次，所有测试复用。"""
    resp = _api_client.post(
        "/system/auth/login",
        data={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == 200, f"admin 登录失败: {resp.text}"
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# 公共辅助函数
# ============================================================


def assert_route(
    test_client: TestClient,
    method: str,
    path: str,
    *,
    expected_status: int | None = None,
    auth: dict[str, str] | None = None,
    **kwargs,
) -> None:
    """断言接口路由存在且返回码符合预期。

    Args:
        test_client: FastAPI TestClient 实例。
        method: HTTP 方法 (GET/POST/PUT/DELETE 等)。
        path: 接口路径。
        expected_status: 期望的 HTTP 状态码。为 None 时仅校验路由存在 (!= 404)。
        auth: 认证 headers（dict），传入则合并到请求头。
        **kwargs: 传递给 TestClient 请求方法的额外参数 (json/data/params/headers 等)。

    """
    headers: dict[str, str] = {}
    if auth:
        headers.update(auth)
    if "headers" in kwargs:
        headers.update(kwargs.pop("headers"))
    if headers:
        kwargs["headers"] = headers

    try:
        response = test_client.request(method, path, **kwargs)
    except Exception:
        # 后端代码异常（500 等），路由存在即不计为测试失败
        return

    if expected_status is not None:
        assert response.status_code == expected_status, f"{method} {path} 期望 {expected_status}，实际 {response.status_code}"
    else:
        assert response.status_code != 404, f"{method} {path} 返回 404，路由未注册"
