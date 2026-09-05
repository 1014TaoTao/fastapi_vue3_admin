from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.base_schema import BaseQueryParam, BaseSchema

TransferStatus = Literal["pending", "running", "success", "failed", "canceled"]
TransferTaskType = Literal["parallel", "chain"]
TransferSourceType = Literal["local", "remote"]
TransferMode = Literal["stream", "multipart"]


class TransferTargetSchema(BaseModel):
    """传输目标配置"""

    target_id: int = Field(..., ge=1, description="目标存储源ID")
    target_path: str = Field(..., min_length=1, max_length=1024, description="目标路径")


class TransferTaskCreateSchema(BaseModel):
    """创建传输任务（远端源，JSON 提交）"""

    name: str = Field(..., min_length=1, max_length=128, description="任务名称")
    task_type: TransferTaskType = Field(..., description="任务类型(parallel:多目标 chain:链式)")
    source_type: TransferSourceType = Field(default="remote", description="源类型(local:本地 remote:远端)")
    source_id: int | None = Field(default=None, ge=1, description="源存储源ID(remote 必填)")
    source_path: str | None = Field(default=None, min_length=1, max_length=1024, description="源远端路径(remote 必填)")
    targets: list[TransferTargetSchema] = Field(..., min_length=1, description="目标列表(顺序即链式执行顺序)")
    transfer_mode: TransferMode | None = Field(default=None, description="传输方式(stream:流式 multipart:分片；空=用存储源默认)")
    multipart_part_size: int | None = Field(default=None, ge=5, le=5000, description="分片大小(MB，分片传输时覆盖存储源配置)")
    multipart_concurrency: int | None = Field(default=None, ge=1, le=64, description="分片上传并发路数(分片传输时覆盖存储源配置)")

    @model_validator(mode="after")
    def validate_source(self):
        if self.source_type == "remote" and not self.source_id:
            raise ValueError("远端源必须指定源存储源 source_id")
        if self.source_type == "remote" and not self.source_path:
            raise ValueError("远端源必须指定源路径 source_path")
        return self


class LocalUploadInfoSchema(BaseModel):
    """本地源上传文件信息（服务端临时文件）"""

    source_path: str = Field(..., description="服务端临时文件路径")
    source_name: str = Field(..., description="原始文件名")
    source_size: int = Field(..., ge=0, description="文件大小(字节)")


class TransferTaskStoreSchema(BaseModel):
    """传输任务落库模型（create 展开明细后持久化）"""

    name: str = Field(..., min_length=1, max_length=128, description="任务名称")
    task_type: TransferTaskType = Field(..., description="任务类型")
    source_type: TransferSourceType = Field(default="remote", description="源类型")
    source_id: int | None = Field(default=None, ge=1, description="源存储源ID")
    source_path: str | None = Field(default=None, max_length=1024, description="源路径")
    source_name: str | None = Field(default=None, max_length=255, description="源文件名")
    source_size: int | None = Field(default=None, ge=0, description="源文件大小")
    status: TransferStatus = Field(default="pending", description="状态")


class TransferStepCreateSchema(BaseModel):
    """传输步骤落库模型（由目标列表展开）"""

    step_order: int = Field(..., ge=0, description="步骤序号")
    source_id: int | None = Field(default=None, ge=1, description="源存储源ID")
    source_path: str | None = Field(default=None, max_length=1024, description="源路径")
    target_id: int = Field(..., ge=1, description="目标存储源ID")
    target_path: str = Field(..., min_length=1, max_length=1024, description="目标路径")
    transfer_mode: TransferMode | None = Field(default=None, description="传输方式")
    multipart_part_size: int | None = Field(default=None, ge=1, description="分片大小(MB)")
    multipart_concurrency: int | None = Field(default=None, ge=1, description="分片并发数")


class TransferStepOutSchema(BaseSchema):
    """传输步骤详情"""

    model_config = ConfigDict(from_attributes=True)

    task_id: int = Field(description="任务ID")
    step_order: int = Field(description="步骤序号")
    source_id: int | None = Field(default=None, description="源存储源ID")
    source_path: str | None = Field(default=None, description="源路径")
    target_id: int = Field(description="目标存储源ID")
    target_path: str = Field(description="目标路径")
    transfer_mode: TransferMode | None = Field(default=None, description="传输方式(空=用存储源默认)")
    multipart_part_size: int | None = Field(default=None, description="分片大小(MB)")
    multipart_concurrency: int | None = Field(default=None, description="分片上传并发路数")
    status: TransferStatus = Field(description="状态")
    progress: int = Field(default=0, description="进度(0-100)")
    speed: float = Field(default=0.0, description="速度(B/s)")
    total_size: int = Field(default=0, description="本步总字节")
    transferred_size: int = Field(default=0, description="本步已传输字节")
    error_msg: str | None = Field(default=None, description="错误信息")
    started_at: datetime | None = Field(default=None, description="开始时间")
    finished_at: datetime | None = Field(default=None, description="结束时间")


class TransferTaskCreateResultSchema(BaseModel):
    """创建传输任务结果"""

    id: int = Field(..., ge=1, description="任务ID")


class TransferTaskOutSchema(BaseSchema):
    """传输任务详情"""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(description="任务名称")
    task_type: TransferTaskType = Field(description="任务类型")
    source_type: TransferSourceType = Field(description="源类型")
    source_id: int | None = Field(default=None, description="源存储源ID")
    source_path: str | None = Field(default=None, description="源远端路径")
    source_name: str | None = Field(default=None, description="源文件名")
    source_size: int | None = Field(default=None, description="源文件大小")
    status: TransferStatus = Field(description="状态")
    total_size: int = Field(default=0, description="总字节")
    transferred_size: int = Field(default=0, description="已传输字节")
    progress: int = Field(default=0, description="进度(0-100)")
    speed: float = Field(default=0.0, description="实时速度(B/s)")
    error_msg: str | None = Field(default=None, description="错误信息")
    started_at: datetime | None = Field(default=None, description="开始时间")
    finished_at: datetime | None = Field(default=None, description="结束时间")
    steps: list[TransferStepOutSchema] = Field(default_factory=list, description="传输步骤")


class TransferTaskQueryParam(BaseQueryParam):
    """传输任务查询参数"""

    name: str | None = Field(None, description="任务名称", json_schema_extra={"q": "like"})
    task_type: TransferTaskType | None = Field(None, description="任务类型", json_schema_extra={"q": "eq"})
    status: TransferStatus | None = Field(None, description="状态", json_schema_extra={"q": "eq"})
