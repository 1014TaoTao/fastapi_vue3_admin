from app.api.v1.module_task.workflow.core.base import BaseStorageAdapter, StorageAdapterConfig, StorageProtocol
from app.api.v1.module_task.workflow.core.cos_adapter import CosStorageAdapter
from app.api.v1.module_task.workflow.core.ftp_ftps_adapter import FtpStorageAdapter
from app.api.v1.module_task.workflow.core.local_adapter import LocalStorageAdapter
from app.api.v1.module_task.workflow.core.obs_adapter import ObsStorageAdapter
from app.api.v1.module_task.workflow.core.oss_adapter import OssStorageAdapter
from app.api.v1.module_task.workflow.core.s3_adapter import S3StorageAdapter
from app.api.v1.module_task.workflow.core.sftp_adapter import SftpStorageAdapter
from app.core.exceptions import CustomException

# 协议 → 适配器类映射（FTPS 复用 FTP 适配器，由配置区分显式/隐式 TLS）
_STORAGE_ADAPTERS: dict[str, type[BaseStorageAdapter]] = {
    StorageProtocol.FTP.value: FtpStorageAdapter,
    StorageProtocol.FTPS.value: FtpStorageAdapter,
    StorageProtocol.SFTP.value: SftpStorageAdapter,
    StorageProtocol.S3.value: S3StorageAdapter,
    StorageProtocol.OBS.value: ObsStorageAdapter,
    StorageProtocol.OSS.value: OssStorageAdapter,
    StorageProtocol.COS.value: CosStorageAdapter,
    StorageProtocol.LOCAL.value: LocalStorageAdapter,
}


class StorageAdapterFactory:
    """存储适配器工厂：根据协议创建对应适配器实例。"""

    @staticmethod
    def create(config: StorageAdapterConfig) -> BaseStorageAdapter:
        adapter_cls = _STORAGE_ADAPTERS.get(config.protocol.value)
        if adapter_cls is None:
            raise CustomException(msg=f"不支持的存储协议: {config.protocol}")
        return adapter_cls(config)
