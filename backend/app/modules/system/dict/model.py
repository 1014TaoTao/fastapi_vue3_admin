from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import ModelMixin


class DictTypeModel(ModelMixin):
    """字典类型表"""

    __tablename__: str = "sys_dict_type"
    __table_args__: dict[str, str] = {"comment": "字典类型表"}

    dict_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="字典名称")
    dict_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True, unique=True, comment="字典类型")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:启动 1:停用)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")
    dict_data_list: Mapped[list["DictDataModel"]] = relationship("DictDataModel", back_populates="dict_type_obj")


class DictDataModel(ModelMixin):
    """字典数据表"""

    __tablename__: str = "sys_dict_data"
    __table_args__: dict[str, str] = {"comment": "字典数据表"}

    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True, comment="状态(0:启动 1:停用)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")
    dict_sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="字典排序")
    dict_label: Mapped[str] = mapped_column(String(255), nullable=False, comment="字典标签")
    dict_value: Mapped[str] = mapped_column(String(255), nullable=False, comment="字典键值")
    css_class: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="样式属性（其他样式扩展）")
    list_class: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="表格回显样式")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否默认(True是 False否)")
    dict_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="字典类型")

    # 添加外键关系，同时保留dict_type字段用于业务查询
    dict_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_dict_type.id", ondelete="CASCADE"),
        nullable=False,
        comment="字典类型ID",
    )

    # 关系定义
    dict_type_obj: Mapped[DictTypeModel] = relationship("DictTypeModel", back_populates="dict_data_list")
