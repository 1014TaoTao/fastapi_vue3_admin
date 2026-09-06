"""静态数据加密工具（Fernet 对称加密）。

用于统一「落库/落缓存的敏感字段」加密方式（存储源口令、AI 密钥等），
密钥与 JWT 签名密钥分离：

- 主密钥优先取 ``DATA_ENCRYPTION_KEY``，未配置时由 ``SECRET_KEY`` 经
  HKDF-SHA256（带域分隔 info）派生，避免与令牌签名密钥直接同源；
- 解密按 [主密钥, ``DATA_ENCRYPTION_OLD_KEYS`` 中的旧密钥..., 历史 SHA256(SECRET_KEY)]
  顺序尝试，因此支持密钥轮换，也不会打断升级前已加密的存量数据。
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.config.setting import settings
from app.core.exceptions import CustomException

# HKDF 域分隔：与 SECRET_KEY 用于其它目的时派生出不同密钥
_INFO = b"fastapiadmin:data-encryption:v1"
# Fernet token 首字节为版本 0x80，url-safe base64 编码后固定以 "gAAAAA" 开头
_TOKEN_PREFIX = "gAAAAA"


class CryptoUtil:
    """敏感字段加解密（进程内缓存密钥环，配置变更时自动重建）。"""

    _cache_signature: tuple | None = None
    _fernets: list[Fernet] = []

    @classmethod
    def _derive_key(cls, secret: str) -> bytes:
        return base64.urlsafe_b64encode(
            HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=_INFO).derive(secret.encode("utf-8"))
        )

    @classmethod
    def _legacy_key(cls, secret: str) -> bytes:
        """升级前的派生方式：直接对 SECRET_KEY 取 SHA-256，仅用于解密历史密文。"""
        return base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())

    @classmethod
    def _key_ring(cls) -> list[Fernet]:
        signature = (settings.DATA_ENCRYPTION_KEY, settings.DATA_ENCRYPTION_OLD_KEYS, settings.SECRET_KEY)
        if cls._cache_signature != signature:
            primaries = [settings.DATA_ENCRYPTION_KEY or settings.SECRET_KEY]
            primaries += [key.strip() for key in (settings.DATA_ENCRYPTION_OLD_KEYS or "").split(",") if key.strip()]
            fernets = [Fernet(cls._derive_key(secret)) for secret in primaries]
            fernets.append(Fernet(cls._legacy_key(settings.SECRET_KEY)))
            cls._fernets = fernets
            cls._cache_signature = signature
        return cls._fernets

    @classmethod
    def encrypt(cls, plain: str | None) -> str:
        """明文 → 密文；空值原样返回空串（始终使用主密钥加密）。"""
        if not plain:
            return ""
        return cls._key_ring()[0].encrypt(plain.encode("utf-8")).decode("utf-8")

    @classmethod
    def decrypt(cls, cipher: str | None) -> str:
        """密文 → 明文；所有密钥均解不开视为密钥已变更/数据损坏，抛出可定位的异常。"""
        if not cipher:
            return ""
        for fernet in cls._key_ring():
            try:
                return fernet.decrypt(cipher.encode("utf-8")).decode("utf-8")
            except (InvalidToken, ValueError):
                continue
        raise CustomException(msg="敏感数据解密失败，可能原因：DATA_ENCRYPTION_KEY/SECRET_KEY 变更或数据损坏")

    @classmethod
    def decrypt_or_keep(cls, value: str | None) -> str:
        """兼容历史明文的解密：值不是 Fernet 密文格式时原样返回。

        用于加密能力上线前就已存在的明文（如 Redis 中的 AI 密钥缓存，
        带 TTL，会随用户重新保存自然收敛为密文）。
        """
        if not value or not cls.is_token(value):
            return value or ""
        return cls.decrypt(value)

    @staticmethod
    def is_token(value: str) -> bool:
        """判断字符串是否具备 Fernet 密文的外形（前缀 + 可 base64 解码 + 最小长度）。"""
        if not value.startswith(_TOKEN_PREFIX) or len(value) < 60:
            return False
        try:
            base64.urlsafe_b64decode(value.encode("utf-8"))
        except ValueError:
            return False
        return True
