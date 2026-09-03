import asyncio
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import aiofiles
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_task.workflow.core.base import _OBJECT_STORE_PROTOCOLS, StorageAdapterConfig, StorageObject, StoragePage
from app.api.v1.module_task.workflow.core.factory import StorageAdapterFactory
from app.api.v1.module_task.workflow.node.service import StorageSourceService
from app.core.base_schema import AuthSchema
from app.core.exceptions import CustomException
from app.utils.upload_util import UploadUtil

from .schema import StoragePathCreateSchema, StoragePathResultSchema, StorageUploadResultSchema


class StorageFileService:
    """存储文件操作服务（上传/下载/删除/列表/预签名URL）"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    # ── 内部工具 ────────────────────────────────────────────────────

    @staticmethod
    def _validate_remote_path(remote_path: str) -> str:
        """规范化并校验远端相对路径（禁止路径穿越）。"""
        if not remote_path or not remote_path.strip():
            raise CustomException(msg="请提供文件路径")
        parts = [p for p in remote_path.replace("\\", "/").split("/") if p not in ("", ".")]
        if any(p == ".." for p in parts) or "\x00" in remote_path:
            raise CustomException(msg="非法的文件路径")
        return "/".join(parts)

    async def _get_source(self, source_id: int | None) -> StorageAdapterConfig:
        """获取存储源并构造适配器配置（密码已解密，含 SDK 高级配置）。"""
        source = await StorageSourceService(self.auth, self.db).get_active_source(source_id)
        return StorageSourceService._build_config(source)

    async def _get_adapter(self, source_id: int | None, bucket: str | None = None):
        """构造适配器并切换当前操作桶（对象存储多桶浏览：桶随请求传入，适配器按请求创建）。"""
        config = await self._get_source(source_id)
        adapter = StorageAdapterFactory.create(config)
        if bucket:
            adapter.set_bucket(bucket)
        return adapter

    @staticmethod
    async def _save_to_temp(file: UploadFile, suffix: str = "") -> str:
        """将上传文件内容落盘到系统临时目录，返回临时路径。"""
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        try:
            async with aiofiles.open(path, "wb") as f:
                while chunk := await file.read(1024 * 1024):
                    await f.write(chunk)
        except Exception:
            os.unlink(path)
            raise
        finally:
            await file.seek(0)
        return path

    @staticmethod
    def _zip_directory(src_root: Path, zip_path: str, arc_root: Path) -> None:
        """把 src_root 下所有文件打包到 zip_path（相对于 arc_root 计算归档名）。

        ZIP_DEFLATED 是纯 CPU + 磁盘 IO 的同步操作，目录较大时会在事件循环里
        独占数秒，因此统一由调用方通过 asyncio.to_thread 在线程中执行。
        """
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in src_root.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(arc_root).as_posix())

    # ── 业务方法 ────────────────────────────────────────────────────

    async def upload(
        self,
        source_id: int | None,
        file: UploadFile,
        remote_path: str | None = None,
        bucket: str | None = None,
    ) -> StorageUploadResultSchema:
        """上传文件到远端存储。remote_path 为空时自动生成安全文件名。"""
        if not file or not file.filename:
            raise CustomException(msg="请选择要上传的文件")

        if not UploadUtil.check_path_traversal(file.filename):
            raise CustomException(msg="文件名包含非法字符")
        extension = UploadUtil.get_extension_from_filename(file.filename)
        if not extension:
            raise CustomException(msg="无法识别文件类型")
        if UploadUtil.is_dangerous_extension(extension):
            raise CustomException(msg=f"不允许上传此类型的文件: {extension}")
        UploadUtil.check_file_size(file)

        # 确定远端路径
        if remote_path:
            if remote_path.endswith("/"):
                # 以 / 结尾视为目录：保留原文件名，拼接到目录下
                dir_path = self._validate_remote_path(remote_path)
                target = f"{dir_path}/{file.filename}"
            else:
                target = self._validate_remote_path(remote_path)
                # 大小写不敏感比较扩展名，避免 photo.JPG 被追加成 photo.JPG.jpg
                if not target.lower().endswith(extension.lower()):
                    target = f"{target}{extension}"
        else:
            target = UploadUtil.generate_safe_filename(file.filename, extension)

        temp_path = await self._save_to_temp(file, suffix=extension)
        adapter = await self._get_adapter(source_id, bucket)
        try:
            await adapter.upload(temp_path, target)
            file_url = await adapter.get_url(target)
        finally:
            await adapter.close()
            os.unlink(temp_path)

        return StorageUploadResultSchema(
            file_path=target,
            file_name=Path(target).name,
            origin_name=file.filename,
            file_url=file_url,
        )

    async def download(self, source_id: int | None, remote_path: str, bucket: str | None = None) -> tuple[str, str]:
        """下载远端文件到临时目录，返回 (本地临时路径, 文件名)。"""
        target = self._validate_remote_path(remote_path)
        extension = Path(target).suffix
        fd, temp_path = tempfile.mkstemp(suffix=extension)
        os.close(fd)
        adapter = await self._get_adapter(source_id, bucket)
        try:
            local_path = await adapter.download(target, temp_path)
        except Exception:
            os.unlink(temp_path)
            raise
        finally:
            await adapter.close()
        return local_path, Path(target).name

    async def download_dir(self, source_id: int | None, remote_path: str, bucket: str | None = None) -> tuple[str, str]:
        """递归下载目录并打包 ZIP，返回 (zip临时路径, zip文件名)。"""
        target = self._validate_remote_path(remote_path)
        adapter = await self._get_adapter(source_id, bucket)
        tmp_root = tempfile.mkdtemp(prefix="stor_dir_")
        zip_path = ""
        try:
            dir_name = Path(target).name or "download"
            local_dir = Path(tmp_root) / dir_name
            local_dir.mkdir(parents=True, exist_ok=True)
            await adapter.download_dir(target, str(local_dir), concurrency=3)
            fd, zip_path = tempfile.mkstemp(suffix=".zip")
            os.close(fd)
            await asyncio.to_thread(self._zip_directory, local_dir, zip_path, Path(tmp_root))
        except Exception:
            if zip_path:
                os.unlink(zip_path)
            raise
        finally:
            await adapter.close()
            await asyncio.to_thread(shutil.rmtree, tmp_root, ignore_errors=True)
        return zip_path, f"{dir_name}.zip"

    async def delete(self, source_id: int | None, remote_path: str, bucket: str | None = None) -> None:
        target = self._validate_remote_path(remote_path)
        adapter = await self._get_adapter(source_id, bucket)
        try:
            # 目录探测：对象存储对不存在的目录 key 执行 delete 会幂等成功（不抛异常），
            # 无法触发 delete_dir 回退，导致子文件残留；先探测再决定删除策略。
            is_dir = False
            try:
                objects = await adapter.list_files(target)
                t = target.rstrip("/")
                is_dir = any(o.is_dir or o.key.startswith(f"{t}/") for o in objects)
            except Exception:
                is_dir = False
            if is_dir:
                await adapter.delete_dir(target)
            else:
                try:
                    await adapter.delete(target)
                except Exception:
                    # 文件删除失败时回退为递归删除：兼容 FTP/SFTP 等协议无原生目录删除
                    await adapter.delete_dir(target)
        finally:
            await adapter.close()

    async def exists(self, source_id: int | None, remote_path: str, bucket: str | None = None) -> bool:
        target = self._validate_remote_path(remote_path)
        adapter = await self._get_adapter(source_id, bucket)
        try:
            return await adapter.exists(target)
        finally:
            await adapter.close()

    async def list_files(
        self,
        source_id: int | None,
        prefix: str = "",
        bucket: str | None = None,
        page_size: int | None = None,
        cursor: str | None = None,
    ) -> list[StorageObject] | StoragePage:
        """列出目录条目。

        - 不传 page_size：全量拉取（目录选择器/搜索等场景）。
        - 传 page_size：游标分页（对象存储走 SDK 原生游标，FTP/SFTP/LOCAL 走内存切片）。
        """
        safe_prefix = self._validate_remote_path(prefix) if prefix else ""
        adapter = await self._get_adapter(source_id, bucket)
        try:
            if page_size is not None:
                return await adapter.list_files(safe_prefix, page_size=page_size, cursor=cursor)
            return await adapter.list_files(safe_prefix)
        finally:
            await adapter.close()

    async def list_buckets(self, source_id: int | None) -> list[str]:
        """列出账号下全部存储桶（仅对象存储协议；FTP/SFTP/LOCAL 无桶概念返回空列表）。"""
        config = await self._get_source(source_id)
        if config.protocol not in _OBJECT_STORE_PROTOCOLS:
            return []
        adapter = StorageAdapterFactory.create(config)
        try:
            return await adapter.list_buckets()
        finally:
            await adapter.close()

    async def copy_or_move(
        self,
        source_id: int | None,
        source_path: str,
        target_id: int,
        target_path: str,
        move: bool = False,
        bucket: str | None = None,
    ) -> StoragePathResultSchema:
        """复制/移动文件：跨端点时下载到临时再上传；同端点 move 即重命名。"""
        src = self._validate_remote_path(source_path)
        dst = self._validate_remote_path(target_path)
        if move and source_id == target_id and src == dst:
            raise CustomException(msg="源路径与目标路径相同")
        source_config = await self._get_source(source_id)
        target_config = await self._get_source(target_id)
        src_adapter = StorageAdapterFactory.create(source_config)
        dst_adapter = StorageAdapterFactory.create(target_config)
        # 多桶浏览：操作在指定桶内进行；同端点复制/移动目标桶与源桶一致
        if bucket:
            src_adapter.set_bucket(bucket)
            if target_id == source_id:
                dst_adapter.set_bucket(bucket)
        # 目录守卫：本接口为文件级实现（临时文件 download/upload），目录会走进
        # download_dir 的目录逻辑而报错，且可能移入自身子树导致数据丢失，显式拦截。
        try:
            entries = await src_adapter.list_files(src)
        except Exception:
            entries = []
        if any((e.is_dir and e.key.rstrip("/") == src) or e.key.startswith(f"{src}/") for e in entries):
            raise CustomException(msg="暂不支持目录复制/移动，请使用传输任务")
        fd, temp_path = tempfile.mkstemp(suffix=Path(dst).suffix)
        os.close(fd)
        try:
            await src_adapter.download(src, temp_path)
            await dst_adapter.upload(temp_path, dst)
            if move:
                await src_adapter.delete(src)
        finally:
            await src_adapter.close()
            await dst_adapter.close()
            os.unlink(temp_path)
        return StoragePathResultSchema(source_path=src, target_path=dst)

    async def rename(self, source_id: int | None, src_path: str, dst_path: str, bucket: str | None = None) -> StoragePathResultSchema:
        """重命名/移动（同一存储源内）。"""
        src = self._validate_remote_path(src_path)
        dst = self._validate_remote_path(dst_path)
        if src == dst:
            raise CustomException(msg="源路径与目标路径相同")
        adapter = await self._get_adapter(source_id, bucket)
        try:
            await adapter.rename(src, dst)
        finally:
            await adapter.close()
        return StoragePathResultSchema(source_path=src, target_path=dst)

    async def mkdir(self, source_id: int | None, remote_dir: str, bucket: str | None = None) -> StoragePathCreateSchema:
        """新建目录。"""
        path = self._validate_remote_path(remote_dir)
        adapter = await self._get_adapter(source_id, bucket)
        try:
            await adapter.mkdir(path)
        finally:
            await adapter.close()
        return StoragePathCreateSchema(path=path)

    async def share(self, source_id: int | None, remote_path: str, expire: int = 3600, bucket: str | None = None) -> str | None:
        """生成分享链接（对象存储为预签名 URL，FTP/SFTP/LOCAL 返回 None）。"""
        target = self._validate_remote_path(remote_path)
        adapter = await self._get_adapter(source_id, bucket)
        try:
            return await adapter.get_url(target, expire=expire)
        finally:
            await adapter.close()
