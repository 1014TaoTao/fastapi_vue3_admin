from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class StorageTransferTaskModel(ModelMixin, UserMixin):
    """文件传输任务模型（多目标 / 链式）"""

    __tablename__: str = "task_workflow_transfer_task"
    __table_args__: dict[str, str] = {"comment": "文件传输任务表"}

    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="任务名称")
    task_type: Mapped[str] = mapped_column(String(16), nullable=False, comment="任务类型(parallel:多目标 chain:链式)")
    source_type: Mapped[str] = mapped_column(String(16), nullable=False, comment="源类型(local:本地 remote:远端)")
    source_id: Mapped[int | None] = mapped_column(Integer, default=None, nullable=True, comment="源存储源ID(本地源为空)")
    source_path: Mapped[str | None] = mapped_column(String(1024), default=None, nullable=True, comment="源远端路径(本地源为服务端临时文件)")
    source_name: Mapped[str | None] = mapped_column(String(512), default=None, nullable=True, comment="源文件名")
    source_size: Mapped[int | None] = mapped_column(BigInteger, default=None, nullable=True, comment="源文件大小(字节)")
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False, index=True, comment="状态(pending/running/success/failed/canceled)")
    total_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False, comment="总字节")
    transferred_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False, comment="已传输字节")
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="进度(0-100)")
    speed: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, comment="实时速度(B/s)")
    error_msg: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="错误信息")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, nullable=True, comment="开始时间")
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, nullable=True, comment="结束时间")


class StorageTransferStepModel(ModelMixin):
    """文件传输步骤模型（一个任务展开为多个步骤）"""

    __tablename__: str = "task_workflow_transfer_step"
    __table_args__: dict[str, str] = {"comment": "文件传输步骤表"}

    task_id: Mapped[int] = mapped_column(
        ForeignKey("task_workflow_transfer_task.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="任务ID",
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False, comment="步骤序号(从0开始)")
    source_id: Mapped[int | None] = mapped_column(Integer, default=None, nullable=True, comment="源存储源ID(首步本地源为空)")
    source_path: Mapped[str | None] = mapped_column(String(1024), default=None, nullable=True, comment="源路径(本地源为服务端临时文件)")
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="目标存储源ID")
    target_path: Mapped[str] = mapped_column(String(1024), nullable=False, comment="目标路径")
    transfer_mode: Mapped[str | None] = mapped_column(String(16), default=None, nullable=True, comment="传输方式(stream:流式 multipart:分片；空=用存储源默认)")
    multipart_part_size: Mapped[int | None] = mapped_column(Integer, default=None, nullable=True, comment="分片大小(MB，分片传输时覆盖存储源配置)")
    multipart_concurrency: Mapped[int | None] = mapped_column(Integer, default=None, nullable=True, comment="分片上传并发路数(分片传输时覆盖存储源配置)")
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False, comment="状态(pending/running/success/failed/canceled)")
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="进度(0-100)")
    speed: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, comment="实时速度(B/s)")
    total_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False, comment="本步总字节")
    transferred_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False, comment="本步已传输字节")
    error_msg: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="错误信息")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, nullable=True, comment="开始时间")
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, nullable=True, comment="结束时间")
