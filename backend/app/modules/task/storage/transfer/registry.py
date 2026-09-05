"""传输任务运行时注册表（单实例部署）"""


class TransferTaskRegistry:
    """维护任务取消标志等运行时状态（不持久化，重启后任务按状态恢复）"""

    def __init__(self) -> None:
        self._cancel_flags: dict[int, bool] = {}

    def mark_cancel(self, task_id: int) -> None:
        self._cancel_flags[task_id] = True

    def is_canceled(self, task_id: int) -> bool:
        return self._cancel_flags.get(task_id, False)

    def clear(self, task_id: int) -> None:
        self._cancel_flags.pop(task_id, None)


transfer_task_registry = TransferTaskRegistry()
