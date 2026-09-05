"""存储协议适配器抽象基类

子类只需实现同步的 _sync_* 方法（协议相关逻辑），异步公开接口统一在
基类中经 asyncio.to_thread 包装提供，避免阻塞事件循环。
可选钩子：_sync_get_url（预签名 URL，不支持则省略，get_url 返回 None）、
_sync_close（释放连接资源，无持久连接则省略，close 为空操作）。
适配器实例按请求创建（无连接池复用），用完由调用方关闭。
"""
import asyncio
import os
import types
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from typing import Any, Literal, get_args, get_origin

from pydantic import BaseModel, Field

from app.core.exceptions import CustomException
from app.core.logger import logger
from app.utils.crypto_util import CryptoUtil


class StorageProtocolDefSchema(BaseModel):
    """存储协议定义（/protocols 接口返回）"""

    protocol: str = Field(..., description="协议标识")
    name: str = Field(..., description="协议名称")
    default_port: int = Field(..., description="默认端口")


class AdvancedFieldDefSchema(BaseModel):
    """高级配置字段定义元数据（/advanced-fields 接口返回，前端按类型动态渲染）"""

    key: str = Field(..., description="字段名")
    label: str = Field(..., description="字段显示名")
    default: Any | None = Field(default=None, description="默认值")
    type: Literal["boolean", "number", "text", "select"] = Field("text", description="组件类型")
    options: list[str] | None = Field(default=None, description="下拉选项")


class StorageProtocol(str, Enum):
    """存储协议枚举"""

    FTP = "ftp"
    FTPS = "ftps"
    SFTP = "sftp"
    S3 = "s3"
    OBS = "obs"
    OSS = "oss"
    COS = "cos"
    LOCAL = "local"


# 各协议默认端口
DEFAULT_PORTS: dict[StorageProtocol, int] = {
    StorageProtocol.FTP: 21,
    StorageProtocol.FTPS: 990,
    StorageProtocol.SFTP: 22,
    StorageProtocol.S3: 443,
    StorageProtocol.OBS: 443,
    StorageProtocol.OSS: 443,
    StorageProtocol.COS: 443,
    StorageProtocol.LOCAL: 0,
}


def encrypt_password(plain: str | None) -> str:
    """明文密码 → 密文。空值原样返回空串。

    统一走 CryptoUtil（独立数据加密密钥 + 支持轮换），不再自行从
    SECRET_KEY 派生，避免 JWT 签名密钥与落库敏感数据的加密密钥同源。
    """
    return CryptoUtil.encrypt(plain)


def decrypt_password(cipher: str | None) -> str:
    """密文 → 明文密码。空值原样返回空串，解不开时抛业务异常。"""
    try:
        return CryptoUtil.decrypt(cipher)
    except CustomException as e:
        raise CustomException(msg=f"存储源密码解密失败：{e!s}")


# 文件系统类协议与对象存储类协议的划分：仅用于文档说明与配置元数据，
# 浏览/操作统一以"存储真根"为基准，path_prefix 不参与任何 key 计算。
_FILE_SYSTEM_PROTOCOLS: frozenset[StorageProtocol] = frozenset(
    {StorageProtocol.FTP, StorageProtocol.FTPS, StorageProtocol.SFTP, StorageProtocol.LOCAL}
)
_OBJECT_STORE_PROTOCOLS: frozenset[StorageProtocol] = frozenset(
    {StorageProtocol.S3, StorageProtocol.OSS, StorageProtocol.COS, StorageProtocol.OBS}
)


# 流式传输阈值：SDK 高层上传超过该大小才触发分片（100GB，等效单次上传）
_STREAM_THRESHOLD = 100 * 1024 * 1024 * 1024


class StorageAdapterConfig(BaseModel):
    """存储适配器配置（从 StorageNodeModel 剥离加密字段后注入，解耦 ORM 与协议层）"""

    protocol: StorageProtocol = Field(description="存储协议")
    host: str | None = Field(default=None, description="主机地址（对象存储可不填）")
    port: int = Field(description="端口")
    username: str | None = Field(default=None, description="用户名/AccessKey")
    password: str | None = Field(default=None, description="密码/SecretKey（已解密）")
    bucket: str | None = Field(default=None, description="桶名（对象存储专用；FTP/SFTP/LOCAL 不使用）")
    endpoint: str | None = Field(default=None, description="接入点（对象存储）")
    scheme: str = Field(default="https", description="对象存储访问协议(http/https)")
    region: str | None = Field(default=None, description="区域（对象存储）")
    path_prefix: str | None = Field(default=None, description="路径前缀（仅作节点元数据/传输默认路径，不参与浏览与 key 计算）")
    is_secure: bool = Field(default=False, description="是否启用 TLS（FTPS 显示加密 / COS 访问协议）")
    implicit_tls: bool = Field(default=False, description="FTPS 是否隐式 TLS（默认显式）")
    encrypt_type: int = Field(default=1, description="FTPS加密类型(0=明文 1=显式TLS可用时 2=要求显式TLS 3=隐式TLS)")
    connection_mode: int = Field(default=0, description="FTP/FTPS传输模式(0=默认 1=主动 2=被动)")
    encoding: str = Field(default="UTF-8", description="FTP/FTPS/SFTP编码(utf-8/gbk 等)")
    # 分片传输参数（对象存储分片上传，MB 单位；每个端点独立配置；单片上限 5GB 对齐各对象存储 SDK 上限）
    multipart_part_size: int = Field(default=50, ge=5, le=5000, description="分片大小(MB)")
    multipart_concurrency: int = Field(default=6, ge=1, le=64, description="分片上传并发路数")
    multipart_memory_budget: int = Field(default=512, ge=8, le=10240, description="分片上传内存预算(MB)")
    # 传输方式（连线/任务级覆盖）：stream 不触发分片（等效单次上传），multipart 使用分片参数；空=按分片参数走 SDK 高层上传
    transfer_mode: Literal["stream", "multipart"] | None = Field(default=None, description="传输方式")
    # SDK 高级配置（原始 JSON，由各适配器按协议解析合并默认值）
    advanced_config: dict = Field(default_factory=dict, description="SDK高级配置")


def normalize_endpoint(endpoint: str | None, scheme: str = "https") -> str | None:
    """规范化对象存储接入点：SDK 要求完整 URL（带协议），缺失时按 scheme 自动补充。

    例如 ``s3.example.com`` -> ``https://s3.example.com``。
    """
    if not endpoint:
        return endpoint
    return endpoint if "://" in endpoint else f"{scheme or 'https'}://{endpoint}"


class StorageObject(BaseModel):
    """远端文件对象信息"""

    name: str = Field(description="文件/目录名")
    key: str = Field(description="相对存储真根的路径（path_prefix 仅作为普通目录层，不做剥离）")
    is_dir: bool = Field(default=False, description="是否目录")
    size: int | None = Field(default=None, description="大小（字节）")
    modified_time: datetime | None = Field(default=None, description="修改时间")


class StoragePage(BaseModel):
    """游标分页结果（对象存储 SDK 原生游标分页，无总条数，只能顺序翻页）"""

    items: list[StorageObject] = Field(description="当前页条目")
    has_next: bool = Field(default=False, description="是否还有下一页")
    next_cursor: str | None = Field(default=None, description="下一页游标（无下一页为 None）")


class BaseStorageAdapter(ABC):
    """存储协议适配器抽象基类

    子类实现同步 _sync_* 方法即可，基类统一经 asyncio.to_thread 包装为异步接口。
    可选钩子：_sync_get_url（生成预签名 URL，不支持则省略，get_url 返回 None）、
    _sync_close（释放连接资源，无持久连接则省略，close 为空操作）。
    适配器实例按请求创建（无连接池复用），用完由调用方关闭。
    """

    # 并发安全：持共享连接的协议（如 SFTP）不支持多线程并发读写同一连接
    concurrency_safe: bool = True

    def __init__(self, config: StorageAdapterConfig) -> None:
        self.config = config
        # 当前操作桶（对象存储）：默认取节点配置，多桶浏览时经 set_bucket 覆盖
        self.bucket_name = config.bucket or ""

    def set_bucket(self, name: str) -> None:
        """切换当前操作桶（对象存储多桶浏览用）。"""
        self.bucket_name = name

    def _require_bucket(self) -> str:
        """获取当前操作桶，未配置时抛出异常。"""
        if not self.bucket_name:
            raise CustomException(msg="存储源未配置 bucket")
        return self.bucket_name

    def _sync_list_buckets(self) -> list[str]:
        """列出账号下全部存储桶（对象存储专用）。FTP/SFTP/LOCAL 等协议无需实现。"""
        raise NotImplementedError(f"{type(self).__name__} 不支持桶列表")

    def _multipart_settings(self) -> tuple[int, int, bool]:
        """返回 (分片大小, 并发数, 是否分片)，分片大小单位字节；并发按内存预算护栏收敛。

        源项目运行设置语义：分片大小默认 50MB、并发默认 6、内存预算默认 512MB。
        仅对象存储分片上传使用，FTP/SFTP/LOCAL 等协议忽略。
        传输方式为 stream 时返回超大阈值并关闭分片（等效单次上传）。
        """
        if self.config.transfer_mode == "stream":
            return _STREAM_THRESHOLD, 1, False
        part_size = max(self.config.multipart_part_size, 5) * 1024 * 1024
        concurrency = max(self.config.multipart_concurrency, 1)
        budget = self.config.multipart_memory_budget * 1024 * 1024
        if budget > 0:
            max_by_budget = max(1, budget // part_size)
            concurrency = min(concurrency, max_by_budget)
        return part_size, concurrency, True

    # ── 同步协议操作（子类实现，经 asyncio.to_thread 包装对外）─────────

    @abstractmethod
    def _sync_test_connection(self) -> bool:
        """测试连接是否可用。"""

    @abstractmethod
    def _sync_upload(self, local_path: str, remote_path: str) -> str:
        """上传本地文件到远端，返回远端完整 key。"""

    @abstractmethod
    def _sync_download(self, remote_path: str, local_path: str) -> str:
        """下载远端文件到本地，返回本地路径。"""

    @abstractmethod
    def _sync_delete(self, remote_path: str) -> None:
        """删除远端文件（目录递归删除由 delete_dir 处理）。"""

    @abstractmethod
    def _sync_exists(self, remote_path: str) -> bool:
        """判断远端文件是否存在。"""

    @abstractmethod
    def _sync_list(self, prefix: str) -> list[StorageObject]:
        """列出远端目录下的文件与目录（不含前缀）。"""

    # ── 目录操作（子类实现，经 asyncio.to_thread 包装对外）─────────────

    @abstractmethod
    def _sync_mkdir(self, remote_dir: str) -> None:
        """创建目录（remote_dir 为相对存储真根的目录路径）。"""

    @abstractmethod
    def _sync_rmdir(self, remote_dir: str) -> None:
        """删除空目录（对象存储删除占位标记）。"""

    @abstractmethod
    def _sync_rename(self, src: str, dst: str) -> None:
        """重命名/移动（src/dst 为相对存储真根的路径，支持文件与目录）。"""

    @abstractmethod
    def _sync_copy(self, src: str, dst: str) -> None:
        """复制文件或目录（src/dst 为相对存储真根的路径）。"""

    # ── 默认实现（子类可按协议优化覆盖）───────────────────────────────

    def _sync_list_recursive(self, prefix: str) -> list[StorageObject]:
        """递归列出（prefix 为相对存储真根的目录路径）。默认深度优先遍历；对象存储可覆盖为单次 API。"""
        result: list[StorageObject] = []
        stack = [prefix]
        while stack:
            current = stack.pop()
            for entry in self._sync_list(current):
                if entry.is_dir:
                    stack.append(f"{current}/{entry.name}" if current else entry.name)
                result.append(entry)
        return result

    def _sync_delete_dir(self, remote_dir: str) -> None:
        """递归删除目录（含目录本身）。默认：先删文件，再自底向上删空目录。"""
        for entry in reversed(self._sync_list_recursive(remote_dir)):
            if entry.is_dir:
                try:
                    self._sync_rmdir(entry.key)
                except Exception as e:
                    logger.warning("删除远端目录失败（将残留空目录）: {}: {}", entry.key, e)
            else:
                self._sync_delete(entry.key)
        if remote_dir:
            try:
                self._sync_rmdir(remote_dir)
            except Exception as e:
                logger.warning("删除远端目录失败（将残留空目录）: {}: {}", remote_dir, e)

    def _sync_copy_dir(self, src: str, dst: str) -> None:
        """递归复制目录（src/dst 为相对存储真根的路径）：遍历后先建目录再逐文件复制。"""
        src = src.rstrip("/")
        for entry in self._sync_list_recursive(src):
            full = entry.key
            rel = full[len(src) + 1 :] if full.startswith(src + "/") else entry.key
            target = f"{dst}/{rel}".strip("/")
            if entry.is_dir:
                self._sync_mkdir(target)
            else:
                self._sync_copy(full, target)

    def _sync_move_dir(self, src: str, dst: str) -> None:
        """递归移动目录（对象存储无原生目录重命名）：先复制后删除源。"""
        self._sync_copy_dir(src, dst)
        self._sync_delete_dir(src)

    def _sync_upload_dir(self, local_dir: str, remote_dir: str, concurrency: int) -> int:
        """批量上传目录：os.walk 收集文件后按 concurrency 并发上传，返回上传文件数。"""
        if not os.path.isdir(local_dir):
            raise CustomException(msg=f"本地目录不存在: {local_dir}")
        base = os.path.normpath(local_dir)
        tasks: list[tuple[str, str]] = []
        for root, _dirs, names in os.walk(base):
            for name in names:
                local_path = os.path.join(root, name)
                rel = os.path.relpath(local_path, base).replace(os.sep, "/")
                remote_path = f"{remote_dir}/{rel}".strip("/") if remote_dir else rel
                tasks.append((local_path, remote_path))
        if not tasks:
            return 0
        errors: list[Exception] = []

        def _run(task: tuple[str, str]) -> None:
            try:
                self._sync_upload(task[0], task[1])
            except Exception as e:
                errors.append(e)

        workers = max(1, concurrency) if self.concurrency_safe else 1
        if workers == 1:
            for task in tasks:
                _run(task)
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                list(pool.map(_run, tasks))
        if errors:
            raise CustomException(msg=f"批量上传失败 {len(errors)}/{len(tasks)} 个文件，首个错误: {errors[0]!s}")
        return len(tasks)

    def _sync_download_dir(self, remote_dir: str, local_dir: str, concurrency: int) -> int:
        """批量下载目录：递归列出后按 concurrency 并发下载，返回下载文件数。"""
        entries = [e for e in self._sync_list_recursive(remote_dir) if not e.is_dir]
        base = remote_dir.strip("/")
        tasks: list[tuple[str, str]] = []
        for e in entries:
            rel = e.key[len(base) + 1 :] if base and e.key.startswith(base + "/") else e.key
            tasks.append((e.key, os.path.join(local_dir, rel.replace("/", os.sep))))
        if not tasks:
            return 0
        errors: list[Exception] = []

        def _run(task: tuple[str, str]) -> None:
            try:
                os.makedirs(os.path.dirname(task[1]), exist_ok=True)
                self._sync_download(task[0], task[1])
            except Exception as e:
                errors.append(e)

        workers = max(1, concurrency) if self.concurrency_safe else 1
        if workers == 1:
            for task in tasks:
                _run(task)
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                list(pool.map(_run, tasks))
        if errors:
            raise CustomException(msg=f"批量下载失败 {len(errors)}/{len(tasks)} 个文件，首个错误: {errors[0]!s}")
        return len(tasks)

    @staticmethod
    def _entries_from_keys(keys: list[str]) -> list[StorageObject]:
        """由扁平 key 列表构造含隐含目录的条目列表（对象存储递归列举用，key 已剥离前缀）。"""
        dirs: set[str] = set()
        files: set[str] = set()
        for raw in keys:
            key = raw.rstrip("/")
            if not key:
                continue
            (dirs if raw.endswith("/") else files).add(key)
            parts = key.split("/")
            for i in range(1, len(parts)):
                dirs.add("/".join(parts[:i]))
        result: list[StorageObject] = []
        for k in sorted(dirs):
            result.append(StorageObject(name=k.rsplit("/", 1)[-1], key=k, is_dir=True))
        for k in sorted(files):
            result.append(StorageObject(name=k.rsplit("/", 1)[-1], key=k, is_dir=False))
        return result

    # ── 异步公开接口（经 asyncio.to_thread 包装）─────────────────────

    async def test_connection(self) -> bool:
        return await asyncio.to_thread(self._sync_test_connection)

    async def upload(self, local_path: str, remote_path: str) -> str:
        return await asyncio.to_thread(self._sync_upload, local_path, remote_path)

    async def download(self, remote_path: str, local_path: str) -> str:
        return await asyncio.to_thread(self._sync_download, remote_path, local_path)

    async def delete(self, remote_path: str) -> None:
        await asyncio.to_thread(self._sync_delete, remote_path)

    async def exists(self, remote_path: str) -> bool:
        return await asyncio.to_thread(self._sync_exists, remote_path)

    async def list_files(
        self, prefix: str = "", page_size: int | None = None, cursor: str | None = None
    ) -> list[StorageObject] | StoragePage:
        """列出目录条目。

        - 不传 page_size：全量拉取（目录选择器/搜索等场景）。
        - 传 page_size：游标分页。对象存储子类重写 _sync_list_page 走 SDK 原生游标
          （每页只拉一页数据）；FTP/SFTP/LOCAL 等无服务器游标的协议用基类默认实现
          （全量列举 + 内存切片，游标即偏移量）。
        """
        if page_size is not None:
            return await asyncio.to_thread(self._sync_list_page, prefix, page_size, cursor)
        return await asyncio.to_thread(self._sync_list, prefix)

    def _sync_list_page(self, prefix: str, page_size: int, cursor: str | None) -> StoragePage:
        """游标分页默认实现：全量列举后内存切片（游标为字符串偏移量，FTP/SFTP/LOCAL 使用）。"""
        items = self._sync_list(prefix)
        start = 0
        if cursor:
            try:
                start = int(cursor)
            except ValueError:
                start = 0
        page = items[start : start + page_size]
        has_next = start + page_size < len(items)
        return StoragePage(
            items=page,
            has_next=has_next,
            next_cursor=str(start + page_size) if has_next else None,
        )

    async def list_buckets(self) -> list[str]:
        """列出账号下全部存储桶（对象存储专用）。"""
        return await asyncio.to_thread(self._sync_list_buckets)

    async def list_recursive(self, prefix: str = "") -> list[StorageObject]:
        """递归列出目录树（含隐含目录条目）。"""
        return await asyncio.to_thread(self._sync_list_recursive, prefix)

    async def mkdir(self, remote_dir: str) -> None:
        """创建目录。"""
        await asyncio.to_thread(self._sync_mkdir, remote_dir)

    async def rmdir(self, remote_dir: str) -> None:
        """删除空目录。"""
        await asyncio.to_thread(self._sync_rmdir, remote_dir)

    async def delete_dir(self, remote_dir: str) -> None:
        """递归删除目录（含目录本身）。"""
        await asyncio.to_thread(self._sync_delete_dir, remote_dir)

    async def rename(self, src: str, dst: str) -> None:
        """重命名/移动（文件或目录）。"""
        await asyncio.to_thread(self._sync_rename, src, dst)

    async def copy(self, src: str, dst: str) -> None:
        """复制（文件或目录）。"""
        await asyncio.to_thread(self._sync_copy, src, dst)

    async def upload_dir(self, local_dir: str, remote_dir: str = "", concurrency: int = 1) -> int:
        """批量上传本地目录到远端，返回上传文件数。"""
        return await asyncio.to_thread(self._sync_upload_dir, local_dir, remote_dir, concurrency)

    async def download_dir(self, remote_dir: str, local_dir: str, concurrency: int = 1) -> int:
        """批量下载远端目录到本地，返回下载文件数。"""
        return await asyncio.to_thread(self._sync_download_dir, remote_dir, local_dir, concurrency)

    async def get_url(self, remote_path: str, expire: int = 3600) -> str | None:
        """获取访问 URL（对象存储返回预签名 URL；FTP/SFTP/LOCAL 不支持返回 None）。"""
        sync = getattr(self, "_sync_get_url", None)
        if sync is None:
            return None
        return await asyncio.to_thread(sync, remote_path, expire)

    async def close(self) -> None:
        """释放连接资源（无持久连接的协议实现为空操作）。"""
        sync = getattr(self, "_sync_close", None)
        if sync is None:
            return
        await asyncio.to_thread(sync)


class S3AdvancedConfig(BaseModel):
    """S3 兼容对象存储（boto3/botocore Config）"""

    connect_timeout: int = Field(default=60, ge=1, le=300, description="连接超时(秒)")
    read_timeout: int = Field(default=60, ge=1, le=300, description="读取超时(秒)")
    max_attempts: int = Field(default=3, ge=1, le=10, description="最大重试次数")
    retries_mode: str = Field(default="standard", description="重试模式")
    max_pool_connections: int = Field(default=10, ge=1, le=100, description="连接池大小")
    tcp_keepalive: bool = Field(default=False, description="TCP 长连接保活")
    use_dualstack_endpoint: bool = Field(default=False, description="使用双栈端点(IPv4/IPv6)")
    signature_version: str = Field(default="s3v4", description="签名版本")
    addressing_style: str = Field(default="auto", description="寻址风格")
    proxies: str | None = Field(default=None, max_length=255, description="代理地址(http://host:port，HTTP/HTTPS 通用)")
    use_accelerate_endpoint: bool = Field(default=False, description="使用传输加速端点")
    parameter_validation: bool = Field(default=True, description="启用请求参数校验(关闭可提升性能)")
    us_east_1_regional_endpoint: str | None = Field(default=None, description="us-east-1 区域端点策略(regional/legacy)")
    request_checksum_calculation: str = Field(default="when_supported", description="请求校验和计算时机(when_supported/when_required)")
    response_checksum_validation: str = Field(default="when_supported", description="响应校验和验证时机(when_supported/when_required)")


class OssAdvancedConfig(BaseModel):
    """阿里云 OSS（alibabacloud_oss_v2 Config）"""

    connect_timeout: int = Field(default=10, ge=1, le=300, description="连接超时(秒)")
    readwrite_timeout: int = Field(default=20, ge=1, le=300, description="读写超时(秒)")
    retry_max_attempts: int = Field(default=3, ge=1, le=10, description="最大重试次数")
    use_cname: bool = Field(default=False, description="使用自定义域名(CNAME)访问")
    use_path_style: bool = Field(default=False, description="路径风格寻址(兼容自建服务)")
    use_internal_endpoint: bool = Field(default=False, description="使用内网访问")
    use_accelerate_endpoint: bool = Field(default=False, description="使用传输加速端点")
    use_dualstack_endpoint: bool = Field(default=False, description="使用双栈端点(IPv4/IPv6)")
    insecure_skip_verify: bool = Field(default=False, description="跳过服务端证书校验")
    proxy_host: str | None = Field(default=None, max_length=255, description="代理服务器地址")
    signature_version: str = Field(default="v4", description="签名版本")
    disable_upload_crc64_check: bool = Field(default=False, description="关闭上传 CRC64 校验(提升性能)")
    disable_download_crc64_check: bool = Field(default=False, description="关闭下载 CRC64 校验(提升性能)")
    enabled_redirect: bool = Field(default=False, description="启用 HTTP 重定向")


class CosAdvancedConfig(BaseModel):
    """腾讯云 COS（cos-python-sdk-v5：CosConfig + CosS3Client retry）"""

    appid: str | None = Field(default=None, max_length=64, description="账号 Appid(部分场景必需)")
    token: str | None = Field(default=None, max_length=1024, description="临时密钥 Token(临时密钥认证时填写)")
    endpoint: str | None = Field(default=None, max_length=255, description="自定义接入域名(默认按 region 解析)")
    timeout: int = Field(default=60, ge=1, le=300, description="请求超时(秒)")
    retry: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    enable_md5: bool = Field(default=False, description="分片上传启用 MD5 校验")
    verify_ssl: bool = Field(default=True, description="验证服务端证书")
    auto_switch_domain_on_retry: bool = Field(default=False, description="重试时自动切换域名")
    pool_connections: int = Field(default=10, ge=1, le=100, description="连接池大小")
    pool_max_size: int = Field(default=100, ge=10, le=1000, description="连接池最大容量")
    keep_alive: bool = Field(default=True, description="HTTP 连接保活")
    allow_redirects: bool = Field(default=True, description="允许 HTTP 重定向")
    http_proxy: str | None = Field(default=None, max_length=255, description="HTTP 代理")
    https_proxy: str | None = Field(default=None, max_length=255, description="HTTPS 代理")


class ObsAdvancedConfig(BaseModel):
    """华为云 OBS（esdk-obs-python ObsClient，3.26.x 无独立连接超时参数）"""

    timeout: int = Field(default=60, ge=10, le=600, description="请求超时(秒)")
    max_retry_count: int = Field(default=3, ge=1, le=5, description="最大重试次数")
    ssl_verify: bool = Field(default=False, description="验证服务端证书")
    is_cname: bool = Field(default=False, description="使用自定义域名访问")
    path_style: bool = Field(default=False, description="路径风格寻址(兼容自建服务)")
    pool_size: int = Field(default=10, ge=1, le=200, description="连接池大小")
    signature: str = Field(default="v4", description="签名类型(v2/v4/obs)")
    region: str | None = Field(default=None, max_length=64, description="区域(部分场景必需)")
    security_token: str | None = Field(default=None, max_length=1024, description="临时密钥 Token(临时密钥认证时填写)")


class SftpAdvancedConfig(BaseModel):
    """SFTP（paramiko SSHClient.connect）"""

    connect_timeout: int = Field(default=30, ge=1, le=300, description="连接超时(秒)")
    banner_timeout: int = Field(default=30, ge=1, le=300, description="横幅超时(秒)")
    auth_timeout: int = Field(default=30, ge=1, le=300, description="认证超时(秒)")
    channel_timeout: int = Field(default=30, ge=1, le=300, description="通道操作超时(秒)")
    compress: bool = Field(default=False, description="启用传输压缩")
    allow_agent: bool = Field(default=True, description="允许使用 ssh-agent 认证")
    look_for_keys: bool = Field(default=True, description="查找本地密钥文件认证")
    keepalive_interval: int = Field(default=0, ge=0, le=3600, description="心跳间隔(秒，0 关闭)")


class FtpAdvancedConfig(BaseModel):
    """FTP / FTPS（ftplib）"""

    timeout: int = Field(default=30, ge=1, le=300, description="连接超时(秒)")


# ════════════════════════════════════════════════════════════════════════════
# 各协议数据完整性校验能力对照（通常用于传输后的数据完整性保障，平时保持默认即可）
#
#   S3   : 请求/响应 Checksum（CRC32/CRC32C 等算法）
#          由 botocore 控制计算与验证时机：
#          - request_checksum_calculation: when_supported / when_required
#          - response_checksum_validation: when_supported / when_required
#          （注意：当前 botocore 版本运行时不接受文档中的 "never" 值）
#   OSS  : CRC64（默认开启）：
#          - disable_upload_crc64_check   : 关闭上传校验（性能敏感时可开）
#          - disable_download_crc64_check : 关闭下载校验（性能敏感时可开）
#   COS  : MD5（分片上传，默认关闭）：
#          - enable_md5: 开启后分片上传附带 MD5 校验，可靠性提升、略有性能开销
#   OBS  : SDK 自动校验（esdk-obs-python 无用户可控开关，内部计算并在失败时报错）
#
# 提示：以上校验字段均为"隐藏级"配置（不在前端高级配置面板展示），
#       确有需要时通过接口在 advanced_config 中传入。
# ════════════════════════════════════════════════════════════════════════════
# 各协议传输加速能力对照（用于跨地域大文件传输加速，需先在云控制台开通）
#
#   S3   : use_accelerate_endpoint（botocore 原生开关，advanced_config 隐藏字段）
#   OSS  : use_accelerate_endpoint（oss_v2 原生开关，advanced_config 隐藏字段）
#   COS  : 无 SDK 开关，改用加速域名接入：
#          endpoint 填 {bucket}.cos.accelerate.myqcloud.com
#   OBS  : 无 SDK 开关，改用 CDN/自定义域名接入：
#          server 填 CDN 加速域名 + is_cname=true（advanced_config 隐藏字段）
# ════════════════════════════════════════════════════════════════════════════
# 协议 → 高级配置模型（local 无高级参数）
ADVANCED_CONFIG_MODELS: dict[StorageProtocol, type[BaseModel]] = {
    StorageProtocol.S3: S3AdvancedConfig,
    StorageProtocol.OSS: OssAdvancedConfig,
    StorageProtocol.COS: CosAdvancedConfig,
    StorageProtocol.OBS: ObsAdvancedConfig,
    StorageProtocol.SFTP: SftpAdvancedConfig,
    StorageProtocol.FTP: FtpAdvancedConfig,
    StorageProtocol.FTPS: FtpAdvancedConfig,
}


def parse_advanced_config(protocol: StorageProtocol, raw: dict[str, Any] | None) -> BaseModel | None:
    """解析端点高级配置 JSON 为对应协议模型；local 或无配置返回 None。"""
    model_cls = ADVANCED_CONFIG_MODELS.get(protocol)
    if model_cls is None:
        return None
    return model_cls.model_validate(raw or {})


# 前端渲染元数据：协议 → 字段 key → 可选值（按协议区分同名枚举，如 signature_version）
_SELECT_OPTIONS: dict[str, dict[str, list[str]]] = {
    "s3": {
        "signature_version": ["s3v4", "s3", "v2"],
        "addressing_style": ["auto", "path", "virtual"],
        "retries_mode": ["standard", "adaptive", "legacy"],
        "us_east_1_regional_endpoint": ["regional", "legacy"],
        "request_checksum_calculation": ["when_supported", "when_required"],
        "response_checksum_validation": ["when_supported", "when_required"],
    },
    "oss": {"signature_version": ["v4", "v1"]},
    "obs": {"signature": ["v2", "v4", "obs"]},
}


def _field_defs(model_cls: type[BaseModel], protocol_key: str) -> list[AdvancedFieldDefSchema]:
    defs: list[AdvancedFieldDefSchema] = []
    protocol_options = _SELECT_OPTIONS.get(protocol_key, {})
    for name, field_info in model_cls.model_fields.items():
        default = field_info.default
        if isinstance(default, BaseModel):
            default = None
        annotation = field_info.annotation
        if annotation is bool:
            field_type = "boolean"
        elif annotation is int:
            field_type = "number"
        elif annotation is str:
            field_type = "text"
        elif get_origin(annotation) is types.UnionType:
            # Optional[X]：取非 None 的分支推断组件类型
            inner = next((a for a in get_args(annotation) if a is not type(None)), str)
            field_type = "number" if inner is int else "text"
        else:
            field_type = "text"
        options = protocol_options.get(name)
        if options is not None:
            field_type = "select"
        defs.append(
            AdvancedFieldDefSchema(
                key=name,
                label=field_info.description or name,
                default=default,
                type=field_type,
                options=options,
            )
        )
    return defs


ADVANCED_FIELD_DEFS: dict[str, list[AdvancedFieldDefSchema]] = {
    protocol.value: _field_defs(model_cls, protocol.value) for protocol, model_cls in ADVANCED_CONFIG_MODELS.items()
}
