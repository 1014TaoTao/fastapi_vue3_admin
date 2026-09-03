import asyncio
import platform
import socket
import time
from pathlib import Path

import psutil

from app.utils.common_util import bytes2human

from .schema import (
    CpuInfoSchema,
    DiskInfoSchema,
    MemoryInfoSchema,
    PyInfoSchema,
    ServerMonitorSchema,
    SysInfoSchema,
)


class ServerService:
    """服务监控模块服务层"""

    @staticmethod
    async def get_server_monitor_info() -> ServerMonitorSchema:
        # 采样全部为同步阻塞调用（psutil.disk_usage 在网络盘/卸载中的挂载点上
        # 可达秒级，socket.gethostbyname 依赖 DNS），放到工作线程执行避免拖慢事件循环
        return await asyncio.to_thread(ServerService._collect_monitor_info)

    @staticmethod
    def _collect_monitor_info() -> ServerMonitorSchema:
        return ServerMonitorSchema(
            cpu=ServerService._get_cpu_info(),
            mem=ServerService._get_memory_info(),
            sys=ServerService._get_system_info(),
            py=ServerService._get_python_info(),
            disks=ServerService._get_disk_info(),
        )

    @staticmethod
    def _get_cpu_info() -> CpuInfoSchema:
        cpu_times = psutil.cpu_times_percent()
        cpu_num = psutil.cpu_count(logical=True)
        if not cpu_num:
            cpu_num = 1
        return CpuInfoSchema(
            cpu_num=cpu_num,
            used=cpu_times.user,
            sys=cpu_times.system,
            free=cpu_times.idle,
        )

    @staticmethod
    def _get_memory_info() -> MemoryInfoSchema:
        memory = psutil.virtual_memory()
        return MemoryInfoSchema(
            total=bytes2human(memory.total),
            used=bytes2human(memory.used),
            free=bytes2human(memory.free),
            usage=memory.percent,
        )

    @staticmethod
    def _get_system_info() -> SysInfoSchema:
        hostname = socket.gethostname()
        return SysInfoSchema(
            computer_ip=socket.gethostbyname(hostname),
            computer_name=platform.node(),
            os_arch=platform.machine(),
            os_name=platform.platform(),
            user_dir=str(Path.cwd()),
        )

    @staticmethod
    def _get_python_info() -> PyInfoSchema:
        current_process = psutil.Process()
        memory = psutil.virtual_memory()
        process_memory = current_process.memory_info()

        start_time = current_process.create_time()
        run_time = ServerService._calculate_run_time(start_time)

        return PyInfoSchema(
            name=current_process.name(),
            version=platform.python_version(),
            start_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
            run_time=run_time,
            home=str(Path(current_process.exe())),
            memory_total=bytes2human(memory.available),
            memory_used=bytes2human(process_memory.rss),
            memory_free=bytes2human(memory.available - process_memory.rss),
            memory_usage=round((process_memory.rss / memory.available) * 100, 2),
        )

    @staticmethod
    def _get_disk_info() -> list[DiskInfoSchema]:
        disk_info = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                mount_point = str(Path(partition.mountpoint))
                disk_info.append(
                    DiskInfoSchema(
                        dir_name=mount_point,
                        sys_type_name=partition.fstype,
                        type_name=f"本地固定磁盘（{mount_point}）",
                        total=bytes2human(usage.total),
                        used=bytes2human(usage.used),
                        free=bytes2human(usage.free),
                        usage=usage.percent,
                    ),
                )
            except (PermissionError, FileNotFoundError):
                continue
        return disk_info

    @staticmethod
    def _calculate_run_time(start_time: float) -> str:
        difference = time.time() - start_time
        days = int(difference // (24 * 60 * 60))
        hours = int((difference % (24 * 60 * 60)) // (60 * 60))
        minutes = int((difference % (60 * 60)) // 60)
        return f"{days}天{hours}小时{minutes}分钟"
