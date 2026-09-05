import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.base_schema import BaseQueryParam, BaseSchema, UserByQueryParam, UserBySchema


class GenDBTableSchema(BaseModel):
    """数据库中的表信息（跨方言统一结构）。
    - 供“导入表结构”与“同步结构”环节使用。
    """

    model_config = ConfigDict(from_attributes=True)

    database_name: str | None = Field(default=None, description="数据库名称")
    table_name: str | None = Field(default=None, description="表名称")
    table_type: str | None = Field(default=None, description="表类型")
    table_comment: str | None = Field(default=None, description="表描述")


class GenCreateTableSqlBody(BaseModel):
    """从代码生成页提交的建表 SQL（JSON 对象，便于与前端 axios 一致）。"""

    sql: str = Field(..., description="CREATE TABLE 等 DDL，可多条语句")


class GenTableColumnSchema(BaseModel):
    """代码生成业务表字段创建模型（原始字段+生成配置）。
    - 从根本上解决问题：所有字段都设置了合理的默认值，避免None值问题
    """

    model_config = ConfigDict(from_attributes=True)

    table_id: int = Field(default=0, description="归属表编号")
    column_name: str = Field(default="", description="列名称")
    column_comment: str | None = Field(default="", description="列描述")
    column_type: str = Field(default="varchar(255)", description="列类型")
    column_length: str | None = Field(default="", description="列长度")
    column_default: str | None = Field(default="", description="列默认值")
    is_pk: bool = Field(default=False, description="是否主键（True是 False否）")
    is_increment: bool = Field(default=False, description="是否自增（True是 False否）")
    is_nullable: bool = Field(default=True, description="是否允许为空（True是 False否）")
    is_unique: bool = Field(default=False, description="是否唯一（True是 False否）")
    python_type: str = Field(default="str", description="python类型")
    python_field: str = Field(default="", description="python字段名")
    # 这些开关若默认 True，会导致导入/同步时无法触发自动推断（如主键 id 误入新增/编辑/列表/查询）
    # 约定：None 表示“未配置”，由 GenUtils.init_column_field 推断填充
    is_insert: bool | None = Field(default=None, description="是否为新增字段（True是 False否）")
    is_edit: bool | None = Field(default=None, description="是否编辑字段（True是 False否）")
    is_list: bool | None = Field(default=None, description="是否列表字段（True是 False否）")
    is_query: bool | None = Field(default=None, description="是否查询字段（True是 False否）")
    query_type: str | None = Field(default=None, description="查询方式（等于、不等于、大于、小于、范围）")
    # html_type 若给默认值会导致导入/同步时无法触发自动推断（全部变成 input）
    # 约定：None 表示“未配置”，由 GenUtils.init_column_field 推断填充
    html_type: str | None = Field(
        default=None,
        description="显示类型（文本框、文本域、下拉框、复选框、单选框、日期控件）",
    )
    dict_type: str | None = Field(default="", description="字典类型")
    sort: int = Field(default=0, description="排序")


class GenTableColumnOutSchema(GenTableColumnSchema, BaseSchema):
    """业务表字段输出模型
    """

    model_config = ConfigDict(from_attributes=True)

    super_column: str | None = Field(default="0", description="是否为基类字段（1是 0否）")


class GenTableSchema(BaseModel):
    """代码生成业务表更新模型（扩展聚合字段）。
    - 聚合：`columns`字段包含字段列表；`pk_column`主键字段；子表结构`sub_table`。
    """

    """代码生成业务表基础模型（创建/更新共享字段）。
    - 说明：`params`为前端结构体，后端持久化为`options`的JSON。
    """
    model_config = ConfigDict(from_attributes=True)

    table_name: str = Field(..., description="表名称")
    table_comment: str | None = Field(default=None, description="表描述")
    class_name: str | None = Field(default=None, description="实体类名称")
    package_name: str | None = Field(default=None, description="生成包路径")
    module_name: str | None = Field(default=None, description="生成模块名")
    business_name: str | None = Field(
        default=None,
        description=("功能子目录/路由段；导入时默认表名；同 module_name 下多表须不同。可含斜杠表示嵌套，参考 module_example：demo、demo/subdir、gen_demo。"),
    )
    function_name: str | None = Field(default=None, description="生成功能名")
    sub_table_name: str | None = Field(default=None, description="关联子表的表名")
    sub_table_fk_name: str | None = Field(default=None, description="子表关联的外键名")
    parent_menu_id: int | None = Field(
        default=None,
        description=(
            "写入本地须选目录类型。有值：侧栏 上级/短包名/功能/按钮，页面路由 /包名/业务名。"
            "留空：侧栏 module_包名/功能/按钮，页面路由 /module_包名/业务名（与 plugin 一致）；"
            "后端 HTTP 接口仍为 /短名（module_xxx→/xxx）。"
        ),
    )
    description: str | None = Field(default=None, max_length=255, description="描述")

    columns: list["GenTableColumnOutSchema"] | None = Field(default=None, description="表列信息")

    @staticmethod
    def _normalize_slug_segment(v: str, *, allow_slash: bool = False) -> str:
        """将输入规范成工程约定的路径片段：
        - 小写
        - 只保留 a-z 0-9 _
        - 连续 _ 合并
        - 首字符不能是数字（则前置 _）
        - allow_slash=True 时允许多段 path（每段分别规范）
        """
        raw = (v or "").strip()
        if not raw:
            return ""
        if allow_slash:
            segs = [s for s in raw.strip("/").split("/") if s.strip()]
            norm = [GenTableSchema._normalize_slug_segment(s, allow_slash=False) for s in segs]
            norm = [s for s in norm if s]
            return "/".join(norm)
        s = raw.lower()
        s = re.sub(r"[^a-z0-9_]+", "_", s)
        s = re.sub(r"_+", "_", s).strip("_")
        if not s:
            return ""
        if s[0].isdigit():
            s = "_" + s
        return s

    @field_validator("table_name")
    @classmethod
    def table_name_update(cls, v: str) -> str:
        """校验并规范化表名称。

        参数:
        - v (str): 原始表名。

        返回:
        - str: 去空白后的表名。

        异常:
        - ValueError: 表名为空时抛出。
        """
        if not v:
            raise ValueError("表名称不能为空")
        return v.strip()

    @field_validator(
        "table_comment",
        "class_name",
        "function_name",
        "description",
        mode="before",
    )
    @classmethod
    def strip_optional_text_fields(cls, v: str | None) -> str | None:
        """文本类字段统一去首尾空格；空串视为 None。

        参数:
        - v (str | None): 原始值。

        返回:
        - str | None: 非空字符串或 None。
        """
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("package_name", mode="before")
    @classmethod
    def normalize_package_name(cls, v: str | None) -> str | None:
        """包名规范：必须是 module_xxx 形态（工程约定）。

        参数:
        - v (str | None): 原始包名。

        返回:
        - str | None: 规范化后的包名或 None。
        """
        if v is None:
            return None
        s = cls._normalize_slug_segment(str(v), allow_slash=False)
        if not s:
            return None
        return s if s.startswith("module_") else f"module_{s}"

    @field_validator("module_name", mode="before")
    @classmethod
    def normalize_module_name(cls, v: str | None) -> str | None:
        """模块名规范：不带 module_ 前缀；统一按 slug 规范。

        参数:
        - v (str | None): 原始模块名。

        返回:
        - str | None: 规范化后的模块名或 None。
        """
        if v is None:
            return None
        s = cls._normalize_slug_segment(str(v), allow_slash=False)
        if not s:
            return None
        return s.removeprefix("module_")

    @field_validator("business_name", mode="before")
    @classmethod
    def normalize_business_name(cls, v: str | None) -> str | None:
        """业务名允许多段（如 demo/subdir）；统一按 slug 规范。

        参数:
        - v (str | None): 原始业务名。

        返回:
        - str | None: 规范化后的业务名或 None。
        """
        if v is None:
            return None
        s = cls._normalize_slug_segment(str(v), allow_slash=True)
        return s if s else None

    @field_validator("sub_table_name", "sub_table_fk_name", mode="before")
    @classmethod
    def strip_optional_sub_fields(cls, v: str | None) -> str | None:
        """主子表字段去首尾空格，空串视为未填。

        参数:
        - v (str | None): 原始值。

        返回:
        - str | None: 非空字符串或 None。
        """
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None


class GenTableOutSchema(GenTableSchema, BaseSchema, UserBySchema):
    """业务表输出模型（面向控制器/前端）。"""

    model_config = ConfigDict(from_attributes=True)

    pk_column: GenTableColumnOutSchema | None = Field(default=None, description="主键信息")
    # 子表同样需要携带 columns/pk_column 等输出字段，使用 OutSchema 便于模板与类型检查
    sub_table: "GenTableOutSchema | None" = Field(default=None, description="子表信息")
    sub: bool | None = Field(default=None, description="是否为子表")
    master_sub_hint: str | None = Field(
        default=None,
        description="主子表配置说明或异常提示（仅接口输出，不落库）",
    )


class GenSyncColumnChange(BaseModel):
    """同步差异：单个字段的变化项（用于预览，不落库）。"""

    model_config = ConfigDict(from_attributes=True)

    column_name: str = Field(..., description="列名")
    change_fields: list[str] = Field(default_factory=list, description="变化字段名列表")
    before: dict = Field(default_factory=dict, description="同步前（当前 gen 配置）摘要")
    after: dict = Field(default_factory=dict, description="同步后（来自 DB）摘要")


class GenSyncPreviewSchema(BaseModel):
    """同步数据库前的差异预览（主表 + 可选子表）。"""

    model_config = ConfigDict(from_attributes=True)

    table_name: str = Field(..., description="表名")
    added: list[str] = Field(default_factory=list, description="新增列（DB有、gen无）")
    removed: list[str] = Field(default_factory=list, description="删除列（gen有、DB无）")
    changed: list[GenSyncColumnChange] = Field(default_factory=list, description="变更列（同名但属性变化）")
    unchanged: int = Field(default=0, description="未变化列数（同名且关键属性一致）")

    sub_table_name: str | None = Field(default=None, description="子表表名")
    sub: "GenSyncPreviewSchema | None" = Field(default=None, description="子表差异（若配置了主子表）")


class GenTableQueryParam(BaseQueryParam, UserByQueryParam):
    """代码生成业务表查询参数
    - 支持按`table_name`、`table_comment`进行模糊检索（由CRUD层实现like）。
    - 空值将被忽略，不参与过滤。
    """

    table_name: str | None = Field(None, description="表名称", json_schema_extra={"q": "like"})
    table_comment: str | None = Field(None, description="表注释", json_schema_extra={"q": "like"})
    status: int | None = Field(None, ge=0, le=1, description="状态(0:启动 1:停用)", json_schema_extra={"q": "eq"})


