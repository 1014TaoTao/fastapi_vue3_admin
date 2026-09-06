import re

from app.common.constant import GenConstant
from app.config.setting import settings
from app.utils.string_util import StringUtil

from .schema import (
    GenTableColumnSchema,
    GenTableOutSchema,
    GenTableSchema,
)


class GenUtils:
    """代码生成器工具类"""

    @classmethod
    def init_table(cls, gen_table: GenTableSchema) -> None:
        """初始化表信息

        参数:
        - gen_table (GenTableSchema): 业务表对象。

        返回:
        - None
        """
        gen_table.class_name = cls.convert_class_name(gen_table.table_name or "")
        # 导入时给出"可用默认值"，减少用户点开后看到空表单：
        # - module_name：从表名推导（去掉 gen_/tb_ 前缀）
        # - package_name：默认 module_{module_name}（仍可在前端改）
        if gen_table.business_name is None:
            gen_table.business_name = gen_table.table_name
        if gen_table.module_name is None or not str(gen_table.module_name).strip():
            tn = (gen_table.table_name or "").strip().lower()
            if tn.startswith("gen_"):
                tn = tn[4:]
            elif tn.startswith("tb_"):
                tn = tn[3:]
            tn = re.sub(r"[^a-z0-9_]+", "_", tn)
            tn = re.sub(r"_+", "_", tn).strip("_") or "module"
            gen_table.module_name = tn

        if gen_table.package_name is None or not str(gen_table.package_name).strip():
            mn = (gen_table.module_name or "").strip()
            if mn:
                gen_table.package_name = mn if mn.startswith("module_") else f"module_{mn}"

        fn = re.sub(r"(?:表|测试)", "", gen_table.table_comment or "")
        fn = (fn or "").strip()
        if not fn:
            # 表注释为空时：用表名兜底，至少不为空
            fn = (gen_table.table_name or "").strip()
        gen_table.function_name = fn

    @classmethod
    def init_column_field(cls, column: GenTableColumnSchema, table: GenTableOutSchema) -> None:
        """初始化列属性字段

        参数:
        - column (GenTableColumnSchema): 业务表字段对象。
        - table (GenTableOutSchema): 业务表对象。

        返回:
        - None
        """
        data_type = cls.get_db_type(column.column_type or "")
        column_name = column.column_name or ""
        if table.id is None:
            raise ValueError("业务表ID不能为空")
        column.table_id = table.id
        column.python_field = StringUtil.to_lower_camel_case(column_name)

        # 特殊处理几何类型，根据数据库类型选择不同的映射
        if data_type in [
            "point",
            "line",
            "linestring",
            "polygon",
            "multipoint",
            "multilinestring",
            "multipolygon",
            "geometrycollection",
            "geometry",
        ]:
            if settings.DATABASE_TYPE == "mysql":
                column.python_type = "bytes"
            elif settings.DATABASE_TYPE == "postgres":
                column.python_type = "list"
        else:
            # 只有当python_type为None时才设置默认类型
            column.python_type = StringUtil.get_mapping_value_by_key_ignore_case(GenConstant.DB_TO_PYTHON, data_type)

        if column.column_length is None:
            column.column_length = ""

        if column.column_default is None:
            column.column_default = ""

        if column.html_type is None:
            # 先按"字段名语义"推断（优先级高于通用字符串规则）
            lower_name = column_name.lower()
            if lower_name.endswith("status"):
                column.html_type = GenConstant.HTML_RADIO
            elif lower_name.endswith("type") or lower_name.endswith("sex"):
                column.html_type = GenConstant.HTML_SELECT
            elif lower_name.endswith("image"):
                column.html_type = GenConstant.HTML_IMAGE_UPLOAD
            elif lower_name.endswith("file"):
                column.html_type = GenConstant.HTML_FILE_UPLOAD
            elif lower_name.endswith("content"):
                column.html_type = GenConstant.HTML_EDITOR
            # 再按"数据类型"推断
            elif cls.arrays_contains(GenConstant.COLUMNTYPE_TIME, data_type):
                column.html_type = GenConstant.HTML_DATETIME
            elif cls.arrays_contains(GenConstant.COLUMNTYPE_NUMBER, data_type):
                column.html_type = GenConstant.HTML_INPUT
            elif cls.arrays_contains(GenConstant.COLUMNTYPE_STR, data_type) or cls.arrays_contains(GenConstant.COLUMNTYPE_TEXT, data_type):
                # 字符串长度超过500设置为文本域
                column_length = cls.get_column_length(column.column_type or "")
                column.html_type = GenConstant.HTML_TEXTAREA if column_length >= 500 or cls.arrays_contains(GenConstant.COLUMNTYPE_TEXT, data_type) else GenConstant.HTML_INPUT
            else:
                column.html_type = GenConstant.HTML_INPUT

        # 默认新增字段：非主键且不在"新增不展示"黑名单中
        # 说明：schema 默认值可能为 True/False；仅当调用方未显式配置时才做推断
        if column.is_insert is None:
            column.is_insert = bool((not column.is_pk) and (not cls.arrays_contains(GenConstant.COLUMNNAME_NOT_ADD_SHOW, column_name)))

        # 默认编辑字段：非主键且不在"不编辑"黑名单中
        if column.is_edit is None:
            column.is_edit = bool((not cls.arrays_contains(GenConstant.COLUMNNAME_NOT_EDIT, column_name)) and (not column.is_pk))

        # 默认列表字段：非主键且不在"不列表显示"黑名单中
        if column.is_list is None:
            column.is_list = bool((not cls.arrays_contains(GenConstant.COLUMNNAME_NOT_LIST, column_name)) and (not column.is_pk))

        # 默认查询字段：非主键且不在"不查询"黑名单中
        if column.is_query is None:
            column.is_query = bool((not cls.arrays_contains(GenConstant.COLUMNNAME_NOT_QUERY, column_name)) and (not column.is_pk))

        # 查询类型：仅当开启查询且 query_type 未显式配置时推断
        if column.is_query:
            if column.query_type is None:
                if column_name.lower().endswith("name") or data_type in ["varchar", "char", "text"]:
                    column.query_type = GenConstant.QUERY_LIKE
                else:
                    column.query_type = GenConstant.QUERY_EQ
        else:
            column.query_type = None

        # 主键强约束：无论默认推断/历史配置如何，主键列不应出现在新增/编辑/列表/查询
        if bool(column.is_pk):
            column.is_insert = False
            column.is_edit = False
            column.is_list = False
            column.is_query = False
            column.query_type = None

    @classmethod
    def arrays_contains(cls, arr: list, target_value: str) -> bool:
        """检查目标值是否在数组中

        注意：从根本上解决问题，现在确保传入的参数都是正确的类型：
        - arr 是列表类型，且在GenConstant中定义
        - target_value 不会是None

        参数:
        - arr: 数组类型
        - target_value: 目标值

        返回:
        - bool: 如果目标值在数组中，返回True；否则返回False
        """
        # 从根本上解决问题，不再需要复杂的防御性检查
        # 因为现在我们确保传入的arr是GenConstant中定义的列表常量
        # 并且target_value在调用前已经被处理过不会是None

        # 移除 COLLATE 子句和 UNSIGNED 标记（不区分大小写）
        target_str = str(target_value)

        # 移除 COLLATE 子句
        collate_pattern = re.compile(r"\s+COLLATE\s+", re.IGNORECASE)
        if collate_pattern.search(target_str):
            target_str = collate_pattern.split(target_str)[0].strip()

        # 移除 UNSIGNED 标记
        unsigned_pattern = re.compile(r"\s+UNSIGNED", re.IGNORECASE)
        if unsigned_pattern.search(target_str):
            target_str = unsigned_pattern.sub("", target_str).strip()

        # 转换为小写进行比较
        target_str = target_str.lower()

        # 对于包含括号的类型（如TINYINT(1)），需要特殊处理
        # 先获取基本类型名称（不含括号）用于比较
        target_base_type = target_str.split("(")[0] if "(" in target_str else target_str

        for item in arr:
            item_str = str(item).lower()
            item_base_type = item_str.split("(")[0] if "(" in item_str else item_str
            if target_base_type == item_base_type:
                return True
        return False

    @classmethod
    def convert_class_name(cls, table_name: str) -> str:
        """表名转换成 Python 类名

        参数:
        - table_name (str): 业务表名。

        返回:
        - str: Python 类名。
        """
        return StringUtil.convert_to_camel_case(table_name)

    @classmethod
    def replace_first(cls, input_string: str, search_list: list[str]) -> str:
        """批量替换前缀

        参数:
        - input_string (str): 需要被替换的字符串。
        - search_list (list[str]): 可替换的字符串列表。

        返回:
        - str: 替换后的字符串。
        """
        for search_string in search_list:
            if input_string.startswith(search_string):
                return input_string.replace(search_string, "", 1)
        return input_string

    @classmethod
    def get_db_type(cls, column_type: str) -> str:
        """获取数据库类型字段

        参数:
        - column_type (str): 字段类型。

        返回:
        - str: 数据库类型。
        """
        # 移除 COLLATE 子句（处理带引号和不带引号的情况，不区分大小写）
        collate_pattern = re.compile(r"\s+COLLATE\s+", re.IGNORECASE)
        if collate_pattern.search(column_type):
            column_type = collate_pattern.split(column_type)[0].strip()

        # 移除 UNSIGNED 标记（不区分大小写）
        unsigned_pattern = re.compile(r"\s+UNSIGNED", re.IGNORECASE)
        if unsigned_pattern.search(column_type):
            column_type = unsigned_pattern.sub("", column_type).strip()

        # 特殊处理tinyint(1)，映射为boolean
        if column_type.lower().startswith("tinyint(1)"):
            return "boolean"

        # 处理PostgreSQL数组类型（如 integer[], text[] 或 ARRAY[INTEGER]）
        if "[]" in column_type or column_type.upper().startswith("ARRAY["):
            return "array"

        # 提取基本类型：
        # - 去掉括号参数：varchar(64) -> varchar
        # - 去掉空格后的修饰：timestamp without time zone -> timestamp
        # - 统一小写
        base = column_type.split("(", 1)[0].strip()
        if not base:
            return ""
        base = base.split(None, 1)[0].strip()
        return base.lower()

    @classmethod
    def get_column_length(cls, column_type: str) -> int:
        """获取字段长度

        参数:
        - column_type (str): 字段类型，例如 'varchar(255)' 或 'decimal(10,2)'

        返回:
        - int: 字段长度（优先取第一个长度值，无法解析时返回0）。
        """
        if not column_type:
            return 0
        if "(" not in column_type or ")" not in column_type:
            return 0

        # 形如 varchar(255) / decimal(10,2) / numeric(20, 0)
        inner = column_type.split("(", 1)[1].split(")", 1)[0].strip()
        if not inner:
            return 0

        first = inner.split(",", 1)[0].strip()
        try:
            return int(first)
        except ValueError:
            return 0

    @classmethod
    def split_column_type(cls, column_type: str) -> list[str]:
        """拆分列类型

        参数:
        - column_type (str): 字段类型。

        返回:
        - list[str]: 拆分结果。
        """
        if "(" in column_type and ")" in column_type:
            return column_type.split("(")[1].split(")")[0].split(",")
        return []
