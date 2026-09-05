from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin


class JobModel(ModelMixin):
    """任务执行日志表
    """

    __tablename__: str = "task_job"
    __table_args__: dict[str, str] = {"comment": "任务执行日志表"}
    
    job_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="任务ID")
    job_name: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="任务名称")
    trigger_type: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="触发方式: cron/interval/date/manual")
    next_run_time: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="下次执行时间")
    job_state: Mapped[str | None] = mapped_column(Text, nullable=True, comment="任务状态信息")
    result: Mapped[str | None] = mapped_column(Text, nullable=True, comment="执行结果")
    error: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="执行状态(0:待执行 1:执行中 2:成功 3:失败 4:超时 5:已取消)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")
