"""简化的动态路由发现与注册。

目录与命名规范：
- 插件放在 ``app/plugin`` 下，顶级目录名以 ``module_`` 开头（如 ``module_example``）。
- 控制器文件必须为 ``controller.py``。
- 从 ``module_xxx`` 到 ``controller.py`` 的每级目录名须为合法 Python 标识符。
- 每级目录应有 ``__init__.py``（或符合 namespace package 规则）。
- 在 ``controller.py`` 模块顶层定义 ``APIRouter`` 实例并赋值给变量。

路由前缀：``module_xxx`` 映射为 ``/xxx``。
"""

import importlib
import re
from pathlib import Path

from fastapi import APIRouter, FastAPI

from app.core.logger import logger

# 路径参数只参与匹配、不参与语义，比较重复路由时先抹掉参数名
_PATH_PARAM_RE = re.compile(r"\{[^}]*\}")


class DynamicRouterRegistry:
    """动态路由注册器，管理插件路由的扫描与注册。"""

    def __init__(self) -> None:
        self._cache: APIRouter | None = None

    def init_app(self, app: FastAPI) -> "DynamicRouterRegistry":
        """构建动态路由、注册到 app——返回 self 支持链式调用。"""
        router = self._build()
        app.include_router(router)
        check_route_conflicts(app)
        return self

    def _build(self) -> APIRouter:
        """扫描并构建动态路由（带缓存）。

        任何插件导入失败都会中止启动：半成品 router 会让进程带着缺失的接口正常
        提供服务，故障被推迟成"某个模块突然 404"，比启动即失败难定位得多。
        """
        if self._cache is not None:
            return self._cache

        root_router = APIRouter()
        seen_router_ids: set[int] = set()
        base_package = importlib.import_module("app.plugin")
        base_dir = Path(next(iter(base_package.__path__)))

        controller_files = sorted(base_dir.glob("module_*/**/controller.py"))

        container_routers: dict[str, APIRouter] = {}
        failed: list[str] = []

        for file in controller_files:
            rel_path = file.relative_to(base_dir)
            path_parts = rel_path.parts
            top_module = path_parts[0]

            suffix = top_module[7:] if top_module.startswith("module_") else ""
            if not suffix:
                logger.error(f"❌ 跳过异常顶级目录名（须为 module_ 前缀）: {top_module!r}，文件: {file}")
                continue
            prefix = f"/{suffix}"

            if prefix not in container_routers:
                container_routers[prefix] = APIRouter(prefix=prefix)
            container_router = container_routers[prefix]

            module_path = f"app.plugin.{'.'.join(path_parts[:-1])}.controller"
            try:
                module = importlib.import_module(module_path)
                registered_here = 0
                for attr_name in dir(module):
                    attr_value = getattr(module, attr_name, None)
                    if isinstance(attr_value, APIRouter):
                        router_id = id(attr_value)
                        if router_id not in seen_router_ids:
                            seen_router_ids.add(router_id)
                            container_router.include_router(attr_value)
                            registered_here += 1

                if registered_here == 0:
                    logger.warning(
                        f"⚠️ 模块已加载但未注册任何路由: {module_path}\n"
                        f"   文件中未找到顶层 APIRouter 实例",
                    )

            except Exception as e:
                hint = _import_failure_hint(e)
                logger.error(f"❌ 处理模块失败: {module_path}\n   {hint}\n   异常: {e!s}")
                failed.append(module_path)

        if failed:
            raise RuntimeError(
                f"动态路由发现失败，{len(failed)} 个插件模块无法导入，已中止启动：\n   " + "\n   ".join(failed)
            )

        for prefix, container_router in sorted(container_routers.items()):
            route_count = len(container_router.routes)
            root_router.include_router(container_router)
            if route_count == 0:
                logger.warning(f"⚠️ 容器前缀 {prefix} 下未挂载任何子路由")
            logger.info(f"✅ 动态注册路由: {prefix} (子路由数: {route_count})")

        self._cache = root_router
        return root_router


def check_route_conflicts(app: FastAPI) -> None:
    """启动期检测路由冲突：同一路径被注册两次时，先注册的会静默屏蔽后注册的。

    FastAPI 按注册顺序首次匹配，冲突不会报错，只会让部分接口永远不可达——
    通常来自插件自带 prefix 与内置模块撞车，或同一 router 被重复挂载。
    """
    seen: dict[tuple[str, str], str] = {}
    conflicts: list[str] = []
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        if not methods or not path:
            continue
        # 参数名不参与匹配语义，/user/{id} 与 /user/{uid} 属于冲突
        normalized = _PATH_PARAM_RE.sub("{}", path)
        for method in sorted(methods):
            key = (method, normalized)
            endpoint = getattr(route, "name", None) or str(path)
            if key in seen:
                conflicts.append(f"{method} {path}（{endpoint}）已被 {seen[key]} 占用")
            else:
                seen[key] = endpoint

    if conflicts:
        raise RuntimeError(
            f"检测到 {len(conflicts)} 处路由冲突，已中止启动（后注册者将永远不可达）：\n   "
            + "\n   ".join(conflicts)
        )


# 模块级单例
dynamic_router = DynamicRouterRegistry()


def _import_failure_hint(exc: BaseException) -> str:
    """根据异常类型给出简短排查提示。"""
    if isinstance(exc, ModuleNotFoundError):
        missing = getattr(exc, "name", None) or str(exc)
        return (
            f"无法解析模块（ModuleNotFoundError: {missing}）。"
            "常见原因："
            "① 从 app.plugin 到 controller 的某级目录缺少 __init__.py;"
            "② 目录名不是合法 Python 标识符；"
            "③ 磁盘路径与 import 路径不一致。"
        )
    if isinstance(exc, ImportError):
        return "导入失败（ImportError），常见原因：循环导入、依赖未安装、或相对导入路径错误。"
    if isinstance(exc, SyntaxError):
        return f"controller.py 存在语法错误：{exc.msg}（约第 {exc.lineno} 行）。"
    if isinstance(exc, PermissionError):
        return (
            "权限错误（PermissionError）。多见于受限环境：import 链上某模块初始化时调用了被禁止的系统能力。"
            "在完整操作系统下重试；若仍失败再结合堆栈排查。"
        )
    return f"未分类异常（{type(exc).__name__}）。请查看下方堆栈排查。"
