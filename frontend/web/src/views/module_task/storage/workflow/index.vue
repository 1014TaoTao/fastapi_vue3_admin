<!-- 传输流程管理：VueFlow 画布定义源节点 → 目标节点，执行生成传输任务 -->
<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="flowSearchItems"
      :rules="searchBarRules"
      :is-expand="false"
      :show-expand="true"
      :show-reset="true"
      :show-search="true"
      :default-expanded="false"
      include-audit
      @search="handleSearchBarSearch"
      @reset="onResetSearch"
    />

    <ElCard class="fa-table-card" :style="{ 'margin-top': showSearchBar ? '12px' : '0' }">
      <FaTableHeader
        v-model:columns="columnChecks"
        v-model:showSearchBar="showSearchBar"
        :loading="loading"
        @refresh="refreshData"
      >
        <template #left>
          <FaTableHeaderLeft
            :remove-ids="selectedIds"
            :perm-create="['module_task:storage:flow:create']"
            :perm-delete="['module_task:storage:flow:delete']"
            :delete-loading="batchDeleting"
            :create-loading="createLoading"
            @add="handleAdd"
            @delete="handleBatchDelete"
          />
        </template>
      </FaTableHeader>

      <FaTable
        ref="faTableRef"
        :loading="loading"
        :data="data"
        :columns="columns"
        :pagination="pagination"
        @selection-change="onTableSelectionChange"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      />
    </ElCard>

    <!-- 详情弹窗 -->
    <FaDialog
      v-model="detailVisible"
      title="流程详情"
      width="680px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      @cancel="detailVisible = false"
    >
      <FaDescriptions :column="2" :data="detailFormData" :items="flowDetailItems" max-height="70vh">
        <template #sources="{ row }">
          <div class="flex flex-col gap-1">
            <ElTooltip
              v-for="(s, idx) in (row as unknown as FlowTable)?.sources || []"
              :key="idx"
              :content="nodeTip(s.source_id)"
              placement="top"
              :show-after="200"
            >
              <ElTag
                size="small"
                effect="plain"
                :style="protocolTagStyle(sourceMap[s.source_id])"
                class="w-fit"
                >{{ sourceName(s.source_id) }}</ElTag
              >
            </ElTooltip>
          </div>
        </template>
        <template #task_type="{ row }">
          <span>{{ taskTypeLabel((row as unknown as FlowTable)?.task_type) }}</span>
        </template>
        <template #targets="{ row }">
          <div class="flex flex-col gap-1">
            <div
              v-for="(t, idx) in (row as unknown as FlowTable)?.targets || []"
              :key="idx"
              class="flex items-center gap-2 text-[13px]"
            >
              <ElTooltip :content="nodeTip(t.target_id)" placement="top" :show-after="200">
                <ElTag
                  size="small"
                  effect="plain"
                  :style="protocolTagStyle(sourceMap[t.target_id])"
                  >{{ sourceName(t.target_id) }}</ElTag
                >
              </ElTooltip>
              <span class="text-xs text-[#909399]">{{ t.target_path }}</span>
            </div>
          </div>
        </template>
        <template #graph="{ row }">
          <span>{{ graphText(row as unknown as FlowTable) }}</span>
        </template>
      </FaDescriptions>
      <template #footer>
        <div class="fa-dialog-footer" style="padding-right: var(--el-dialog-padding-primary)">
          <ElButton type="primary" @click="detailVisible = false">关闭</ElButton>
        </div>
      </template>
    </FaDialog>

    <!-- 画布设计器（新增 / 编辑） -->
    <FaWorkflowDesignDrawer
      v-model:visible="drawerVisible"
      :flow="editingFlow"
      @refresh="refreshData"
    />

    <!-- 执行流程：为每个启用连线的源节点选择源文件/目录 -->
    <FaDialog
      v-model="executeVisible"
      :title="`执行流程 · ${executeRow?.name || ''}`"
      width="620px"
      @cancel="executeVisible = false"
    >
      <div class="mb-3 text-[13px] text-(--el-text-color-regular)">
        为以下源节点选择源文件 / 目录（回显节点默认源目录，可修改或浏览选择）：
      </div>
      <div class="flex flex-col gap-3">
        <div
          v-for="(s, idx) in executeSources"
          :key="s.source_id"
          class="flex items-center gap-2 rounded-lg border border-(--el-border-color-lighter) px-3 py-2"
        >
          <span class="w-24 shrink-0 truncate text-[13px] font-medium" :title="s.source_name">{{
            s.source_name
          }}</span>
          <ElInput
            v-model="s.path"
            size="small"
            placeholder="源文件 / 目录，留空使用节点默认源目录"
          />
          <ElButton size="small" @click="openExecuteBrowser(idx)">浏览</ElButton>
        </div>
      </div>
      <template #footer>
        <div class="fa-dialog-footer" style="padding-right: var(--el-dialog-padding-primary)">
          <ElButton type="primary" :loading="executing" @click="handleExecuteConfirm"
            >确认执行</ElButton
          >
          <ElButton @click="executeVisible = false">取消</ElButton>
        </div>
      </template>
    </FaDialog>

    <!-- 执行时浏览某个源节点的目录 -->
    <FaFileBrowserDialog
      v-model:visible="executeBrowseVisible"
      :title="`选择源文件 / 目录 · ${executeSourceName}`"
      :source-id="executeSourceId"
      :source-name="executeSourceName"
      :init-path="executeInitPath"
      :bucket="executeBucket"
      :root-path="executeRootPath"
      selectable
      @select="handleExecuteSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ElButton, ElTag, ElTooltip } from "element-plus";
import { useRouter } from "vue-router";
import { resolveStatusColumns, renderTableOperationCell, type TableOperationAction } from "@utils";
import FlowAPI, { type FlowTable } from "@/api/module_storage/workflow.ts";
import NodeAPI, { type SourceTable } from "@/api/module_storage/node.ts";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import FaWorkflowDesignDrawer from "./components/FaWorkflowDesignDrawer.vue";
import FaFileBrowserDialog from "./components/FaFileBrowserDialog.vue";
import { protocolColor, protocolLabel } from "./components/protocol.ts";

defineOptions({
  name: "Workflow",
  inheritAttrs: false,
});

const TASK_TYPE_OPTIONS = [
  { label: "多目标（并行）", value: "parallel" },
  { label: "链式（逐跳）", value: "chain" },
] as const;

const STATUS_OPTIONS = [
  { label: "启用", value: 0 },
  { label: "停用", value: 1 },
] as const;

function taskTypeLabel(value?: string): string {
  const opt = TASK_TYPE_OPTIONS.find((o) => o.value === value);
  return opt ? opt.label : (value ?? "-");
}

/** 画布统计文案（列表用 graph_stats，详情用 graph 兜底） */
function graphText(row?: FlowTable): string {
  const stats = row?.graph_stats;
  const graph = row?.graph;
  const nodeCount = stats?.node_count ?? graph?.nodes?.length ?? 0;
  const edgeCount = stats?.edge_count ?? graph?.edges?.length ?? 0;
  return nodeCount || edgeCount ? `${nodeCount} 节点 / ${edgeCount} 连线` : "—";
}

// ── 节点选项 ─────────────────────────────────────────────────────────
const router = useRouter();

const nodes = ref<SourceTable[]>([]);
const sourceMap = computed<Record<number, SourceTable>>(() => {
  const map: Record<number, SourceTable> = {};
  nodes.value.forEach((n) => {
    if (n.id) map[n.id] = n;
  });
  return map;
});
const sourceName = (id?: number | null) => (id ? sourceMap.value[id]?.name || `#${id}` : "—");

/** 节点地址摘要：对象存储取端点/桶，FTP/SFTP 取 host:port，本地取路径前缀 */
function sourceAddress(node?: SourceTable): string {
  if (!node) return "";
  const p = (node.protocol || "").toLowerCase();
  if (["s3", "obs", "oss", "cos"].includes(p)) return node.endpoint || node.bucket || "";
  if (p === "local") return node.path_prefix || "本地目录";
  return node.port ? `${node.host}:${node.port}` : (node.host ?? "");
}

/** 协议色样式（与画布节点/连线标签配色一致） */
function protocolTagStyle(node?: SourceTable) {
  return {
    color: protocolColor(node?.protocol),
    borderColor: protocolColor(node?.protocol),
  };
}

/** 协议色 Tag（与画布节点/连线标签配色一致） */
function protocolTag(node?: SourceTable) {
  return h(
    ElTag,
    {
      size: "small",
      effect: "plain",
      style: protocolTagStyle(node),
    },
    () => node?.name ?? "#—"
  );
}

/** 节点协议·地址提示（tooltip 内容） */
function nodeTip(id?: number | null): string {
  const node = id ? sourceMap.value[id] : undefined;
  return node ? `${protocolLabel(node.protocol)} · ${sourceAddress(node)}` : id ? `#${id}` : "—";
}

async function loadNodes() {
  const { data } = await NodeAPI.listNode({});
  nodes.value = data.data;
}

// ── 搜索 ─────────────────────────────────────────────────────────────
type FlowSearchForm = {
  name?: string;
  task_type?: string;
  status?: number;
  created_id?: number;
  updated_id?: number;
  created_time?: string[];
  updated_time?: string[];
};

const searchForm = ref<FlowSearchForm>({
  name: undefined,
  task_type: undefined,
  status: undefined,
  created_id: undefined,
  updated_id: undefined,
  created_time: undefined,
  updated_time: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const searchBarRules: Record<string, unknown> = {};

const flowSearchItems = computed<SearchFormItem[]>(() => [
  {
    label: "流程名称",
    key: "name",
    type: "input",
    placeholder: "请输入流程名称",
    clearable: true,
    span: 6,
  },
  {
    label: "类型",
    key: "task_type",
    type: "select",
    props: {
      placeholder: "请选择类型",
      options: TASK_TYPE_OPTIONS,
      clearable: true,
    },
    span: 6,
  },
  {
    label: "状态",
    key: "status",
    type: "select",
    props: {
      placeholder: "请选择状态",
      options: STATUS_OPTIONS,
      clearable: true,
    },
    span: 6,
  },
]);

function buildFlowReplaceParams(p: FlowSearchForm): Record<string, unknown> {
  return {
    name: p.name,
    task_type: p.task_type,
    status: p.status,
    created_id: p.created_id,
    updated_id: p.updated_id,
    created_time:
      Array.isArray(p.created_time) && p.created_time.length === 2 ? p.created_time : undefined,
    updated_time:
      Array.isArray(p.updated_time) && p.updated_time.length === 2 ? p.updated_time : undefined,
  };
}

// ── 表格 ─────────────────────────────────────────────────────────────
const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);
const { selectedRows, selectedIds, batchDeleting, onTableSelectionChange } =
  useTableSelection<FlowTable>();
const createLoading = ref(false);

function buildFlowRowActions(
  row: FlowTable,
  ctx: {
    onDetail: (id: number) => void;
    onEdit: (id: number) => void;
    onExecute: (row: FlowTable) => void;
    onDelete: (id: number, name: string) => void;
  }
): TableOperationAction[] {
  return [
    {
      key: "detail",
      label: "查看",
      artType: "view",
      perm: "module_task:storage:flow:query",
      run: () => ctx.onDetail(row.id!),
    },
    {
      key: "edit",
      label: "设计",
      artType: "edit",
      icon: "ri:pen-nib-line",
      perm: "module_task:storage:flow:update",
      run: () => ctx.onEdit(row.id!),
    },
    {
      key: "execute",
      label: "执行",
      artType: "view",
      icon: "ri:play-line",
      iconColor: "var(--el-color-success)",
      perm: "module_task:storage:transfer:create",
      run: () => ctx.onExecute(row),
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      icon: "ri:delete-bin-4-line",
      perm: "module_task:storage:flow:delete",
      run: () => ctx.onDelete(row.id!, row.name ?? ""),
    },
  ];
}

function formatFlowOperationCell(row: FlowTable, ctx: Parameters<typeof buildFlowRowActions>[1]) {
  return renderTableOperationCell(buildFlowRowActions(row, ctx), {
    wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1 flow-table-actions",
  });
}

async function deleteFlowRow(id: number, name: string) {
  try {
    await confirmDelete(`确定删除流程「${name}」吗？`);
  } catch {
    return; // 用户取消
  }
  await FlowAPI.deleteFlow([id]);
  faTableRef.value?.elTableRef?.clearSelection();
  await refreshRemove();
}

/** 执行流程：列出所有启用连线的源节点，各自选择源文件/目录后按画布连线生成传输任务 */
async function executeFlowRow(row: FlowTable) {
  const { data: flowDetail } = await FlowAPI.detailFlow(row.id!);
  const graph = flowDetail.data?.graph || {};
  const graphNodes = (graph.nodes || []) as Record<string, any>[];
  const graphEdges = (graph.edges || []) as Record<string, any>[];
  // 只取启用连线的源节点（去重），禁用的连线不参与执行
  const sourceIds: number[] = [];
  graphEdges.forEach((e) => {
    const ed = e.data || {};
    if (ed.enabled === false) return;
    const sid = graphNodes.find((n) => n.id === e.source)?.data?.source_id as number | undefined;
    if (sid != null && !sourceIds.includes(sid)) sourceIds.push(sid);
  });
  if (sourceIds.length === 0) {
    ElMessage.warning(`流程「${row.name}」没有启用的传输连线，无法执行`);
    return;
  }
  executeSources.value = sourceIds.map((sid) => {
    const srcNode = graphNodes.find((n) => (n.data?.source_id as number) === sid);
    const d = srcNode?.data || {};
    const bucket = (d.bucket as string) || "";
    const pathPrefix = ((d.path_prefix as string) || "").replace(/^\/+|\/+$/g, "");
    const nodeDefault = ((d.source_path as string) || "").replace(/^\/+|\/+$/g, "");
    return {
      source_id: sid,
      source_name: (d.label as string) || `#${sid}`,
      // 回显节点默认源目录，留空执行时后端回退使用节点默认源目录
      path: nodeDefault || pathPrefix,
      bucket,
      rootPath: bucket ? "" : pathPrefix,
    };
  });
  executeRow.value = row;
  executeVisible.value = true;
}

/** 浏览某个源节点的目录，选择后回填该源的源文件/目录 */
function openExecuteBrowser(index: number) {
  const src = executeSources.value[index];
  if (!src) return;
  executeBrowseIndex.value = index;
  executeSourceId.value = src.source_id;
  executeSourceName.value = src.source_name;
  executeInitPath.value = src.path;
  executeBucket.value = src.bucket;
  executeRootPath.value = src.rootPath;
  executeBrowseVisible.value = true;
}

/** 用户选定源文件/目录后回填对应源节点 */
function handleExecuteSelect(path: string) {
  const idx = executeBrowseIndex.value;
  if (idx >= 0 && executeSources.value[idx]) {
    executeSources.value[idx].path = path;
  }
}

/** 确认执行：组装 {源ID: 路径} 映射提交，禁用的连线由后端跳过 */
async function handleExecuteConfirm() {
  const row = executeRow.value;
  if (!row?.id) return;
  executing.value = true;
  try {
    const source_paths: Record<string, string> = {};
    executeSources.value.forEach((s) => {
      const p = s.path.trim();
      if (p) source_paths[String(s.source_id)] = p;
    });
    const { data } = await FlowAPI.executeFlow(row.id, { source_paths });
    const count = (data.data || []).length;
    ElNotification({
      title: "执行成功",
      type: "success",
      duration: 5000,
      position: "bottom-right",
      message: h("div", { class: "flex items-center gap-3" }, [
        h("span", `已生成 ${count} 个传输任务`),
        h(
          ElButton,
          {
            type: "primary",
            size: "small",
            text: true,
            onClick: () => void router.push("/task/storage/workflow/transfer"),
          },
          () => "查看任务"
        ),
      ]),
    });
    executeVisible.value = false;
    await refreshUpdate();
  } finally {
    executing.value = false;
  }
}

// ── 执行流程状态（选择每个源的源文件/目录）────────────────────────────
interface ExecuteSourceRow {
  source_id: number;
  source_name: string;
  path: string;
  bucket: string;
  rootPath: string;
}

const executeVisible = ref(false);
const executing = ref(false);
const executeRow = ref<FlowTable | null>(null);
const executeSources = ref<ExecuteSourceRow[]>([]);
const executeBrowseVisible = ref(false);
const executeBrowseIndex = ref(-1);
const executeSourceId = ref<number | null>(null);
const executeSourceName = ref("");
const executeInitPath = ref("");
const executeBucket = ref("");
const executeRootPath = ref("");

// ── 详情 ─────────────────────────────────────────────────────────────
const detailVisible = ref(false);
const detailFormData = ref<FlowTable>({} as FlowTable);

const flowDetailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] =
  [
    { label: "流程名称", prop: "name" },
    { label: "源节点", prop: "sources", slot: "sources" },
    { label: "类型", prop: "task_type", slot: "task_type" },
    { label: "目标节点", prop: "targets", slot: "targets" },
    { label: "流程图", prop: "graph", slot: "graph" },
    {
      label: "状态",
      prop: "status",
      tag: { map: { 0: { type: "success", text: "启用" }, 1: { type: "danger", text: "停用" } } },
    },
    { label: "备注", prop: "description" },
    { label: "创建时间", prop: "created_time" },
    { label: "更新时间", prop: "updated_time" },
  ];

async function openDetail(id: number) {
  const { data } = await FlowAPI.detailFlow(id);
  detailFormData.value = data.data || ({} as FlowTable);
  detailVisible.value = true;
}

// ── 画布设计器 ───────────────────────────────────────────────────────
const drawerVisible = ref(false);
const editingFlow = ref<FlowTable | null>(null);

async function openDrawer(id?: number) {
  if (id) {
    const { data } = await FlowAPI.detailFlow(id);
    editingFlow.value = data.data || null;
  } else {
    editingFlow.value = null;
  }
  drawerVisible.value = true;
}

async function handleAdd() {
  createLoading.value = true;
  try {
    await openDrawer();
  } finally {
    createLoading.value = false;
  }
}

// ── 表格配置 ─────────────────────────────────────────────────────────
// 操作列回调集合（columnsFactory 渲染时按行注入）
const opCtx = {
  onDetail: (id: number) => void openDetail(id),
  onEdit: (id: number) => void openDrawer(id),
  onExecute: executeFlowRow,
  onDelete: deleteFlowRow,
};

const {
  columns,
  columnChecks,
  data,
  loading,
  pagination,
  getData,
  replaceSearchParams,
  resetSearchParams,
  handleSizeChange,
  handleCurrentChange,
  refreshData,
  refreshUpdate,
  refreshRemove,
} = useTable({
  core: {
    apiFn: FlowAPI.pageFlow,
    apiParams: {
      page_no: 1,
      page_size: 10,
    },
    columnsFactory: resolveStatusColumns<FlowTable>(() => [
      { type: "selection", width: 48, fixed: "left" },
      { type: "globalIndex", width: 56, label: "序号" },
      { prop: "name", label: "流程名称", minWidth: 140, showOverflowTooltip: true },
      {
        prop: "sources",
        label: "源节点",
        minWidth: 180,
        formatter: (row: FlowTable) => {
          const sources = row.sources || [];
          if (sources.length === 0) return "—";
          const visible = sources.slice(0, 2);
          const rest = sources.slice(2);
          return h("span", { class: "flex flex-wrap items-center gap-1" }, [
            ...visible.map((s) =>
              h(
                ElTooltip,
                {
                  key: s.source_id,
                  content: nodeTip(s.source_id),
                  placement: "top",
                  showAfter: 200,
                },
                { default: () => protocolTag(sourceMap.value[s.source_id]) }
              )
            ),
            ...(rest.length
              ? [
                  h(
                    ElTooltip,
                    {
                      key: "__rest",
                      content: rest.map((s) => sourceName(s.source_id)).join("、"),
                      placement: "top",
                      showAfter: 200,
                    },
                    {
                      default: () =>
                        h(
                          ElTag,
                          { size: "small", type: "info", effect: "plain" },
                          () => `+${rest.length}`
                        ),
                    }
                  ),
                ]
              : []),
          ]);
        },
      },
      {
        prop: "task_type",
        label: "类型",
        width: 120,
        formatter: (row: FlowTable) =>
          h(
            ElTag,
            {
              type: row.task_type === "chain" ? "warning" : "primary",
              size: "small",
              effect: "plain",
            },
            () => taskTypeLabel(row.task_type)
          ),
      },
      {
        prop: "targets",
        label: "目标节点",
        minWidth: 220,
        formatter: (row: FlowTable) => {
          const targets = row.targets || [];
          if (targets.length === 0) return "—";
          const visible = targets.slice(0, 2);
          const rest = targets.slice(2);
          return h("div", { class: "flex flex-col gap-0.5" }, [
            ...visible.map((t) =>
              h("div", { key: t.target_id, class: "flex items-center gap-1.5" }, [
                h(
                  ElTooltip,
                  { content: nodeTip(t.target_id), placement: "top", showAfter: 200 },
                  { default: () => protocolTag(sourceMap.value[t.target_id]) }
                ),
                h(
                  "span",
                  {
                    class: "max-w-32 truncate text-xs text-(--el-text-color-secondary)",
                    title: t.target_path ?? "",
                  },
                  t.target_path ?? ""
                ),
              ])
            ),
            ...(rest.length
              ? [
                  h(
                    "div",
                    { key: "__rest", class: "text-xs text-(--el-text-color-secondary)" },
                    `+${rest.length} 个目标`
                  ),
                ]
              : []),
          ]);
        },
      },
      {
        prop: "graph",
        label: "传输关系",
        width: 110,
        formatter: (row: FlowTable) => {
          const stats = row.graph_stats;
          const graph = row.graph;
          const nodeCount = stats?.node_count ?? graph?.nodes?.length ?? 0;
          const edgeCount = stats?.edge_count ?? graph?.edges?.length ?? 0;
          if (!nodeCount && !edgeCount) return "—";
          return h(
            ElTooltip,
            { content: `${nodeCount} 节点 · ${edgeCount} 连线`, placement: "top", showAfter: 200 },
            {
              default: () =>
                h("span", { class: "text-(--el-text-color-regular)" }, `${edgeCount} 条连线`),
            }
          );
        },
      },
      {
        prop: "status",
        label: "状态",
        width: 80,
        status: {
          0: { type: "success", text: "启用" },
          1: { type: "danger", text: "停用" },
        },
      },
      { prop: "description", label: "备注", minWidth: 120, showOverflowTooltip: true },
      {
        prop: "created_time",
        label: "创建时间",
        width: 168,
        sortable: true,
        showOverflowTooltip: true,
      },
      {
        prop: "operation",
        label: "操作",
        width: 230,
        fixed: "right",
        align: "center",
        formatter: (row: FlowTable) => formatFlowOperationCell(row, opCtx),
      },
    ]),
  },
});

async function handleSearchBarSearch(params: FlowSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildFlowReplaceParams(params));
  await getData();
}

async function onResetSearch() {
  searchForm.value = {
    name: undefined,
    task_type: undefined,
    status: undefined,
    created_id: undefined,
    updated_id: undefined,
    created_time: undefined,
    updated_time: undefined,
  };
  await resetSearchParams();
}

async function handleBatchDelete() {
  const ids = selectedIds.value;
  if (ids.length === 0) return;
  try {
    await confirmBatchDelete(
      ids.length,
      selectedRows.value.map((r) => String(r.name ?? r.id))
    );
  } catch {
    return; // 用户取消
  }
  batchDeleting.value = true;
  try {
    await FlowAPI.deleteFlow(ids);
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } finally {
    batchDeleting.value = false;
  }
}

onMounted(() => {
  loadNodes();
});
</script>
