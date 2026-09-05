from pydantic import BaseModel, Field


class DependencyStatus(BaseModel):
    """依赖状态"""

    status: int = Field(..., description="状态(0:异常 1:正常)")
    latency_ms: float | None = Field(default=None, description="延迟(毫秒)")


class HealthOut(BaseModel):
    """基础健康检查响应"""

    status: int = Field(..., description="状态(0:异常 1:正常)")
    timestamp: str = Field(..., description="时间戳")
    version: str = Field(..., description="版本号")
    uptime_seconds: float = Field(..., description="运行时间(秒)")


class ReadinessOut(BaseModel):
    """就绪探针响应"""

    status: int = Field(..., description="状态(0:异常 1:正常)")
    timestamp: str = Field(..., description="时间戳")
    version: str = Field(..., description="版本号")
    uptime_seconds: float = Field(..., description="运行时间(秒)")
    dependencies: dict[str, DependencyStatus] = Field(..., description="依赖状态")
    disk_usage: float = Field(..., description="磁盘使用率")
