"""SFTP 存储适配器

基于 paramiko。连接在首次使用时建立，并在适配器实例生命周期内复用
（避免每次操作都重新进行 SSH 握手，与 FTP/FTPS 客户端保持一致）；
同步操作经基类 asyncio.to_thread 包装，不阻塞事件循环。
用完由调用方调用 close() 释放连接。
"""
import os
import stat
from datetime import UTC, datetime

import paramiko

from app.core.exceptions import CustomException
from app.core.logger import logger
from app.modules.task.storage.core.base import BaseStorageAdapter, SftpAdvancedConfig, StorageObject, StorageProtocol


class SftpStorageAdapter(BaseStorageAdapter):
    """SFTP 存储适配器（paramiko，同步调用经 asyncio.to_thread 包装）。"""

    protocol = StorageProtocol.SFTP

    # SFTP 通道复用同一连接，不支持多线程并发读写
    concurrency_safe: bool = False

    def __init__(self, config) -> None:
        super().__init__(config)
        self._ssh: paramiko.SSHClient | None = None
        self._sftp: paramiko.SFTPClient | None = None
        self._adv = SftpAdvancedConfig(**self.config.advanced_config)

    # ── 连接管理 ──────────────────────────────────────────────────

    def _connect(self) -> paramiko.SFTPClient:
        """建立并复用 SFTP 连接：首次使用时连接，之后直接复用。"""
        if self._sftp is not None:
            return self._sftp
        if not self.config.username or not self.config.password:
            raise CustomException(msg="SFTP 存储源必须配置用户名与密码")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(
                hostname=self.config.host,
                port=self.config.port,
                username=self.config.username or "",
                password=self.config.password or "",
                timeout=self._adv.connect_timeout,
                banner_timeout=self._adv.banner_timeout,
                auth_timeout=self._adv.auth_timeout,
                channel_timeout=self._adv.channel_timeout,
                allow_agent=self._adv.allow_agent,
                look_for_keys=self._adv.look_for_keys,
                compress=self._adv.compress,
            )
            transport = ssh.get_transport()
            if transport is None or not transport.is_active():
                raise RuntimeError("SSH 连接已断开")
            if self._adv.keepalive_interval > 0:
                transport.set_keepalive(self._adv.keepalive_interval)
            sftp = ssh.open_sftp()
            # 给 SFTP 通道设置超时，防止服务器不响应时 listdir/stat 等操作无限阻塞
            channel = sftp.get_channel()
            if channel:
                channel.settimeout(self._adv.connect_timeout)
        except Exception:
            ssh.close()
            raise
        self._ssh = ssh
        self._sftp = sftp
        return sftp

    @staticmethod
    def _ensure_remote_dir(client: paramiko.SFTPClient, remote_dir: str) -> None:
        """递归创建远端目录（mkdir -p）。"""
        parts = [p for p in remote_dir.split("/") if p]
        current = ""
        for part in parts:
            current = f"{current}/{part}" if current else part
            try:
                client.stat(current)
            except FileNotFoundError:
                client.mkdir(current)
            except OSError:
                pass

    def _sync_close(self) -> None:
        """关闭 SFTP 通道与 SSH 连接。"""
        if self._sftp:
            try:
                self._sftp.close()
            except Exception:
                pass
            self._sftp = None
        if self._ssh:
            try:
                self._ssh.close()
            except Exception:
                pass
            self._ssh = None

    # ── 同步协议操作 ──────────────────────────────────────────────

    def _sync_test_connection(self) -> bool:
        try:
            self._connect().listdir(".")
            return True
        except Exception as e:
            logger.warning(f"SFTP 连接测试失败: {e}")
            return False

    def _sync_upload(self, local_path: str, remote_path: str) -> str:
        client = self._connect()
        try:
            dir_part, _ = remote_path.rsplit("/", 1) if "/" in remote_path else ("", remote_path)
            if dir_part:
                self._ensure_remote_dir(client, dir_part)
            client.put(local_path, remote_path)
        except Exception as e:
            raise CustomException(msg=f"SFTP 上传失败: {e!s}")
        return remote_path

    def _sync_download(self, remote_path: str, local_path: str) -> str:
        """下载，支持断点续传：本地已有部分文件时从偏移处继续。"""
        client = self._connect()
        try:
            remote_size = client.stat(remote_path).st_size or 0
            local_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0
            if local_size > remote_size:
                # 本地文件比远端还大（可能内容不一致），整文件重新下载
                os.remove(local_path)
                local_size = 0
            if local_size == remote_size:
                return local_path  # 已完整下载，跳过
            if local_size:
                with client.open(remote_path, "rb") as rf, open(local_path, "ab") as lf:
                    rf.seek(local_size)
                    while chunk := rf.read(1024 * 1024):
                        lf.write(chunk)
            else:
                client.get(remote_path, local_path)
        except Exception as e:
            raise CustomException(msg=f"SFTP 下载失败: {e!s}")
        return local_path

    def _sync_delete(self, remote_path: str) -> None:
        try:
            self._connect().remove(remote_path)
        except Exception as e:
            raise CustomException(msg=f"SFTP 删除失败: {e!s}")

    def _sync_exists(self, remote_path: str) -> bool:
        try:
            self._connect().stat(remote_path)
            return True
        except (FileNotFoundError, OSError):
            return False

    def _sync_list(self, prefix: str) -> list[StorageObject]:
        try:
            # 空 prefix 表示浏览根目录：SFTP 用 "." 表示登录后的当前目录
            attrs = self._connect().listdir_attr(prefix or ".")
        except Exception as e:
            raise CustomException(msg=f"SFTP 列表失败: {e!s}")
        result: list[StorageObject] = []
        for attr in attrs:
            result.append(
                StorageObject(
                    name=attr.filename,
                    key=f"{prefix}/{attr.filename}" if prefix else attr.filename,
                    is_dir=bool(attr.st_mode and stat.S_ISDIR(attr.st_mode)),
                    size=attr.st_size,
                    modified_time=datetime.fromtimestamp(attr.st_mtime, tz=UTC) if attr.st_mtime else None,
                )
            )
        return result

    # ── 目录操作（SFTP 原生支持目录重命名，复制则流式传输）────────────

    def _is_dir(self, path: str) -> bool:
        try:
            attr = self._connect().stat(path)
            return bool(attr.st_mode and stat.S_ISDIR(attr.st_mode))
        except (FileNotFoundError, OSError):
            return False

    def _sync_mkdir(self, remote_dir: str) -> None:
        try:
            self._ensure_remote_dir(self._connect(), remote_dir)
        except Exception as e:
            raise CustomException(msg=f"SFTP 创建目录失败: {e!s}")

    def _sync_rmdir(self, remote_dir: str) -> None:
        try:
            self._connect().rmdir(remote_dir)
        except Exception as e:
            raise CustomException(msg=f"SFTP 删除目录失败: {e!s}")

    def _sync_rename(self, src: str, dst: str) -> None:
        try:
            self._connect().posix_rename(src, dst)
        except Exception as e:
            raise CustomException(msg=f"SFTP 重命名失败: {e!s}")

    def _sync_copy(self, src: str, dst: str) -> None:
        """复制：目录走基类递归实现；文件用通道流式复制（SFTP 无服务端复制）。"""
        client = self._connect()
        try:
            if self._is_dir(src):
                self._sync_copy_dir(src, dst)
                return
            with client.open(src, "rb") as rf, client.open(dst, "wb") as wf:
                while chunk := rf.read(1024 * 1024):
                    wf.write(chunk)
        except Exception as e:
            raise CustomException(msg=f"SFTP 复制失败: {e!s}")
