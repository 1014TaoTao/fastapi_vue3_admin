from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.config.setting import settings
from app.core.base_model import ModelMixin, UserMixin
from app.utils.common_util import SqlalchemyUtil


class GenTableModel(ModelMixin, UserMixin):
    """代码生成表
    """

    __tablename__: str = "gen_table"
    __table_args__: dict[str, str] = {"comment": "代码生成表"}
    
    table_name: Mapped[str] = mapped_column(String(200), nullable=False, default="", index=True, comment="表名称")
    table_comment: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="表描述")
    class_name: Mapped[str] = mapped_column(String(100), nullable=False, default="", comment="实体类名称")
    package_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="生成包路径")
    module_name: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="生成模块名")
    business_name: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="生成业务名")
    function_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="生成功能名")
    sub_table_name: Mapped[str | None] = mapped_column(String(64), nullable=True, server_default=SqlalchemyUtil.get_server_default_null(settings.DATABASE_TYPE), comment="关联子表的表名")
    sub_table_fk_name: Mapped[str | None] = mapped_column(String(64), nullable=True, server_default=SqlalchemyUtil.get_server_default_null(settings.DATABASE_TYPE), comment="子表关联的外键名")
    parent_menu_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="父菜单ID")
    columns: Mapped[list["GenTableColumnModel"]] = relationship(order_by="GenTableColumnModel.sort", back_populates="table", cascade="all, delete-orphan")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:启动 1:停用)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")

    @validates("table_name")
    def validate_table_name(self, key: str, table_name: str) -> str:
        """验证表名非空并去首尾空格。"""
        if not table_name or not table_name.strip():
            raise ValueError("表名称不能为空")
        return table_name.strip()

    @validates("class_name")
    def validate_class_name(self, key: str, class_name: str) -> str:
        """验证实体类名非空并去首尾空格。"""
        if not class_name or not class_name.strip():
            raise ValueError("实体类名称不能为空")
        return class_name.strip()


class GenTableColumnModel(ModelMixin, UserMixin):
    """代码生成表字段"""

    __tablename__: str = "gen_table_column"
    __table_args__: dict[str, str] = {"comment": "代码生成表字段"}
    
    column_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="列名称")
    column_comment: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="列描述")
    column_type: Mapped[str] = mapped_column(String(100), nullable=False, comment="列类型")
    column_length: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="列长度")
    column_default: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="列默认值")
    is_pk: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=SqlalchemyUtil.get_boolean_server_default(settings.DATABASE_TYPE, False), comment="是否主键")
    is_increment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=SqlalchemyUtil.get_boolean_server_default(settings.DATABASE_TYPE, False), comment="是否自增")
    is_nullable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=SqlalchemyUtil.get_boolean_server_default(settings.DATABASE_TYPE, True), comment="是否允许为空")
    is_unique: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=SqlalchemyUtil.get_boolean_server_default(settings.DATABASE_TYPE, False), comment="是否唯一")
    python_type: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="Python类型")
    python_field: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="Python字段名")
    is_insert: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=SqlalchemyUtil.get_boolean_server_default(settings.DATABASE_TYPE, True), comment="是否为新增字段")
    is_edit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=SqlalchemyUtil.get_boolean_server_default(settings.DATABASE_TYPE, True), comment="是否编辑字段")
    is_list: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=SqlalchemyUtil.get_boolean_server_default(settings.DATABASE_TYPE, True), comment="是否列表字段")
    is_query: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=SqlalchemyUtil.get_boolean_server_default(settings.DATABASE_TYPE, False), comment="是否查询字段")
    query_type: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None, comment="查询方式")
    html_type: Mapped[str | None] = mapped_column(String(100), nullable=True, default="input", comment="前端显示类型")
    dict_type: Mapped[str | None] = mapped_column(String(200), nullable=True, default="", comment="前端对应字典类型")
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="排序")
    table_id: Mapped[int] = mapped_column(Integer, ForeignKey("gen_table.id", ondelete="CASCADE"), nullable=False, index=True, comment="归属表编号")
    table: Mapped["GenTableModel"] = relationship(back_populates="columns")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:启动 1:停用)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")

    @validates("column_name")
    def validate_column_name(self, key: str, column_name: str) -> str:
        """验证列名非空并去首尾空格。"""
        if not column_name or not column_name.strip():
            raise ValueError("列名称不能为空")
        return column_name.strip()

    @validates("column_type")
    def validate_column_type(self, key: str, column_type: str) -> str:
        """验证列类型非空并去首尾空格。"""
        if not column_type or not column_type.strip():
            raise ValueError("列类型不能为空")
        return column_type.strip()
