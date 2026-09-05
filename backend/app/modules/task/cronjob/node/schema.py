import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.base_schema import BaseQueryParam, BaseSchema, UserByQueryParam, UserBySchema
from app.core.validator import datetime_validator

# 节点可持久化的触发方式（"立即执行"不在其中，属于手动执行、不占用计划）
NODE_TRIGGER_TYPES = {"cron", "interval", "date"}


class NodeCreateSchema(BaseModel):
    """节点创建/编辑：基本信息 + 可选的定时执行计划。

    trigger/trigger_args 一旦设置并保存，节点即注册/刷新 APScheduler 任务（job id = 节点 id）；
    trigger 为空表示只保存定义、不排程，可随时手动执行一次。
    """

    name: str = Field(..., max_length=64, description="任务名称")
    func: str | None = Field(default=None, description="代码块")
    args: str | None = Field(default=None, description="位置参数")
    kwargs: str | None = Field(default=None, description="关键字参数")
    coalesce: bool | None = Field(default=False, description="是否合并运行:是否在多个运行时间到期时仅运行作业一次")
    max_instances: int | None = Field(default=1, ge=1, description="最大实例数:允许的最大并发执行实例数")
    jobstore: str | None = Field(default="default", max_length=64, description="任务存储")
    executor: str | None = Field(default="threadpool", max_length=64, description="任务执行器:将运行此作业的执行程序的名称")
    trigger: str | None = Field(default=None, description="触发方式: cron/interval/date，为空则不排程仅保存定义")
    trigger_args: str | None = Field(default=None, description="触发参数(表达式/间隔/执行时间)")
    start_date: str | None = Field(default=None, description="开始时间")
    end_date: str | None = Field(default=None, description="结束时间")
    code: str | None = Field(default=None, max_length=32, description="节点编码")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1 or len(v) > 64:
            raise ValueError("任务名称长度必须在1-64个字符之间")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2 or len(v) > 32:
            raise ValueError("节点编码长度必须在2-32个字符之间")
        if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", v):
            raise ValueError("节点编码必须以字母开头，仅允许字母、数字、下划线")
        return v

    @field_validator("trigger")
    @classmethod
    def validate_trigger(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if v not in NODE_TRIGGER_TYPES:
            raise ValueError("触发器必须为 cron/interval/date，或留空表示不排程")
        return v

    @model_validator(mode="after")
    def _validate_trigger_args(self):
        """设置触发器时必须提供触发参数；不排程时忽略历史 trigger_args。"""
        if self.trigger and not (self.trigger_args or "").strip():
            raise ValueError("设置了触发方式(cron/interval/date)时必须提供触发参数")
        if not self.trigger:
            self.trigger_args = None
        return self

    @model_validator(mode="after")
    def _validate_func(self):
        if not self.func or not self.func.strip():
            raise ValueError("必须提供代码块(func)")
        return self

    @model_validator(mode="after")
    def _validate_dates(self):
        """跨字段校验：结束时间不得早于开始时间。"""
        if self.start_date and self.end_date:
            try:
                start = datetime_validator(self.start_date)
                end = datetime_validator(self.end_date)
            except Exception:
                raise ValueError("时间格式必须为 YYYY-MM-DD HH:MM:SS")
            if end < start:
                raise ValueError("结束时间不能早于开始时间")
        return self


class NodeUpdateSchema(NodeCreateSchema):
    """节点更新模型"""


class NodeOutSchema(NodeCreateSchema, BaseSchema, UserBySchema):
    """节点响应模型"""

    status: int | None = Field(default=0, ge=0, le=1, description="状态(0:启用 1:停用)")

    # 运行时状态（由 service 查询调度器/执行日志后填充，静态场景为空）
    next_run_time: str | None = Field(default=None, description="下次运行时间")
    last_run_time: str | None = Field(default=None, description="最近一次运行时间")
    last_run_status: int | None = Field(default=None, description="最近一次运行状态(2:成功 3:失败)")

    model_config = ConfigDict(from_attributes=True)


class NodeQueryParam(BaseQueryParam, UserByQueryParam):
    """节点查询参数"""

    name: str | None = Field(None, description="节点名称", json_schema_extra={"q": "like"})
    status: int | None = Field(None, ge=0, le=1, description="状态(0:启动 1:停用)", json_schema_extra={"q": "eq"})


class NodeRunResultSchema(BaseModel):
    """手动执行一次的结果"""

    job_id: str = Field(..., description="临时任务ID")
    status: str = Field(..., description="执行状态")
    trigger: str = Field(default="manual", description="触发方式")
