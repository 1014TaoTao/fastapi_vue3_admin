<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="transferSearchItems"
      :rules="searchBarRules"
      :is-expand="false"
      :show-expand="true"
      :show-reset="true"
      :show-search="true"
      :default-expanded="false"
      @search="handleSearchBarSearch"
      @reset="onResetSearch"
    />

    <ElCard class="fa-table-card" :style="{ 'margin-top': showSearchBar ? '12px' : '0' }">
      <FaTableHeader
        v-model:showSearchBar="showSearchBar"
        v-model:columns="columnChecks"
        :loading="loading"
        @refresh="refreshTasks"
      >
        <template #left>
          <div class="flex items-center gap-2.5">
            <span class="text-base font-semibold">传输任务列表</span>
            <span
              class="inline-flex items-center gap-1.25 text-xs"
              :class="sseConnected ? 'text-(--el-color-success)' : 'text-(--el-color-info)'"
            >
              <i
                class="h-2 w-2 rounded-full"
                :class="sseConnected ? 'bg-(--el-color-success)' : 'bg-(--el-color-info)'"
              />{{ sseConnected ? "实时连接" : "连接中…" }}
            </span>
            <el-button type="primary" @click="openCreate">新建传输任务</el-button>
          </div>
        </template>
      </FaTableHeader>

      <div class="min-h-0 flex-1">
        <FaTable
          :data="tasks"
          :columns="columns"
          :pagination="{ current: page, size: pageSize, total }"
          stripe
          border
          height="100%"
          @pagination:size-change="onPageSizeChange"
          @pagination:current-change="onPageChange"
        >
          <template #task_type="{ row }">
            <el-tag :type="row.task_type === 'chain' ? 'warning' : 'primary'" size="small">
              {{ row.task_type === "chain" ? "链式" : "多目标" }}
            </el-tag>
          </template>
          <template #source="{ row }">
            <div class="min-w-0">
              <div>
                <el-tag v-if="row.source_type === 'local'" size="small" type="success">本地</el-tag>
                <el-tag v-else size="small" type="info">{{
                  protoText(sourceById(row.source_id))
                }}</el-tag>
                <span class="ml-1 text-[#606266]">{{
                  row.source_type === "local"
                    ? row.source_name || "本地文件"
                    : sourceName(row.source_id)
                }}</span>
              </div>
              <div v-if="row.source_path" class="mt-0.5 truncate text-xs text-[#909399]">
                {{ row.source_path }}
              </div>
            </div>
          </template>
          <template #target="{ row }">
            <span class="text-[#606266]" :title="targetFullText(row as TransferTaskItem)">{{
              targetShortText(row as TransferTaskItem)
            }}</span>
          </template>
          <template #status="{ row }">
            <el-tag :type="statusTypeMap[row.status as TransferStatus] || 'info'">{{
              statusText[row.status as TransferStatus] || row.status
            }}</el-tag>
          </template>
          <template #progress="{ row }">
            <div class="flex flex-col gap-0.5">
              <el-progress
                :percentage="row.progress || 0"
                :status="row.status === 'failed' ? 'exception' : undefined"
              />
              <div
                v-if="row.status === 'running' || row.speed > 0"
                class="flex items-center gap-1.5 text-xs"
              >
                <span
                  class="shrink-0 rounded-[3px] bg-(--el-color-success) px-1.25 py-0.5 text-[11px] leading-none text-white"
                  >{{ formatSpeed(row.speed) }}</span
                >
                <span class="whitespace-nowrap text-(--el-text-color-secondary)"
                  >{{ formatSize(row.transferred_size) }} / {{ formatSize(row.total_size) }}</span
                >
              </div>
            </div>
          </template>
          <template #info="{ row }">
            <div v-if="row.error_msg" class="flex min-w-0 items-center gap-1.5">
              <el-popover placement="top-start" width="360" trigger="hover">
                <div
                  class="max-h-75 overflow-auto break-all whitespace-pre-line text-[#800000] leading-[1.6]"
                >
                  {{ row.error_msg }}
                </div>
                <template #reference>
                  <span class="inline-block max-w-full truncate align-bottom text-[#800000]">{{
                    row.error_msg
                  }}</span>
                </template>
              </el-popover>
              <el-button
                v-if="row.status === 'failed'"
                size="small"
                type="primary"
                link
                @click="copyMessage(row.error_msg)"
                >复制</el-button
              >
            </div>
            <span v-else class="ml-1 text-[#606266]">{{
              stepSummaryText(row as TransferTaskItem)
            }}</span>
          </template>
          <template #actions="{ row }">
            <el-button size="small" link type="primary" @click="openDetail(row as TransferTaskItem)"
              >详情</el-button
            >
            <el-button
              v-if="row.status === 'pending' || row.status === 'running'"
              size="small"
              link
              type="warning"
              @click="cancelTask(row as TransferTaskItem)"
            >
              取消
            </el-button>
            <el-button size="small" link type="danger" @click="removeTask(row as TransferTaskItem)"
              >删除</el-button
            >
          </template>
        </FaTable>
      </div>
    </ElCard>

    <!-- 新建传输任务 -->
    <FaDialog
      v-model="createVisible"
      title="新建传输任务"
      width="640px"
      form-mode="create"
      confirm-text="开始传输"
      :confirm-loading="submitting"
      @cancel="createVisible = false"
      @confirm="submit"
    >
      <FaForm
        ref="formRef"
        v-model="form"
        :items="createFormItems"
        :rules="formRules"
        label-width="86px"
        :span="24"
        scrollbar
        max-height="70vh"
      >
        <!-- 传输流程：具名插槽接管（需 @change 触发流程填充） -->
        <template #flow_id>
          <el-select
            v-model="selectedFlowId"
            placeholder="从已配置流程自动填充（可选，仍可手动调整）"
            clearable
            filterable
            style="width: 100%"
            @change="applyFlow"
          >
            <el-option
              v-for="f in enabledFlows"
              :key="f.id"
              :value="f.id!"
              :label="flowOptionLabel(f)"
            />
          </el-select>
        </template>

        <!-- 本地文件：componentMap 无 upload 类型，具名插槽接管 -->
        <template #local_file>
          <el-upload
            drag
            :auto-upload="false"
            :limit="1"
            :on-change="onFileChange"
            :on-exceed="onExceed"
            :on-remove="onFileRemove"
            style="width: 100%"
          >
            <div class="el-upload__text">将文件拖到此处，或 <em>点击选择文件</em></div>
          </el-upload>
        </template>

        <!-- 目标列表：动态增删行，具名插槽接管 -->
        <template #targets>
          <div style="width: 100%">
            <div v-for="(t, idx) in form.targets" :key="idx" class="mb-2 flex items-center gap-2">
              <el-tag
                v-if="form.task_type === 'chain'"
                size="small"
                :type="idx === 0 ? 'primary' : 'warning'"
                class="shrink-0"
              >
                #{{ idx + 1 }}
              </el-tag>
              <el-select
                v-model="t.target_id"
                placeholder="目标存储源"
                filterable
                style="width: 250px"
              >
                <el-option
                  v-for="s in enabledSources"
                  :key="s.id"
                  :label="`${s.name}（${s.protocol}${s.host ? ' · ' + s.host : ''}）`"
                  :value="s.id!"
                />
              </el-select>
              <el-input
                v-model="t.target_path"
                :placeholder="
                  selectedFlowId && !t.target_path
                    ? '目标节点未配置默认源目录，请填写目标路径'
                    : '目标路径（对象存储填 Key 前缀）'
                "
                style="flex: 1"
              />
              <el-button link type="danger" @click="removeTarget(idx)">删除</el-button>
            </div>
            <div class="flex items-center gap-3">
              <el-button type="primary" plain size="small" @click="addTarget"
                >＋ 添加目标</el-button
              >
              <span
                v-if="form.task_type === 'chain' && form.targets.length > 1"
                class="text-[#909399]"
              >
                将按顺序执行：{{ flowPreview }}
              </span>
            </div>
          </div>
        </template>
      </FaForm>
    </FaDialog>

    <!-- 传输任务详情 -->
    <FaDialog
      v-model="detailVisible"
      title="传输任务详情"
      width="920px"
      form-mode="detail"
      @close="detailVisible = false"
    >
      <template v-if="detailRow">
        <FaDescriptions
          :column="2"
          :span="1"
          size="small"
          label-width="200px"
          :data="detailRowData"
          :items="transferDetailItems"
          max-height="70vh"
        >
          <template #name="{ row }">
            <el-tooltip :content="String(row?.name ?? '')" placement="top" :show-after="100">
              <div class="max-w-45 truncate">{{ row?.name }}</div>
            </el-tooltip>
          </template>
          <template #source="{ row }">
            <el-tooltip
              :content="row ? sourceShortText(row as unknown as TransferTaskItem) : ''"
              placement="top"
              :show-after="100"
            >
              <div class="max-w-55 truncate">
                {{ row ? sourceShortText(row as unknown as TransferTaskItem) : "" }}
              </div>
            </el-tooltip>
          </template>
          <template #total_size="{ row }">{{ formatSize(row?.total_size as number) }}</template>
          <template #speed="{ row }">{{ formatSpeed(row?.speed as number) }}</template>
          <template #started_at="{ row }">{{ formatTime(row?.started_at as string) }}</template>
          <template #finished_at="{ row }">{{ formatTime(row?.finished_at as string) }}</template>
        </FaDescriptions>
        <div
          v-if="detailRow.error_msg"
          class="mt-2.5 break-all rounded bg-(--el-color-danger-light-9) px-3 py-2 text-xs text-(--el-color-danger)"
        >
          {{ detailRow.error_msg }}
        </div>
        <div
          class="mb-2.5 mt-3.5 border-t border-(--el-border-color-lighter) pt-3 text-[13px] font-semibold text-(--el-text-color-primary)"
        >
          传输步骤
        </div>
        <div v-if="detailSteps.length" class="flex flex-col gap-2">
          <template v-for="(step, idx) in detailSteps" :key="step.id ?? idx">
            <div
              class="rounded-md border border-(--el-border-color-lighter) bg-(--el-fill-color-lighter) px-3 py-2.5"
            >
              <div class="flex items-center gap-2">
                <el-tag :type="idx === 0 ? 'primary' : 'warning'" size="small"
                  >#{{ idx + 1 }}</el-tag
                >
                <el-tag :type="statusTypeMap[step.status] || 'info'" size="small">{{
                  statusText[step.status] || step.status
                }}</el-tag>
                <span class="ml-auto text-xs text-(--el-text-color-secondary)"
                  >{{ step.progress }}% · {{ formatSpeed(step.speed) }}</span
                >
              </div>
              <div class="mt-1.5 break-all text-xs text-(--el-text-color-regular)">
                <span
                  class="mr-1.5 inline-block rounded-[3px] bg-(--el-color-info) px-1.25 py-0.5 text-[11px] leading-none text-white"
                  >源</span
                >{{ sourceName(step.source_id) }} · {{ step.source_path || "—" }}
              </div>
              <div
                class="mt-1 text-center text-[14px] font-bold text-(--el-text-color-placeholder)"
              >
                ↓
              </div>
              <div class="mt-1.5 break-all text-xs text-(--el-text-color-regular)">
                <span
                  class="mr-1.5 inline-block rounded-[3px] bg-(--el-color-primary) px-1.25 py-0.5 text-[11px] leading-none text-white"
                  >目标</span
                >{{ sourceName(step.target_id) }} · {{ step.target_path }}
              </div>
              <div v-if="step.error_msg" class="mt-1.5 break-all text-xs text-(--el-color-danger)">
                {{ step.error_msg }}
              </div>
            </div>
            <div
              v-if="idx < detailSteps.length - 1"
              class="text-center text-[18px] font-bold text-(--el-text-color-placeholder)"
            >
              →
            </div>
          </template>
        </div>
        <el-empty v-else description="暂无步骤" :image-size="60" />
      </template>
    </FaDialog>
  </div>
</template>

<script setup lang="ts">
import TransferAPI, {
  TransferStream,
  type TransferPushMessage,
  type TransferSourceType,
  type TransferStatus,
  type TransferTaskItem,
  type TransferTaskType,
} from "@/api/module_task/workflow/transfer";
import NodeAPI, { type SourceTable } from "@/api/module_task/workflow/node";
import FlowAPI, { type FlowTable } from "@/api/module_task/workflow/flow";
import FaDescriptions, {
  type DescriptionsItem,
} from "@/components/display/fa-descriptions/index.vue";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import type { ColumnOption } from "@/types/component";
import type { FormItemRule, FormRules } from "element-plus";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";

// ── 存储源 ────────────────────────────────────────────────────────────
const sources = ref<SourceTable[]>([]);
const sourceMap = computed<Record<number, SourceTable>>(() => {
  const map: Record<number, SourceTable> = {};
  sources.value.forEach((s) => {
    if (s.id) map[s.id] = s;
  });
  return map;
});
/** 可用的存储源（status 0=启用 1=停用） */
const enabledSources = computed(() => sources.value.filter((s) => s.status !== 1));
const sourceById = (id?: number | null) => (id ? sourceMap.value[id] : undefined);
const sourceName = (id?: number | null) => (id ? sourceMap.value[id]?.name || `#${id}` : "—");
const protoText = (s?: SourceTable) => s?.protocol || "?";

async function loadSources() {
  const { data } = await NodeAPI.listNode({});
  sources.value = data.data;
}

// ── 传输流程 ──────────────────────────────────────────────────────────
const flows = ref<FlowTable[]>([]);
const selectedFlowId = ref<number | null>(null);
/** 启用的流程（status 0=启用 1=停用） */
const enabledFlows = computed(() => flows.value.filter((f) => f.status !== 1));

function flowOptionLabel(f: FlowTable): string {
  const sources = (f.sources || []).map((s) => sourceName(s.source_id)).join("、");
  const targets = (f.targets || []).map((t) => sourceName(t.target_id)).join("、");
  return `${f.name}（${sources || "—"} → ${targets || "—"}）`;
}

/** 选中流程后自动填充目标列表（手动任务表单为单源模型：仅流程为单源时自动填充源） */
function applyFlow(id?: number | null) {
  selectedFlowId.value = id ?? null;
  const flow = flows.value.find((f) => f.id === id);
  if (!flow) return;
  form.value.task_type = flow.task_type || "parallel";
  form.value.source_type = "remote";
  const sources = flow.sources || [];
  form.value.source_id = sources.length === 1 && sources[0] ? sources[0].source_id : null;
  form.value.source_path = "";
  form.value.targets = (flow.targets || []).map((t) => ({
    target_id: t.target_id,
    target_path: t.target_path,
  }));
  if (flow.name) form.value.name = flow.name;
  formRef.value?.validateField("targets").catch(() => {});
}

async function loadFlows() {
  const { data } = await FlowAPI.listFlow({});
  flows.value = data.data;
}

// ── 任务列表 ──────────────────────────────────────────────────────────
const tasks = ref<TransferTaskItem[]>([]);
const loading = ref(false);
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);

type TransferSearchForm = {
  name?: string;
  status?: TransferStatus;
};
const searchForm = ref<TransferSearchForm>({ name: undefined, status: undefined });
const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const searchBarRules: Record<string, unknown> = {};

const statusOptions = computed<{ label: string; value: string }[]>(() =>
  Object.entries(statusText).map(([value, label]) => ({ label, value }))
);

const transferSearchItems = computed<SearchFormItem[]>(() => [
  {
    label: "任务名称",
    key: "name",
    type: "input",
    placeholder: "请输入任务名称",
    clearable: true,
    span: 6,
  },
  {
    label: "状态",
    key: "status",
    type: "select",
    props: {
      placeholder: "全部",
      options: statusOptions.value,
      clearable: true,
    },
    span: 6,
  },
]);

// ── 表格列配置（FaTable：复杂列走具名插槽，名称/来源列透传 show-overflow-tooltip） ──
const columnChecks = ref<ColumnOption[]>([
  { prop: "id", label: "ID", width: 70 },
  { prop: "name", label: "任务名称", minWidth: 150, showOverflowTooltip: true },
  { prop: "task_type", label: "类型", width: 90, useSlot: true },
  { prop: "source", label: "来源", minWidth: 180, showOverflowTooltip: true, useSlot: true },
  { prop: "target", label: "目标", minWidth: 190, useSlot: true },
  { prop: "status", label: "状态", width: 92, useSlot: true },
  { prop: "progress", label: "进度", minWidth: 240, useSlot: true },
  { prop: "info", label: "信息", minWidth: 180, useSlot: true },
  { prop: "actions", label: "操作", width: 150, fixed: "right", useSlot: true },
]);
/** 渲染列：仅保留列设置中可见的列 */
const columns = computed(() => columnChecks.value.filter((c) => c.visible !== false));

async function loadTasks() {
  loading.value = true;
  try {
    const { data } = await TransferAPI.pageTask({
      page_no: page.value,
      page_size: pageSize.value,
      name: searchForm.value.name || undefined,
      status: searchForm.value.status,
    });
    tasks.value = data.data.items || [];
    total.value = data.data.total || 0;
    syncStream(); // 列表刷新后重新评估：有进行中任务才保持连接
  } finally {
    loading.value = false;
  }
}

function onPageChange(p: number) {
  page.value = p;
  loadTasks();
}
function onPageSizeChange(size: number) {
  pageSize.value = size;
  page.value = 1;
  loadTasks();
}
function refreshTasks() {
  page.value = 1;
  loadTasks();
}
function handleSearchBarSearch() {
  page.value = 1;
  loadTasks();
}
function onResetSearch() {
  searchForm.value = { name: undefined, status: undefined };
  page.value = 1;
  loadTasks();
}

// ── 状态 / 格式化 ─────────────────────────────────────────────────────
const statusText: Record<TransferStatus, string> = {
  pending: "等待中",
  running: "传输中",
  success: "成功",
  failed: "失败",
  canceled: "已取消",
};
const statusTypeMap: Record<TransferStatus, "info" | "warning" | "success" | "danger"> = {
  pending: "info",
  running: "warning",
  success: "success",
  failed: "danger",
  canceled: "info",
};

function formatSize(bytes?: number | null): string {
  if (!bytes || bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  let n = bytes;
  while (n >= 1024 && i < units.length - 1) {
    n /= 1024;
    i += 1;
  }
  return `${n.toFixed(i ? 1 : 0)} ${units[i]}`;
}
function formatSpeed(bytesPerSec: number): string {
  if (!bytesPerSec || bytesPerSec <= 0) return "0 B/s";
  return `${formatSize(bytesPerSec)}/s`;
}
function formatTime(t?: string | null): string {
  if (!t) return "—";
  const d = new Date(t);
  if (Number.isNaN(d.getTime())) return "—";
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

// ── 任务展示辅助 ──────────────────────────────────────────────────────
function sourceShortText(row: TransferTaskItem): string {
  const who = row.source_type === "local" ? "本地文件" : sourceName(row.source_id);
  const path = row.source_path || row.source_name || "—";
  return `${who} · ${path}`;
}
function targetShortText(row: TransferTaskItem): string {
  const steps = row.steps || [];
  const first = steps[0];
  if (!first) return "—";
  const text = `${sourceName(first.target_id)}/${first.target_path}`;
  return steps.length > 1 ? `${text} 等 ${steps.length} 个目标` : text;
}
function targetFullText(row: TransferTaskItem): string {
  const steps = row.steps || [];
  if (!steps.length) return "—";
  return steps.map((s) => `${sourceName(s.target_id)}:${s.target_path}`).join("  →  ");
}
function stepSummaryText(row: TransferTaskItem): string {
  const steps = row.steps || [];
  const first = steps[0];
  if (!first) return "";
  if (steps.length > 1) {
    const done = steps.filter((s) => s.status === "success").length;
    return `${done}/${steps.length} 步完成`;
  }
  return first.status === "success" ? "传输完成" : "";
}
async function copyMessage(message: string) {
  try {
    await navigator.clipboard.writeText(message);
  } catch {
    const ta = document.createElement("textarea");
    ta.value = message;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
  }
  ElMessage.success("报错信息已复制");
}

// ── 新建任务对话框 ────────────────────────────────────────────────────
const createVisible = ref(false);
const submitting = ref(false);
const formRef = ref();

interface TargetRow {
  target_id: number | null;
  target_path: string;
}
const form = ref({
  name: "",
  task_type: "parallel" as TransferTaskType,
  source_type: "remote" as TransferSourceType,
  source_id: null as number | null,
  source_path: "",
  local_file: null as File | null,
  targets: [] as TargetRow[],
});

/** 创建表单 items：源相关字段随 source_type 显隐；flow/targets/local_file 走具名插槽 */
const createFormItems = computed<FormItem[]>(() => [
  {
    key: "name",
    label: "任务名称",
    type: "input",
    props: { placeholder: "例如：传输_文件A_20260825" },
  },
  { key: "flow_id", label: "传输流程" /* #flow_id 插槽接管 */ },
  {
    key: "task_type",
    label: "传输方式",
    type: "radiogroup",
    props: {
      options: [
        { label: "多目标（同时传输到多个存储源）", value: "parallel" },
        { label: "链式（按目标顺序逐跳传输）", value: "chain" },
      ],
    },
  },
  {
    key: "source_type",
    label: "源类型",
    type: "radiogroup",
    props: {
      options: [
        { label: "远端存储源", value: "remote" },
        { label: "本地文件", value: "local" },
      ],
    },
  },
  {
    key: "source_id",
    label: "源存储源",
    type: "select",
    hidden: form.value.source_type !== "remote",
    props: {
      placeholder: "选择源存储源",
      filterable: true,
      style: "width: 100%",
      options: enabledSources.value.map((s) => ({
        label: `${s.name}（${s.protocol}${s.host ? " · " + s.host : ""}）`,
        value: s.id!,
      })),
    },
  },
  {
    key: "source_path",
    label: "源路径",
    type: "input",
    hidden: form.value.source_type !== "remote",
    props: { placeholder: "源文件/目录在存储源中的路径（对象存储填 Key）" },
  },
  {
    key: "local_file",
    label: "本地文件",
    hidden: form.value.source_type === "remote" /* #local_file 插槽接管 */,
  },
  { key: "targets", label: "目标" /* #targets 插槽接管 */ },
]);

function timeStamp(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}

function openCreate() {
  form.value.name = `传输_${timeStamp()}`;
  form.value.task_type = "parallel";
  form.value.source_type = "remote";
  form.value.source_id = null;
  form.value.source_path = "";
  form.value.local_file = null;
  form.value.targets = [{ target_id: null, target_path: "" }];
  selectedFlowId.value = null;
  createVisible.value = true;
}

function addTarget() {
  form.value.targets.push({ target_id: null, target_path: "" });
}
function removeTarget(idx: number) {
  form.value.targets.splice(idx, 1);
  formRef.value?.validateField("targets").catch(() => {});
}
function onFileChange(file: { raw?: File }) {
  if (!file.raw) return;
  form.value.local_file = file.raw;
  formRef.value?.validateField("local_file").catch(() => {});
}
function onFileRemove() {
  form.value.local_file = null;
}
function onExceed() {
  ElMessage.warning("仅支持选择一个文件");
}

const validateTargets: NonNullable<FormItemRule["validator"]> = (_rule, _value, callback) => {
  if (!form.value.targets.length) {
    callback(new Error("请至少添加一个目标存储源"));
    return;
  }
  for (const t of form.value.targets) {
    if (!t.target_id) {
      callback(new Error("请选择目标存储源"));
      return;
    }
    if (!t.target_path.trim()) {
      callback(new Error("请填写目标路径"));
      return;
    }
  }
  callback();
};

const formRules = computed<FormRules>(() => {
  const rules: FormRules = {
    name: [{ required: true, message: "请填写任务名称", trigger: "blur" }],
    targets: [
      { required: true, message: "请至少添加一个目标存储源", trigger: "change" },
      { validator: validateTargets, trigger: "change" },
    ],
  };
  if (form.value.source_type === "remote") {
    rules.source_id = [{ required: true, message: "请选择源存储源", trigger: "change" }];
    rules.source_path = [{ required: true, message: "请填写源路径", trigger: "blur" }];
  } else {
    rules.local_file = [{ required: true, message: "请选择本地文件", trigger: "change" }];
  }
  return rules;
});

/** 链式预览：源 → 目标1 → 目标2 … */
const flowPreview = computed(() => {
  const parts: string[] = [];
  parts.push(form.value.source_type === "remote" ? sourceName(form.value.source_id) : "本地文件");
  form.value.targets.forEach((t) => parts.push(t.target_id ? sourceName(t.target_id) : "目标"));
  return parts.join(" → ");
});

async function submit() {
  try {
    // 提交前先整体校验：目标存储源与目标路径必填（选择流程带入的空目标路径也会被拦截提示）
    await formRef.value?.validate();
  } catch {
    return; // 校验未通过，错误提示由表单字段展示
  }
  submitting.value = true;
  try {
    const targets = form.value.targets.map((t) => ({
      target_id: t.target_id!,
      target_path: t.target_path.trim(),
    }));
    if (form.value.source_type === "remote") {
      await TransferAPI.createTask({
        name: form.value.name.trim(),
        task_type: form.value.task_type,
        source_type: "remote",
        source_id: form.value.source_id!,
        source_path: form.value.source_path.trim(),
        targets,
      });
    } else {
      const fd = new FormData();
      fd.append("file", form.value.local_file!);
      fd.append("name", form.value.name.trim());
      fd.append("task_type", form.value.task_type);
      fd.append("targets", JSON.stringify(targets));
      await TransferAPI.createLocalTask(fd);
    }
    createVisible.value = false;
    page.value = 1;
    await loadTasks();
  } finally {
    submitting.value = false;
  }
}

// ── 取消 / 删除 ───────────────────────────────────────────────────────
async function cancelTask(row: TransferTaskItem) {
  if (!row.id) return;
  try {
    await ElMessageBox.confirm(`确认取消任务「${row.name}」？`, "提示", { type: "warning" });
  } catch {
    return;
  }
  await TransferAPI.cancelTask(row.id);
  await loadTasks();
}
async function removeTask(row: TransferTaskItem) {
  if (!row.id) return;
  try {
    await ElMessageBox.confirm(`确认删除任务「${row.name}」？`, "提示", { type: "warning" });
  } catch {
    return;
  }
  await TransferAPI.deleteTask([row.id]);
  await loadTasks();
}

// ── 任务详情 ──────────────────────────────────────────────────────────
const detailVisible = ref(false);
const detailRow = ref<TransferTaskItem | null>(null);
const detailSteps = computed(() => detailRow.value?.steps || []);
/** FaDescriptions 数据源：TransferTaskItem 无索引签名，转为 Record 供组件读取 */
const detailRowData = computed<Record<string, unknown> | null>(() =>
  detailRow.value ? (detailRow.value as unknown as Record<string, unknown>) : null
);
/** 详情字段：类型/状态用 tag 渲染，其余格式化字段走具名插槽 */
const transferDetailItems: DescriptionsItem[] = [
  { label: "任务名称", prop: "name", slot: "name" },
  {
    label: "类型",
    prop: "task_type",
    tag: {
      map: {
        chain: { type: "warning", text: "链式" },
        parallel: { type: "primary", text: "多目标" },
      },
    },
  },
  { label: "来源", prop: "source", slot: "source" },
  {
    label: "状态",
    prop: "status",
    tag: {
      map: {
        pending: { type: "info", text: "等待中" },
        running: { type: "warning", text: "传输中" },
        success: { type: "success", text: "成功" },
        failed: { type: "danger", text: "失败" },
        canceled: { type: "info", text: "已取消" },
      },
    },
  },
  { label: "总大小", prop: "total_size", slot: "total_size" },
  { label: "实时速度", prop: "speed", slot: "speed" },
  { label: "开始时间", prop: "started_at", slot: "started_at" },
  { label: "结束时间", prop: "finished_at", slot: "finished_at" },
];
async function openDetail(row: TransferTaskItem) {
  detailRow.value = row;
  detailVisible.value = true;
  if (!row.id) return;
  const { data } = await TransferAPI.detailTask(row.id);
  detailRow.value = data.data;
}

// ── SSE 实时进度（按需连接：仅存在进行中任务时保持连接，全部终态即断开） ──
const sseConnected = ref(false);
let transferStream: TransferStream | null = null;

const hasActiveTask = computed(() =>
  tasks.value.some((t) => t.status === "pending" || t.status === "running")
);

/** 连接生命周期跟随任务列表：有 pending/running 任务才连；全部终态即断开（终态前服务端已推过一次收尾帧） */
function syncStream() {
  if (!transferStream) return;
  if (hasActiveTask.value) transferStream.connect();
  else transferStream.disconnect();
}

function onMessage(msg: TransferPushMessage) {
  if (msg.type !== "task_update") return;
  const item = msg.data;
  const idx = tasks.value.findIndex((t) => t.id === item.id);
  if (idx >= 0) {
    tasks.value[idx] = item;
  } else {
    loadTasks();
  }
  // 详情对话框随 WS 实时刷新（无需关闭重开）
  if (detailVisible.value && detailRow.value?.id === item.id) {
    detailRow.value = item;
  }
  syncStream(); // 收到终态帧且无其他进行中任务时自动断开
}
function onStatus(connected: boolean) {
  sseConnected.value = connected;
}

onMounted(() => {
  loadSources();
  loadFlows();
  loadTasks(); // 末尾 syncStream 决定是否连接
  transferStream = new TransferStream({ onMessage, onStatus });
});
onUnmounted(() => {
  transferStream?.disconnect();
  transferStream = null;
});
</script>
