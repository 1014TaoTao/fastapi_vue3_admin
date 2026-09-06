import ftplib
import os
import socket
import ssl
import tempfile
from datetime import datetime

from app.core.exceptions import CustomException
from app.core.logger import logger
from app.modules.task.storage.core.base import BaseStorageAdapter, FtpAdvancedConfig, StorageObject, StorageProtocol


class _ImplicitFTP_TLS(ftplib.FTP_TLS):
    """隐式 FTPS（默认端口 990）连接子类：socket 直连即套 TLS。"""

    def connect(self, host: str = "", port: int = 0, timeout: int = -999, source_address=None) -> str:
        if host != "":
            self.host = host
        if port > 0:
            self.port = port
        if timeout != -999:
            self.timeout = timeout
        if source_address is not None:
            self.source_address = source_address
        context = self.context
        if context is None:
            # FTP_TLS 默认 context 未设置时，构造宽松校验的客户端上下文（兼容自签名证书）
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        self.sock = context.wrap_socket(
            socket.create_connection((self.host, self.port), self.timeout, self.source_address),
            server_hostname=self.host,
        )
        self.file = self.sock.makefile("r", encoding=self.encoding)
        self.welcome = self.getresp()
        return self.welcome


class FtpStorageAdapter(BaseStorageAdapter):
    """FTP / FTPS 存储适配器（ftplib 标准库，同步调用经 asyncio.to_thread 包装）。"""

    protocol = StorageProtocol.FTP

    def __init__(self, config) -> None:
        super().__init__(config)
        self._adv = FtpAdvancedConfig(**self.config.advanced_config)

    def _new_client(self) -> ftplib.FTP_TLS | ftplib.FTP:
        """建立连接并登录。FTP 明文 / FTPS（显式或隐式 TLS）按配置选择。"""
        implicit = False
        if self.config.protocol == StorageProtocol.FTPS:
            # 隐式 TLS：implicit_tls 开关或 encrypt_type>=3（兼容两种配置写法）
            implicit = self.config.implicit_tls or (self.config.encrypt_type or 0) >= 3
            client = _ImplicitFTP_TLS() if implicit else ftplib.FTP_TLS()
        else:
            client = ftplib.FTP()
        client.encoding = self.config.encoding or "utf-8"
        client.connect(host=self.config.host, port=self.config.port, timeout=self._adv.timeout)
        # 传输模式：0=默认(被动) 1=主动 2=被动
        if self.config.connection_mode == 1:
            client.set_pasv(False)
        elif self.config.connection_mode == 2:
            client.set_pasv(True)
        if isinstance(client, ftplib.FTP_TLS):
            if not implicit:
                client.auth()  # 显式 FTPS：升级 TLS 通道（隐式 TLS 连接时已是加密通道，重复升级会报错）
        client.login(user=self.config.username or "", passwd=self.config.password or "")
        if isinstance(client, ftplib.FTP_TLS):
            client.prot_p()  # 数据通道加密
        return client

    @staticmethod
    def _close_client(client: ftplib.FTP) -> None:
        try:
            client.quit()
        except Exception:
            try:
                client.close()
            except Exception:
                pass

    def _sync_test_connection(self) -> bool:
        client = self._new_client()
        try:
            client.pwd()
            return True
        except Exception as e:
            logger.warning(f"FTP 连接测试失败: {e}")
            return False
        finally:
            self._close_client(client)

    def _sync_upload(self, local_path: str, remote_path: str) -> str:
        client = self._new_client()
        try:
            # 目标目录不存在时逐级创建（与 SFTP 上传行为对齐，否则 STOR 直接失败）
            dir_part = remote_path.rsplit("/", 1)[0] if "/" in remote_path else ""
            if dir_part:
                self._ensure_remote_dir(client, dir_part)
            with open(local_path, "rb") as f:
                client.storbinary(f"STOR {remote_path}", f)
        except Exception as e:
            raise CustomException(msg=f"FTP 上传失败: {e!s}")
        finally:
            self._close_client(client)
        return remote_path

    @staticmethod
    def _ensure_remote_dir(client: ftplib.FTP, remote_dir: str) -> None:
        """逐级创建远端目录（mkd -p，目录已存在的 550 错误静默跳过）。"""
        current = ""
        for part in [p for p in remote_dir.split("/") if p]:
            current = f"{current}/{part}"
            try:
                client.mkd(current)
            except ftplib.error_perm:
                pass

    def _sync_download(self, remote_path: str, local_path: str) -> str:
        client = self._new_client()
        try:
            with open(local_path, "wb") as f:
                client.retrbinary(f"RETR {remote_path}", f.write)
        except Exception as e:
            raise CustomException(msg=f"FTP 下载失败: {e!s}")
        finally:
            self._close_client(client)
        return local_path

    def _sync_delete(self, remote_path: str) -> None:
        client = self._new_client()
        try:
            client.delete(remote_path)
        except Exception as e:
            raise CustomException(msg=f"FTP 删除失败: {e!s}")
        finally:
            self._close_client(client)

    def _sync_exists(self, remote_path: str) -> bool:
        client = self._new_client()
        try:
            try:
                client.size(remote_path)
                return True
            except ftplib.error_perm:
                # 部分服务器不支持 SIZE，退化为 NLST 判断
                try:
                    client.nlst(remote_path)
                    return True
                except ftplib.error_perm:
                    return False
        except Exception:
            return False
        finally:
            self._close_client(client)

    def _sync_list(self, prefix: str) -> list[StorageObject]:
        client = self._new_client()
        try:
            # 空 prefix 表示浏览根目录：FTP 用 "." 表示登录后的当前目录
            entries = list(client.mlsd(prefix or "."))
            result: list[StorageObject] = []
            for name, facts in entries:
                if name in (".", ".."):
                    continue
                modified_time = None
                raw_mtime = facts.get("modify")
                if raw_mtime:
                    try:
                        modified_time = datetime.strptime(raw_mtime, "%Y%m%d%H%M%S")
                    except ValueError:
                        modified_time = None
                result.append(
                    StorageObject(
                        name=name,
                        key=f"{prefix}/{name}" if prefix else name,
                        is_dir=facts.get("type") == "dir",
                        size=int(facts["size"]) if facts.get("size") else None,
                        modified_time=modified_time,
                    )
                )
            return result
        except Exception as e:
            raise CustomException(msg=f"FTP 列表失败: {e!s}")
        finally:
            self._close_client(client)

    # ── 目录操作（FTP mkd 不自动创建父目录，需逐级创建）────────────────

    def _sync_mkdir(self, remote_dir: str) -> None:
        client = self._new_client()
        try:
            parts = [p for p in remote_dir.split("/") if p]
            current = ""
            for part in parts:
                current = f"{current}/{part}" if current else part
                try:
                    client.mkd(current)
                except ftplib.error_perm:
                    pass  # 目录已存在时跳过（部分服务器返回 550）
        except Exception as e:
            raise CustomException(msg=f"FTP 创建目录失败: {e!s}")
        finally:
            self._close_client(client)

    def _sync_rmdir(self, remote_dir: str) -> None:
        client = self._new_client()
        try:
            client.rmd(remote_dir)
        except Exception as e:
            raise CustomException(msg=f"FTP 删除目录失败: {e!s}")
        finally:
            self._close_client(client)

    def _sync_rename(self, src: str, dst: str) -> None:
        client = self._new_client()
        try:
            client.rename(src, dst)
        except Exception as e:
            raise CustomException(msg=f"FTP 重命名失败: {e!s}")
        finally:
            self._close_client(client)

    @staticmethod
    def _is_dir(client: ftplib.FTP, path: str) -> bool:
        """通过 MLSD 类型判断路径是否为目录。"""
        try:
            return any(facts.get("type") == "dir" for _name, facts in client.mlsd(path))
        except Exception:
            return False

    def _sync_copy(self, src: str, dst: str) -> None:
        """复制：目录走基类递归实现；文件经本地临时文件中转（FTP 无服务端复制）。"""
        client = self._new_client()
        try:
            if self._is_dir(client, src):
                self._close_client(client)
                self._sync_copy_dir(src, dst)
                return
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name
            try:
                with open(tmp_path, "wb") as f:
                    client.retrbinary(f"RETR {src}", f.write)
                with open(tmp_path, "rb") as f:
                    client.storbinary(f"STOR {dst}", f)
            finally:
                os.remove(tmp_path)
        except Exception as e:
            raise CustomException(msg=f"FTP 复制失败: {e!s}")
        finally:
            self._close_client(client)
