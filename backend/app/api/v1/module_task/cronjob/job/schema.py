from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.core.base_schema import BaseQueryParam, BaseSchema, UserByQueryParam, UserBySchema


class SchedulerStatusSchema(BaseModel):
    """调度器状态"""

    status: str = Field(..., description="调度器状态(运行中/已暂停/已停止/未知)")
    is_running: bool = Field(..., description="是否运行中")
    job_count: int = Field(..., description="调度器任务数量")


class SchedulerJobSchema(BaseModel):
    """调度器任务列表项"""

    id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    trigger: str = Field(..., description="触发器")
    next_run_time: str | None = Field(default=None, description="下次运行时间")
    status: int = Field(..., description="任务状态(0:运行中 1:暂停中 2:已停止 3:未知)")


class SchedulerJobModifySchema(BaseModel):
    """调度器任务属性修改模型（仅允许白名单属性）"""

    name: str | None = Field(default=None, min_length=1, max_length=128, description="任务名称")
    coalesce: bool | None = Field(default=None, description="是否合并错过的执行")
    max_instances: int | None = Field(default=None, ge=1, le=100, description="最大并发实例数")
    misfire_grace_time: int | None = Field(default=None, ge=0, le=86400, description="错过执行的宽限时间(秒)")

    def to_changes(self) -> dict:
        """转换为调度器属性参数（忽略未传字段）"""
        return self.model_dump(exclude_none=True)


class JobCreateSchema(BaseModel):
    """执行日志创建模型"""

    job_id: str = Field(..., max_length=64, description="任务ID")
    job_name: str | None = Field(default=None, max_length=128, description="任务名称")
    trigger_type: str | None = Field(default=None, max_length=32, description="触发方式")
    status: int = Field(default=0, ge=0, le=5, description="执行状态(0:待执行 1:执行中 2:成功 3:失败 4:超时 5:已取消)")
    next_run_time: str | None = Field(default=None, description="下次执行时间")
    job_state: str | None = Field(default=None, description="任务状态信息")
    result: str | None = Field(default=None, description="执行结果")
    error: str | None = Field(default=None, description="错误信息")

    @field_validator("job_id")
    @classmethod
    def validate_job_id(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1 or len(v) > 64:
            raise ValueError("任务ID长度必须在1-64个字符之间")
        return v

    @field_validator("trigger_type")
    @classmethod
    def validate_trigger_type(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"cron", "interval", "date", "manual"}
        v = v.strip()
        if v not in allowed:
            raise ValueError(f"触发方式必须为 {allowed}")
        return v


class JobUpdateSchema(BaseModel):
    """执行日志更新模型"""

    status: int | None = Field(default=None, ge=0, le=5, description="执行状态(0:待执行 1:执行中 2:成功 3:失败 4:超时 5:已取消)")
    next_run_time: str | None = Field(default=None, description="下次执行时间")
    job_state: str | None = Field(default=None, description="任务状态信息")
    result: str | None = Field(default=None, description="执行结果")
    error: str | None = Field(default=None, description="错误信息")


class JobOutSchema(JobCreateSchema, BaseSchema, UserBySchema):
    """执行日志响应模型"""

    model_config = ConfigDict(from_attributes=True)


class JobQueryParam(BaseQueryParam, UserByQueryParam):
    """执行日志查询参数"""

    job_id: str | None = Field(None, description="任务ID", json_schema_extra={"q": "eq"})
    job_name: str | None = Field(None, description="任务名称", json_schema_extra={"q": "like"})
    trigger_type: str | None = Field(None, description="触发方式", json_schema_extra={"q": "eq"})
    status: int | None = Field(None, ge=0, le=5, description="执行状态(0:待执行 1:执行中 2:成功 3:失败 4:超时 5:已取消)", json_schema_extra={"q": "eq"})
