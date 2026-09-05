import codecs

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.base_schema import BaseQueryParam, BaseSchema, UserByQueryParam, UserBySchema
from app.modules.workflow.core.base import DEFAULT_PORTS, StorageProtocol


class StorageSourceConfigSchema(BaseModel):
    """存储源连接配置模型（创建/测试共用）"""

    protocol: StorageProtocol = Field(..., description="协议(ftp/ftps/sftp/s3/obs/oss/cos/local)")
    host: str | None = Field(default=None, max_length=255, description="主机地址/根目录（对象存储可不填，用 endpoint）")
    port: int | None = Field(default=None, ge=0, le=65535, description="端口(local 协议为0；不传则使用协议默认端口)")
    username: str | None = Field(default=None, max_length=255, description="用户名/AccessKey")
    password: str | None = Field(default=None, max_length=512, description="密码/SecretKey")
    bucket: str | None = Field(default=None, max_length=255, description="桶名/根目录")
    endpoint: str | None = Field(default=None, max_length=255, description="接入点(对象存储)")
    region: str | None = Field(default=None, max_length=64, description="区域(对象存储)")
    path_prefix: str | None = Field(default=None, max_length=255, description="统一路径前缀")
    is_secure: bool = Field(default=False, description="是否启用TLS(FTPS)")
    implicit_tls: bool = Field(default=False, description="FTPS是否隐式TLS(默认显式)")
    scheme: str = Field(default="https", description="对象存储访问协议(http/https)")
    encrypt_type: int = Field(default=1, description="FTPS加密类型(0=明文 1=显式TLS可用时 2=要求显式TLS 3=隐式TLS)")
    connection_mode: int = Field(default=0, description="FTP/FTPS传输模式(0=默认 1=主动 2=被动)")
    encoding: str = Field(default="UTF-8", description="FTP/FTPS/SFTP编码(utf-8/gbk 等)")
    # 分片传输参数（对象存储分片上传，每个端点独立配置；FTP/SFTP/LOCAL 等协议忽略）
    multipart_part_size: int = Field(default=50, ge=5, le=5000, description="分片大小(MB)")
    multipart_concurrency: int = Field(default=6, ge=1, le=64, description="分片上传并发路数")
    multipart_memory_budget: int = Field(default=512, ge=8, le=10240, description="分片上传内存预算(MB)")
    # SDK 高级配置（按协议解析，见 core/base.py；留空使用默认值）
    advanced_config: dict | None = Field(default=None, description="SDK高级配置(JSON)")

    @field_validator("path_prefix")
    @classmethod
    def validate_path_prefix(cls, value: str | None) -> str | None:
        if value:
            value = value.strip()
            if ".." in value or "\x00" in value:
                raise ValueError("路径前缀包含非法字符")
        return value

    @field_validator("encoding")
    @classmethod
    def validate_encoding(cls, value: str | None) -> str | None:
        if value:
            try:
                codecs.lookup(value)
            except LookupError:
                raise ValueError(f"未知的编码: {value}（如 utf-8/gbk 等）")
        return value

    @field_validator("advanced_config")
    @classmethod
    def validate_advanced_config(cls, value: dict | None, info) -> dict | None:
        """校验协议 SDK 高级配置取值，避免非法值直达 SDK 报错。"""
        if not value:
            return value
        if info.data.get("protocol") == StorageProtocol.S3:
            s3_enum = {
                "signature_version": {"s3v4", "s3", "v2"},
                "retries_mode": {"standard", "adaptive", "legacy"},
                "addressing_style": {"auto", "path", "virtual"},
            }
            for key, allowed in s3_enum.items():
                if key in value and value[key] not in allowed:
                    raise ValueError(f"S3 {key} 取值必须为 {'/'.join(sorted(allowed))}")
        return value

    @model_validator(mode="after")
    def validate_protocol_fields(self):
        """按协议校验必填字段并填充默认端口。"""
        if self.port is None:
            self.port = DEFAULT_PORTS[self.protocol]
        # 对象存储类协议必须配置桶/空间名
        obj_store_protocols = (
            StorageProtocol.S3,
            StorageProtocol.OBS,
            StorageProtocol.OSS,
            StorageProtocol.COS,
        )
        if self.protocol in obj_store_protocols:
            # 对象存储协议由接入点 URL 决定端口，统一置 0（避免无意义的端口输入）
            self.port = 0
        if self.protocol in obj_store_protocols and not self.bucket:
            raise ValueError(f"{self.protocol.value} 协议必须配置 bucket")
        # 非对象存储协议必须配置主机地址
        if self.protocol not in obj_store_protocols and not self.host:
            raise ValueError(f"{self.protocol.value} 协议必须配置 host")
        # endpoint 必须配置的协议（接入点须为完整 URL，如 https://xxx）
        if self.protocol in (StorageProtocol.S3, StorageProtocol.OBS, StorageProtocol.OSS) and not self.endpoint:
            raise ValueError(f"{self.protocol.value} 协议必须配置 endpoint")
        if self.protocol == StorageProtocol.COS and not self.region:
            raise ValueError("cos 协议必须配置 region")
        if self.protocol == StorageProtocol.COS:
            # COS 默认走 https（适配器以 is_secure 决定 Scheme）
            self.is_secure = True
            appid = self.advanced_config.get("appid") if self.advanced_config else None
            if appid and not str(appid).isdigit():
                raise ValueError("COS appid 必须为纯数字")
        if self.protocol == StorageProtocol.FTPS:
            if self.encrypt_type < 1:
                raise ValueError("FTPS 加密方式不能为 0(明文)，明文请使用 FTP 协议")
            # 显式 TLS(1/2) 默认端口 21，990 是隐式 TLS 端口
            if self.encrypt_type < 3 and self.port == DEFAULT_PORTS[StorageProtocol.FTPS]:
                self.port = 21
            self.is_secure = True
        return self


class StorageSourceCreateSchema(StorageSourceConfigSchema):
    """存储源创建模型"""

    name: str = Field(..., min_length=1, max_length=64, description="存储源名称")
    is_default: bool = Field(default=False, description="是否默认存储源")
    status: int = Field(default=0, ge=0, le=1, description="状态(0:启用 1:停用)")
    description: str | None = Field(default=None, max_length=255, description="备注")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("存储源名称不能为空")
        return value


class StorageSourceUpdateSchema(StorageSourceCreateSchema):
    """存储源更新模型（password 为空表示不修改原密码）"""


class StorageSourceTestSchema(StorageSourceConfigSchema):
    """存储源连接测试模型（仅校验连接配置，不落库；密码留空且传 source_id 时回退已保存密码）"""

    source_id: int | None = Field(default=None, ge=1, description="已保存的存储源ID(编辑态测试时使用)")


class StorageSourceOutSchema(StorageSourceCreateSchema, BaseSchema, UserBySchema):
    """存储源详情响应模型（密码永不明文返回）"""

    model_config = ConfigDict(from_attributes=True)

    password: None = Field(default=None, exclude=True, repr=False, description="密码(不返回)")
    has_password: bool = Field(default=False, description="是否已配置密码")

    @field_validator("password", mode="before")
    @classmethod
    def mask_password(cls, value) -> None:
        return None


class StorageSourceQueryParam(BaseQueryParam, UserByQueryParam):
    """存储源管理查询参数"""

    name: str | None = Field(None, description="存储源名称", json_schema_extra={"q": "like"})
    protocol: StorageProtocol | None = Field(None, description="协议", json_schema_extra={"q": "eq"})
    status: int | None = Field(None, ge=0, le=1, description="状态(0:启用 1:停用)", json_schema_extra={"q": "eq"})
