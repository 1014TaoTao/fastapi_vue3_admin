from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class StorageSourceModel(ModelMixin, UserMixin):
    """存储源配置模型"""

    __tablename__: str = "task_workflow_storage_source"
    __table_args__: dict[str, str] = {"comment": "存储源配置表"}

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True, comment="存储源名称")
    protocol: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="协议(ftp/ftps/sftp/s3/obs/oss/cos/local)")
    host: Mapped[str | None] = mapped_column(String(255), default=None, nullable=True, comment="主机地址（对象存储可不填，用 endpoint）")
    port: Mapped[int] = mapped_column(Integer, nullable=False, comment="端口号（FTP/FTPS/SFTP 用）")
    username: Mapped[str | None] = mapped_column(String(255), default=None, nullable=True, comment="用户名/AccessKey")
    password: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="密码/SecretKey(Fernet加密)")
    bucket: Mapped[str | None] = mapped_column(String(255), default=None, nullable=True, comment="桶名（对象存储专用）")
    endpoint: Mapped[str | None] = mapped_column(String(255), default=None, nullable=True, comment="接入点(对象存储)")
    region: Mapped[str | None] = mapped_column(String(64), default=None, nullable=True, comment="区域(对象存储)")
    path_prefix: Mapped[str | None] = mapped_column(String(255), default=None, nullable=True, comment="统一路径前缀")
    is_secure: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否启用TLS(FTPS)")
    implicit_tls: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="FTPS是否隐式TLS(默认显式)")
    scheme: Mapped[str] = mapped_column(String(16), default="https", nullable=False, comment="对象存储访问协议(http/https)")
    encrypt_type: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="FTPS加密类型(0=明文 1=显式TLS可用时 2=要求显式TLS 3=隐式TLS)")
    connection_mode: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="FTP/FTPS传输模式(0=默认 1=主动 2=被动)")
    encoding: Mapped[str] = mapped_column(String(16), default="UTF-8", nullable=False, comment="FTP/FTPS/SFTP编码(utf-8/gbk 等)")
    multipart_part_size: Mapped[int] = mapped_column(Integer, default=50, nullable=False, comment="分片大小(MB，对象存储分片上传)")
    multipart_concurrency: Mapped[int] = mapped_column(Integer, default=6, nullable=False, comment="分片上传并发路数")
    multipart_memory_budget: Mapped[int] = mapped_column(Integer, default=512, nullable=False, comment="分片上传内存预算(MB)")
    advanced_config: Mapped[dict | None] = mapped_column(JSON, default=None, nullable=True, comment="SDK高级配置(JSON，按协议解析)")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否默认存储源")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:启用 1:停用)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")
