<template>
  <FaDrawer
    v-model="dialogVisible"
    :title="drawerTitle"
    :close-on-click-modal="true"
    size="80%"
    drawer-class="workflow-drawer"
    @close="handleClose"
    @opened="handleDrawerOpened"
  >
    <ElContainer class="workflow-create-content flex flex-col h-full">
      <ElSplitter direction="horizontal" :style="'height: 100%'">
        <ElSplitterPanel size="250px" :min="200" :max="400">
          <ElScrollbar :style="'height: 100%'">
            <div class="p-3">
              <div class="mb-3 text-sm font-bold">基础信息</div>
              <FaForm
                ref="formRef"
                v-model="formData"
                :items="workflowBaseFormItems"
                :rules="formRules"
                label-width="50px"
                label-position="right"
                size="small"
                :span="24"
                :gutter="12"
                :show-reset="false"
                :show-submit="false"
                class="workflow-base-art-form"
              />
            </div>

            <ElDivider :style="'margin: 4px 0'" />

            <div class="p-3">
              <div class="mb-3 flex items-center justify-between">
                <span class="text-sm font-bold">存储节点</span>
                <span class="text-[10px] text-(--el-text-color-secondary)">拖拽到画布</span>
              </div>
              <ElInput
                v-model="searchKeyword"
                placeholder="搜索存储源名称"
                clearable
                size="small"
                class="mb-3"
              >
                <template #prefix>
                  <ElIcon><Search /></ElIcon>
                </template>
              </ElInput>
              <div
                v-if="filteredSources.length === 0"
                class="py-6 text-center text-xs text-(--el-text-color-secondary)"
              >
                未找到匹配的存储源
              </div>
              <div
                v-for="item in filteredSources"
                :key="item.id"
                class="mb-1.5 flex items-center gap-2.5 rounded-lg border border-(--el-border-color-lighter) px-2.5 py-2 cursor-move select-none transition-all hover:border-(--el-color-primary) hover:shadow-sm"
                :class="{ 'opacity-50 pointer-events-none': isNodePlaced(item.id) }"
                :title="item.description"
                draggable="true"
                @dragstart="onDragStart($event, item)"
              >
                <ElIcon :size="15" :color="protocolColor(item.protocol)"><Folder /></ElIcon>
                <div class="flex flex-col min-w-0 leading-tight">
                  <span class="truncate text-xs font-medium text-(--el-text-color-primary)">{{
                    item.name
                  }}</span>
                  <span class="truncate text-[10px] text-(--el-text-color-secondary)">
                    {{ protocolText(item.protocol, item.host) }}
                  </span>
                </div>
                <span
                  v-if="isNodePlaced(item.id)"
                  class="ml-auto shrink-0 whitespace-nowrap text-[10px] text-(--el-color-success)"
                  >已添加</span
                >
              </div>
            </div>
          </ElScrollbar>
        </ElSplitterPanel>

        <ElSplitterPanel>
          <div class="canvas-main relative flex flex-col h-full p-0">
            <div
              v-if="canvasReady"
              class="canvas-container flex-1 w-full h-full min-h-100 overflow-hidden"
            >
              <VueFlow
                v-model:nodes="nodes"
                v-model:edges="edges"
                class="basic-flow"
                :default-viewport="{ zoom: 1 }"
                :min-zoom="0.2"
                :max-zoom="1"
                :fit-view-on-init="true"
                :node-types="nodeTypesRegistry"
                :edge-types="edgeTypesRegistry"
                :default-edge-options="defaultEdgeOptions"
                :delete-key-code="['Backspace', 'Delete']"
                :selection-mode="SelectionMode.Partial"
                :snap-to-grid="true"
                :snap-grid="[16, 16]"
                @node-click="onNodeClick"
                @node-double-click="onNodeDoubleClick"
                @edge-click="onEdgeClick"
                @pane-click="handleCanvasClick"
                @drop="onDrop"
                @dragover="onDragOver"
              >
                <Controls />
                <Background pattern-color="#aaa" :gap="16" />
                <Panel
                  position="top-right"
                  class="workflow-toolbar flex items-center rounded-lg border border-(--el-border-color-lighter) bg-(--el-bg-color) p-1 shadow-[0_2px_8px_rgba(0,0,0,0.08)]"
                >
                  <ElTooltip content="自动排列节点布局" placement="bottom" :show-after="300">
                    <button type="button" class="workflow-toolbar-btn" @click="handleLayout">
                      <ElIcon :size="14"><Grid /></ElIcon>
                      <span>自动布局</span>
                    </button>
                  </ElTooltip>

                  <span class="mx-1 h-4 w-px bg-(--el-border-color-lighter)"></span>

                  <ElTooltip
                    :content="edgeAnimated ? '关闭连线动画' : '开启动画'"
                    placement="bottom"
                    :show-after="300"
                  >
                    <button
                      type="button"
                      class="workflow-toolbar-btn"
                      :class="{ active: edgeAnimated }"
                      @click="handleEdgeAnimatedChange(!edgeAnimated)"
                    >
                      <ElIcon :size="14">
                        <VideoPlay v-if="edgeAnimated" />
                        <VideoPause v-else />
                      </ElIcon>
                      <span>连线动画</span>
                    </button>
                  </ElTooltip>

                  <span class="mx-1 h-4 w-px bg-(--el-border-color-lighter)"></span>

                  <ElDropdown trigger="click" @command="handleLayoutDirection">
                    <button type="button" class="workflow-toolbar-btn">
                      <ElIcon :size="14"><Rank /></ElIcon>
                      <span>{{ layoutDirection === "LR" ? "横向布局" : "纵向布局" }}</span>
                    </button>
                    <template #dropdown>
                      <ElDropdownMenu>
                        <ElDropdownItem
                          command="LR"
                          :icon="layoutDirection === 'LR' ? Check : undefined"
                          >横向布局</ElDropdownItem
                        >
                        <ElDropdownItem
                          command="TB"
                          :icon="layoutDirection === 'TB' ? Check : undefined"
                          >纵向布局</ElDropdownItem
                        >
                      </ElDropdownMenu>
                    </template>
                  </ElDropdown>
                </Panel>
                <MiniMap pannable zoomable />
              </VueFlow>

              <div
                v-if="nodes.length === 0"
                class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-2 text-(--el-text-color-secondary)"
              >
                <ElIcon :size="44"><FolderOpened /></ElIcon>
                <p class="text-sm font-medium">从左侧拖入存储节点</p>
                <p class="text-xs">点击节点配置默认源目录，拖拽连线并点击配置传输方式与启用状态</p>
              </div>
            </div>
          </div>
        </ElSplitterPanel>

        <ElSplitterPanel v-if="updateState" size="320px" :min="280" :max="400">
          <FaStorageNodePanel
            v-if="updateState === 'node'"
            :node="selectedNode"
            @close="handleClosePanel"
            @delete="handleDeleteNode"
            @view-files="handleViewFiles"
            @save="handleSaveNode"
          />
          <FaEdgeConfigPanel
            v-if="updateState === 'edge'"
            :edge="selectedEdge"
            @close="handleClosePanel"
            @save="handleSaveEdge"
            @delete="handleDeleteEdge"
          />
        </ElSplitterPanel>
      </ElSplitter>
    </ElContainer>

    <FaFileBrowserDialog
      v-model:visible="fileBrowserVisible"
      :source-id="fileBrowserSourceId"
      :source-name="fileBrowserSourceName"
      :init-path="fileBrowserInitPath"
      :bucket="fileBrowserBucket"
      :root-path="fileBrowserRootPath"
    />

    <template #footer>
      <div class="drawer-footer flex gap-3 justify-end">
        <ElButton @click="handleClose">取消</ElButton>
        <ElButton type="primary" :loading="saving" @click="handleFinish">保存</ElButton>
      </div>
    </template>
  </FaDrawer>
</template>

<script setup lang="ts">
import type { Component } from "vue";
import { ElMessage } from "element-plus";
import { MarkerType, Panel, Position, SelectionMode, VueFlow, useVueFlow } from "@vue-flow/core";
import { Background } from "@vue-flow/background";
import { MiniMap } from "@vue-flow/minimap";
import { Controls } from "@vue-flow/controls";
import type {
  Node,
  Edge,
  DefaultEdgeOptions,
  NodeMouseEvent,
  EdgeMouseEvent,
} from "@vue-flow/core";
import {
  Folder,
  FolderOpened,
  Grid,
  Rank,
  Search,
  VideoPlay,
  VideoPause,
  Check,
} from "@element-plus/icons-vue";

import dagre from "dagre";
import "@vue-flow/core/dist/style.css";
import "@vue-flow/core/dist/theme-default.css";
import "@vue-flow/controls/dist/style.css";
import "@vue-flow/minimap/dist/style.css";

import FaDynamicNode from "./FaDynamicNode.vue";
import FaDynamicEdge from "./FaDynamicEdge.vue";
import FaStorageNodePanel from "./FaStorageNodePanel.vue";
import FaEdgeConfigPanel from "./FaEdgeConfigPanel.vue";
import FaFileBrowserDialog from "./FaFileBrowserDialog.vue";
import { protocolColor, protocolText } from "./protocol";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import type FaForm from "@/components/forms/fa-form/index.vue";
import FlowAPI, { type FlowForm, type FlowTable } from "@/api/module_task/workflow/flow";
import NodeAPI, { type SourceTable } from "@/api/module_task/workflow/node";

defineOptions({
  name: "WorkflowFlowDesignDrawer",
  inheritAttrs: false,
});

interface Props {
  visible?: boolean;
  flow?: FlowTable | null;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  flow: null,
});

const emit = defineEmits(["update:visible", "refresh"]);

const formRef = ref<InstanceType<typeof FaForm> | null>(null);
const saving = ref(false);

const formData = ref<{ name: string; description: string }>({ name: "", description: "" });

const formRules = {
  name: [{ required: true, message: "请输入流程名称", trigger: "blur" }],
};

const workflowBaseFormItems = computed<FormItem[]>(() => [
  {
    label: "名称",
    key: "name",
    type: "input",
    span: 24,
    props: { placeholder: "请输入流程名称", maxlength: 64 },
  },
  {
    label: "描述",
    key: "description",
    type: "input",
    span: 24,
    props: { type: "textarea", rows: 2, placeholder: "请输入流程描述", maxlength: 255 },
  },
]);

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit("update:visible", val),
});

const drawerTitle = computed(() => (props.flow ? "编辑传输流程" : "新增传输流程"));

const {
  onConnect,
  addEdges,
  getNodes: getNodesRef,
  getEdges: getEdgesRef,
  setNodes,
  setEdges,
  screenToFlowCoordinate,
  addNodes,
  fitView,
  findNode,
} = useVueFlow();

const defaultEdgeOptions: DefaultEdgeOptions = {
  type: "smoothstep",
  animated: true,
  markerEnd: MarkerType.ArrowClosed,
  // 加宽连线命中区（默认 2px），便于点选细长的连线
  interactionWidth: 20,
};

const edgeAnimated = ref<boolean>(true);

/** 连线展示文案：传输方式 + 分片信息，禁用时前置「已禁用」 */
function edgeDisplayLabel(data?: Record<string, any>): string {
  if (!data) return "";
  const modeText =
    data.transfer_mode === "multipart"
      ? `分片 ${data.multipart_part_size ?? 50}MB · ${data.multipart_concurrency ?? 6}线程`
      : "流式传输";
  return data.enabled === false ? `已禁用 · ${modeText}` : modeText;
}

const handleEdgeAnimatedChange = (value: boolean) => {
  edgeAnimated.value = value;
  defaultEdgeOptions.animated = value;
  setEdges(
    getEdgesRef.value.map((edge) => ({
      ...edge,
      // 禁用的连线不播放动画
      animated: (edge.data as Record<string, any> | undefined)?.enabled === false ? false : value,
    }))
  );
};

const layoutDirection = ref<"LR" | "TB">("LR");
// 用户是否显式点击过布局方向（点过则自动布局尊重该选择，否则按节点分布推断）
const userPickedDirection = ref(false);

// 根据连线方向推断布局方向：连线总体纵向（Δy 主导）→ 纵向布局（排成上下直线），否则横向
const inferLayoutDirection = (nodes: Node[], edges: Edge[]): "LR" | "TB" => {
  if (edges.length) {
    let sumX = 0;
    let sumY = 0;
    edges.forEach((e) => {
      const src = nodes.find((n) => n.id === e.source);
      const tgt = nodes.find((n) => n.id === e.target);
      if (src && tgt) {
        sumX += Math.abs(tgt.position.x - src.position.x);
        sumY += Math.abs(tgt.position.y - src.position.y);
      }
    });
    if (sumX > 0 || sumY > 0) return sumY > sumX ? "TB" : "LR";
  }
  // 无连线时按节点位置跨度兜底
  const xs = nodes.map((n) => n.position.x);
  const ys = nodes.map((n) => n.position.y);
  const spanX = Math.max(...xs) - Math.min(...xs);
  const spanY = Math.max(...ys) - Math.min(...ys);
  return spanY > spanX ? "TB" : "LR";
};

const handleLayout = () => {
  const currentNodes = getNodesRef.value;
  const currentEdges = getEdgesRef.value;

  if (currentNodes.length === 0) {
    ElMessage.warning("画布中没有节点，无法布局");
    return;
  }

  // 未显式指定方向时，按连线方向自动推断，把上下连线排成上下直线、左右连线排成左右直线
  const direction = userPickedDirection.value
    ? layoutDirection.value
    : inferLayoutDirection(currentNodes, currentEdges);
  const isHorizontal = direction === "LR";

  // dagre 布局（参考 VueFlow 官网 Layout 示例的标准写法）
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 100,
    ranksep: 140,
    marginx: 80,
    marginy: 80,
  });

  currentNodes.forEach((node) => {
    // 使用节点真实渲染尺寸（VueFlow 渲染后测量），避免估算偏差导致连线穿节点、间距失衡
    const gNode = findNode(node.id);
    dagreGraph.setNode(node.id, {
      width: gNode?.dimensions?.width || 180,
      height: gNode?.dimensions?.height || 60,
    });
  });

  currentEdges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = currentNodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    const gNode = findNode(node.id);
    const width = gNode?.dimensions?.width || 180;
    const height = gNode?.dimensions?.height || 60;
    return {
      ...node,
      // 指定连线出入口：纵向布局从上/下出发，横向布局从左/右出发，使链式连线呈直线
      targetPosition: isHorizontal ? Position.Left : Position.Top,
      sourcePosition: isHorizontal ? Position.Right : Position.Bottom,
      position: {
        // 取整避免亚像素渲染，保证链式流程节点严格对齐成直线
        x: Math.round(nodeWithPosition.x - width / 2),
        y: Math.round(nodeWithPosition.y - height / 2),
      },
    };
  });

  setNodes(layoutedNodes);
  setEdges(
    currentEdges.map((edge) => ({
      ...edge,
      type: "smoothstep",
      animated: edgeAnimated.value,
    }))
  );
  // 记录实际生效方向，供工具栏展示当前布局方向
  layoutDirection.value = direction;
  // 布局后自动缩放居中；与打开画布（fit-view-on-init）使用相同默认参数，保证保存后再打开位置一致
  nextTick(() => void fitView());
  ElMessage.success("画布布局完成");
};

const handleLayoutDirection = (direction: string | number | object) => {
  layoutDirection.value = direction as "LR" | "TB";
  handleLayout();
};

const nodes = ref<Node[]>([]);
const edges = ref<Edge[]>([]);

const canvasReady = ref(false);
const searchKeyword = ref("");

// ── 存储源节点面板 ───────────────────────────────────────────────
const allSources = ref<SourceTable[]>([]);

const filteredSources = computed(() => {
  const kw = searchKeyword.value.trim().toLowerCase();
  const list = allSources.value.filter((n) => n.status !== 1);
  if (!kw) return list;
  return list.filter((n) => (n.name || "").toLowerCase().includes(kw));
});

const placedSourceIds = computed(() => {
  const set = new Set<number>();
  nodes.value.forEach((n) => {
    const sid = n.data?.source_id;
    if (sid != null) set.add(sid as number);
  });
  return set;
});

const isNodePlaced = (id?: number) => (id != null ? placedSourceIds.value.has(id) : false);

async function loadSources() {
  const { data } = await NodeAPI.listNode({});
  allSources.value = data.data;
}

const nodeTypesRegistry = ref<Record<string, Component>>({ storage: markRaw(FaDynamicNode) });
// 覆盖内置 smoothstep 类型：渲染自定义可点击标签（EdgeLabelRenderer），保留原路径/箭头/动画能力
const edgeTypesRegistry = ref<Record<string, Component>>({ smoothstep: markRaw(FaDynamicEdge) });

// ── 选中状态与右侧面板 ───────────────────────────────────────────
const updateState = ref("");
const selectedEdge = ref<Edge>();
const selectedNode = ref<Node>();

const fileBrowserVisible = ref(false);
const fileBrowserSourceId = ref<number | null>(null);
const fileBrowserSourceName = ref("");
const fileBrowserInitPath = ref("");
const fileBrowserBucket = ref("");
const fileBrowserRootPath = ref("");

onMounted(() => {
  loadSources();
});

// 打开时加载已有画布（新增模式重置为空画布，避免残留上次数据）
watch(
  [() => props.visible, () => props.flow],
  ([visible, flow]) => {
    if (!visible) return;
    if (flow) {
      formData.value = { name: flow.name || "", description: flow.description || "" };
      // 节点/连线数据由后端详情接口补全存储源字段，直接回显
      const graphNodes = (flow.graph?.nodes as Node[]) || [];
      nodes.value = graphNodes;
      edges.value = ((flow.graph?.edges as Edge[]) || []).map((e) => ({
        ...e,
        // 连线文案由传输方式/分片信息/启用状态派生，不再使用自定义名称
        label: edgeDisplayLabel(e.data as Record<string, any> | undefined),
        animated:
          (e.data as Record<string, any> | undefined)?.enabled === false ? false : e.animated,
      }));
    } else {
      formData.value = { name: "", description: "" };
      nodes.value = [];
      edges.value = [];
    }
  },
  { immediate: true }
);

onConnect((connection) => {
  const srcNode = getNodesRef.value.find((n) => n.id === connection.source);
  const tgtNode = getNodesRef.value.find((n) => n.id === connection.target);
  addEdges({
    ...connection,
    type: "smoothstep",
    animated: edgeAnimated.value,
    label: "流式传输",
    data: {
      enabled: true,
      transfer_mode: "stream",
      source_label: srcNode?.data?.label || "",
      target_label: tgtNode?.data?.label || "",
      source_protocol: srcNode?.data?.protocol || "",
      target_protocol: tgtNode?.data?.protocol || "",
      source_storage_id: srcNode?.data?.source_id ?? null,
      target_storage_id: tgtNode?.data?.source_id ?? null,
    },
  });
});

// ── 节点/连线交互 ────────────────────────────────────────────────
const onNodeClick = ({ node }: NodeMouseEvent) => {
  selectedNode.value = node;
  updateState.value = "node";
};

const onNodeDoubleClick = ({ node }: NodeMouseEvent) => {
  openFileBrowser(node);
};

const onEdgeClick = ({ edge }: EdgeMouseEvent) => {
  selectedEdge.value = edge;
  updateState.value = "edge";
};

// 点击画布空白处关闭右侧面板（官网 pane-click：节点/连线上的点击不会触发）
const handleCanvasClick = () => {
  updateState.value = "";
  selectedNode.value = undefined;
  selectedEdge.value = undefined;
};

function handleClosePanel() {
  updateState.value = "";
  selectedNode.value = undefined;
  selectedEdge.value = undefined;
}

function handleSaveNode(data: { source_path?: string }) {
  if (!selectedNode.value) return;
  const nodeId = selectedNode.value!.id;
  const currentNodes = getNodesRef.value;
  const nodeIndex = currentNodes.findIndex((n) => n.id === nodeId);
  if (nodeIndex === -1) return;
  const updatedNodes = [...currentNodes];
  const prev = updatedNodes[nodeIndex]!;
  updatedNodes[nodeIndex] = {
    ...prev,
    data: {
      ...(prev.data || {}),
      source_path: data.source_path || "",
    },
  };
  setNodes(updatedNodes);
  ElMessage.success("已保存默认源目录");
}

function handleDeleteNode() {
  if (!selectedNode.value) return;
  const nodeId = selectedNode.value!.id;
  (async () => {
    try {
      await confirmDelete(`确定删除节点「${selectedNode.value?.data?.label ?? nodeId}」吗？`);
      const currentNodes = getNodesRef.value;
      const currentEdges = getEdgesRef.value;
      setNodes(currentNodes.filter((n) => n.id !== nodeId));
      setEdges(currentEdges.filter((e) => e.source !== nodeId && e.target !== nodeId));
      handleClosePanel();
    } catch {
      // 用户取消
    }
  })();
}

function handleSaveEdge(data: {
  data?: Record<string, unknown>;
  animated?: boolean;
  style?: Record<string, any>;
}) {
  if (!selectedEdge.value) return;
  const edgeId = selectedEdge.value!.id;
  const currentEdges = getEdgesRef.value;
  const edgeIndex = currentEdges.findIndex((e) => e.id === edgeId);
  if (edgeIndex === -1) return;
  const updatedEdges = [...currentEdges];
  const prev = updatedEdges[edgeIndex]!;
  const mergedData = {
    ...(prev.data || {}),
    ...(data.data || {}),
    source_label: prev.data?.source_label || "",
    target_label: prev.data?.target_label || "",
  };
  const enabled = mergedData.enabled !== false;
  // 源路径不再属于画布连线，保存时从连线数据中移除
  delete mergedData.source_path;
  updatedEdges[edgeIndex] = {
    ...prev,
    label: edgeDisplayLabel(mergedData),
    animated: enabled ? data.animated : false,
    style: enabled ? data.style : { stroke: "#c0c4cc" },
    data: mergedData,
  };
  setEdges(updatedEdges);
  handleClosePanel();
}

function handleDeleteEdge() {
  if (!selectedEdge.value) return;
  const edgeId = selectedEdge.value!.id;
  (async () => {
    try {
      await confirmDelete("确定删除该传输连线吗？");
      setEdges(getEdgesRef.value.filter((e) => e.id !== edgeId));
      handleClosePanel();
    } catch {
      // 用户取消
    }
  })();
}

// 键盘 Delete 删除选中元素后，若当前编辑的节点/连线已不存在则自动关闭右侧面板
watch(
  () => [
    getNodesRef.value.map((n) => n.id).join(","),
    getEdgesRef.value.map((e) => e.id).join(","),
  ],
  () => {
    if (
      updateState.value === "node" &&
      selectedNode.value &&
      !getNodesRef.value.some((n) => n.id === selectedNode.value!.id)
    ) {
      handleClosePanel();
    } else if (
      updateState.value === "edge" &&
      selectedEdge.value &&
      !getEdgesRef.value.some((e) => e.id === selectedEdge.value!.id)
    ) {
      handleClosePanel();
    }
  }
);

async function openFileBrowser(node: Node) {
  const sourceId = node?.data?.source_id;
  if (!sourceId) return;
  // 打开时实时获取节点配置的路径前缀与存储桶，默认定位到该目录（不依赖列表加载时序）
  const { data } = await NodeAPI.detailNode(sourceId);
  const src = data.data;
  const initPath = (src?.path_prefix || "").replace(/^\/+|\/+$/g, "");
  const bucket = src?.bucket || "";
  // 工作根：对象存储为桶根（空），文件系统协议为 path_prefix，点击"根目录"回到该位置
  const rootPath = bucket ? "" : initPath;
  // 等待详情期间用户可能已打开其他节点的浏览器，忽略迟到的响应
  if (fileBrowserVisible.value) return;
  fileBrowserInitPath.value = initPath;
  fileBrowserBucket.value = bucket;
  fileBrowserRootPath.value = rootPath;
  fileBrowserSourceId.value = sourceId;
  fileBrowserSourceName.value = node?.data?.label || "";
  fileBrowserVisible.value = true;
}

function handleViewFiles() {
  if (selectedNode.value) openFileBrowser(selectedNode.value);
}

// ── 拖拽添加节点 ─────────────────────────────────────────────────
function onDragStart(event: DragEvent, source: SourceTable) {
  if (event.dataTransfer) {
    event.dataTransfer.setData(
      "application/vueflow",
      JSON.stringify({
        id: source.id,
        label: source.name,
        protocol: source.protocol,
        host: source.host,
      })
    );
    event.dataTransfer.effectAllowed = "move";
  }
}

function onDragOver(event: DragEvent) {
  event.preventDefault();
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = "move";
  }
}

function onDrop(event: DragEvent) {
  const data = event.dataTransfer?.getData("application/vueflow");
  if (!data) return;

  const source = JSON.parse(data);
  const sourceId = source.id as number;
  if (placedSourceIds.value.has(sourceId)) {
    ElMessage.warning(`存储源「${source.label}」已在画布中`);
    return;
  }

  const position = screenToFlowCoordinate({ x: event.clientX, y: event.clientY });
  const srcMeta = allSources.value.find((s) => s.id === sourceId);
  const isObjectStorage = ["s3", "obs", "oss", "cos"].includes(
    (srcMeta?.protocol || "").toLowerCase()
  );
  const newNode: Node = {
    id: `src-${sourceId}`,
    type: "storage",
    position,
    data: {
      label: source.label,
      source_id: sourceId,
      protocol: source.protocol,
      host: source.host,
      // 默认源目录：对象存储取桶名，文件系统协议取路径前缀（本地取 host 目录）
      source_path: isObjectStorage
        ? srcMeta?.bucket || ""
        : srcMeta?.path_prefix || srcMeta?.host || "",
      // 存储源关键配置：节点上回显桶/地址/路径前缀（未在节点面板单独配置默认源目录时）
      bucket: srcMeta?.bucket || "",
      endpoint: srcMeta?.endpoint || "",
      region: srcMeta?.region || "",
      path_prefix: srcMeta?.path_prefix || "",
    },
  };
  addNodes([newNode]);
}

// ── 校验与保存 ───────────────────────────────────────────────────
function buildGraph(): { nodes: Record<string, any>[]; edges: Record<string, any>[] } {
  const cleanNodes = getNodesRef.value.map((node) => ({
    id: node.id,
    type: node.type,
    position: node.position,
    data: node.data,
  }));
  const cleanEdges = getEdgesRef.value.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: typeof edge.label === "string" ? edge.label : undefined,
    type: edge.type,
    animated: edge.animated,
    style: edge.style,
    data: edge.data,
  }));
  return { nodes: cleanNodes, edges: cleanEdges };
}

const handleFinish = async () => {
  // 提交前校验基础信息（名称必填），校验失败不发起保存
  try {
    await formRef.value?.validate();
  } catch {
    return;
  }
  saving.value = true;
  try {
    const graph = buildGraph();
    const payload: FlowForm = {
      name: formData.value.name.trim(),
      description: formData.value.description || undefined,
      status: 0,
      task_type: "parallel",
      graph,
    };
    if (props.flow?.id) {
      await FlowAPI.updateFlow(props.flow.id, payload);
    } else {
      await FlowAPI.createFlow(payload);
    }
    emit("refresh");
    handleClose();
  } finally {
    saving.value = false;
  }
};

const handleDrawerOpened = () => {
  canvasReady.value = true;
};

const handleClose = () => {
  canvasReady.value = false;
  updateState.value = "";
  selectedNode.value = undefined;
  selectedEdge.value = undefined;
  emit("update:visible", false);
};
</script>

<style scoped lang="scss">
.workflow-drawer {
  :deep(.el-drawer__body) {
    display: flex;
    flex-direction: column;
  }
}

:deep(.el-splitter) {
  flex: 1;
}

:deep(.el-splitter-panel) {
  overflow: hidden;
}

.canvas-container :deep(.vue-flow) {
  width: 100%;
  height: 100%;
}

:deep(.vue-flow__controls) {
  display: flex;
  flex-direction: column;
}

:deep(.vue-flow__controls-button) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  color: #000;
  cursor: pointer;
  border: none;
}

:deep(.el-dropdown) {
  display: flex;
}

.workflow-toolbar-btn {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 5px 10px;
  font-size: 12px;
  line-height: 1;
  color: var(--el-text-color-regular);
  white-space: nowrap;
  cursor: pointer;
  background: transparent;
  border: none;
  border-radius: 6px;
  transition:
    background-color 0.2s,
    color 0.2s;
}

.workflow-toolbar-btn:hover {
  color: var(--el-color-primary);
  background: var(--el-fill-color-light);
}

.workflow-toolbar-btn.active {
  color: var(--el-color-primary);
}

.workflow-base-art-form :deep(.el-row > .el-col:last-child) {
  display: none;
}

.workflow-base-art-form :deep(.el-form-item__content) {
  max-width: 100%;
}

.workflow-base-art-form :deep(section) {
  padding: 0;
}
</style>
