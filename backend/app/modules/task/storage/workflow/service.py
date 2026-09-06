from collections import defaultdict
from collections.abc import Sequence
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import AuthSchema, PageResultSchema
from app.core.exceptions import CustomException
from app.modules.task.storage.node.crud import StorageNodeCRUD
from app.modules.task.storage.node.model import StorageNodeModel
from app.modules.task.storage.node.service import StorageNodeService
from app.modules.task.storage.transfer.schema import TransferMode, TransferTargetSchema, TransferTaskCreateSchema
from app.modules.task.storage.transfer.service import StorageTransferService
from app.utils.common_util import search_to_dict

from .crud import WorkflowCRUD, WorkflowEdgeCRUD, WorkflowNodeCRUD
from .model import WorkflowEdgeModel, WorkflowModel, WorkflowNodeModel
from .schema import (
    WorkflowCreateSchema,
    WorkflowEdgeSchema,
    WorkflowGraphEdgeDataSchema,
    WorkflowGraphNodeDataSchema,
    WorkflowLayoutEdgeSchema,
    WorkflowLayoutNodeSchema,
    WorkflowNodeSchema,
    WorkflowOutSchema,
    WorkflowQueryParam,
    WorkflowSourceSchema,
    WorkflowSplitResultSchema,
    WorkflowTargetSchema,
    WorkflowTransferPlanSchema,
    WorkflowUpdateSchema,
)


class WorkflowService:
    """传输流程服务（源节点 → 目标节点，支持 1对多 / 多对1）

    数据职责划分：
    - flow.graph：仅存画布布局与展示字段（节点位置、连线样式/动画），不做业务解析
    - flow_node / flow_edge 表：节点存储源与默认源目录、连线启用与传输方式（业务配置）
    - sources / targets：由连线明细实时派生，仅用于列表展示/校验

    保存时拆分画布、回显时组装画布、执行直接读明细表，避免对 graph 的重复解析。
    """

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    # ── 内部工具 ────────────────────────────────────────────────────

    def _crud(self) -> WorkflowCRUD:
        return WorkflowCRUD(self.auth, self.db)

    async def _validate_nodes(
        self, sources: list[WorkflowSourceSchema], targets: list[WorkflowTargetSchema]
    ) -> None:
        """校验源节点与目标节点均存在且启用。"""
        node_service = StorageNodeService(self.auth, self.db)
        ids = [s.source_id for s in sources] + [t.target_id for t in targets]
        if ids:
            await node_service.get_active_sources(ids)

    @staticmethod
    def _sources_from(
        edge_rows: Sequence[WorkflowEdgeModel], node_map: dict[str, WorkflowNodeModel]
    ) -> list[WorkflowSourceSchema]:
        """由连线明细派生源节点列表（去重）。"""
        out: list[WorkflowSourceSchema] = []
        seen: set[int] = set()
        for e in edge_rows:
            src_node = node_map.get(e.source_node_key)
            if not src_node:
                continue
            if src_node.source_id in seen:
                continue
            seen.add(src_node.source_id)
            out.append(WorkflowSourceSchema(source_id=src_node.source_id))
        return out

    @staticmethod
    def _targets_from(
        edge_rows: Sequence[WorkflowEdgeModel], node_map: dict[str, WorkflowNodeModel]
    ) -> list[WorkflowTargetSchema]:
        """由连线明细派生目标列表（去重），目标目录取目标节点的默认源目录。"""
        out: list[WorkflowTargetSchema] = []
        seen: set[int] = set()
        for e in edge_rows:
            tgt_node = node_map.get(e.target_node_key)
            if not tgt_node:
                continue
            if tgt_node.source_id in seen:
                continue
            seen.add(tgt_node.source_id)
            out.append(
                WorkflowTargetSchema(target_id=tgt_node.source_id, target_path=tgt_node.source_path or "")
            )
        return out

    # ── 画布拆分/组装 ───────────────────────────────────────────────

    @staticmethod
    def _split_graph(graph: dict) -> WorkflowSplitResultSchema:
        """校验并拆分提交的画布。

        - 业务配置（节点 source_id/source_path、连线启用与传输方式）→ FlowNode/FlowEdge 明细
        - 布局展示（位置、连线样式/动画）→ 精简后的 layout
        同时完成画布完整性校验（存在连线、源≠目标），支持 1对多 / 多对1 拓扑。
        """
        nodes = {n["id"]: n for n in (graph.get("nodes") or [])}
        edges = graph.get("edges") or []
        if not edges:
            raise CustomException(msg="画布中未找到有效的传输连线（源节点 → 目标节点）")

        layout_nodes: list[dict] = []
        node_items: list[WorkflowNodeSchema] = []
        for nid, n in nodes.items():
            d = n.get("data") or {}
            layout_nodes.append(
                WorkflowLayoutNodeSchema(
                    id=nid,
                    type=n.get("type") or "storage",
                    position=n.get("position") or {"x": 0, "y": 0},
                    label=n.get("label") or d.get("label"),
                    style=n.get("style"),
                ).model_dump(exclude_none=True)
            )
            if d.get("source_id") is not None:
                node_items.append(
                    WorkflowNodeSchema(node_key=nid, source_id=d["source_id"], source_path=d.get("source_path"))
                )
        node_map = {it.node_key: it for it in node_items}

        sources: list[WorkflowSourceSchema] = []
        targets: list[WorkflowTargetSchema] = []
        edge_items: list[WorkflowEdgeSchema] = []
        layout_edges: list[dict] = []
        seen_edges: set[tuple[int, int]] = set()
        seen_sources: set[int] = set()
        seen_targets: set[int] = set()
        for e in edges:
            src_n = node_map.get(e.get("source"))
            tgt_n = node_map.get(e.get("target"))
            if not src_n or not tgt_n:
                continue
            sid, tid = src_n.source_id, tgt_n.source_id
            src_label = (nodes.get(e.get("source")) or {}).get("data", {}).get("label") or sid
            tgt_label = (nodes.get(e.get("target")) or {}).get("data", {}).get("label") or tid
            if sid == tid:
                raise CustomException(msg=f"流程保存失败，连线「{src_label} → {tgt_label}」源与目标不能相同")
            pair = (sid, tid)
            if pair in seen_edges:
                continue
            seen_edges.add(pair)
            if sid not in seen_sources:
                seen_sources.add(sid)
                sources.append(WorkflowSourceSchema(source_id=sid))
            if tid not in seen_targets:
                seen_targets.add(tid)
                # 目标目录由目标节点默认源目录决定
                targets.append(WorkflowTargetSchema(target_id=tid, target_path=tgt_n.source_path or ""))
            ed = e.get("data") or {}
            edge_items.append(
                WorkflowEdgeSchema(
                    edge_key=e["id"],
                    source_node_key=e.get("source"),
                    target_node_key=e.get("target"),
                    enabled=ed.get("enabled", True),
                    transfer_mode=ed.get("transfer_mode"),
                    multipart_part_size=ed.get("multipart_part_size"),
                    multipart_concurrency=ed.get("multipart_concurrency"),
                )
            )
            layout_edges.append(
                WorkflowLayoutEdgeSchema(
                    id=e["id"],
                    source=e.get("source"),
                    target=e.get("target"),
                    type=e.get("type") or "smoothstep",
                    animated=e.get("animated"),
                    style=e.get("style"),
                    label=e.get("label"),
                ).model_dump(exclude_none=True)
            )

        if not edge_items:
            raise CustomException(msg="画布中未找到有效的传输连线（源节点 → 目标节点）")
        return WorkflowSplitResultSchema(
            layout={"nodes": layout_nodes, "edges": layout_edges},
            nodes=node_items,
            edges=edge_items,
            sources=sources,
            targets=targets,
        )

    async def _save_graph(self, flow_id: int, nodes: list[WorkflowNodeSchema], edges: list[WorkflowEdgeSchema]) -> None:
        """覆写流程的业务明细（附属表物理删除后重建，不做逻辑删除）。

        父流程行已在调用方经 WorkflowCRUD 做过数据权限校验，明细随父全量覆写，
        删除统一走子表 CRUD 的物理清理方法（基类软删 delete 不适用于逐次覆写场景）。
        """
        await WorkflowNodeCRUD(self.auth, self.db).hard_delete_by_flow_ids([flow_id])
        await WorkflowEdgeCRUD(self.auth, self.db).hard_delete_by_flow_ids([flow_id])
        user_id = self.auth.user.id
        for it in nodes:
            self.db.add(WorkflowNodeModel(flow_id=flow_id, created_id=user_id, updated_id=user_id, **it.model_dump()))
        for it in edges:
            self.db.add(WorkflowEdgeModel(flow_id=flow_id, created_id=user_id, updated_id=user_id, **it.model_dump()))
        await self.db.flush()

    async def _load_flow_graph(self, flow_id: int) -> tuple[list[WorkflowNodeModel], list[WorkflowEdgeModel]]:
        result = await self.db.execute(
            select(WorkflowNodeModel)
            .where(WorkflowNodeModel.flow_id == flow_id)
            .order_by(WorkflowNodeModel.id)
        )
        node_rows = list(result.scalars().all())
        result = await self.db.execute(
            select(WorkflowEdgeModel)
            .where(WorkflowEdgeModel.flow_id == flow_id)
            .order_by(WorkflowEdgeModel.id)
        )
        edge_rows = list(result.scalars().all())
        return node_rows, edge_rows

    async def _build_graph(
        self,
        flow: WorkflowModel,
        node_rows: Sequence[WorkflowNodeModel],
        edge_rows: Sequence[WorkflowEdgeModel],
    ) -> dict:
        """由布局（flow.graph）+ 业务明细（node/edge 表）+ 存储源组装完整画布，供前端直接回显。"""
        layout = flow.graph or {}
        layout_nodes = {n["id"]: n for n in (layout.get("nodes") or [])}
        layout_edges = {e["id"]: e for e in (layout.get("edges") or [])}
        nodes_by_key = {n.node_key: n for n in node_rows}
        edges_by_key = {e.edge_key: e for e in edge_rows}

        ids = {n.source_id for n in node_rows}
        src_map: dict[int, StorageNodeModel] = {}
        if ids:
            sources = await StorageNodeCRUD(self.auth, self.db).get_list(search={"id": ("in", sorted(ids))})
            src_map = {s.id: s for s in sources}

        out_nodes: list[dict] = []
        for key, ln in layout_nodes.items():
            node_row = nodes_by_key.get(key)
            if not node_row:
                continue
            src = src_map.get(node_row.source_id)
            node = dict(ln)
            node["data"] = WorkflowGraphNodeDataSchema(
                source_id=node_row.source_id,
                source_path=node_row.source_path,
                label=ln.get("label") or (src.name if src else None),
                protocol=src.protocol if src else None,
                host=src.host if src else None,
                bucket=src.bucket if src else None,
                endpoint=src.endpoint if src else None,
                region=src.region if src else None,
                path_prefix=src.path_prefix if src else None,
            ).model_dump(exclude_none=True)
            out_nodes.append(node)

        out_edges: list[dict] = []
        for key, le in layout_edges.items():
            edge_row = edges_by_key.get(key)
            if not edge_row:
                continue
            src_node = nodes_by_key.get(edge_row.source_node_key)
            tgt_node = nodes_by_key.get(edge_row.target_node_key)
            src = src_map.get(src_node.source_id) if src_node else None
            tgt = src_map.get(tgt_node.source_id) if tgt_node else None
            edge = dict(le)
            edge["data"] = WorkflowGraphEdgeDataSchema(
                enabled=edge_row.enabled,
                transfer_mode=edge_row.transfer_mode,
                multipart_part_size=edge_row.multipart_part_size,
                multipart_concurrency=edge_row.multipart_concurrency,
                source_label=src.name if src else (str(src_node.source_id) if src_node else None),
                target_label=tgt.name if tgt else (str(tgt_node.source_id) if tgt_node else None),
                source_protocol=src.protocol if src else None,
                target_protocol=tgt.protocol if tgt else None,
                source_storage_id=src_node.source_id if src_node else None,
                target_storage_id=tgt_node.source_id if tgt_node else None,
            ).model_dump(exclude_none=True)
            out_edges.append(edge)

        return {"nodes": out_nodes, "edges": out_edges}

    # ── 查询 ────────────────────────────────────────────────────────

    async def _to_out(self, obj: WorkflowModel) -> WorkflowOutSchema:
        out = WorkflowOutSchema.model_validate(obj)
        node_rows, edge_rows = await self._load_flow_graph(obj.id)
        out.graph_stats = {"node_count": len(node_rows), "edge_count": len(edge_rows)}
        if edge_rows:
            node_map = {n.node_key: n for n in node_rows}
            out.sources = self._sources_from(edge_rows, node_map)
            out.targets = self._targets_from(edge_rows, node_map)
        if obj.graph:
            out.graph = await self._build_graph(obj, node_rows, edge_rows)
        return out

    async def _to_out_list(self, objs: Sequence[WorkflowModel]) -> list[WorkflowOutSchema]:
        """批量组装列表概览：源/目标列表、画布统计，一次查询避免 N+1。"""
        flow_ids = [o.id for o in objs]
        nodes_by_flow: dict[int, list[WorkflowNodeModel]] = defaultdict(list)
        edges_by_flow: dict[int, list[WorkflowEdgeModel]] = defaultdict(list)
        if flow_ids:
            result = await self.db.execute(
                select(WorkflowNodeModel).where(WorkflowNodeModel.flow_id.in_(flow_ids))
            )
            for n in result.scalars().all():
                nodes_by_flow[n.flow_id].append(n)
            result = await self.db.execute(
                select(WorkflowEdgeModel).where(WorkflowEdgeModel.flow_id.in_(flow_ids))
            )
            for e in result.scalars().all():
                edges_by_flow[e.flow_id].append(e)

        outs = [WorkflowOutSchema.model_validate(o) for o in objs]
        for obj, out in zip(objs, outs, strict=False):
            out.graph = None
            ns = nodes_by_flow.get(obj.id, [])
            es = edges_by_flow.get(obj.id, [])
            out.graph_stats = {"node_count": len(ns), "edge_count": len(es)}
            if es:
                node_map = {n.node_key: n for n in ns}
                out.sources = self._sources_from(es, node_map)
                out.targets = self._targets_from(es, node_map)
        return outs

    async def detail(self, id: int) -> WorkflowOutSchema:
        obj = await self._crud().get_or_404(id=id)
        return await self._to_out(obj)

    async def page(
        self,
        search: WorkflowQueryParam | None,
        page_no: int,
        page_size: int,
        order_by: list[dict] | None = None,
    ) -> PageResultSchema[WorkflowOutSchema]:
        result = await self._crud().page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search_to_dict(search),
        )
        items = await self._to_out_list(result.items)
        return PageResultSchema[WorkflowOutSchema](
            page_no=result.page_no,
            page_size=result.page_size,
            total=result.total,
            has_next=result.has_next,
            items=items,
        )

    async def get_list(self, search: WorkflowQueryParam | None = None) -> list[WorkflowOutSchema]:
        objs = await self._crud().get_list(search=search_to_dict(search), order_by=[{"id": "asc"}])
        return await self._to_out_list(objs)

    # ── 写入 ────────────────────────────────────────────────────────

    async def _prepare_and_save(
        self, flow_id: int | None, data: WorkflowCreateSchema | WorkflowUpdateSchema
    ) -> tuple[dict, list[WorkflowNodeSchema], list[WorkflowEdgeSchema]]:
        """拆分画布：业务配置写入明细表，布局存入 flow.graph。"""
        data_dict = data.model_dump(exclude_unset=True, exclude_none=True)
        graph = data_dict.pop("graph", None)
        if not graph:
            raise CustomException(msg="创建失败，请至少添加一条传输连线")
        split = self._split_graph(graph)
        await self._validate_nodes(split.sources, split.targets)
        data_dict["graph"] = split.layout
        if flow_id is not None:
            await self._save_graph(flow_id, split.nodes, split.edges)
        return data_dict, split.nodes, split.edges

    async def create(self, data: WorkflowCreateSchema) -> WorkflowOutSchema:
        exist = await self._crud().get(name=data.name)
        if exist:
            raise CustomException(msg="创建失败，流程名称已存在")
        data_dict, node_items, edge_items = await self._prepare_and_save(None, data)
        obj = await self._crud().create(data=data_dict)
        await self._save_graph(obj.id, node_items, edge_items)
        return await self._to_out(obj)

    async def update(self, id: int, data: WorkflowUpdateSchema) -> WorkflowOutSchema:
        await self._crud().get_or_404(id=id, msg="更新失败，该流程不存在")
        exist = await self._crud().get(name=data.name)
        if exist and exist.id != id:
            raise CustomException(msg="更新失败，流程名称已存在")
        # _prepare_and_save 在 flow_id 非空时已覆写明细，无需再次 _save_graph
        data_dict, _, _ = await self._prepare_and_save(id, data)
        await self._crud().update(id=id, data=data_dict)
        obj = await self._crud().get_or_404(id=id)
        return await self._to_out(obj)

    async def delete(self, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        await self._crud().delete(ids=ids)
        # 子表随父流程一并物理清理（无软删消费场景）
        await WorkflowNodeCRUD(self.auth, self.db).hard_delete_by_flow_ids(ids)
        await WorkflowEdgeCRUD(self.auth, self.db).hard_delete_by_flow_ids(ids)

    # ── 执行 ────────────────────────────────────────────────────────

    async def execute(self, id: int, source_paths: dict[str, str] | None = None) -> list[int]:
        """执行传输流程：直接读取业务明细表，每条启用的连线生成一个传输任务。

        支持 1对多 / 多对1 拓扑；源文件/目录优先取执行时传入的 source_paths
        （按源存储源ID映射），未传入时回退使用节点配置的默认源目录；
        传输方式未配置时默认流式传输；禁用的连线不参与执行。
        """
        obj = await self._crud().get_or_404(id=id, msg="执行失败，该流程不存在")
        node_rows, edge_rows = await self._load_flow_graph(id)
        # 只执行启用的连线（禁用的连线不生成传输任务）
        enabled_edges = [e for e in edge_rows if e.enabled]
        if not enabled_edges:
            raise CustomException(msg="执行失败，该流程画布没有启用的传输连线")
        nodes_by_key = {n.node_key: n for n in node_rows}
        source_paths = source_paths or {}

        # 阶段一：解析并校验每条连线
        plans: list[WorkflowTransferPlanSchema] = []
        for e in enabled_edges:
            src_node = nodes_by_key.get(e.source_node_key)
            tgt_node = nodes_by_key.get(e.target_node_key)
            if not src_node or not tgt_node:
                raise CustomException(msg=f"执行失败，连线 {e.edge_key} 对应的节点不存在")
            src_id, tgt_id = src_node.source_id, tgt_node.source_id
            src_path = (source_paths.get(str(src_id)) or (src_node.source_path or "")).strip()
            # 目标目录由目标节点默认源目录决定
            tgt_path = (tgt_node.source_path or "").strip()
            edge_label = f"「存储源{src_id} → 存储源{tgt_id}」"
            if not src_id or not tgt_id:
                raise CustomException(msg=f"执行失败，连线 {edge_label} 存在无效的存储源节点")
            if src_id == tgt_id:
                raise CustomException(msg=f"执行失败，连线 {edge_label} 源与目标不能相同")
            if not src_path or not tgt_path:
                missing = "未选择源文件/目录" if not src_path else "目标节点未配置默认目录"
                raise CustomException(msg=f"执行失败，连线 {edge_label} {missing}")
            plans.append(
                WorkflowTransferPlanSchema(
                    src_id=src_id,
                    tgt_id=tgt_id,
                    src_path=src_path,
                    tgt_path=tgt_path,
                    transfer_mode=e.transfer_mode or "stream",
                    multipart_part_size=e.multipart_part_size,
                    multipart_concurrency=e.multipart_concurrency,
                )
            )

        # 阶段二：统一校验所有涉及的存储源可用，再逐个生成传输任务
        node_service = StorageNodeService(self.auth, self.db)
        sources = await node_service.get_active_sources(
            [p.src_id for p in plans] + [p.tgt_id for p in plans]
        )
        name_map = {s.id: s.name for s in sources}

        transfer_service = StorageTransferService(self.auth, self.db)
        task_ids: list[int] = []
        for p in plans:
            src_label = name_map.get(p.src_id) or f"存储源{p.src_id}"
            tgt_label = name_map.get(p.tgt_id) or f"存储源{p.tgt_id}"
            # 任务名最大 128 字符，超长时截断避免 422
            task_name = f"{obj.name}-{src_label}→{tgt_label}"[:128]
            task_id = await transfer_service.create(
                TransferTaskCreateSchema(
                    name=task_name,
                    task_type="parallel",
                    source_type="remote",
                    source_id=p.src_id,
                    source_path=p.src_path,
                    targets=[TransferTargetSchema(target_id=p.tgt_id, target_path=p.tgt_path)],
                    # flow 侧以 str 保存传输方式，接口侧字面量校验由 pydantic 兜底，此处仅收窄静态类型
                    transfer_mode=cast(TransferMode | None, p.transfer_mode),
                    multipart_part_size=p.multipart_part_size,
                    multipart_concurrency=p.multipart_concurrency,
                )
            )
            task_ids.append(task_id)
        return task_ids
