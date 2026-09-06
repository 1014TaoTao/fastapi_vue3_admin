import asyncio
import base64
import hashlib
import hmac
import os
import re
import secrets
import string

from app.core.logger import logger

_PBKDF2_ALGO = "sha256"
_PBKDF2_LABEL = "pbkdf2-sha256"
_PBKDF2_ITERATIONS = 600_000
_PBKDF2_SALT_LEN = 16
_PBKDF2_PREFIX = f"${_PBKDF2_LABEL}$"

_STRONG_PWD_CHARS = string.ascii_letters + string.digits + "!@#$%^&*"

# 口令字符类别：字母 / 数字 / 符号，用于复杂度校验（至少覆盖两类）
_PASSWORD_CLASSES = (re.compile(r"[A-Za-z]"), re.compile(r"\d"), re.compile(r"[^A-Za-z0-9]"))


class PwdUtil:
    @staticmethod
    def hash_password(password: str) -> str:
        salt = os.urandom(_PBKDF2_SALT_LEN)
        dk = hashlib.pbkdf2_hmac(_PBKDF2_ALGO, password.encode(), salt, _PBKDF2_ITERATIONS)
        return f"{_PBKDF2_PREFIX}{_PBKDF2_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"

    @staticmethod
    async def ahash_password(password: str) -> str:
        """hash_password 的异步版本：在线程池中执行派生。

        PBKDF2 默认 60 万次迭代是纯 CPU 计算（单次约数百毫秒），直接在
        async 接口里调用会把事件循环独占，导致同进程内所有并发请求一起卡顿；
        登录、建用户、改密等路径必须走本方法。
        """
        return await asyncio.to_thread(PwdUtil.hash_password, password)

    @staticmethod
    def verify_password(plain_password: str, password_hash: str) -> bool:
        """校验口令。

        - 使用常量时间比较，避免通过响应耗时逐字节猜测派生密钥；
        - 仅捕获格式类异常，并把异常信息落到日志（静默 False 会掩盖
          哈希格式损坏/算法不匹配，导致用户永远无法登录而无人知晓）。
        """
        try:
            _, label, iters_str, salt_b64, hash_b64 = password_hash.split("$")
            if label != _PBKDF2_LABEL:
                raise ValueError(f"未知的口令算法标识: {label!r}")
            iterations = int(iters_str)
            if not 1_000 <= iterations <= 10_000_000:
                raise ValueError(f"非法的迭代次数: {iterations}")
            salt = base64.b64decode(salt_b64, validate=True)
            expected = base64.b64decode(hash_b64, validate=True)
            derived = hashlib.pbkdf2_hmac(_PBKDF2_ALGO, plain_password.encode(), salt, iterations)
            return hmac.compare_digest(derived, expected)
        except (ValueError, TypeError) as e:
            logger.error(f"口令格式非法，无法校验（该用户需重置密码）: {e}")
            return False

    @staticmethod
    async def averify_password(plain_password: str, password_hash: str) -> bool:
        """verify_password 的异步版本：在线程池中执行派生。

        与 ``ahash_password`` 同理，校验同样要跑满哈希里记录的迭代次数，
        属阻塞计算；所有 async 调用点必须使用本方法。
        """
        return await asyncio.to_thread(PwdUtil.verify_password, plain_password, password_hash)

    @staticmethod
    def check_password_strength(password: str) -> str | None:
        """口令复杂度：字母、数字、符号至少覆盖两类。

        纯字母或纯数字的口令（``123456``、``abcdef``）会被字典与撞库首轮直接命中，
        必须在写库前挡掉；这里不校验长度——区间是接口字段约束，两处各说一套
        只会互相矛盾。

        返回:
        - str | None: 不满足时返回可直接展示给用户的提示语，满足时返回 ``None``。
        """
        classes = sum(1 for pattern in _PASSWORD_CLASSES if pattern.search(password))
        if classes < 2:
            return "密码需包含字母、数字、符号中的至少两类"
        return None

    @staticmethod
    def generate_strong_password(length: int = 12) -> str:
        """生成符合强度要求的强随机密码（大写+小写+数字+特殊符号）。

        使用 ``secrets`` 而非 ``random``，避免伪随机带来的安全风险。

        参数:
        - length (int): 密码长度，默认 12，最小 8。

        返回:
        - str: 生成的明文密码。
        """
        if length < 8:
            raise ValueError("密码长度至少 8 位")

        # 保证每类字符至少出现一次
        uppercase = secrets.choice(string.ascii_uppercase)
        lowercase = secrets.choice(string.ascii_lowercase)
        digit = secrets.choice(string.digits)
        special = secrets.choice("!@#$%^&*")

        remaining_length = length - 4
        rest = [secrets.choice(_STRONG_PWD_CHARS) for _ in range(remaining_length)]

        chars = list(rest) + [uppercase, lowercase, digit, special]
        secrets.SystemRandom().shuffle(chars)
        return "".join(chars)
