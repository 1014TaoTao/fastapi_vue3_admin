import importlib
import inspect
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy import inspect as sa_inspect

from app.config.path_conf import BASE_DIR
from app.core.exceptions import CustomException


class ImportUtil:
    """扫描工程中的 ORM 模型文件并做有效性校验的辅助类。
    """

    @classmethod
    def find_project_root(cls) -> Path:
        """返回项目根目录（与配置中的 `BASE_DIR` 一致）。

        返回:
        - Path: 项目根路径。
        """
        return BASE_DIR

    @classmethod
    def is_valid_model(cls, obj: Any, base_class: type) -> bool:
        """判断是否为可映射的 SQLAlchemy 模型类（含表名与非空列）。

        参数:
        - obj (Any): 待验证对象（一般为类）。
        - base_class (type): ORM 声明基类。

        返回:
        - bool: 是否为有效模型类。
        """
        # 必须继承自base_class且不是base_class本身
        if not (inspect.isclass(obj) and issubclass(obj, base_class) and obj is not base_class):
            return False

        # 必须有表名定义（排除抽象基类）
        if not hasattr(obj, "__tablename__") or getattr(obj, "__tablename__", None) is None:
            return False

        # 必须有至少一个列定义
        try:
            inspected = sa_inspect(obj)
            return inspected is not None and len(inspected.columns) > 0
        except Exception:
            return False

    @classmethod
    @lru_cache(maxsize=256)
    def find_models(cls, base_class: type) -> list[Any]:
        """遍历工程内 `model.py` / `models.py`，收集去重后的有效模型类。

        参数:
        - base_class (type): SQLAlchemy 声明基类。

        返回:
        - list[Any]: 模型类列表。

        异常:
        - ImportError: 模块导入失败（非「无法从某名导入」类警告）。
        - CustomException: 处理模块时发生未预期错误。
        """
        models = []
        # 按类对象去重
        seen_models = set()
        # 按表名去重（防止同表名冲突）
        seen_tables = set()
        # 记录已经处理过的model.py文件路径
        processed_model_files = set()

        project_root = cls.find_project_root()

        # 排除目录扩展
        exclude_dirs = {
            "venv",
            ".env",
            ".git",
            "__pycache__",
            "migrations",
            "alembic",
            "tests",
            "test",
            "docs",
            "examples",
            "scripts",
            ".venv",
            "static",
            "templates",
            "sql",
            "env",
        }

        # 定义要搜索的模型目录模式
        model_dir_patterns = ["model.py", "models.py"]

        # 使用一个更高效的方法来查找所有model.py文件
        model_files = []
        for root, dirs, files in os.walk(project_root):
            # 过滤排除目录
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if file in model_dir_patterns:
                    file_path = Path(root) / file
                    # 构建相对于项目根的模块路径
                    relative_path = file_path.relative_to(project_root)
                    model_files.append((file_path, relative_path))

        # 按模块路径排序，确保先导入基础模块
        model_files.sort(key=lambda x: str(x[1]))

        for file_path, relative_path in model_files:
            # 确保文件路径没有被处理过
            if str(file_path) in processed_model_files:
                continue

            processed_model_files.add(str(file_path))

            # 构建模块名（将路径分隔符转换为点）
            module_parts = (*relative_path.parts[:-1], relative_path.stem)
            module_name = ".".join(module_parts)

            try:
                # 导入模块
                module = importlib.import_module(module_name)

                # 获取模块中的所有类
                for _name, obj in inspect.getmembers(module, inspect.isclass):
                    # 验证模型有效性
                    if not cls.is_valid_model(obj, base_class):
                        continue

                    # 检查类对象重复
                    if obj in seen_models:
                        continue

                    # 检查表名重复
                    table_name = getattr(obj, "__tablename__", None)
                    if table_name is None:
                        continue
                    if table_name in seen_tables:
                        continue

                    # 添加到已处理集合
                    seen_models.add(obj)
                    seen_tables.add(table_name)
                    models.append(obj)
            except ImportError as e:
                if "cannot import name" not in str(e):
                    raise ImportError(f"❗️ 警告: 无法导入模块 {module_name}: {e}")
            except Exception as e:
                raise CustomException(f"❌️ 处理模块 {module_name} 时出错: {e}")

        # 查找apscheduler_jobs表的模型（如果存在）
        cls._find_apscheduler_model(base_class, models, seen_models, seen_tables)

        return models

    @classmethod
    def _find_apscheduler_model(
        cls,
        base_class: type,
        models: list[Any],
        seen_models: set[Any],
        seen_tables: set[str],
    ) -> None:
        """尝试从调度相关模块补充 `apscheduler_jobs` 表对应模型。

        参数:
        - base_class (type): ORM 声明基类。
        - models (list[Any]): 已收集模型列表（就地追加）。
        - seen_models (set[Any]): 已见模型对象集合。
        - seen_tables (set[str]): 已见表名集合。

        返回:
        - None

        异常:
        - CustomException: 扫描过程出现未预期错误。
        """
        # 尝试从apscheduler相关模块导入
        try:
            # 检查是否有自定义的apscheduler模型
            for module_name in [
                "app.core.ap_scheduler",
                "app.modules.task.scheduler_test",
            ]:
                try:
                    module = importlib.import_module(module_name)
                    for _name, obj in inspect.getmembers(module, inspect.isclass):
                        if (cls.is_valid_model(obj, base_class)
                            and getattr(obj, "__tablename__", None) == "apscheduler_jobs"
                            and obj not in seen_models
                            and "apscheduler_jobs" not in seen_tables
                        ):
                            seen_models.add(obj)
                            seen_tables.add("apscheduler_jobs")
                            models.append(obj)
                            print(f"✅️ 找到有效模型: {obj.__module__}.{obj.__name__} (表: apscheduler_jobs)")
                except ImportError:
                    pass
        except Exception as e:
            raise CustomException(f"❗️ 查找APScheduler模型时出错: {e}")
