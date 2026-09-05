from pydantic import BaseModel, Field


class ServiceInfoOut(BaseModel):
    """健康状态：应用进程元信息 + 服务器 / 数据库 / Redis 连通状态"""

    name: str = Field(..., description="服务名称")
    version: str = Field(..., description="版本号")
    environment: str = Field(..., description="运行环境")
    db_status: int = Field(..., description="数据库状态(0:异常 1:正常)")
    redis_status: int = Field(..., description="Redis状态(0:异常 1:正常)")
