from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class WorkflowModel(ModelMixin, UserMixin):
    """传输流程：定义源节点 → 目标节点列表（parallel 多目标 / chain 链式）

    graph 仅存画布布局与展示字段（节点位置、连线样式），业务配置落于
    flow_node / flow_edge 表，回显时由 service 组装，避免双份数据不一致。
    """

    __tablename__: str = "task_storage_workflow"
    __table_args__: dict[str, str] = {"comment": "传输流程定义表"}

    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="流程名称")
    task_type: Mapped[str] = mapped_column(String(16), nullable=False, default="parallel", comment="类型(parallel:多目标 chain:链式)")
    graph: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="VueFlow画布布局数据 {nodes:[{id,type,position,label}],edges:[{id,source,target,type,animated,style,label}]}")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:启用 1:停用)")
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True, comment="备注")


class WorkflowNodeModel(ModelMixin, UserMixin):
    """流程画布节点（业务配置）：节点关联的存储源与默认源目录。

    节点在画布上的位置/名称等布局字段存 flow.graph 的 nodes 项（key=node_key）。
    """

    __tablename__: str = "task_storage_workflow_node"
    __table_args__: dict[str, str] = {"comment": "流程画布节点表"}

    flow_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="流程ID")
    node_key: Mapped[str] = mapped_column(String(64), nullable=False, comment="画布节点ID")
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="存储源ID")
    source_path: Mapped[str | None] = mapped_column(String(1024), default=None, nullable=True, comment="默认源目录")


class WorkflowEdgeModel(ModelMixin, UserMixin):
    """流程画布连线（业务配置）：传输方式与分片参数。

    连线的目标目录由目标节点的默认源目录决定（节点 source_path），连线不再配置路径。
    连线的样式/动画等展示字段存 flow.graph 的 edges 项（key=edge_key）。
    """

    __tablename__: str = "task_storage_workflow_edge"
    __table_args__: dict[str, str] = {"comment": "流程画布连线表"}

    flow_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="流程ID")
    edge_key: Mapped[str] = mapped_column(String(64), nullable=False, comment="画布连线ID")
    source_node_key: Mapped[str] = mapped_column(String(64), nullable=False, comment="源画布节点ID")
    target_node_key: Mapped[str] = mapped_column(String(64), nullable=False, comment="目标画布节点ID")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="是否启用(禁用则不执行)")
    transfer_mode: Mapped[str | None] = mapped_column(String(16), default=None, nullable=True, comment="传输方式(stream/multipart，空用存储源默认)")
    multipart_part_size: Mapped[int | None] = mapped_column(Integer, default=None, nullable=True, comment="分片大小(MB)")
    multipart_concurrency: Mapped[int | None] = mapped_column(Integer, default=None, nullable=True, comment="分片并发数")
