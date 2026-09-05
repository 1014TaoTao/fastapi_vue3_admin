from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class NodeModel(ModelMixin, UserMixin):
    """节点类型模型 - 动态定义节点类型
    """

    __tablename__: str = "task_node"
    __table_args__: dict[str, str] = {"comment": "节点类型表"}
    
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="节点名称")
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, comment="节点编码")
    jobstore: Mapped[str | None] = mapped_column(String(64), nullable=True, default="default", comment="存储器")
    executor: Mapped[str | None] = mapped_column(String(64), nullable=True, default="threadpool", comment="执行器")
    trigger: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="触发器(cron/interval/date)")
    trigger_args: Mapped[str | None] = mapped_column(Text, nullable=True, comment="触发器参数")
    func: Mapped[str | None] = mapped_column(Text, nullable=True, comment="代码块")
    args: Mapped[str | None] = mapped_column(Text, nullable=True, comment="位置参数")
    kwargs: Mapped[str | None] = mapped_column(Text, nullable=True, comment="关键字参数")
    coalesce: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False, comment="是否合并运行")
    max_instances: Mapped[int] = mapped_column(Integer, nullable=True, default=1, comment="最大实例数")
    start_date: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="开始时间")
    end_date: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="结束时间")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:启动 1:停用)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")
