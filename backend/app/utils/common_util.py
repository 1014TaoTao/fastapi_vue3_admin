import importlib
import re
import uuid
from collections.abc import Generator, Sequence
from pathlib import Path
from typing import Any, Literal

from sqlalchemy import text
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.sql.elements import Null
from sqlalchemy.sql.expression import false, null, true

from app.config.path_conf import STATIC_DIR
from app.core.exceptions import CustomException
from app.core.logger import logger


def import_module(module: str, desc: str) -> Any:
    """动态导入模块

    参数:
    - module (str): 模块名称。
    - desc (str): 模块描述。

    返回:
    - Any: 模块对象。
    """
    try:
        module_path, module_class = module.rsplit(".", 1)
        module = importlib.import_module(module_path)  # pyright: ignore[reportAssignmentType]
        return getattr(module, module_class)
    except ModuleNotFoundError:
        logger.error(f"❗️ 导入{desc}失败,未找到模块:{module}")
        raise
    except AttributeError:
        logger.error(f"❗ ️导入{desc}失败,未找到模块方法:{module}")
        raise


async def import_modules_async(modules: list, desc: str, **kwargs) -> None:
    """异步导入模块列表

    参数:
    - modules (list[str]): 模块列表。
    - desc (str): 模块描述。
    - kwargs: 额外参数。

    返回:
    - None
    """
    for module in modules:
        if not module:
            continue
        try:
            module_path = module[0 : module.rindex(".")]
            module_name = module[module.rindex(".") + 1 :]
            module_obj = importlib.import_module(module_path)
            await getattr(module_obj, module_name)(**kwargs)
        except ModuleNotFoundError:
            logger.error(f"❌️ 导入{desc}失败,未找到模块:{module}")
            raise
        except AttributeError:
            logger.error(f"❌️ 导入{desc}失败,未找到模块方法:{module}")
            raise


def get_random_character() -> str:
    """生成随机字符串

    返回:
    - str: 随机字符串。
    """
    return uuid.uuid4().hex


def uuid4_str() -> str:
    """数据库引擎 UUID 类型兼容：返回无连字符的 UUID 字符串。

    返回:
    - str: UUID 字符串。
    """
    return str(uuid.uuid4())


def search_to_dict(search: Any, default: Any = None) -> dict | None:
    """将 Pydantic 查询模型转为参数字典。

    - search 为 None 时返回 default（默认 None）。
    - search 非空时调用 model_dump() 提取字段字典，排除 None 值。
    - 自动合并 ``_start`` / ``_end`` 时间范围对为 ``("between", [start, end])``。
    - 自动将 ``json_schema_extra={"q": "op"}`` 标记的字段转为 ``("op", value)`` 元组。

    参数:
    - search: Pydantic 查询模型或 None。
    - default: search 为 None 时的返回值，默认 None。

    返回:
    - dict | None: 查询参数字典或 None。
    """
    if not search:
        return default
    d = search.model_dump(exclude_none=True)

    # 自动合并 _start/_end 时间范围对 → ("between", [start, end])
    # 适用业务时间列（date/time/datetime），如 begin_date_start / begin_date_end
    for key in list(d.keys()):
        if key.endswith("_start"):
            base = key[: -len("_start")]
            end_key = f"{base}_end"
            if end_key in d:
                d[base] = ("between", [d.pop(key), d.pop(end_key)])

    # 处理数组格式的时间范围参数 → ("between", [start, end])
    for key in list(d.keys()):
        if isinstance(d[key], list) and len(d[key]) == 2 and key.endswith("_time"):
            d[key] = ("between", d[key])

    for field_name, field_info in search.model_fields.items():
        if field_name not in d:
            continue
        q_op = (field_info.json_schema_extra or {}).get("q")
        if q_op:
            d[field_name] = (q_op, d[field_name])
    return d


def get_parent_id_map(model_list: Sequence[DeclarativeBase]) -> dict[int, int]:
    """获取父级 ID 映射字典

    参数:
    - model_list (Sequence[DeclarativeBase]): 模型列表。

    返回:
    - Dict[int, int]: {id: parent_id} 映射字典。
    """
    return {item.id: item.parent_id for item in model_list}  # pyright: ignore[reportAttributeAccessIssue]


def get_parent_recursion(id: int, id_map: dict[int, int], ids: list[int] | None = None) -> list[int]:
    """递归获取所有父级 ID

    参数:
    - id (int): 当前 ID。
    - id_map (dict[int, int]): ID 映射字典。
    - ids (list[int] | None): 已收集的 ID 列表。

    返回:
    - list[int]: 所有父级 ID 列表。
    """
    ids = ids or []
    if id in ids:
        raise CustomException(msg="递归获取父级ID失败,不可以自引用")
    ids.append(id)
    parent_id = id_map.get(id)
    if parent_id:
        get_parent_recursion(parent_id, id_map, ids)
    return ids


def get_child_id_map(
    model_list: Sequence[DeclarativeBase],
) -> dict[int, list[int]]:
    """获取子级 ID 映射字典

    参数:
    - model_list (Sequence[DeclarativeBase]): 模型列表。

    返回:
    - Dict[int, List[int]]: {id: [child_ids]} 映射字典。
    """
    data_map = {}
    for model in model_list:
        data_map.setdefault(model.id, [])  # pyright: ignore[reportAttributeAccessIssue]
        if model.parent_id:  # pyright: ignore[reportAttributeAccessIssue]
            data_map.setdefault(model.parent_id, []).append(model.id)  # pyright: ignore[reportAttributeAccessIssue]
    return data_map


def get_child_recursion(id: int, id_map: dict[int, list[int]], ids: list[int] | None = None) -> list[int]:
    """递归获取所有子级 ID

    参数:
    - id (int): 当前 ID。
    - id_map (dict[int, list[int]]): ID 映射字典。
    - ids (list[int] | None): 已收集的 ID 列表。

    返回:
    - list[int]: 所有子级 ID 列表。
    """
    ids = ids or []
    ids.append(id)
    for child in id_map.get(id, []):
        get_child_recursion(child, id_map, ids)
    return ids


def traversal_to_tree(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """通过遍历算法构造树形结构

    参数:
    - nodes (list[dict[str, Any]]): 树节点列表。

    返回:
    - list[dict[str, Any]]: 构造后的树形结构列表。
    """
    tree: list[dict[str, Any]] = []
    node_dict = {node["id"]: node for node in nodes}

    for node in nodes:
        # 确保每个节点都有children字段，即使没有子节点也设置为null
        if "children" not in node:
            node["children"] = None

        parent_id = node["parent_id"]
        if parent_id is None:
            tree.append(node)
        else:
            parent_node = node_dict.get(parent_id)
            if parent_node is not None:
                if "children" not in parent_node or parent_node["children"] is None:
                    parent_node["children"] = []
                if node not in parent_node["children"]:
                    parent_node["children"].append(node)
            elif node not in tree:
                tree.append(node)

    # 确保所有节点都有children字段
    for node in tree:
        if "children" not in node:
            node["children"] = None

    return tree


def recursive_to_tree(nodes: list[dict[str, Any]], *, parent_id: int | None = None) -> list[dict[str, Any]]:
    """通过递归算法构造树形结构（性能影响较大）

    参数:
    - nodes (list[dict[str, Any]]): 树节点列表。
    - parent_id (int | None): 父节点 ID,默认为 None 表示根节点。

    返回:
    - list[dict[str, Any]]: 构造后的树形结构列表。
    """
    tree: list[dict[str, Any]] = []
    for node in nodes:
        if node["parent_id"] == parent_id:
            child_nodes = recursive_to_tree(nodes, parent_id=node["id"])
            if child_nodes:
                node["children"] = child_nodes
            tree.append(node)
    return tree


def bytes2human(n: int, format_str: str = "%(value).1f%(symbol)s") -> str:
    """字节数转人类可读格式
    Used by various scripts. See:
    http://goo.gl/zeJZl

    >>> bytes2human(10000)
    '9.8K'
    >>> bytes2human(100001221)
    '95.4M'

    参数:
    - n (int): 字节数。
    - format_str (str): 格式化字符串，默认 '%(value).1f%(symbol)s'。

    返回:
    - str: 可读的字节字符串，如 '1.5MB'。
    """
    symbols = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    prefix = {s: 1 << (i + 1) * 10 for i, s in enumerate(symbols[1:])}
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format_str % locals()
    return format_str % {"symbol": symbols[0], "value": n}


def bytes2file_response(bytes_info: bytes) -> Generator[bytes, Any, None]:
    """将字节内容封装为单块流式生成器，供文件下载响应使用。

    参数:
    - bytes_info (bytes): 文件二进制内容。

    返回:
    - Generator[bytes, Any, None]: 仅 yield 一次的字节生成器。
    """
    yield bytes_info


def get_filepath_from_url(url: str) -> Path:
    """工具方法：根据请求参数获取文件路径

    参数:
    - url (str): 请求参数中的 url 参数。

    返回:
    - Path: 文件路径。
    """
    file_info = url.split("?")[1].split("&")
    task_id = file_info[0].split("=")[1]
    file_name = file_info[1].split("=")[1]
    task_path = file_info[2].split("=")[1]
    filepath = STATIC_DIR.joinpath(task_path, task_id, file_name)

    return filepath


def compute_menu_route_first_segment(
    parent_catalog_id: int | None,  # noqa: ARG001
    package_name: str,
    module_name: str | None,  # noqa: ARG001
) -> str:
    """前端页面路由首段 — 始终使用 ``module_xxx`` 作为路由首段。

    中性位置函数，供 ``Jinja2TemplateUtil`` 和 ``GenTableService``
    双方模块级安全导入，避免 ``jinja2_template_util ↔ gencode.service`` 循环依赖。
    """
    pn = (package_name or "").strip()
    if not pn:
        raise CustomException(msg="包名不能为空")
    return pn if pn.startswith("module_") else f"module_{pn}"


class SqlalchemyUtil:
    """sqlalchemy工具类
    """

    @classmethod
    def base_to_dict(
        cls,
        obj: DeclarativeBase | dict[str, Any],
        transform_case: Literal["no_case", "snake_to_camel", "camel_to_snake"] = "no_case",
    ):
        """将 SQLAlchemy 模型或字典转为普通 dict，并可做键名大小写转换。

        参数:
        - obj (DeclarativeBase | dict[str, Any]): 模型实例或字典。
        - transform_case (Literal[...]): no_case / snake_to_camel / camel_to_snake。

        返回:
        - dict[str, Any]: 扁平字典结果。
        """
        if isinstance(obj, DeclarativeBase):
            base_dict = obj.__dict__.copy()
            base_dict.pop("_sa_instance_state", None)
            for name, value in base_dict.items():
                if isinstance(value, InstrumentedList):
                    base_dict[name] = cls.serialize_result(value, "snake_to_camel")
        elif isinstance(obj, dict):
            base_dict = obj.copy()
        if transform_case == "snake_to_camel":
            return {CamelCaseUtil.snake_to_camel(k): v for k, v in base_dict.items()}
        if transform_case == "camel_to_snake":
            return {SnakeCaseUtil.camel_to_snake(k): v for k, v in base_dict.items()}

        return base_dict

    @classmethod
    def serialize_result(
        cls,
        result: Any,
        transform_case: Literal["no_case", "snake_to_camel", "camel_to_snake"] = "no_case",
    ):
        """将 SQLAlchemy 查询结果（模型、列表、Row 等）递归序列化为可 JSON 化结构。

        参数:
        - result (Any): ORM 对象、列表、Row 等。
        - transform_case (Literal[...]): 键名转换策略。

        返回:
        - Any: 序列化后的 Python 内置类型或嵌套结构。
        """
        if isinstance(result, (DeclarativeBase, dict)):
            return cls.base_to_dict(result, transform_case)
        if isinstance(result, list):
            return [cls.serialize_result(row, transform_case) for row in result]
        if isinstance(result, Row):
            if all(isinstance(row, DeclarativeBase) for row in result):
                return [cls.base_to_dict(row, transform_case) for row in result]
            if any(isinstance(row, DeclarativeBase) for row in result):
                return [cls.serialize_result(row, transform_case) for row in result]
            result_dict = result._asdict()
            if transform_case == "snake_to_camel":
                return {CamelCaseUtil.snake_to_camel(k): v for k, v in result_dict.items()}
            if transform_case == "camel_to_snake":
                return {SnakeCaseUtil.camel_to_snake(k): v for k, v in result_dict.items()}
            return result_dict
        return result

    @classmethod
    def get_server_default_null(cls, dialect_name: str, need_explicit_null: bool = True) -> Null | None:
        """按方言返回列默认值中的 NULL 表达（PostgreSQL 可显式 DEFAULT NULL）。

        参数:
        - dialect_name (str): 数据库方言名。
        - need_explicit_null (bool): 是否生成显式 NULL 默认值。

        返回:
        - Null | None: SQLAlchemy null() 或 None。
        """
        if need_explicit_null and dialect_name == "postgres":
            return null()
        return None

    @classmethod
    def get_boolean_server_default(cls, dialect_name: str, value: bool) -> Any:
        """按方言返回布尔列的服务端默认值，保证 Alembic autogenerate 与各库反射结果一致。

        - MySQL/SQLite: 反射结果为 '0'/'1'，使用 text("0")/text("1")
        - PostgreSQL:   反射结果为 'false'/'true'，使用 expression.false()/expression.true()

        参数:
        - dialect_name (str): 数据库方言名。
        - value (bool): 布尔默认值。

        返回:
        - Any: SQLAlchemy 默认值表达式。
        """
        if dialect_name == "postgres":
            return true() if value else false()
        return text("1" if value else "0")


class CamelCaseUtil:
    """下划线形式(snake_case)转小驼峰形式(camelCase)工具方法
    """

    @classmethod
    def snake_to_camel(cls, snake_str: str):
        """下划线形式 (snake_case) 转为大驼峰形式 (PascalCase)。

        参数:
        - snake_str (str): 下划线分隔字符串。

        返回:
        - str: 合并首字母大写后的驼峰字符串。
        """
        words = snake_str.split("_")
        return "".join(word.capitalize() for word in words)

    @classmethod
    def transform_result(cls, result: Any):
        """将查询结果递归序列化并将键名转为小驼峰。

        参数:
        - result (Any): ORM 查询结果或嵌套结构。

        返回:
        - Any: 小驼峰键名的序列化结果。
        """
        return SqlalchemyUtil.serialize_result(result=result, transform_case="snake_to_camel")


class SnakeCaseUtil:
    """小驼峰形式(camelCase)转下划线形式(snake_case)工具方法
    """

    @classmethod
    def camel_to_snake(cls, camel_str: str):
        """小驼峰形式 (camelCase) 转为下划线形式 (snake_case)。

        参数:
        - camel_str (str): 驼峰字符串。

        返回:
        - str: 下划线分隔且全小写。
        """
        # 在大写字母前添加一个下划线，然后将整个字符串转为小写
        words = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", words).lower()

    @classmethod
    def transform_result(cls, result: Any):
        """将查询结果递归序列化并将键名转为下划线形式。

        参数:
        - result (Any): ORM 查询结果或嵌套结构。

        返回:
        - Any: 下划线键名的序列化结果。
        """
        return SqlalchemyUtil.serialize_result(result=result, transform_case="camel_to_snake")
