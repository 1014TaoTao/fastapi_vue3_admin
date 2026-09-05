import re
from datetime import datetime
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template

from app.common.constant import GenConstant
from app.config.path_conf import TEMPLATE_DIR
from app.config.setting import settings
from app.utils.common_util import CamelCaseUtil, SnakeCaseUtil, compute_menu_route_first_segment
from app.utils.string_util import StringUtil

from .gen_util import GenUtils
from .schema import (
    GenTableColumnOutSchema,
    GenTableOutSchema,
)


class Jinja2TemplateUtil:
    """模板处理工具类
    """

    @classmethod
    def normalize_db_column_type_for_mapping(cls, column_type: str | None) -> str:
        """与 ``GenUtils.get_db_type`` 一致地去掉 COLLATE / UNSIGNED，便于与 ``DB_TO_SQLALCHEMY`` 键匹配。

        参数:
        - column_type (str | None): 原始列类型字符串。

        返回:
        - str: 规范化后的类型片段；空输入返回空字符串。
        """
        ct = (column_type or "").strip()
        if not ct:
            return ""
        collate_pattern = re.compile(r"\s+COLLATE\s+", re.IGNORECASE)
        if collate_pattern.search(ct):
            ct = collate_pattern.split(ct)[0].strip()
        unsigned_pattern = re.compile(r"\s+UNSIGNED", re.IGNORECASE)
        if unsigned_pattern.search(ct):
            ct = unsigned_pattern.sub("", ct).strip()
        return ct

    # 项目路径
    FRONTEND_PROJECT_PATH = "frontend/web"
    BACKEND_PROJECT_PATH = "backend"

    # 环境对象
    _env = None

    @classmethod
    def get_env(cls):
        """获取模板环境对象。

        参数:
        - 无

        返回:
        - Environment: Jinja2 环境对象。
        """
        try:
            if cls._env is None:
                cls._env = Environment(
                    loader=FileSystemLoader(TEMPLATE_DIR),
                    autoescape=False,  # 自动转义HTML
                    trim_blocks=True,  # 删除多余的空行
                    lstrip_blocks=True,  # 删除行首空格
                    keep_trailing_newline=True,  # 保留行尾换行符
                    enable_async=True,  # 开启异步支持
                )
                cls._env.filters.update(
                    {
                        "camel_to_snake": SnakeCaseUtil.camel_to_snake,
                        "snake_to_camel": CamelCaseUtil.snake_to_camel,
                        "get_sqlalchemy_type": cls.get_sqlalchemy_type,
                        "python_to_ts_type": cls.python_type_to_ts_type,
                    },
                )
            return cls._env
        except Exception as e:
            raise RuntimeError(f"初始化Jinja2模板引擎失败: {e}")

    @classmethod
    def get_template(cls, template_path: str) -> Template:
        """获取模板。

        参数:
        - template_path (str): 模板路径。

        返回:
        - Template: Jinja2 模板对象。

        异常:
        - TemplateNotFound: 模板未找到时抛出。
        """
        return cls.get_env().get_template(template_path)

    @classmethod
    def business_name_to_slug(cls, business_name: str | None) -> str:
        """业务路径可含斜杠（如 ``demo/subdir``）用于目录与路由前缀；
        Python 函数/方法名仅使用最后一段并规范为合法 snake_case 片段。

        参数:
        - business_name (str | None): 业务路径或名称。

        返回:
        - str: 用于 Python 标识的 slug，默认 entity。
        """
        s = (business_name or "").strip().strip("/")
        if not s:
            return "entity"
        if "/" in s:
            s = s.split("/")[-1]
        s = re.sub(r"[^a-zA-Z0-9_]", "_", s)
        if not s:
            return "entity"
        if s[0].isdigit():
            s = "_" + s
        return s

    @classmethod
    def business_name_to_path(cls, business_name: str | None) -> str:
        """把 business_name 规范为可用于目录/路由的多段路径（保留 `/`）。

        约定：`business_name` 允许 `a/b/c` 表示多级菜单目录。
        - 目录/路由：使用完整多段
        - 文件名/route_name：使用最后一段 slug（见 `business_name_to_slug`）

        参数:
        - business_name (str | None): 业务路径或名称。

        返回:
        - str: 多段路径字符串（小写 slug），默认 entity。
        """
        s = (business_name or "").strip().strip("/")
        if not s:
            return "entity"
        # 每段都做一次轻度规范（与 schema 的 slug 规则一致：a-z0-9_）
        segs = []
        for raw in [p for p in s.split("/") if p]:
            seg = re.sub(r"[^a-zA-Z0-9_]", "_", raw).lower()
            seg = re.sub(r"_+", "_", seg).strip("_") or "entity"
            if seg[0].isdigit():
                seg = "_" + seg
            segs.append(seg)
        return "/".join(segs) if segs else "entity"

    @classmethod
    def prepare_context(cls, gen_table: GenTableOutSchema) -> dict[str, Any]:
        """准备模板变量。

        参数:
        - gen_table (GenTableOutSchema): 生成表的配置信息。

        返回:
        - Dict[str, Any]: 模板上下文字典。
        """
        # 处理options为None的情况
        # if not gen_table.options:
        #     raise ValueError('请先完善生成配置信息')
        class_name = gen_table.class_name or ""
        package_name = (gen_table.package_name or "").strip()
        module_name = (gen_table.module_name or "").strip()
        business_name = (gen_table.business_name or "").strip()
        function_name = gen_table.function_name or ""

        # 生成规则（对齐 module_example/demo）：
        # - 分系统根：package_name = module_xxx
        # - 目录固定为：module_xxx / module_name（不再额外使用业务名作为目录层级）
        # - 权限前缀固定为：module_xxx:module_name（操作在模板里再拼 :query/:create...）
        business_path = cls.business_name_to_path(business_name)
        business_name_slug = cls.business_name_to_slug(business_name)
        permission_prefix = ":".join([s for s in [package_name, module_name] if s])
        api_route_prefix = cls.get_api_route_prefix(package_name)

        _cols = gen_table.columns or []
        table_column_names = frozenset(c.column_name for c in _cols if getattr(c, "column_name", None))
        has_dict_column = any(getattr(c, "dict_type", None) for c in _cols)
        has_image_column = any(getattr(c, "html_type", None) == "imageUpload" for c in _cols)

        sub_class_name = ""
        sub_model_class_name = ""
        sub_rel_list_name = ""
        parent_rel_name = ""
        if gen_table.sub and gen_table.sub_table:
            st = gen_table.sub_table
            scn = (st.class_name or GenUtils.convert_class_name(gen_table.sub_table_name or "")).strip()
            sub_class_name = scn
            sub_model_class_name = f"{scn}Model"
            sub_rel_list_name = f"{SnakeCaseUtil.camel_to_snake(scn)}_list"
            parent_rel_name = SnakeCaseUtil.camel_to_snake(gen_table.class_name or "")

        context = {
            "table_name": gen_table.table_name or "",
            "table_comment": gen_table.table_comment or "",
            "function_name": function_name if StringUtil.is_not_empty(function_name) else "【请填写功能名称】",
            "class_name": class_name,
            "module_name": module_name,
            "business_name": business_name,
            "business_path": business_path,
            "business_file": business_name_slug,
            "business_name_slug": business_name_slug,
            "base_package": cls.get_package_prefix(package_name),
            "package_name": package_name,
            "menu_route_first_segment": cls.get_menu_route_first_segment(gen_table),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pk_column": gen_table.pk_column,
            "model_import_list": cls.get_model_import_list(gen_table),
            "schema_import_list": cls.get_schema_import_list(gen_table),
            "permission_prefix": permission_prefix,
            "api_route_prefix": api_route_prefix,
            "columns": gen_table.columns or [],
            "table_column_names": table_column_names,
            "table": gen_table,
            "dicts": cls.get_dicts(gen_table),
            "db_type": settings.DATABASE_TYPE,
            "column_not_add_show": GenConstant.COLUMNNAME_NOT_ADD_SHOW,
            "column_not_edit_show": GenConstant.COLUMNNAME_NOT_EDIT_SHOW,
            "parent_menu_id": int(gen_table.parent_menu_id) if gen_table.parent_menu_id else None,
            "is_sub_entity": False,
            "sub_class_name": sub_class_name,
            "sub_model_class_name": sub_model_class_name,
            "sub_module_name": (gen_table.sub_table.module_name if gen_table.sub and gen_table.sub_table else ""),
            "sub_rel_list_name": sub_rel_list_name,
            "parent_rel_name": parent_rel_name,
            "parent_list_rel_name": "",
            "parent_table_name": "",
            "parent_model_class_name": "",
            # 数据表实际主键列名（用于生成前端行键等；ModelMixin 仍默认带 id 字段）
            "pk_column_name": (gen_table.pk_column.column_name if gen_table.pk_column else None) or "id",
            "parent_pk_column_name": (gen_table.pk_column.column_name if gen_table.pk_column else None) or "id",
            "sub_table_fk_name": "",
            "has_dict_column": has_dict_column,
            "has_image_column": has_image_column,
        }

        return context

    @classmethod
    def get_menu_route_first_segment(cls, gen_table: GenTableOutSchema) -> str:
        """前端页面路由首段（与写入菜单 ``route_path`` 第一段一致）：始终为 ``module_xxx``。"""
        pid = int(gen_table.parent_menu_id) if gen_table.parent_menu_id is not None else None
        return compute_menu_route_first_segment(
            pid,
            gen_table.package_name or "",
            gen_table.module_name,
        )

    @classmethod
    def prepare_sub_render_context(cls, parent: GenTableOutSchema, sub: GenTableOutSchema) -> dict[str, Any]:
        """子表业务代码渲染上下文（与主表同模块、独立业务目录）。

        参数:
        - parent (GenTableOutSchema): 主表配置。
        - sub (GenTableOutSchema): 子表配置。

        返回:
        - dict[str, Any]: 子表模板上下文字典。
        """
        ctx = cls.prepare_context(sub)
        scn = (sub.class_name or GenUtils.convert_class_name(sub.table_name or "")).strip()
        ctx["is_sub_entity"] = True
        ctx["parent_class_name"] = parent.class_name or ""
        ctx["parent_model_class_name"] = f"{parent.class_name}Model"
        ctx["parent_table_name"] = parent.table_name or ""
        ctx["parent_pk_column_name"] = (parent.pk_column.column_name if parent.pk_column else None) or "id"
        ctx["parent_rel_name"] = SnakeCaseUtil.camel_to_snake(parent.class_name or "parent")
        ctx["parent_list_rel_name"] = f"{SnakeCaseUtil.camel_to_snake(scn)}_list"
        ctx["sub_table_fk_name"] = (parent.sub_table_fk_name or "").strip()
        ctx["model_import_list"] = cls.get_model_import_list(sub, is_sub_entity=True)
        ctx["schema_import_list"] = cls.get_schema_import_list(sub)
        return ctx

    @classmethod
    def get_template_list(cls):
        """获取主表模板列表。

        参数:
        - 无
        返回:
        - List[str]: 模板路径列表。
        """
        templates = [
            "python/controller.py.jinja2",
            "python/service.py.jinja2",
            "python/crud.py.jinja2",
            "python/schema.py.jinja2",
            "python/model.py.jinja2",
            "python/__init__.py.jinja2",
            "ts/api.ts.jinja2",
            "vue/index.vue.jinja2",
        ]
        return templates

    @classmethod
    def get_sub_table_template_list(cls):
        """获取子表模板列表（仅 model / schema / __init__，不含 controller/service/crud/vue/api）。

        参数:
        - 无

        返回:
        - List[str]: 子表模板路径列表。
        """
        return [
            "python/model.py.jinja2",
            "python/schema.py.jinja2",
            "python/__init__.py.jinja2",
        ]

    @classmethod
    def get_file_name(cls, template: str, gen_table: GenTableOutSchema):
        """根据模板生成文件名。

        参数:
        - template (str): 模板路径字符串。
        - gen_table (GenTableOutSchema): 生成表的配置信息。

        返回:
        - str: 模板生成的文件名。

        异常:
        - ValueError: 当无法生成有效文件名时抛出。
        """
        package_name = (gen_table.package_name or "").strip()
        module_name = (gen_table.module_name or "").strip()

        if not package_name:
            raise ValueError(f"无法为模板 {template} 生成文件名：包名未设置")
        if not module_name:
            raise ValueError(f"无法为模板 {template} 生成文件名：模块名未设置")

        # 目录固定为：module_xxx/{module_name}
        backend_base = f"{cls.BACKEND_PROJECT_PATH}/app/plugin/{package_name}"
        frontend_view_base = f"{cls.FRONTEND_PROJECT_PATH}/src/views/{package_name}"
        frontend_api_base = f"{cls.FRONTEND_PROJECT_PATH}/src/api/{package_name}"

        backend_dir = f"{backend_base}/{module_name}"
        view_dir = f"{frontend_view_base}/{module_name}"
        api_path = f"{frontend_api_base}/{module_name}.ts"

        template_mapping = {
            "controller.py.jinja2": f"{backend_dir}/controller.py",
            "service.py.jinja2": f"{backend_dir}/service.py",
            "crud.py.jinja2": f"{backend_dir}/crud.py",
            "schema.py.jinja2": f"{backend_dir}/schema.py",
            "model.py.jinja2": f"{backend_dir}/model.py",
            "__init__.py.jinja2": f"{backend_dir}/__init__.py",
            "api.ts.jinja2": api_path,
            "index.vue.jinja2": f"{view_dir}/index.vue",
        }

        # 查找匹配的模板路径
        for key, path in template_mapping.items():
            if key in template:
                return path

        # 遍历完所有映射都没找到匹配项，才抛出异常
        raise ValueError(f"未找到模板 '{template}' 的路径映射")

    @classmethod
    def get_package_prefix(cls, package_name: str) -> str:
        """获取包前缀。

        参数:
        - package_name (str): 包名。

        返回:
        - str: 包前缀。
        """
        # 修复：当包名中不存在'.'时，直接返回原包名
        return package_name[: package_name.rfind(".")] if "." in package_name else package_name

    @classmethod
    def get_schema_import_list(cls, gen_table: GenTableOutSchema):
        """获取 schema 模板所需的 Python 导入语句集合。

        参数:
        - gen_table (GenTableOutSchema): 生成表配置（含主子表列）。

        返回:
        - set[str]: 导入语句字符串集合。
        """
        columns = gen_table.columns or []
        import_list = set()
        has_datetime_import = False
        has_date_import = False
        has_time_import = False

        for column in columns:
            # 处理datetime类型的导入
            if column.python_type and column.python_type in GenConstant.TYPE_DATE:
                if column.python_type == "datetime":
                    has_datetime_import = True
                elif column.python_type == "date":
                    has_date_import = True
                elif column.python_type == "time":
                    has_time_import = True
            elif column.python_type == GenConstant.TYPE_DECIMAL:
                import_list.add("from decimal import Decimal")

        if gen_table.sub and gen_table.sub_table and gen_table.sub_table.columns:
            sub_columns = gen_table.sub_table.columns or []
            for sub_column in sub_columns:
                # 处理datetime类型的导入
                if sub_column.python_type and sub_column.python_type in GenConstant.TYPE_DATE:
                    if sub_column.python_type == "datetime":
                        has_datetime_import = True
                    elif sub_column.python_type == "date":
                        has_date_import = True
                    elif sub_column.python_type == "time":
                        has_time_import = True
                elif sub_column.python_type == GenConstant.TYPE_DECIMAL:
                    import_list.add("from decimal import Decimal")

        # 添加datetime导入
        if has_datetime_import:
            import_list.add("from datetime import datetime")
        if has_date_import:
            import_list.add("from datetime import date")
        if has_time_import:
            import_list.add("from datetime import time")

        return import_list

    @classmethod
    def get_model_import_list(cls, gen_table: GenTableOutSchema, *, is_sub_entity: bool = False) -> list[str]:
        """获取 model 模板所需的 Python 导入语句列表（含合并后的 sqlalchemy 导入）。

        参数:
        - gen_table (GenTableOutSchema): 生成表配置。
        - is_sub_entity (bool): 是否为子表独立生成（含外键与 relationship）。

        返回:
        - list[str]: 导入语句列表。
        """
        columns = gen_table.columns or []
        import_list = set()
        has_datetime_import = False
        has_date_import = False
        has_time_import = False

        # 基类 ModelMixin/UserMixin 已定义的列，无需导入 SQLAlchemy 类型
        _BASE_MODEL_COLUMNS = {
            "id",
            "uuid",
            "created_time",
            "updated_time",
            "created_id",
            "updated_id",
            "is_deleted",
            "deleted_time",
            "deleted_id",
        }

        for column in columns:
            if column.column_name in _BASE_MODEL_COLUMNS:
                continue
            if column.column_type:
                data_type = cls.get_db_type(column.column_type)
                if data_type in GenConstant.COLUMNTYPE_GEOMETRY:
                    import_list.add("from geoalchemy2 import Geometry")
                import_list.add(f"from sqlalchemy import {StringUtil.get_mapping_value_by_key_ignore_case(GenConstant.DB_TO_SQLALCHEMY, data_type)}")
            # 处理datetime类型的导入
            if column.python_type and column.python_type in GenConstant.TYPE_DATE:
                if column.python_type == "datetime":
                    has_datetime_import = True
                elif column.python_type == "date":
                    has_date_import = True
                elif column.python_type == "time":
                    has_time_import = True
            # 处理Decimal类型的导入
            elif column.python_type == GenConstant.TYPE_DECIMAL:
                import_list.add("from decimal import Decimal")
        if gen_table.sub or is_sub_entity:
            import_list.add("from sqlalchemy import ForeignKey")
            if gen_table.sub and not is_sub_entity and gen_table.sub_table and gen_table.sub_table.columns:
                sub_columns = gen_table.sub_table.columns or []
                for sub_column in sub_columns:
                    if sub_column.column_type:
                        data_type = cls.get_db_type(sub_column.column_type)
                        import_list.add(f"from sqlalchemy import {StringUtil.get_mapping_value_by_key_ignore_case(GenConstant.DB_TO_SQLALCHEMY, data_type)}")
                    # 处理datetime类型的导入
                    if sub_column.python_type and sub_column.python_type in GenConstant.TYPE_DATE:
                        if sub_column.python_type == "datetime":
                            has_datetime_import = True
                        elif sub_column.python_type == "date":
                            has_date_import = True
                        elif sub_column.python_type == "time":
                            has_time_import = True
                    # 处理Decimal类型的导入
                    elif sub_column.python_type == GenConstant.TYPE_DECIMAL:
                        import_list.add("from decimal import Decimal")

        # 添加datetime导入
        if has_datetime_import:
            import_list.add("from datetime import datetime")
        if has_date_import:
            import_list.add("from datetime import date")
        if has_time_import:
            import_list.add("from datetime import time")

        merged = cls.merge_same_imports(list(import_list), "from sqlalchemy import")
        if gen_table.sub or is_sub_entity:
            merged.append("from sqlalchemy.orm import relationship")
        return merged

    @classmethod
    def get_db_type(cls, column_type: str) -> str:
        """获取数据库字段类型。

        参数:
        - column_type (str): 字段类型字符串。

        返回:
        - str: 数据库类型（去除长度等修饰）。
        """
        # 移除 COLLATE 子句（处理带引号和不带引号的情况，不区分大小写）
        collate_pattern = re.compile(r"\s+COLLATE\s+", re.IGNORECASE)
        if collate_pattern.search(column_type):
            column_type = collate_pattern.split(column_type)[0].strip()

        # 移除 UNSIGNED 标记（不区分大小写）
        unsigned_pattern = re.compile(r"\s+UNSIGNED", re.IGNORECASE)
        if unsigned_pattern.search(column_type):
            column_type = unsigned_pattern.sub("", column_type).strip()

        # 处理PostgreSQL数组类型（如 integer[], text[]）
        if "[]" in column_type:
            return "array"

        # 提取基本类型
        if "(" in column_type:
            return column_type.split("(")[0]
        return column_type

    @classmethod
    def merge_same_imports(cls, imports: list[str], import_start: str) -> list[str]:
        """合并相同的导入语句。

        参数:
        - imports (list[str]): 导入语句列表。
        - import_start (str): 导入语句的起始字符串。

        返回:
        - list[str]: 合并后的导入语句列表。
        """
        merged_imports = []
        imports_ = []
        for import_stmt in imports:
            if import_stmt.startswith(import_start):
                imported_items = import_stmt.split("import")[1].strip()
                imports_.extend(imported_items.split(", "))
            else:
                merged_imports.append(import_stmt)

        if imports_:
            # 去重并过滤空字符串，然后用逗号连接
            unique_imports = [item for item in imports_ if item]
            if len(unique_imports) > 0:
                merged_datetime_import = f"{import_start} {', '.join(unique_imports)}"
                merged_imports.append(merged_datetime_import)

        return merged_imports

    @classmethod
    def get_dicts(cls, gen_table: GenTableOutSchema):
        """获取字典列表。

        参数:
        - gen_table (GenTableOutSchema): 生成表的配置信息。

        返回:
        - str: 以逗号分隔的字典类型字符串。
        """
        columns = gen_table.columns or []
        dicts = set()
        cls.add_dicts(dicts, columns)
        # 处理sub_table为None的情况
        if gen_table.sub_table is not None:
            # 处理sub_table.columns为None的情况
            sub_columns = gen_table.sub_table.columns or []
            cls.add_dicts(dicts, sub_columns)
        return ", ".join(dicts)

    @classmethod
    def add_dicts(cls, dicts: set[str], columns: list[GenTableColumnOutSchema]) -> None:
        """添加字典类型到集合。

        参数:
        - dicts (set[str]): 字典类型集合。
        - columns (list[GenTableColumnOutSchema]): 字段列表。

        返回:
        - set[str]: 更新后的字典类型集合。
        """
        for column in columns:
            super_column = column.super_column if column.super_column is not None else "0"
            dict_type = column.dict_type or ""
            html_type = column.html_type or ""

            if (
                not super_column
                and StringUtil.is_not_empty(dict_type)
                and StringUtil.equals_any_ignore_case(
                    html_type,
                    [
                        GenConstant.HTML_SELECT,
                        GenConstant.HTML_RADIO,
                        GenConstant.HTML_CHECKBOX,
                    ],
                )
            ):
                dicts.add(f"'{dict_type}'")

    @classmethod
    def get_permission_prefix(cls, module_name: str | None, business_name: str | None) -> str:
        """获取权限前缀。

        参数:
        - module_name (str | None): 模块名。
        - business_name (str | None): 业务名。

        返回:
        - str: 权限前缀字符串。
        """
        mn = (module_name or "").strip()
        bn = (business_name or "").strip().replace("/", ":")
        if not bn:
            return mn
        return f"{mn}:{bn}"

    @classmethod
    def python_type_to_ts_type(cls, python_type: str | None) -> str:
        """将列上的 Python 类型（`get_db_type` + `DB_TO_PYTHON` 映射结果）转为前端 TS 类型片段。

        与 JSON 序列化习惯一致：Decimal、日期时间多为字符串；dict/list 用宽松类型。

        参数:
        - python_type (str | None): Python 类型名。

        返回:
        - str: 前端 TypeScript 类型片段。
        """
        if not python_type or not str(python_type).strip():
            return "string"
        p = str(python_type).strip()
        mapping: dict[str, str] = {
            "int": "number",
            "float": "number",
            "bool": "boolean",
            "Decimal": "string",
            "date": "string",
            "time": "string",
            "datetime": "string",
            "timedelta": "string",
            "dict": "Record<string, unknown>",
            "list": "unknown[]",
            "bytes": "string",
            "str": "string",
        }
        return mapping.get(p, "string")

    @classmethod
    def get_api_route_prefix(cls, module_name: str | None) -> str:
        """获取前端 API 路径首段，与 `discover` 中插件路由前缀一致（`module_xxx` → `xxx`）。

        参数:
        - module_name (str | None): 模块名，如 ``module_example``。

        返回:
        - str: 路由前缀，如 ``example``。
        """
        if not module_name:
            return ""
        if module_name.startswith("module_"):
            return module_name[7:]
        return module_name

    @classmethod
    def get_sqlalchemy_type(cls, column: Any) -> str:
        """获取 SQLAlchemy 类型。

        参数:
        - column (Any): 列对象或列类型字符串。

        返回:
        - str: SQLAlchemy 类型字符串。
        """
        # 获取column_type和column_length
        column_type = column
        column_length = None

        # 检查是否是对象
        if hasattr(column, "column_type"):
            column_type = column.column_type or ""
            column_length = column.column_length or None

        column_type = cls.normalize_db_column_type_for_mapping(column_type)

        # MySQL：仅 tinyint(1) 映射为 Boolean；其余 tinyint 走 SmallInteger（见 GenConstant.DB_TO_SQLALCHEMY）
        ct_norm = (column_type or "").strip()
        if settings.DATABASE_TYPE != "postgres" and ct_norm:
            ct_lower = ct_norm.lower()
            if ct_lower.startswith("tinyint(1)"):
                return "Boolean"

        # 首先尝试匹配完整类型（包括括号）
        sqlalchemy_type = StringUtil.get_mapping_value_by_key_ignore_case(GenConstant.DB_TO_SQLALCHEMY, column_type)

        # 特殊处理PostgreSQL类型
        if settings.DATABASE_TYPE == "postgres":
            if column_type.upper() == "BOOLEAN":
                return "Boolean"
            if column_type.upper() == "REAL" or column_type.upper() == "DOUBLE PRECISION":
                return "Float"
            if column_type.upper() == "TIMESTAMP":
                return "DateTime"
            if column_type.upper() == "JSONB":
                return "JSONB"
            if column_type.upper() == "UUID":
                return "Uuid"
            if column_type.upper() == "BYTEA":
                return "LargeBinary"

        # get_mapping_value_by_key_ignore_case 未命中时返回 ""，须与 None 同样视为未匹配
        if not sqlalchemy_type and "(" in column_type:
            # 如果没有匹配到，再尝试剥离括号
            column_type_list = column_type.split("(")
            col_type = column_type_list[0]
            # 将 'character' 映射为 'char' 以匹配常量定义
            if col_type.lower() == "character":
                col_type = "char"
            sqlalchemy_type = StringUtil.get_mapping_value_by_key_ignore_case(GenConstant.DB_TO_SQLALCHEMY, col_type)
            # 如果是字符串类型且包含括号参数，保持原参数
            if sqlalchemy_type in ["String", "CHAR"] or sqlalchemy_type in ["Numeric", "DECIMAL"]:
                sqlalchemy_type += "(" + column_type_list[1]
        elif not sqlalchemy_type:
            # 处理没有括号的类型
            col_type = column_type
            # 将 'character' 映射为 'char' 以匹配常量定义
            if col_type.lower() == "character":
                col_type = "char"
            sqlalchemy_type = StringUtil.get_mapping_value_by_key_ignore_case(GenConstant.DB_TO_SQLALCHEMY, col_type)
            # 如果是字符串类型且没有指定长度，使用column_length或默认255
            if sqlalchemy_type in ["String", "CHAR"]:
                length = column_length if column_length and column_length.isdigit() else "255"
                sqlalchemy_type += f"({length})"
        # 对于已经匹配到的类型，如果是字符串类型且column有长度信息，添加长度
        elif sqlalchemy_type in ["String", "CHAR"] and "(" not in sqlalchemy_type:
            # 检查column_length是否有效
            length = column_length if column_length and column_length.isdigit() else "255"
            sqlalchemy_type += f"({length})"

        # 如果没有找到匹配的类型，使用String(column_length)或String(255)作为默认类型
        if not sqlalchemy_type:
            length = column_length if column_length and column_length.isdigit() else "255"
            sqlalchemy_type = f"String({length})"
        return sqlalchemy_type
