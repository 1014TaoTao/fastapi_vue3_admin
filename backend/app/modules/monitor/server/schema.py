from pydantic import BaseModel, Field


class CpuInfoSchema(BaseModel):
    """CPU信息模型"""

    cpu_num: int = Field(description="CPU核心数")
    used: float = Field(ge=0, le=100, description="CPU用户使用率(%)")
    sys: float = Field(ge=0, le=100, description="CPU系统使用率(%)")
    free: float = Field(ge=0, le=100, description="CPU空闲率(%)")


class MemoryInfoSchema(BaseModel):
    """内存信息模型"""

    total: str = Field(description="内存总量")
    used: str = Field(description="已用内存")
    free: str = Field(description="剩余内存")
    usage: float = Field(ge=0, le=100, description="使用率(%)")


class SysInfoSchema(BaseModel):
    """系统信息模型"""

    computer_ip: str = Field(description="服务器IP")
    computer_name: str = Field(description="服务器名称")
    os_arch: str = Field(description="系统架构")
    os_name: str = Field(description="操作系统")
    user_dir: str = Field(description="项目路径")


class PyInfoSchema(BaseModel):
    """Python运行信息模型"""

    name: str = Field(description="Python名称")
    version: str = Field(description="Python版本")
    start_time: str = Field(description="启动时间")
    run_time: str = Field(description="运行时长")
    home: str = Field(description="安装路径")
    memory_used: str = Field(description="内存占用")
    memory_usage: float = Field(ge=0, le=100, description="内存使用率(%)")
    memory_total: str = Field(description="总内存")
    memory_free: str = Field(description="剩余内存")


class DiskInfoSchema(BaseModel):
    """磁盘信息模型"""

    dir_name: str = Field(description="磁盘路径")
    sys_type_name: str = Field(description="文件系统类型")
    type_name: str = Field(description="磁盘类型")
    total: str = Field(description="总容量")
    used: str = Field(description="已用容量")
    free: str = Field(description="可用容量")
    usage: float = Field(ge=0, le=100, description="使用率(%)")


class ServerMonitorSchema(BaseModel):
    """服务器监控信息模型"""

    cpu: CpuInfoSchema = Field(description="CPU信息")
    mem: MemoryInfoSchema = Field(description="内存信息")
    py: PyInfoSchema = Field(description="Python运行信息")
    sys: SysInfoSchema = Field(description="系统信息")
    disks: list[DiskInfoSchema] = Field(default_factory=list, description="磁盘信息")
