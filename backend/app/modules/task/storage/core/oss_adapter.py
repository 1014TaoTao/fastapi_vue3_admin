from datetime import UTC, datetime, timedelta

import alibabacloud_oss_v2 as oss

from app.core.exceptions import CustomException
from app.core.logger import logger
from app.modules.task.storage.core.base import (
    BaseStorageAdapter,
    OssAdvancedConfig,
    StorageObject,
    StoragePage,
    StorageProtocol,
    normalize_endpoint,
)


class OssStorageAdapter(BaseStorageAdapter):
    """阿里云 OSS 存储适配器（alibabacloud_oss_v2 SDK，同步调用经 asyncio.to_thread 包装）。"""

    protocol = StorageProtocol.OSS

    def __init__(self, config) -> None:
        super().__init__(config)
        if not self.config.endpoint:
            raise CustomException(msg="OSS 存储源必须配置 endpoint")
        if not self.config.region:
            raise CustomException(msg="OSS 存储源必须配置 region（V4 签名要求，如 cn-hangzhou）")
        if not self.config.username or not self.config.password:
            raise CustomException(msg="OSS 存储源必须配置 AccessKeyId 与 AccessKeySecret")
        cfg = oss.config.load_default()
        cfg.credentials_provider = oss.credentials.StaticCredentialsProvider(
            self.config.username,
            self.config.password
        )
        cfg.region = self.config.region
        cfg.endpoint = normalize_endpoint(self.config.endpoint, self.config.scheme)
        adv = OssAdvancedConfig(**self.config.advanced_config)
        cfg.connect_timeout = adv.connect_timeout
        cfg.readwrite_timeout = adv.readwrite_timeout
        cfg.retry_max_attempts = adv.retry_max_attempts
        cfg.use_cname = adv.use_cname
        cfg.use_path_style = adv.use_path_style
        cfg.insecure_skip_verify = adv.insecure_skip_verify
        cfg.use_internal_endpoint = adv.use_internal_endpoint
        cfg.use_accelerate_endpoint = adv.use_accelerate_endpoint
        cfg.proxy_host = adv.proxy_host
        cfg.signature_version = adv.signature_version
        cfg.disable_upload_crc64_check = adv.disable_upload_crc64_check
        cfg.disable_download_crc64_check = adv.disable_download_crc64_check
        cfg.enabled_redirect = adv.enabled_redirect
        cfg.use_dualstack_endpoint = adv.use_dualstack_endpoint
        self.client = oss.Client(cfg)

    def _sync_test_connection(self) -> bool:
        try:
            self.client.get_bucket_info(oss.GetBucketInfoRequest(bucket=self.bucket_name))
            return True
        except oss.exceptions.ServiceError as e:
            logger.warning(f"OSS 连接测试失败: {e.code} {e.message}")
            return False
        except Exception as e:
            logger.warning(f"OSS 连接测试失败: {e}")
            return False

    def _sync_upload(self, local_path: str, remote_path: str) -> str:
        try:
            # 走 SDK 高层分片上传：普通小文件自动单次上传，大文件按端点分片参数并发分片；
            # 流式传输（stream）时 part_size 为超大值，等效单次上传
            part_size, concurrency, _ = self._multipart_settings()
            self.client.uploader.upload_file(
                oss.PutObjectRequest(bucket=self.bucket_name, key=remote_path),
                local_path,
                part_size=part_size,
                parallel_num=concurrency,
            )
        except Exception as e:
            raise CustomException(msg=f"OSS 上传失败: {e!s}")
        return remote_path

    def _sync_download(self, remote_path: str, local_path: str) -> str:
        try:
            self.client.get_object_to_file(
                oss.GetObjectRequest(bucket=self.bucket_name, key=remote_path),
                local_path,
            )
        except Exception as e:
            raise CustomException(msg=f"OSS 下载失败: {e!s}")
        return local_path

    def _sync_delete(self, remote_path: str) -> None:
        try:
            self.client.delete_object(oss.DeleteObjectRequest(bucket=self.bucket_name, key=remote_path))
        except Exception as e:
            raise CustomException(msg=f"OSS 删除失败: {e!s}")

    def _sync_exists(self, remote_path: str) -> bool:
        try:
            self.client.head_object(oss.HeadObjectRequest(bucket=self.bucket_name, key=remote_path))
            return True
        except oss.exceptions.ServiceError as e:
            if e.status_code == 404:
                return False
            logger.warning(f"OSS 判断文件存在失败: {e.code} {e.message}")
            return False
        except Exception:
            return False

    @staticmethod
    def _to_utc_dt(value: int | float | datetime | None) -> datetime | None:
        """兼容 SDK 返回的时间戳（int/float）与 datetime 两种类型。"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
        return datetime.fromtimestamp(value, tz=UTC)

    def _sync_list(self, prefix: str) -> list[StorageObject]:
        try:
            paginator = self.client.list_objects_v2_paginator()
            result: list[StorageObject] = []
            for page in paginator.iter_page(oss.ListObjectsV2Request(bucket=self.bucket_name, prefix=prefix, delimiter="/")):
                for common in page.common_prefixes or []:
                    raw_key = (common.prefix or "").rstrip("/")
                    result.append(StorageObject(name=raw_key.rsplit("/", 1)[-1], key=raw_key, is_dir=True))
                for obj in page.contents or []:
                    raw_key = obj.key or ""
                    if raw_key == prefix:
                        continue
                    name = raw_key.rsplit("/", 1)[-1]
                    if not name:  # key 以 "/" 结尾的目录占位对象，不按文件展示
                        continue
                    result.append(
                        StorageObject(
                            name=name,
                            key=raw_key,
                            is_dir=False,
                            size=obj.size,
                            modified_time=self._to_utc_dt(obj.last_modified),
                        )
                    )
            return result
        except Exception as e:
            raise CustomException(msg=f"OSS 列表失败: {e!s}")

    def _sync_list_page(self, prefix: str, page_size: int, cursor: str | None) -> StoragePage:
        """游标分页：单次 SDK 请求只拉一页（OSS continuation_token），翻页经前端回传游标。"""
        try:
            result = self.client.list_objects_v2(
                oss.ListObjectsV2Request(
                    bucket=self.bucket_name,
                    prefix=prefix,
                    delimiter="/",
                    max_keys=page_size,
                    continuation_token=cursor or None,
                )
            )
            truncated = bool(getattr(result, "is_truncated", False))
            next_cursor = getattr(result, "next_continuation_token", None) or None
            items: list[StorageObject] = []
            for common in result.common_prefixes or []:
                raw_key = (common.prefix or "").rstrip("/")
                items.append(StorageObject(name=raw_key.rsplit("/", 1)[-1], key=raw_key, is_dir=True))
            for obj in result.contents or []:
                raw_key = obj.key or ""
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
                        size=obj.size,
                        modified_time=self._to_utc_dt(obj.last_modified),
                    )
                )
            return StoragePage(items=items, has_next=truncated, next_cursor=next_cursor)
        except Exception as e:
            raise CustomException(msg=f"OSS 列表失败: {e!s}")

    def _sync_list_buckets(self) -> list[str]:
        """列出账号下全部存储桶。"""
        try:
            paginator = self.client.list_buckets_paginator()
            result: list[str] = []
            for page in paginator.iter_page(oss.ListBucketsRequest()):
                for b in page.buckets or []:
                    if b.name:
                        result.append(b.name)
            return result
        except Exception as e:
            raise CustomException(msg=f"OSS 桶列表失败: {e!s}")

    def _sync_get_url(self, remote_path: str, expire: int) -> str | None:
        try:
            result = self.client.presign(
                oss.GetObjectRequest(bucket=self.bucket_name, key=remote_path),
                expires=timedelta(seconds=expire),
            )
            return result.url
        except Exception as e:
            raise CustomException(msg=f"OSS 生成预签名 URL 失败: {e!s}")

    # ── 目录操作（对象存储以 key/ 占位对象模拟目录）──────────────────

    def _list_all_keys(self, prefix: str) -> list[str]:
        """分页列举前缀下的全部对象 key。"""
        keys: list[str] = []
        paginator = self.client.list_objects_v2_paginator()
        for page in paginator.iter_page(oss.ListObjectsV2Request(bucket=self.bucket_name, prefix=prefix)):
            for obj in page.contents or []:
                if obj.key:
                    keys.append(obj.key)
        return keys

    def _is_dir(self, key: str) -> bool:
        """判断 key 是否代表目录（存在占位对象或前缀下有任何对象）。"""
        try:
            page = next(
                self.client.list_objects_v2_paginator().iter_page(
                    oss.ListObjectsV2Request(bucket=self.bucket_name, prefix=key.rstrip("/") + "/", max_keys=1)
                )
            )
            return bool(page.contents or page.common_prefixes)
        except Exception:
            return False

    def _sync_mkdir(self, remote_dir: str) -> None:
        try:
            self.client.put_object(oss.PutObjectRequest(bucket=self.bucket_name, key=remote_dir.rstrip("/") + "/", body=b""))
        except Exception as e:
            raise CustomException(msg=f"OSS 创建目录失败: {e!s}")

    def _sync_rmdir(self, remote_dir: str) -> None:
        try:
            self.client.delete_object(oss.DeleteObjectRequest(bucket=self.bucket_name, key=remote_dir.rstrip("/") + "/"))
        except Exception as e:
            raise CustomException(msg=f"OSS 删除目录失败: {e!s}")

    def _sync_copy(self, src: str, dst: str) -> None:
        """复制：目录走基类递归实现；文件用服务端 copy_object。"""
        try:
            if self._is_dir(src):
                self._sync_copy_dir(src, dst)
                return
            self.client.copy_object(
                oss.CopyObjectRequest(bucket=self.bucket_name, key=dst, source_bucket=self.bucket_name, source_key=src)
            )
        except Exception as e:
            raise CustomException(msg=f"OSS 复制失败: {e!s}")

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
            raise CustomException(msg=f"OSS 递归列表失败: {e!s}")
        return self._entries_from_keys(keys)

    def _sync_delete_dir(self, remote_dir: str) -> None:
        """递归删除：一次列举全部对象并分批批量删除（含占位目录对象）。"""
        try:
            keys = self._list_all_keys(remote_dir)
            marker = remote_dir.rstrip("/") + "/"
            if marker not in keys:
                keys.append(marker)
            for i in range(0, len(keys), 1000):
                self.client.delete_multiple_objects(
                    oss.DeleteMultipleObjectsRequest(
                        bucket=self.bucket_name,
                        objects=[oss.DeleteObject(key=k) for k in keys[i : i + 1000]],
                        quiet=True,
                    )
                )
        except Exception as e:
            raise CustomException(msg=f"OSS 递归删除失败: {e!s}")
