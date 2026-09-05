from pydantic import BaseModel, Field


class CacheMonitorSchema(BaseModel):
    """缓存监控信息模型"""

    command_stats: list[dict] = Field(default_factory=list, description="Redis命令统计信息")
    db_size: int = Field(default=0, description="Redis数据库中的Key总数")
    info: dict = Field(default_factory=dict, description="Redis服务器信息")


class CacheInfoSchema(BaseModel):
    """缓存对象信息模型"""

    cache_key: str = Field(..., description="缓存键名")
    cache_name: str = Field(..., description="缓存名称")
    cache_value: str | None = Field(default=None, description="缓存值")
    remark: str | None = Field(default=None, description="备注说明")
