"""示例处理器模块

提供简单的示例方法供节点执行函数调用
"""

from datetime import datetime


def demo_handler(*args, **kwargs) -> dict:
    """示例处理器（演示节点调用形态）。

    返回:
    - dict: 包含 message、入参快照与时间戳。
    """
    return {
        "message": "Hello from demo_handler!",
        "args": args,
        "kwargs": kwargs,
        "time": datetime.now().isoformat(),
    }


def process_data(data: list, operation: str = "sum") -> dict:
    """简单数值列表聚合。

    参数:
    - data (list): 数值列表。
    - operation (str): sum、avg、max、min、count 之一。

    返回:
    - dict: 含 operation 与 result，或 error 说明。
    """
    if not data:
        return {"error": "数据为空"}

    if operation == "sum":
        result = sum(data)
    elif operation == "avg":
        result = sum(data) / len(data)
    elif operation == "max":
        result = max(data)
    elif operation == "min":
        result = min(data)
    elif operation == "count":
        result = len(data)
    else:
        return {"error": f"不支持的操作: {operation}"}

    return {"operation": operation, "result": result}
