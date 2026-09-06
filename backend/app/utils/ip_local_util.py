import hashlib
import ipaddress
import json
import re
from collections.abc import Callable

import httpx
from starlette.requests import Request

from app.common.enums import RedisInitKeyConfig, SysParamKey
from app.config.setting import settings
from app.core.logger import logger
from app.core.redis_crud import RedisCURD

# 归属地缓存：IP 几乎不变化，缓存 7 天可显著减少外网请求
_IP_CACHE_TTL: int = settings.IP_LOCATION_CACHE_TTL
# 硬超时（秒），避免外网查询阻塞主流程
_IP_QUERY_TIMEOUT: float = settings.IP_LOCATION_QUERY_TIMEOUT

# 归属地降级返回文案（登录日志/会话共用，调用方按字面量比较）
LOCATION_INTRANET = "内网IP"
LOCATION_DISABLED = "未解析(已关闭归属地查询)"
LOCATION_PENDING = "归属地查询中"
LOCATION_UNKNOWN = "未知"


def get_client_ip(request: Request) -> str:
    """从请求中提取客户端真实 IP（优先取反向代理透传的头部，返回空字串表示无法识别）。"""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP", "")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host or ""
    return ""


def get_client_fingerprint(request: Request) -> str:
    """客户端来源指纹（IP + User-Agent 摘要）。

    用于把一次性凭证（如验证码 key）绑定到签发它的来源，避免攻击者批量预取
    凭证后再投毒给其它请求使用。UA 由客户端可控，因此这里只能提高滥用成本，
    不能替代真实的人机校验。
    """
    ua = request.headers.get("user-agent", "")
    return hashlib.sha256(f"{get_client_ip(request)}|{ua}".encode()).hexdigest()[:32]


class IpLocalUtil:
    """获取 IP 归属地工具类（带 Redis 缓存、查询决策、硬超时、降级）。"""

    @classmethod
    def is_valid_ip(cls, ip: str | None) -> bool:
        if not ip:
            return False
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @classmethod
    def is_private_ip(cls, ip: str | None) -> bool:
        """判断是否为非公网地址（内网/回环/链路本地/保留段）。

        这类地址无法通过外网归属地 API 解析，用 ``is_global`` 取反判断最稳妥。
        """
        if not ip:
            return False
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            return False
        return not addr.is_global

    @classmethod
    async def _is_location_enabled(cls, redis) -> bool:
        """从参数缓存读取 IP 归属地查询开关。"""
        if not redis:
            return False
        redis_key = f"{RedisInitKeyConfig.SYSTEM_CONFIG.key}:{SysParamKey.IP_LOCATION_ENABLE.value}"
        try:
            raw = await RedisCURD(redis).get(redis_key)
            if raw:
                payload = json.loads(raw)
                cv = payload.get("config_value", "off")
                return cv in (True, "true", "1", "yes", "on")
        except Exception:
            pass
        return False

    @classmethod
    async def _should_query(cls, redis, ip: str | None) -> bool:
        """判断 IP 是否需要发起外网归属地查询（前置条件 + 开关 + IP 类型）。

        不查询的情形（短路返回 False）：
        1. IP 为空或非法 —— 无法查询
        2. Redis 不可用 —— 读不到开关与缓存，直接降级
        3. 开关关闭（ip_location_enable != on）—— 功能总闸
        4. 内网/回环/保留地址 —— 外网 API 无法解析

        缓存命中与否由调用方处理（命中直接返回，未命中才需要查）。
        """
        if not cls.is_valid_ip(ip):
            return False
        if not redis:
            return False
        if not await cls._is_location_enabled(redis):
            return False
        if cls.is_private_ip(ip):
            return False
        return True

    @classmethod
    async def resolve_location_for_log(cls, redis, ip: str | None) -> str | None:
        """登录日志写入入口：仅返回可同步获取的值（开关/内网/缓存）。

        外网查询由后台任务异步执行（见 ``resolve_location_async``），
        此处只做查询决策与缓存读取，不发起任何外网请求。
        """
        if not cls.is_valid_ip(ip):
            return None
        assert ip is not None  # is_valid_ip 已确保非空
        if not await cls._should_query(redis, ip):
            return LOCATION_INTRANET if cls.is_private_ip(ip) else LOCATION_DISABLED
        if redis:
            cached = await cls._cache_get(redis, ip)
            if cached is not None:
                return cached
        return LOCATION_PENDING

    @classmethod
    async def resolve_location_async(cls, redis, ip: str) -> str:
        """异步查询归属地（含决策、缓存、降级、硬超时）。仅供后台任务调用。

        仅查询成功的结果写入缓存池（IP 池），失败（未知）不写缓存，
        下次登录仍会重试，避免缓存池被无效值污染。
        """
        if not cls.is_valid_ip(ip):
            return LOCATION_UNKNOWN
        if not await cls._should_query(redis, ip):
            return LOCATION_INTRANET if cls.is_private_ip(ip) else LOCATION_DISABLED
        if redis:
            cached = await cls._cache_get(redis, ip)
            if cached is not None:
                return cached
        result = await cls._query_with_timeout(ip)
        if redis and result != LOCATION_UNKNOWN:
            await cls._cache_set(redis, ip, result)
        return result

    @classmethod
    async def _query_with_timeout(cls, ip: str) -> str:
        """在硬超时内依次尝试多个 API，全部失败返回未知。"""
        apis: list[tuple[str, Callable, dict[str, str]]] = [
            ("http://ip-api.com/json", cls._parse_ipapi, {"lang": "zh-CN"}),
            ("https://whois.pconline.com.cn/ipJson.jsp", cls._parse_pconline, {"ip": ip, "json": "true"}),
        ]
        async with httpx.AsyncClient(timeout=_IP_QUERY_TIMEOUT) as client:
            for url, parser, params in apis:
                try:
                    resp = await client.get(f"{url}/{ip}" if "ip-api" in url else url, params=params)
                    if resp.status_code == 200:
                        data = resp.json() if "ip-api" in url else resp.text
                        location = parser(data)
                        if location:
                            return location
                except Exception as e:
                    logger.warning(f"IP 归属地 API 失败: {url} - {e}")
        return LOCATION_UNKNOWN

    @staticmethod
    def _parse_ipapi(data: dict) -> str | None:
        if data.get("status") != "success":
            return None
        parts = [data.get("country"), data.get("regionName"), data.get("city"), data.get("isp")]
        joined = "-".join(filter(None, parts))
        return joined or None

    @staticmethod
    def _parse_pconline(text: str) -> str | None:
        """解析 pconline 返回的 JSONP 文本，格式如 'if( {\"ip\":\"...\",\"pro\":\"省\",\"city\":\"市\"} )'。"""
        try:
            match = re.search(r"\{.*\}", text)
            if not match:
                return None
            data = json.loads(match.group())
            parts = [data.get("pro"), data.get("city"), data.get("addr")]
            joined = " ".join(filter(None, parts))
            return joined or None
        except Exception:
            return None

    @staticmethod
    async def _cache_get(redis, ip: str) -> str | None:
        try:
            value = await RedisCURD(redis).get(f"ip:location:{ip}")
            return value.decode("utf-8") if value else None
        except Exception:
            return None

    @staticmethod
    async def _cache_set(redis, ip: str, value: str) -> None:
        try:
            await RedisCURD(redis).set(f"ip:location:{ip}", value, expire=_IP_CACHE_TTL)
        except Exception:
            pass
