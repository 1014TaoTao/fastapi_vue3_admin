from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.base_schema import BaseQueryParam, BaseSchema, UserByQueryParam, UserBySchema

WorkflowTaskType = Literal["parallel", "chain"]


class WorkflowTargetSchema(BaseModel):
    """流程目标节点配置（目标目录由目标节点默认源目录决定）"""

    target_id: int = Field(..., ge=1, description="目标节点ID(存储源)")
    target_path: str = Field(..., max_length=1024, description="目标路径")


class WorkflowSourceSchema(BaseModel):
    """流程源节点概览（由画布连线实时派生）"""

    source_id: int = Field(..., ge=1, description="源节点ID(存储源)")
    source_name: str | None = Field(default=None, description="源存储源名称")


class WorkflowNodeSchema(BaseModel):
    """画布节点业务配置（由画布拆分，落 flow_node 表）"""

    node_key: str = Field(..., description="画布节点ID")
    source_id: int = Field(..., ge=1, description="存储源ID")
    source_path: str | None = Field(default=None, max_length=1024, description="默认源目录")


class WorkflowEdgeSchema(BaseModel):
    """画布连线业务配置（由画布拆分，落 flow_edge 表）

    连线只定义传输方式；目标目录由目标节点的默认源目录（source_path）决定。
    """

    edge_key: str = Field(..., description="画布连线ID")
    source_node_key: str = Field(..., description="源画布节点ID")
    target_node_key: str = Field(..., description="目标画布节点ID")
    enabled: bool = Field(default=True, description="是否启用(禁用则不执行)")
    transfer_mode: str | None = Field(default=None, max_length=16, description="传输方式(stream/multipart，空用存储源默认)")
    multipart_part_size: int | None = Field(default=None, ge=1, description="分片大小(MB)")
    multipart_concurrency: int | None = Field(default=None, ge=1, description="分片并发数")


class WorkflowLayoutNodeSchema(BaseModel):
    """画布节点布局展示字段（存 flow.graph，业务配置在 flow_node 表）"""

    id: str = Field(..., description="画布节点ID")
    type: str = Field("storage", description="节点类型")
    position: dict = Field(default_factory=lambda: {"x": 0, "y": 0}, description="节点位置")
    label: str | None = Field(default=None, description="节点显示名")
    style: dict | None = Field(default=None, description="节点样式")


class WorkflowLayoutEdgeSchema(BaseModel):
    """画布连线布局展示字段（存 flow.graph，业务配置在 flow_edge 表）"""

    id: str = Field(..., description="画布连线ID")
    source: str = Field(..., description="源画布节点ID")
    target: str = Field(..., description="目标画布节点ID")
    type: str = Field("smoothstep", description="连线类型")
    animated: bool | None = Field(default=None, description="连线动画")
    style: dict | None = Field(default=None, description="连线样式")
    label: str | None = Field(default=None, description="连线显示名")


class WorkflowGraphNodeDataSchema(BaseModel):
    """画布节点回显数据（组装完整画布时写入 node.data）"""

    source_id: int = Field(..., ge=1, description="存储源ID")
    source_path: str | None = Field(default=None, description="默认源目录")
    label: str | None = Field(default=None, description="节点显示名")
    protocol: str | None = Field(default=None, description="存储源协议")
    host: str | None = Field(default=None, description="主机地址")
    bucket: str | None = Field(default=None, description="桶名（对象存储）")
    endpoint: str | None = Field(default=None, description="对象存储地址")
    region: str | None = Field(default=None, description="区域")
    path_prefix: str | None = Field(default=None, description="路径前缀")


class WorkflowGraphEdgeDataSchema(BaseModel):
    """画布连线回显数据（组装完整画布时写入 edge.data）"""

    enabled: bool = Field(default=True, description="是否启用(禁用则不执行)")
    transfer_mode: str | None = Field(default=None, description="传输方式")
    multipart_part_size: int | None = Field(default=None, description="分片大小(MB)")
    multipart_concurrency: int | None = Field(default=None, description="分片并发数")
    source_label: str | None = Field(default=None, description="源存储源名称")
    target_label: str | None = Field(default=None, description="目标存储源名称")
    source_protocol: str | None = Field(default=None, description="源存储源协议")
    target_protocol: str | None = Field(default=None, description="目标存储源协议")
    source_storage_id: int | None = Field(default=None, description="源存储源ID")
    target_storage_id: int | None = Field(default=None, description="目标存储源ID")


class WorkflowSplitResultSchema(BaseModel):
    """画布拆分结果：业务明细（node/edge）+ 精简布局 + 派生概览"""

    layout: dict = Field(..., description="精简后的画布布局 {nodes:[{id,type,position,label}],edges:[{id,source,target,type,animated,style,label}]}")
    nodes: list[WorkflowNodeSchema] = Field(default_factory=list, description="节点业务明细")
    edges: list[WorkflowEdgeSchema] = Field(default_factory=list, description="连线业务明细")
    sources: list[WorkflowSourceSchema] = Field(default_factory=list, description="源节点列表（去重）")
    targets: list[WorkflowTargetSchema] = Field(default_factory=list, description="目标列表（去重）")


class WorkflowTransferPlanSchema(BaseModel):
    """执行计划：单条连线生成的传输任务参数"""

    src_id: int = Field(..., ge=1, description="源存储源ID")
    tgt_id: int = Field(..., ge=1, description="目标存储源ID")
    src_path: str = Field(..., description="源文件/目录路径")
    tgt_path: str = Field(..., description="目标路径")
    transfer_mode: str = Field("stream", description="传输方式(stream/multipart)")
    multipart_part_size: int | None = Field(default=None, description="分片大小(MB)")
    multipart_concurrency: int | None = Field(default=None, description="分片并发数")


class WorkflowCreateSchema(BaseModel):
    """创建传输流程（画布驱动：业务配置解析后落 flow_node/flow_edge 表）"""

    name: str = Field(..., min_length=1, max_length=64, description="流程名称")
    task_type: WorkflowTaskType = Field("parallel", description="类型(parallel:多目标 chain:链式)")
    graph: dict = Field(..., description="VueFlow画布数据 {nodes:[{id,type,position,data}],edges:[{id,source,target,data}]}")
    status: int = Field(default=0, ge=0, le=1, description="状态(0:启用 1:停用)")
    description: str | None = Field(default=None, max_length=255, description="备注")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("流程名称不能为空")
        return value

    @model_validator(mode="after")
    def validate_graph(self):
        """画布必须包含传输连线（源节点 → 目标节点）。"""
        if not self.graph or not self.graph.get("edges"):
            raise ValueError("请至少添加一条传输连线（源节点 → 目标节点）")
        return self


class WorkflowUpdateSchema(WorkflowCreateSchema):
    """更新传输流程"""


class WorkflowExecuteSchema(BaseModel):
    """执行传输流程参数"""

    source_paths: dict[str, str] | None = Field(
        default=None,
        description="源文件/目录路径映射 {源存储源ID: 路径}，执行时必须为每条连线的源存储源指定",
    )


class WorkflowOutSchema(BaseSchema, UserBySchema):
    """传输流程详情响应模型（sources/targets 由 service 从明细表派生）"""

    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    task_type: WorkflowTaskType = "parallel"
    sources: list[WorkflowSourceSchema] = Field(default_factory=list, description="源节点列表（由画布派生）")
    targets: list[WorkflowTargetSchema] = Field(default_factory=list)
    graph: dict | None = None
    graph_stats: dict | None = None
    status: int = 0
    description: str | None = None


class WorkflowQueryParam(BaseQueryParam, UserByQueryParam):
    """传输流程查询参数"""

    name: str | None = Field(None, description="流程名称", json_schema_extra={"q": "like"})
    task_type: WorkflowTaskType | None = Field(None, description="类型(parallel/chain)", json_schema_extra={"q": "eq"})
    status: int | None = Field(None, ge=0, le=1, description="状态(0:启用 1:停用)", json_schema_extra={"q": "eq"})
