from datetime import UTC, datetime
from typing import Any

from obs import ObsClient

from app.core.exceptions import CustomException
from app.core.logger import logger
from app.modules.workflow.core.base import (
    BaseStorageAdapter,
    ObsAdvancedConfig,
    StorageObject,
    StoragePage,
    StorageProtocol,
    normalize_endpoint,
)


class ObsStorageAdapter(BaseStorageAdapter):
    """华为云 OBS 存储适配器（esdk-obs-python，同步调用经 asyncio.to_thread 包装）。
    SDK API 概览
    ------------

    一、桶管理（Bucket）

    | 接口名 | 方法 | 功能描述 |
    | --- | --- | --- |
    | 创建桶 | ObsClient.createBucket | 创建桶。 |
    | 获取桶列表 | ObsClient.listBuckets | 查询桶列表，返回结果按照桶名字典序排列。 |
    | 判断桶是否存在 | ObsClient.headBucket | 判断桶是否存在。 |
    | 删除桶 | ObsClient.deleteBucket | 删除桶，待删除的桶必须为空。 |
    | 列举桶内对象 | ObsClient.listObjects | 列举桶内对象，默认返回最大1000个对象。 |
    | 列举桶内多版本对象 | ObsClient.listVersions | 列举桶内多版本对象，默认返回最大1000个多版本对象。 |
    | 列举分段上传任务 | ObsClient.listMultipartUploads | 列举指定桶中所有的初始化后还未合并或还未取消的分段上传任务。 |
    | 获取桶元数据 | ObsClient.getBucketMetadata | 对桶发送HEAD请求，获取桶的存储类型、CORS规则（如果已设置）等信息。 |
    | 获取桶区域位置 | ObsClient.getBucketLocation | 获取桶所在的区域位置。 |
    | 获取桶存量信息 | ObsClient.getBucketStorageInfo | 获取桶的存量信息，包含桶的空间大小以及对象个数。 |
    | 设置桶配额 | ObsClient.setBucketQuota | 设置桶的配额值，单位为字节，支持的最大值为2^63-1，配额值设为0表示桶的配额没有上限。 |
    | 获取桶配额 | ObsClient.getBucketQuota | 获取桶的配额值，0代表配额没有上限。 |
    | 设置桶存储类型 | ObsClient.setBucketStoragePolicy | 设置桶的存储类型，桶中对象的存储类型默认将与桶的存储类型保持一致。 |
    | 获取桶存储类型 | ObsClient.getBucketStoragePolicy | 获取桶的存储类型。 |
    | 设置桶ACL | ObsClient.setBucketAcl | 设置桶ACL。 |
    | 获取桶ACL | ObsClient.getBucketAcl | 获取桶ACL。 |
    | 设置桶日志管理配置 | ObsClient.setBucketLogging | 设置桶的访问日志配置。 |
    | 获取桶日志管理配置 | ObsClient.getBucketLogging | 获取桶的访问日志配置。 |
    | 设置桶策略 | ObsClient.setBucketPolicy | 配置桶的策略，如果桶已经存在一个策略，当前请求中的策略将完全覆盖桶中现存的策略。 |
    | 获取桶策略 | ObsClient.getBucketPolicy | 获取桶的策略配置。 |
    | 删除桶策略 | ObsClient.deleteBucketPolicy | 删除桶的策略配置。 |
    | 设置桶生命周期配置 | ObsClient.setBucketLifecycle | 配置桶的生命周期规则，实现定时转换桶中对象的存储类型，以及定时删除桶中对象的功能。 |
    | 获取桶生命周期配置 | ObsClient.getBucketLifecycle | 获取桶的生命周期规则。 |
    | 删除桶生命周期配置 | ObsClient.deleteBucketLifecycle | 删除桶所有的生命周期规则。 |
    | 设置桶Website配置 | ObsClient.setBucketWebsite | 设置桶的Website配置。 |
    | 获取桶Website配置 | ObsClient.getBucketWebsite | 获取桶的Website配置。 |
    | 删除桶Website配置 | ObsClient.deleteBucketWebsite | 删除指定桶的Website配置。 |
    | 设置桶多版本状态 | ObsClient.setBucketVersioning | 设置桶的多版本状态。 |
    | 获取桶多版本状态 | ObsClient.getBucketVersioning | 获取桶的多版本状态。 |
    | 设置桶CORS配置 | ObsClient.setBucketCors | 设置桶的跨域资源共享规则，以允许客户端浏览器进行跨域请求。 |
    | 获取桶CORS配置 | ObsClient.getBucketCors | 获取指定桶的跨域资源共享规则。 |
    | 删除桶CORS配置 | ObsClient.deleteBucketCors | 删除指定桶的跨域资源共享规则。 |
    | 设置桶标签 | ObsClient.setBucketTagging | 设置桶的标签。 |
    | 获取桶标签 | ObsClient.getBucketTagging | 获取指定桶的标签。 |
    | 删除桶标签 | ObsClient.deleteBucketTagging | 删除指定桶的标签。 |

    二、对象管理（Object）

    | 接口名 | 方法 | 功能描述 |
    | --- | --- | --- |
    | 上传对象 | ObsClient.putContent | 上传对象到指定桶中。 |
    | 上传文件 | ObsClient.putFile | 上传文件/文件夹到指定桶中。 |
    | 追加上传 | ObsClient.appendObject | 对同一个对象追加数据内容。 |
    | 下载对象 | ObsClient.getObject | 下载指定桶中的对象。 |
    | 复制对象 | ObsClient.copyObject | 为指定桶中的对象创建一个副本。 |
    | 删除对象 | ObsClient.deleteObject | 删除指定桶中的对象。 |
    | 批量删除对象 | ObsClient.deleteObjects | 批量删除指定桶中的多个对象。 |
    | 获取对象元数据 | ObsClient.getObjectMetadata | 对指定桶中的对象发送HEAD请求，获取对象的元数据信息。 |
    | 修改对象元数据 | ObsClient.setObjectMetadata | 修改指定桶中对象的元数据信息。 |
    | 设置对象ACL | ObsClient.setObjectAcl | 设置指定桶中对象ACL。 |
    | 获取对象ACL | ObsClient.getObjectAcl | 获取指定桶中对象ACL。 |

    三、分段上传（Multipart Upload）

    | 接口名 | 方法 | 功能描述 |
    | --- | --- | --- |
    | 初始化分段上传任务 | ObsClient.initiateMultipartUpload | 在指定桶中初始化分段上传任务。 |
    | 上传段 | ObsClient.uploadPart | 初始化分段上传任务后，通过分段上传任务的ID，上传段到指定桶中。 |
    | 复制段 | ObsClient.copyPart | 初始化分段上传任务后，通过分段上传任务的ID，复制段到指定桶中。 |
    | 列举已上传的段 | ObsClient.listParts | 通过分段上传任务的ID，列举指定桶中已上传的段。 |
    | 合并段 | ObsClient.completeMultipartUpload | 通过分段上传任务的ID，合并指定桶中已上传的段。 |
    | 取消分段上传任务 | ObsClient.abortMultipartUpload | 通过分段上传任务的ID，取消指定桶中的分段上传任务。 |

    四、高级功能

    | 接口名 | 方法 | 功能描述 |
    | --- | --- | --- |
    | 恢复归档存储对象 | ObsClient.restoreObject | 恢复指定桶中的归档存储对象。 |
    | 生成带授权信息的URL | ObsClient.createSignedUrl | 通过访问密钥、请求方法类型、请求参数等信息生成一个在Query参数中携带鉴权信息的URL，以对OBS服务进行特定操作。 |
    | 生成带授权信息的表单上传参数 | ObsClient.createPostSignature | 生成用于鉴权的请求参数，以进行基于浏览器的POST表单上传。 |
    | 断点续传上传 | ObsClient.uploadFile | 对分段上传的封装和加强，解决上传大文件时由于网络不稳定或程序崩溃导致上传失败的问题。 |
    | 断点续传下载 | ObsClient.downloadFile | 对范围下载的封装和加强，解决下载大对象到本地时由于网络不稳定或程序崩溃导致下载失败的问题。 |

    五、工作流（WorkflowClient）

    | 接口名 | 方法 | 功能描述 |
    | --- | --- | --- |
    | 创建工作流 | WorkflowClient.createWorkflow | 根据模板创建工作流。 |
    | 查询工作流 | WorkflowClient.getWorkflow | 按名称查询工作流。 |
    | 删除工作流 | WorkflowClient.deleteWorkflow | 删除存在的工作流。 |
    | 更新工作流 | WorkflowClient.updateWorkflow | 更新工作流。 |
    | 查询工作流列表 | WorkflowClient.listWorkflow | 查询工作流列表。 |
    | API触发启动工作流 | WorkflowClient.asyncAPIStartWorkflow | API触发启动工作流。 |
    | 查询工作流实例列表 | WorkflowClient.listWorkflowExecution | 查询工作流实例列表。 |
    | 查询工作流实例 | WorkflowClient.getWorkflowExecution | 查询工作流实例详细。 |
    | 恢复失败状态的工作流实例 | WorkflowClient.restoreFailedWorkflowExecution | 当且仅当工作流实例处于执行失败状态才能执行恢复操作。恢复后，工作流实例将从上次失败的状态处继续执行，已执行过的状态不会再执行。 |
    | 配置桶触发器 | WorkflowClient.putTriggerPolicy | 在桶上绑定工作流触发器。 |
    | 查询桶触发器 | WorkflowClient.getTriggerPolicy | 查询桶上绑定工作流触发器。 |
    | 删除桶触发器 | WorkflowClient.deleteTriggerPolicy | 删除在桶上绑定工作流触发器。 |

    """

    protocol = StorageProtocol.OBS

    def __init__(self, config) -> None:
        super().__init__(config)
        if not self.config.endpoint:
            raise CustomException(msg="OBS 存储源必须配置 endpoint")
        adv = ObsAdvancedConfig(**self.config.advanced_config)
        self.client = ObsClient(
            access_key_id=self.config.username or "",
            secret_access_key=self.config.password or "",
            server=normalize_endpoint(self.config.endpoint, self.config.scheme),
            is_secure=self.config.is_secure,
            max_retry_count=adv.max_retry_count,
            timeout=adv.timeout,
            ssl_verify=adv.ssl_verify,
            is_cname=adv.is_cname,
            path_style=adv.path_style,
            pool_size=adv.pool_size,
            signature=adv.signature,
            region=adv.region,
            security_token=adv.security_token,
        )

    @staticmethod
    def _is_ok(resp: Any) -> bool:
        """判断 OBS 响应是否成功（status < 300）。SDK 未提供类型存根，故用 getattr 访问动态属性。"""
        status = getattr(resp, "status", None)
        return status is not None and status < 300

    @staticmethod
    def _error_desc(resp: Any) -> str:
        """提取 OBS 响应中的错误描述。"""
        code = getattr(resp, "errorCode", "") or ""
        message = getattr(resp, "errorMessage", "") or ""
        return f"{code} {message}".strip()

    def _sync_test_connection(self) -> bool:
        try:
            resp = self.client.listBuckets()
            if self._is_ok(resp):
                resp = self.client.headBucket(bucketName=self._require_bucket())
                if self._is_ok(resp):
                    return True
            logger.warning(f"OBS 连接测试失败: {self._error_desc(resp)}")
            return False
        except Exception as e:
            logger.warning(f"OBS 连接测试失败: {e}")
            return False

    def _sync_upload(self, local_path: str, remote_path: str) -> str:
        """上传：默认 uploadFile（断点续传 + 分片并发），流式传输（stream）走 putContent 单次上传。"""
        try:
            if self.config.transfer_mode == "stream":
                with open(local_path, "rb") as f:
                    resp = self.client.putContent(
                        bucketName=self._require_bucket(),
                        objectKey=remote_path,
                        content=f,
                    )
                if not self._is_ok(resp):
                    raise CustomException(msg=f"OBS 上传失败: {self._error_desc(resp)}")
                return remote_path
            part_size, concurrency, _ = self._multipart_settings()
            resp = self.client.uploadFile(
                bucketName=self._require_bucket(),
                objectKey=remote_path,
                uploadFile=local_path,
                partSize=part_size,
                taskNum=concurrency,
                enableCheckpoint=True,
            )
            if not self._is_ok(resp):
                raise CustomException(msg=f"OBS 上传失败: {self._error_desc(resp)}")
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"OBS 上传失败: {e!s}")
        return remote_path

    def _sync_download(self, remote_path: str, local_path: str) -> str:
        """下载（downloadFile 断点续传 + 分片并发）。"""
        try:
            resp = self.client.downloadFile(
                bucketName=self._require_bucket(),
                objectKey=remote_path,
                downloadFile=local_path,
                partSize=5 * 1024 * 1024,
                taskNum=3,
                enableCheckpoint=True,
            )
            if not self._is_ok(resp):
                raise CustomException(msg=f"OBS 下载失败: {self._error_desc(resp)}")
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"OBS 下载失败: {e!s}")
        return local_path

    def _sync_delete(self, remote_path: str) -> None:
        try:
            resp = self.client.deleteObject(bucketName=self._require_bucket(), objectKey=remote_path)
            if not self._is_ok(resp):
                raise CustomException(msg=f"OBS 删除失败: {self._error_desc(resp)}")
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"OBS 删除失败: {e!s}")

    def _sync_exists(self, remote_path: str) -> bool:
        try:
            resp = self.client.getObjectMetadata(bucketName=self._require_bucket(), objectKey=remote_path)
            return self._is_ok(resp)
        except Exception:
            return False

    @staticmethod
    def _to_utc_dt(value: str | None) -> datetime | None:
        """OBS SDK 的 lastModified 为 UTC 字符串（如 '2026/08/25 09:25:27'），转为 aware datetime。"""
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y/%m/%d %H:%M:%S").replace(tzinfo=UTC)
        except ValueError:
            return None

    def _sync_list(self, prefix: str) -> list[StorageObject]:
        """列举桶内“目录层”条目（Delimiter=/ 模拟文件夹，返回名称/是否目录/大小/修改时间）。
        OBS 单次最多返回 1000 条，经 marker 翻页拉全量。"""
        try:
            result: list[StorageObject] = []
            seen_dirs: set[str] = set()
            seen_files: set[str] = set()
            marker: str | None = None
            while True:
                kwargs: dict[str, Any] = {"bucketName": self._require_bucket(), "prefix": prefix, "delimiter": "/"}
                if marker:
                    kwargs["marker"] = marker
                resp = self.client.listObjects(**kwargs)
                if not self._is_ok(resp):
                    raise CustomException(msg=f"OBS 列表失败: {self._error_desc(resp)}")
                body = getattr(resp, "body", None)
                for common in getattr(body, "commonPrefixs", None) or []:
                    raw_key = (getattr(common, "prefix", "") or "").rstrip("/")
                    if raw_key in seen_dirs:
                        continue
                    seen_dirs.add(raw_key)
                    result.append(StorageObject(name=raw_key.rsplit("/", 1)[-1], key=raw_key, is_dir=True))
                for obj in getattr(body, "contents", None) or []:
                    raw_key = getattr(obj, "key", "") or ""
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
                            size=getattr(obj, "size", None),
                            modified_time=self._to_utc_dt(getattr(obj, "lastModified", None)),
                        )
                    )
                if getattr(body, "is_truncated", None):
                    marker = getattr(body, "next_marker", None) or ""
                    if not marker:
                        break
                else:
                    break
            return result
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"OBS 列表失败: {e!s}")

    def _sync_list_page(self, prefix: str, page_size: int, cursor: str | None) -> StoragePage:
        """游标分页：单次 SDK 请求只拉一页（OBS marker），翻页经前端回传游标。"""
        try:
            kwargs: dict[str, Any] = {
                "bucketName": self._require_bucket(),
                "prefix": prefix,
                "delimiter": "/",
                "max_keys": page_size,
            }
            if cursor:
                kwargs["marker"] = cursor
            resp = self.client.listObjects(**kwargs)
            if not self._is_ok(resp):
                raise CustomException(msg=f"OBS 列表失败: {self._error_desc(resp)}")
            body = getattr(resp, "body", None)
            truncated = bool(getattr(body, "is_truncated", None))
            next_cursor = getattr(body, "next_marker", None) or None
            items: list[StorageObject] = []
            for common in getattr(body, "commonPrefixs", None) or []:
                raw_key = (getattr(common, "prefix", "") or "").rstrip("/")
                items.append(StorageObject(name=raw_key.rsplit("/", 1)[-1], key=raw_key, is_dir=True))
            for obj in getattr(body, "contents", None) or []:
                raw_key = getattr(obj, "key", "") or ""
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
                        size=getattr(obj, "size", None),
                        modified_time=self._to_utc_dt(getattr(obj, "lastModified", None)),
                    )
                )
            return StoragePage(
                items=items,
                has_next=truncated,
                next_cursor=next_cursor,
            )
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"OBS 列表失败: {e!s}")

    def _sync_list_buckets(self) -> list[str]:
        """列出账号下全部存储桶。"""
        try:
            resp = self.client.listBuckets()
            if not self._is_ok(resp):
                raise CustomException(msg=f"OBS 桶列表失败: {self._error_desc(resp)}")
            body = getattr(resp, "body", None)
            buckets = getattr(body, "buckets", None) or []
            return [getattr(b, "name", "") or "" for b in buckets if getattr(b, "name", "")]
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"OBS 桶列表失败: {e!s}")

    def _sync_get_url(self, remote_path: str, expire: int) -> str:
        try:
            resp = self.client.createSignedUrl("GET", bucketName=self._require_bucket(), objectKey=remote_path, expires=expire)
            return getattr(resp, "signedUrl", "")
        except Exception as e:
            raise CustomException(msg=f"OBS 生成预签名 URL 失败: {e!s}")

    # ── 目录操作（对象存储以 key/ 占位对象模拟目录）──────────────────

    def _list_all_keys(self, prefix: str) -> list[str]:
        """分页列举前缀下的全部对象 key。"""
        keys: list[str] = []
        marker: str | None = None
        while True:
            kwargs: dict[str, Any] = {"bucketName": self._require_bucket(), "prefix": prefix}
            if marker:
                kwargs["marker"] = marker
            resp = self.client.listObjects(**kwargs)
            if not self._is_ok(resp):
                raise CustomException(msg=f"OBS 列举对象失败: {self._error_desc(resp)}")
            body = getattr(resp, "body", None)
            for obj in getattr(body, "contents", None) or []:
                key = getattr(obj, "key", "")
                if key:
                    keys.append(key)
            if not getattr(body, "is_truncated", False):
                break
            # 未指定 delimiter 时服务端可能不返回 next_marker，退化为当前页最后一个 key，避免死循环
            marker = getattr(body, "next_marker", None) or (keys[-1] if keys else "")
            if not marker:
                break
        return keys

    def _is_dir(self, key: str) -> bool:
        """判断 key 是否代表目录（存在占位对象或前缀下有任何对象）。"""
        try:
            resp = self.client.listObjects(bucketName=self._require_bucket(), prefix=key.rstrip("/") + "/", max_keys=1)
            if not self._is_ok(resp):
                return False
            body = getattr(resp, "body", None)
            return bool(getattr(body, "contents", None) or getattr(body, "commonPrefixs", None))
        except Exception:
            return False

    def _sync_mkdir(self, remote_dir: str) -> None:
        try:
            resp = self.client.putContent(bucketName=self._require_bucket(), objectKey=remote_dir.rstrip("/") + "/", content=b"")
            if not self._is_ok(resp):
                raise CustomException(msg=f"OBS 创建目录失败: {self._error_desc(resp)}")
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"OBS 创建目录失败: {e!s}")

    def _sync_rmdir(self, remote_dir: str) -> None:
        try:
            resp = self.client.deleteObject(bucketName=self._require_bucket(), objectKey=remote_dir.rstrip("/") + "/")
            if not self._is_ok(resp):
                raise CustomException(msg=f"OBS 删除目录失败: {self._error_desc(resp)}")
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"OBS 删除目录失败: {e!s}")

    def _sync_copy(self, src: str, dst: str) -> None:
        """复制：目录走基类递归实现；文件用服务端 copyObject。"""
        try:
            if self._is_dir(src):
                self._sync_copy_dir(src, dst)
                return
            resp = self.client.copyObject(
                sourceBucketName=self._require_bucket(),
                sourceObjectKey=src,
                destBucketName=self._require_bucket(),
                destObjectKey=dst,
            )
            if not self._is_ok(resp):
                raise CustomException(msg=f"OBS 复制失败: {self._error_desc(resp)}")
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"OBS 复制失败: {e!s}")

    def _sync_rename(self, src: str, dst: str) -> None:
        """重命名/移动：优先 OBS 原生 renameFile（支持目录级），失败回退先复制后删除。"""
        try:
            resp = self.client.renameFile(bucketName=self._require_bucket(), objectKey=src, newObjectKey=dst)
            if self._is_ok(resp):
                return
        except Exception:
            pass
        if self._is_dir(src):
            self._sync_move_dir(src, dst)
        else:
            self._sync_copy(src, dst)
            self._sync_delete(src)

    def _sync_list_recursive(self, prefix: str) -> list[StorageObject]:
        try:
            keys = self._list_all_keys(prefix)
        except Exception as e:
            raise CustomException(msg=f"OBS 递归列表失败: {e!s}")
        return self._entries_from_keys(keys)

    def _sync_delete_dir(self, remote_dir: str) -> None:
        """递归删除：一次列举全部对象并分批批量删除（含占位目录对象）。"""
        try:
            keys = self._list_all_keys(remote_dir)
            marker = remote_dir.rstrip("/") + "/"
            if marker not in keys:
                keys.append(marker)
            for i in range(0, len(keys), 1000):
                batch = keys[i : i + 1000]
                resp = self.client.deleteObjects(
                    bucketName=self._require_bucket(),
                    deleteObjectsRequest={"quiet": True, "objects": [{"key": k} for k in batch]},
                )
                if not self._is_ok(resp):
                    raise CustomException(msg=f"OBS 递归删除失败: {self._error_desc(resp)}")
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"OBS 递归删除失败: {e!s}")

    def _sync_close(self) -> None:
        """关闭 OBS 客户端连接。"""
        try:
            self.client.close()
        except Exception as e:
            logger.warning(f"OBS 关闭连接失败: {e}")
