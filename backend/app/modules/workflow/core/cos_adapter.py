from typing import Any

from qcloud_cos import CosConfig, CosS3Client

from app.core.exceptions import CustomException
from app.core.logger import logger
from app.modules.workflow.core.base import (
    BaseStorageAdapter,
    CosAdvancedConfig,
    StorageObject,
    StoragePage,
    StorageProtocol,
)


class CosStorageAdapter(BaseStorageAdapter):
    """腾讯云 COS 存储适配器（cos-python-sdk-v5，同步调用经 asyncio.to_thread 包装）。"""

    protocol = StorageProtocol.COS

    def __init__(self, config) -> None:
        super().__init__(config)
        if not self.config.region:
            raise CustomException(msg="COS 存储源必须配置 region")
        if not self.config.username or not self.config.password:
            raise CustomException(msg="COS 存储源必须配置 SecretId/SecretKey")
        adv = CosAdvancedConfig(**self.config.advanced_config)
        proxies: dict[str, str] = {}
        if adv.http_proxy:
            proxies["http"] = adv.http_proxy
        if adv.https_proxy:
            proxies["https"] = adv.https_proxy
        cos_config = CosConfig(
            Region=self.config.region,
            SecretId=self.config.username or "",
            SecretKey=self.config.password or "",
            Scheme="https" if self.config.is_secure else "http",
            Token=adv.token,
            Appid=adv.appid,
            Endpoint=adv.endpoint,
            Timeout=adv.timeout,
            Proxies=proxies or None,
            VerifySSL=adv.verify_ssl,
            AutoSwitchDomainOnRetry=adv.auto_switch_domain_on_retry,
            PoolConnections=adv.pool_connections,
            PoolMaxSize=adv.pool_max_size,
            KeepAlive=adv.keep_alive,
            AllowRedirects=adv.allow_redirects,
        )
        self.client = CosS3Client(cos_config, retry=adv.retry)
        self._adv = adv

    def _sync_test_connection(self) -> bool:
        """
        列出符合条件的bucket
        :param Bucket(string): 存储桶名称
        :param TagKey(string): 标签键
        :param TagValue(string): 标签值
        :param Region(string): 地域名称
        :param CreateTime(Timestamp): GMT时间戳, 和 Range 参数一起使用, 支持根据创建时间过滤存储桶
        :param Range(string): 和 CreateTime 参数一起使用, 支持根据创建时间过滤存储桶，支持枚举值 lt（创建时间早于 create-time）、gt（创建时间晚于 create-time）、lte（创建时间早于或等于 create-time）、gte（创建时间晚于或等于create-time）
        :param Marker(string): 起始标记, 从该标记之后（不含）按照 UTF-8 字典序返回存储桶条目
        :param MaxKeys(int): 单次返回最大的条目数量，默认值为2000，最大为2000

        :return(dict): 账号下bucket相关信息.
        """
        try:
            self.client.list_buckets()
            if self.client.head_bucket(Bucket=self._require_bucket()):
                return True
            return False
        except Exception as e:
            logger.warning(f"COS 连接测试失败: {e}")
            return False

    def _sync_upload(self, local_path: str, remote_path: str) -> str:
        """
        :param Bucket(string): 存储桶名称.
        :param key(string): 分块上传路径名.
        :param LocalFilePath(string): 本地文件路径名.
        :param PartSize(int): 分块的大小设置,单位为MB.
        :param MAXThread(int): 并发上传的最大线程数.
        :param EnableMD5(bool): 是否打开MD5校验.
        :param kwargs(dict): 设置请求headers.
        :return(dict): 成功上传文件的元信息.
        """
        try:
            # 分片大小/并发取端点配置；文件小于分片大小自动单次上传（流式传输时该值为超大值，等效单次）
            part_size, concurrency, _ = self._multipart_settings()
            self.client.upload_file(
                Bucket=self._require_bucket(),
                Key=remote_path,
                LocalFilePath=local_path,
                PartSize=part_size // (1024 * 1024),
                MAXThread=concurrency,
                EnableMD5=self._adv.enable_md5,
            )
        except Exception as e:
            raise CustomException(msg=f"COS 上传失败: {e!s}")
        return remote_path

    def _sync_download(self, remote_path: str, local_path: str) -> str:
        try:
            self.client.download_file(
                Bucket=self._require_bucket(),
                Key=remote_path,
                DestFilePath=local_path,
            )
        except Exception as e:
            raise CustomException(msg=f"COS 下载失败: {e!s}")
        return local_path

    def _sync_delete(self, remote_path: str) -> None:
        """
        单文件删除接口

        :param Bucket(string): 存储桶名称.
        :param Key(string): COS路径.
        :param kwargs(dict): 设置请求headers.
        :return: dict.
        """
        try:
            self.client.delete_object(Bucket=self._require_bucket(), Key=remote_path)
        except Exception as e:
            raise CustomException(msg=f"COS 删除失败: {e!s}")

    def _sync_exists(self, remote_path: str) -> bool:
        try:
            return self.client.object_exists(Bucket=self._require_bucket(), Key=remote_path)
        except Exception:
            return False

    def _sync_list(self, prefix: str) -> list[StorageObject]:
        """列举目录层条目。COS 单次最多返回 1000 条，经 Marker 翻页拉全量。"""
        try:
            result: list[StorageObject] = []
            seen_dirs: set[str] = set()
            seen_files: set[str] = set()
            marker: str | None = None
            while True:
                kwargs: dict[str, Any] = {
                    "Bucket": self._require_bucket(),
                    "Prefix": prefix,
                    "Delimiter": "/",
                }
                if marker:
                    kwargs["Marker"] = marker
                resp = self.client.list_objects(**kwargs)
                for common in resp.get("CommonPrefixes", []):
                    raw_key = common.get("Prefix", "").rstrip("/")
                    if raw_key in seen_dirs:
                        continue
                    seen_dirs.add(raw_key)
                    result.append(StorageObject(name=raw_key.rsplit("/", 1)[-1], key=raw_key, is_dir=True))
                for obj in resp.get("Contents", []):
                    raw_key = obj.get("Key", "")
                    if raw_key == prefix:
                        continue
                    name = raw_key.rsplit("/", 1)[-1]
                    if not name:  # key 以 "/" 结尾的目录占位对象，不按文件展示
                        continue
                    if raw_key in seen_files:
                        continue
                    seen_files.add(raw_key)
                    result.append(
                        StorageObject(
                            name=name,
                            key=raw_key,
                            is_dir=False,
                            size=obj.get("Size"),
                            modified_time=obj.get("LastModified"),
                        )
                    )
                if resp.get("IsTruncated"):
                    marker = resp.get("NextMarker") or ""
                    if not marker and resp.get("Contents"):
                        marker = resp["Contents"][-1].get("Key", "")  # 部分实现不返回 NextMarker 时回退最后 key
                    if not marker:
                        break
                else:
                    break
            return result
        except Exception as e:
            raise CustomException(msg=f"COS 列表失败: {e!s}")

    def _sync_list_page(self, prefix: str, page_size: int, cursor: str | None) -> StoragePage:
        """游标分页：单次 SDK 请求只拉一页（COS Marker），翻页经前端回传游标。"""
        try:
            kwargs: dict[str, Any] = {
                "Bucket": self._require_bucket(),
                "Prefix": prefix,
                "Delimiter": "/",
                "MaxKeys": page_size,
            }
            if cursor:
                kwargs["Marker"] = cursor
            resp = self.client.list_objects(**kwargs)
            contents = resp.get("Contents", [])
            prefixes = resp.get("CommonPrefixes", [])
            truncated = bool(resp.get("IsTruncated"))
            # 条目数（含子目录前缀）少于请求页大小 → 必然已枚举完，忽略服务端边界误报
            if len(contents) + len(prefixes) < page_size:
                truncated = False
            next_cursor = resp.get("NextMarker") or ""
            if not next_cursor and truncated:
                # COS 带 Delimiter 时 NextMarker 可能缺失（如目录下只有子目录前缀、Contents 为空）：
                # 取全部条目（子目录前缀 + 文件）字典序最后的 key 作为游标，避免翻页失效
                keys = [p.get("Prefix", "").rstrip("/") for p in prefixes if p.get("Prefix")] + [
                    o.get("Key", "") for o in contents if o.get("Key")
                ]
                if keys:
                    next_cursor = max(keys)
            # COS 服务端在条目数恰好等于 MaxKeys 时可能保守返回 IsTruncated=true（实际已枚举完），
            # 用 MaxKeys=1 探测确认是否存在真正的下一页，避免出现空的下一页
            if truncated and next_cursor:
                try:
                    probe = self.client.list_objects(
                        Bucket=self._require_bucket(),
                        Prefix=prefix,
                        Delimiter="/",
                        Marker=next_cursor,
                        MaxKeys=1,
                    )
                    truncated = bool(probe.get("Contents")) or bool(probe.get("CommonPrefixes"))
                except Exception:
                    pass  # 探测失败时保持原判定
            items: list[StorageObject] = []
            for common in resp.get("CommonPrefixes", []):
                raw_key = common.get("Prefix", "").rstrip("/")
                items.append(StorageObject(name=raw_key.rsplit("/", 1)[-1], key=raw_key, is_dir=True))
            for obj in resp.get("Contents", []):
                raw_key = obj.get("Key", "")
                if raw_key == prefix:
                    continue
                name = raw_key.rsplit("/", 1)[-1]
                if not name:  # key 以 "/" 结尾的目录占位对象，不按文件展示
                    continue
                items.append(
                    StorageObject(
                        name=name,
                        key=raw_key,
                        is_dir=False,
                        size=obj.get("Size"),
                        modified_time=obj.get("LastModified"),
                    )
                )
            return StoragePage(
                items=items,
                has_next=truncated,
                next_cursor=next_cursor or None,
            )
        except Exception as e:
            raise CustomException(msg=f"COS 列表失败: {e!s}")

    def _sync_list_buckets(self) -> list[str]:
        """列出账号下全部存储桶。"""
        try:
            resp = self.client.list_buckets()
            buckets = (resp.get("Buckets") or {}).get("Bucket") or []
            return [b.get("Name", "") for b in buckets if b.get("Name")]
        except Exception as e:
            raise CustomException(msg=f"COS 桶列表失败: {e!s}")

    def _sync_get_url(self, remote_path: str, expire: int) -> str:
        """生成预签名 URL
        :param Bucket(string): 存储桶名称.
        :param Key(string): COS路径.
        :param Method(string): HTTP请求的方法, 'PUT'|'POST'|'GET'|'DELETE'|'HEAD'
        :param Expired(int): 签名过期时间.
        :param Params(dict): 签入签名的参数
        :param Headers(dict): 签入签名的头部
        :param SignHost(bool): 是否将host算入签名.
        :return(string): 预先签名的URL.
        """
        try:
            return self.client.get_presigned_url(
                Method="GET",
                Bucket=self._require_bucket(),
                Key=remote_path,
                Expired=expire,
            )
        except Exception as e:
            raise CustomException(msg=f"COS 生成预签名 URL 失败: {e!s}")

    # ── 目录操作（对象存储以 key/ 占位对象模拟目录）──────────────────

    def _list_all_keys(self, prefix: str) -> list[str]:
        """分页列举前缀下的全部对象 key。"""
        keys: list[str] = []
        marker = ""
        while True:
            resp = self.client.list_objects(Bucket=self._require_bucket(), Prefix=prefix, Marker=marker)
            keys.extend(obj["Key"] for obj in resp.get("Contents", []))
            if not resp.get("IsTruncated"):
                break
            # 未指定 delimiter 时服务端可能不返回 NextMarker，退化为当前页最后一个 key，避免死循环
            marker = resp.get("NextMarker") or (resp["Contents"][-1]["Key"] if resp.get("Contents") else "")
            if not marker:
                break
        return keys

    def _is_dir(self, key: str) -> bool:
        """判断 key 是否代表目录（存在占位对象或前缀下有任何对象）。"""
        try:
            resp = self.client.list_objects(Bucket=self._require_bucket(), Prefix=key.rstrip("/") + "/", MaxKeys=1)
            return bool(resp.get("Contents") or resp.get("CommonPrefixes"))
        except Exception:
            return False

    def _sync_mkdir(self, remote_dir: str) -> None:
        try:
            self.client.put_object(Bucket=self._require_bucket(), Key=remote_dir.rstrip("/") + "/", Body=b"")
        except Exception as e:
            raise CustomException(msg=f"COS 创建目录失败: {e!s}")

    def _sync_rmdir(self, remote_dir: str) -> None:
        try:
            self.client.delete_object(Bucket=self._require_bucket(), Key=remote_dir.rstrip("/") + "/")
        except Exception as e:
            raise CustomException(msg=f"COS 删除目录失败: {e!s}")

    def _sync_copy(self, src: str, dst: str) -> None:
        """复制：目录走基类递归实现；文件用服务端 copy_object。"""
        try:
            if self._is_dir(src):
                self._sync_copy_dir(src, dst)
                return
            self.client.copy_object(
                Bucket=self._require_bucket(),
                Key=dst,
                CopySource={"Bucket": self._require_bucket(), "Key": src},
            )
        except Exception as e:
            raise CustomException(msg=f"COS 复制失败: {e!s}")

    def _sync_rename(self, src: str, dst: str) -> None:
        """重命名/移动：目录先复制后删除；文件 copy_object 后删源。"""
        if self._is_dir(src):
            self._sync_move_dir(src, dst)
        else:
            self._sync_copy(src, dst)
            self._sync_delete(src)

    def _sync_list_recursive(self, prefix: str) -> list[StorageObject]:
        try:
            keys = self._list_all_keys(prefix)
        except Exception as e:
            raise CustomException(msg=f"COS 递归列表失败: {e!s}")
        return self._entries_from_keys(keys)

    def _sync_delete_dir(self, remote_dir: str) -> None:
        """递归删除：一次列举全部对象并分批批量删除（含占位目录对象）。"""
        try:
            keys = self._list_all_keys(remote_dir)
            marker = remote_dir.rstrip("/") + "/"
            if marker not in keys:
                keys.append(marker)
            for i in range(0, len(keys), 1000):
                self.client.delete_objects(
                    Bucket=self._require_bucket(),
                    Delete={"Objects": [{"Key": k} for k in keys[i : i + 1000]], "Quiet": True},
                )
        except Exception as e:
            raise CustomException(msg=f"COS 递归删除失败: {e!s}")
