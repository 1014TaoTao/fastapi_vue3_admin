from typing import Any

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.exceptions import CustomException
from app.core.logger import logger
from app.modules.task.storage.core.base import (
    BaseStorageAdapter,
    S3AdvancedConfig,
    StorageObject,
    StoragePage,
    StorageProtocol,
    normalize_endpoint,
)


class S3StorageAdapter(BaseStorageAdapter):
    """S3 兼容对象存储适配器（boto3，同步调用经 asyncio.to_thread 包装）。"""

    protocol = StorageProtocol.S3

    def __init__(self, config) -> None:
        super().__init__(config)
        # 凭据为空时传空串而非 None，避免 boto3 走 EC2 实例元数据(IMDS)探测导致超时
        if not self.config.username or not self.config.password:
            raise CustomException(msg="S3 存储源必须配置 AccessKeyId 与 AccessKeySecret")
        if not self.config.bucket:
            raise CustomException(msg="S3 存储源必须配置 bucket")
        adv = S3AdvancedConfig(**self.config.advanced_config)
        proxies: dict[str, str] | None = None
        if adv.proxies:
            proxies = {"http": adv.proxies, "https": adv.proxies}
        s3_options: dict[str, Any] = {"addressing_style": adv.addressing_style}
        if adv.use_accelerate_endpoint:
            s3_options["use_accelerate_endpoint"] = True
        if adv.us_east_1_regional_endpoint:
            s3_options["us_east_1_regional_endpoint"] = adv.us_east_1_regional_endpoint
        config = Config(
            signature_version=adv.signature_version,
            retries={"max_attempts": adv.max_attempts, "mode": adv.retries_mode},
            connect_timeout=adv.connect_timeout,
            read_timeout=adv.read_timeout,
            max_pool_connections=adv.max_pool_connections,
            tcp_keepalive=adv.tcp_keepalive,
            use_dualstack_endpoint=adv.use_dualstack_endpoint,
            proxies=proxies,
            parameter_validation=adv.parameter_validation,
            request_checksum_calculation=adv.request_checksum_calculation,
            response_checksum_validation=adv.response_checksum_validation,
            s3=s3_options,
        )
        self.client = boto3.client(
            "s3",
            endpoint_url=normalize_endpoint(self.config.endpoint, self.config.scheme),
            region_name=self.config.region,
            aws_access_key_id=self.config.username or "",
            aws_secret_access_key=self.config.password or "",
            config=config,
        )

    def _sync_test_connection(self) -> bool:
        try:
            self.client.head_bucket(Bucket=self._require_bucket())
            return True
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            # 403 表示凭据有效但无权限查看桶，连接本身是通的
            if code == "403":
                return True
            logger.warning(f"S3 连接测试失败: {code} {e}")
            return False
        except Exception as e:
            logger.warning(f"S3 连接测试失败: {e}")
            return False

    def _sync_upload(self, local_path: str, remote_path: str) -> str:
        try:
            # 按端点分片参数配置：超过分片大小阈值即分片并发上传（并发受内存预算护栏约束）；
            # 流式传输（stream）时阈值为超大值，等效单次上传
            part_size, concurrency, _ = self._multipart_settings()
            transfer_config = TransferConfig(
                multipart_threshold=part_size,
                multipart_chunksize=part_size,
                max_concurrency=concurrency,
            )
            self.client.upload_file(local_path, self._require_bucket(), remote_path, Config=transfer_config)
        except Exception as e:
            raise CustomException(msg=f"S3 上传失败: {e!s}")
        return remote_path

    def _sync_download(self, remote_path: str, local_path: str) -> str:
        try:
            self.client.download_file(self._require_bucket(), remote_path, local_path)
        except Exception as e:
            raise CustomException(msg=f"S3 下载失败: {e!s}")
        return local_path

    def _sync_delete(self, remote_path: str) -> None:
        try:
            self.client.delete_object(Bucket=self._require_bucket(), Key=remote_path)
        except Exception as e:
            raise CustomException(msg=f"S3 删除失败: {e!s}")

    def _sync_exists(self, remote_path: str) -> bool:
        try:
            self.client.head_object(Bucket=self._require_bucket(), Key=remote_path)
            return True
        except ClientError as e:
            if e.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                return False
            logger.warning(f"S3 head_object 失败: {e}")
            return False
        except Exception:
            return False

    def _sync_list(self, prefix: str) -> list[StorageObject]:
        """列举目录层条目。S3 单次最多返回 1000 条，经 ContinuationToken 翻页拉全量。"""
        try:
            result: list[StorageObject] = []
            seen_dirs: set[str] = set()
            seen_files: set[str] = set()
            token: str | None = None
            while True:
                kwargs: dict[str, Any] = {
                    "Bucket": self._require_bucket(),
                    "Prefix": prefix,
                    "Delimiter": "/",
                }
                if token:
                    kwargs["ContinuationToken"] = token
                resp = self.client.list_objects_v2(**kwargs)
                for cp in resp.get("CommonPrefixes", []):
                    raw_key = cp.get("Prefix", "").rstrip("/")
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
                if resp.get("IsTruncated") and resp.get("NextContinuationToken"):
                    token = resp["NextContinuationToken"]
                else:
                    break
            return result
        except Exception as e:
            raise CustomException(msg=f"S3 列表失败: {e!s}")

    def _sync_list_page(self, prefix: str, page_size: int, cursor: str | None) -> StoragePage:
        """游标分页：单次 SDK 请求只拉一页（S3 ContinuationToken），翻页经前端回传游标。"""
        try:
            kwargs: dict[str, Any] = {
                "Bucket": self._require_bucket(),
                "Prefix": prefix,
                "Delimiter": "/",
                "MaxKeys": page_size,
            }
            if cursor:
                kwargs["ContinuationToken"] = cursor
            resp = self.client.list_objects_v2(**kwargs)
            items: list[StorageObject] = []
            for cp in resp.get("CommonPrefixes", []):
                raw_key = cp.get("Prefix", "").rstrip("/")
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
                has_next=bool(resp.get("IsTruncated")),
                next_cursor=resp.get("NextContinuationToken"),
            )
        except Exception as e:
            raise CustomException(msg=f"S3 列表失败: {e!s}")

    def _sync_list_buckets(self) -> list[str]:
        """列出账号下全部存储桶。"""
        try:
            resp = self.client.list_buckets()
            return [b.get("Name", "") for b in resp.get("Buckets", []) if b.get("Name")]
        except Exception as e:
            raise CustomException(msg=f"S3 桶列表失败: {e!s}")

    def _sync_get_url(self, remote_path: str, expire: int) -> str:
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._require_bucket(), "Key": remote_path},
                ExpiresIn=expire,
            )
        except Exception as e:
            raise CustomException(msg=f"S3 生成预签名 URL 失败: {e!s}")

    def _sync_close(self) -> None:
        """关闭 boto3 客户端连接。"""
        close = getattr(self.client, "close", None)
        if callable(close):
            close()

    # ── 目录操作（对象存储以 key/ 占位对象模拟目录）──────────────────

    def _list_all_keys(self, prefix: str) -> list[str]:
        """分页列举前缀下的全部对象 key。"""
        keys: list[str] = []
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._require_bucket(), Prefix=prefix):
            keys.extend(obj["Key"] for obj in page.get("Contents", []))
        return keys

    def _is_dir(self, key: str) -> bool:
        """判断 key 是否代表目录（存在占位对象或前缀下有任何对象）。"""
        try:
            resp = self.client.list_objects_v2(
                Bucket=self._require_bucket(), Prefix=key.rstrip("/") + "/", MaxKeys=1
            )
            return bool(resp.get("Contents") or resp.get("CommonPrefixes"))
        except Exception:
            return False

    def _sync_mkdir(self, remote_dir: str) -> None:
        try:
            self.client.put_object(Bucket=self._require_bucket(), Key=remote_dir.rstrip("/") + "/", Body=b"")
        except Exception as e:
            raise CustomException(msg=f"S3 创建目录失败: {e!s}")

    def _sync_rmdir(self, remote_dir: str) -> None:
        try:
            self.client.delete_object(Bucket=self._require_bucket(), Key=remote_dir.rstrip("/") + "/")
        except Exception as e:
            raise CustomException(msg=f"S3 删除目录失败: {e!s}")

    def _sync_copy(self, src: str, dst: str) -> None:
        """复制：目录走基类递归实现；文件用服务端 copy_object。"""
        try:
            if self._is_dir(src):
                self._sync_copy_dir(src, dst)
                return
            self.client.copy_object(
                Bucket=self._require_bucket(),
                CopySource={"Bucket": self._require_bucket(), "Key": src},
                Key=dst,
            )
        except Exception as e:
            raise CustomException(msg=f"S3 复制失败: {e!s}")

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
            raise CustomException(msg=f"S3 递归列表失败: {e!s}")
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
            raise CustomException(msg=f"S3 递归删除失败: {e!s}")
