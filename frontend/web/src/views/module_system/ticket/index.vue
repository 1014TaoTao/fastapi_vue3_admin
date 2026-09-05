<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      v-model="searchForm"
      :items="ticketSearchItems"
      :is-expand="false"
      :show-expand="true"
      :show-reset="true"
      :show-search="true"
      :disabled-search="false"
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
        layout="search,refresh"
        @refresh="fetchData"
      >
        <template #left>
          <ElButton
            v-hasPerm="['module_system:ticket:create']"
            type="primary"
            @click="handleOpenDialog('create')"
          >
            <ElIcon><Plus /></ElIcon>
            提交工单
          </ElButton>
          <ElButton
            v-hasPerm="['module_system:ticket:delete']"
            v-if="selectedIds.length"
            type="danger"
            :loading="batchDeleting"
            @click="handleBatchDelete"
          >
            <ElIcon><Delete /></ElIcon>
            批量删除
          </ElButton>
        </template>
      </FaTableHeader>

      <FaCardGrid
        :items="data"
        :pagination="{ current: pageNo, size: pageSize, total }"
        :loading="loading"
        :lg="4"
        empty-text="暂无工单"
        @pagination:size-change="onPageSizeChange"
        @pagination:current-change="onPageCurrentChange"
      >
        <template #header="{ item }">
          <div class="flex items-center gap-2 min-w-0">
            <span
              class="flex shrink-0 items-center justify-center w-5 h-5 rounded text-[10px]"
              :class="typeIconClass(item.ticket_type!)"
            >
              <FaSvgIcon :icon="typeIcon(item.ticket_type!)" />
            </span>
            <span class="flex-1 truncate text-sm font-semibold">{{ item.title }}</span>
            <ElTag
              size="small"
              :type="statusTagType(String(item.status))"
              effect="dark"
              class="shrink-0"
            >
              {{ statusLabel(item.status ?? 0) }}
            </ElTag>
          </div>
        </template>

        <template #default="{ item }">
          <div class="flex flex-col cursor-pointer" @click="handleOpenDialog('detail', item.id!)">
            <div
              class="flex items-center gap-1.5 text-xs"
              style="color: var(--el-text-color-secondary)"
            >
              <FaSvgIcon icon="ri:user-3-line" class="shrink-0" />
              <span
                >{{ item.created_by?.name ?? "—" }} ·
                {{ item.created_time?.slice(0, 10) ?? "" }}</span
              >
            </div>
            <div class="flex items-center justify-between">
              <div
                class="flex items-center gap-1.5 text-xs"
                style="color: var(--el-text-color-secondary)"
              >
                <FaSvgIcon icon="ri:user-add-line" class="shrink-0" />
                <span>{{ item.assigned_by?.name ?? "未分配" }}</span>
              </div>
              <ElTag size="small" effect="light" :type="typeTag(item.ticket_type!)">
                {{ typeLabel(item.ticket_type!) }}
              </ElTag>
            </div>
          </div>
        </template>

        <template #footer="{ item }">
          <ElRow :gutter="6" @click.stop>
            <ElCol :span="8">
              <ElButton
                v-if="item.status! < 3"
                v-hasPerm="['module_system:ticket:update']"
                size="small"
                plain
                type="primary"
                class="w-full"
                @click="handleOpenDialog('update', item.id!)"
              >
                处理
              </ElButton>
            </ElCol>
            <ElCol :span="8">
              <ElButton
                v-if="item.status! < 3"
                v-hasPerm="['module_system:ticket:update']"
                size="small"
                plain
                type="warning"
                class="w-full"
                @click="closeTicket(item.id!)"
              >
                关闭
              </ElButton>
            </ElCol>
            <ElCol :span="8">
              <ElButton
                v-hasPerm="['module_system:ticket:delete']"
                size="small"
                plain
                type="danger"
                class="w-full"
                @click="deleteTicketRow(item.id!, item.title ?? '')"
              >
                删除
              </ElButton>
            </ElCol>
          </ElRow>
        </template>
      </FaCardGrid>
    </ElCard>

    <FaDialog
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      width="900px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      :form-mode="dialogVisible.type"
      :confirm-loading="submitLoading"
      @cancel="handleCloseDialog"
      @close="handleCloseDialog"
      @confirm="handleDialogConfirm"
    >
      <template v-if="dialogVisible.type === 'detail'">
        <ElScrollbar max-height="65vh">
          <FaDescriptions
            :column="4"
            :data="detailFormData"
            :items="ticketDetailItems"
            label-width="120px"
          >
            <template #ticket_type="{ row }">
              <FaStatusTag
                :type="typeTag(row?.ticket_type as string)"
                :label="typeLabel(row?.ticket_type as string)"
              />
            </template>
            <template #status="{ row }">
              <FaStatusTag
                :type="statusTagType(String(row?.status ?? 0))"
                :label="statusLabel(Number(row?.status ?? 0))"
              />
            </template>
            <template #ticket_content>
              <ElScrollbar
                class="box-border min-h-30 max-h-[min(360px,45vh)] bg-(--el-bg-color) border border-(--el-border-color-lighter) rounded-[calc(var(--custom-radius)/3+2px)]"
                view-class="p-3"
              >
                <template v-if="detailHasRenderableContent">
                  <div v-html="detailContentHtml" />
                </template>
                <p v-else class="m-0 text-sm text-(--el-text-color-placeholder)">暂无内容</p>
              </ElScrollbar>
            </template>
            <template #reply_content>
              <ElScrollbar
                v-if="detailFormData.reply"
                class="box-border min-h-30h-[min(360px,45vh)] bg-(--el-bg-color) border border-(--el-border-color-lighter) rounded-[calc(var(--custom-radius)/3+2px)]"
                view-class="p-3"
              >
                <div v-html="sanitizedReply" />
              </ElScrollbar>
              <p v-else class="m-0 text-sm text-(--el-text-color-placeholder)">暂无回复</p>
            </template>
          </FaDescriptions>

          <!-- ── 评论区 ── -->
          <ElDivider content-position="left">
            <span
              class="inline-flex items-center text-sm font-semibold text-(--el-text-color-primary)"
            >
              <FaSvgIcon icon="ri:chat-3-line" class="mr-1.5" />
              评论（{{ commentsTotal }}）
            </span>
          </ElDivider>
          <div class="flex flex-col gap-3">
            <ElScrollbar class="px-1">
              <div v-if="commentsLoading" class="py-3">
                <ElSkeleton :rows="2" animated />
              </div>
              <template v-else-if="comments.length">
                <div
                  v-for="c in comments"
                  :key="c.id"
                  class="flex gap-3 py-3 border-b border-(--el-border-color-lighter) last:border-b-0"
                >
                  <div
                    class="flex shrink-0 items-center justify-center w-8 h-8 text-base text-(--el-color-primary) bg-(--el-color-primary-light-9) rounded-full"
                  >
                    <FaSvgIcon icon="ri:user-6-fill" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex gap-2 items-center mb-1.5">
                      <span class="text-sm font-semibold text-(--el-text-color-primary)">{{
                        c.created_by_name || c.created_by?.name || "匿名"
                      }}</span>
                      <span class="text-xs text-(--el-text-color-placeholder)">{{
                        c.created_time?.slice(0, 16) ?? ""
                      }}</span>
                    </div>
                    <div
                      class="text-sm leading-relaxed text-(--el-text-color-regular) wrap-break-word"
                      v-html="sanitizeComment(c.content)"
                    />
                  </div>
                </div>
              </template>
              <ElEmpty v-else description="暂无评论" :image-size="60" />
            </ElScrollbar>

            <!-- 提交评论 -->
            <div
              class="flex gap-3 items-start pt-2 border-t border-(--el-border-color-lighter) [&_.el-textarea]:flex-1 [&_.el-button]:shrink-0 [&_.el-button]:mt-0.5"
            >
              <ElInput
                v-model="commentInput"
                type="textarea"
                :rows="2"
                placeholder="输入评论内容..."
                :disabled="commentSubmitting"
                resize="none"
              />
              <ElButton
                type="primary"
                :loading="commentSubmitting"
                :disabled="!commentInput.trim()"
                @click="handleSubmitComment"
              >
                发表评论
              </ElButton>
            </div>
          </div>
        </ElScrollbar>
      </template>
      <template v-else>
        <FaForm
          v-if="dialogVisible.type === 'create'"
          :key="ticketFormRenderKey"
          scrollbar
          max-height="70vh"
          ref="dataFormRef"
          v-model="formData"
          :items="ticketDialogFormItems"
          :rules="rules"
          label-suffix=":"
          :label-width="100"
          label-position="right"
          :span="24"
          :gutter="16"
          :show-reset="false"
          :show-submit="false"
          class="crud-dialog-art-form"
        >
          <template #ticket_type>
            <ElSelect v-model="formData.ticket_type" placeholder="请选择工单类型">
              <ElOption label="💡 建议" value="suggestion" />
              <ElOption label="🐛 缺陷" value="bug" />
              <ElOption label="⚡ 优化" value="optimize" />
              <ElOption label="📋 其他" value="other" />
            </ElSelect>
          </template>
          <template #status>
            <ElRadioGroup v-model="formData.status">
              <ElRadio :value="0">待处理</ElRadio>
              <ElRadio :value="1">处理中</ElRadio>
              <ElRadio :value="2">已完成</ElRadio>
              <ElRadio :value="3">已关闭</ElRadio>
            </ElRadioGroup>
          </template>
          <template #assigned_id>
            <FaUserTableSelect
              :model-value="formData.assigned_id == null ? undefined : formData.assigned_id"
              @update:model-value="
                (v: number | undefined) => (formData.assigned_id = v ?? undefined)
              "
            />
          </template>
          <template #ticket_content>
            <FaWangEditor
              :model-value="formData.ticket_content ?? ''"
              height="min(18vh, 280px)"
              placeholder="请详细描述您的问题、建议或优化想法..."
              :exclude-keys="[]"
              @update:model-value="(v: string) => (formData.ticket_content = v)"
            />
          </template>
        </FaForm>

        <!-- 处理工单：展示工单信息 + 回复处理 -->
        <ElScrollbar v-else max-height="75vh" class="flex flex-col">
          <!-- 工单信息区 -->
          <div class="flex flex-col gap-3 py-1">
            <div class="flex gap-2.5 items-center">
              <ElTag :type="typeTag(formData.ticket_type!)" size="small" effect="plain">
                {{ typeLabel(formData.ticket_type!) }}
              </ElTag>
              <span class="text-base font-semibold text-(--el-text-color-primary)">{{
                formData.title
              }}</span>
            </div>
            <FaMarkdownRenderer
              :content="formData.ticket_content ?? ''"
              class="min-h-30 p-3 bg-(--el-fill-color-lighter) rounded-[calc(var(--custom-radius)/3+2px)]"
            />
          </div>

          <ElDivider />

          <!-- 处理区 -->
          <div class="flex flex-col gap-5 py-1">
            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-(--el-text-color-primary)">状态</label>
              <ElRadioGroup v-model="formData.status">
                <ElRadio :value="0">待处理</ElRadio>
                <ElRadio :value="1">处理中</ElRadio>
                <ElRadio :value="2">已完成</ElRadio>
                <ElRadio :value="3">已关闭</ElRadio>
              </ElRadioGroup>
            </div>
            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-(--el-text-color-primary)">回复内容</label>
              <FaWangEditor
                :model-value="formData.reply_content ?? ''"
                height="min(18vh, 280px)"
                placeholder="请输入回复内容..."
                :exclude-keys="[]"
                @update:model-value="(v: string) => (formData.reply_content = v)"
              />
            </div>
          </div>
        </ElScrollbar>
      </template>
    </FaDialog>
  </div>
</template>

<script setup lang="ts">
import { useCrudForm } from "@/hooks/core/useCrudForm";
import TicketAPI, {
  getTicketComments,
  createTicketComment,
  type TicketForm,
  type TicketPageQuery,
  type TicketTable,
  type TicketCommentTable,
} from "@/api/module_system/ticket";
import type { ColumnOption } from "@/types/component";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import {
  ElTag,
  ElButton,
  ElCard,
  ElRow,
  ElCol,
  ElSelect,
  ElOption,
  ElRadioGroup,
  ElRadio,
  ElScrollbar,
  ElDivider,
  ElInput,
  ElMessageBox,
} from "element-plus";
import { Plus, Delete } from "@element-plus/icons-vue";
import DOMPurify from "dompurify";
import FaForm from "@/components/forms/fa-form/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import FaCardGrid from "@/components/cards/fa-card-grid/index.vue";

defineOptions({
  name: "TicketCard",
  inheritAttrs: false,
});

// ─── 搜索表单 ───
type TicketSearchForm = {
  title?: string;
  ticket_type?: string;
  status?: number;
  created_id?: number;
  updated_id?: number;
  assigned_id?: number;
};

const searchForm = ref<TicketSearchForm>({
  title: "",
  ticket_type: "",
  status: undefined,
  created_id: undefined,
  updated_id: undefined,
  assigned_id: undefined,
});
const showSearchBar = ref(true);

const STATUS_OPTIONS = [
  { label: "待处理", value: 0 },
  { label: "处理中", value: 1 },
  { label: "已完成", value: 2 },
  { label: "已关闭", value: 3 },
] as const;

const TICKET_TYPE_OPTIONS = [
  { label: "💡 建议", value: "suggestion" },
  { label: "🐛 缺陷", value: "bug" },
  { label: "⚡ 优化", value: "optimize" },
  { label: "📋 其他", value: "other" },
] as const;

const ticketSearchItems = computed<SearchFormItem[]>(() => [
  {
    label: "工单标题",
    key: "title",
    type: "input",
    placeholder: "请输入工单标题",
    clearable: true,
    span: 6,
  },
  {
    label: "工单类型",
    key: "ticket_type",
    type: "select",
    props: {
      placeholder: "请选择类型",
      options: TICKET_TYPE_OPTIONS,
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
  {
    label: "处理人",
    key: "assigned_id",
    type: "input",
    span: 6,
  },
]);

// ─── 数据管理 ───
const data = ref<TicketTable[]>([]);
const loading = ref(false);
const pageNo = ref(1);
const pageSize = ref(12);
const total = ref(0);

function normalizeTicketQuery(params: Record<string, unknown>): TicketPageQuery {
  const r: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") {
      r[k] = v;
    }
  }
  return r as unknown as TicketPageQuery;
}

async function fetchData() {
  loading.value = true;
  try {
    const res = await TicketAPI.listTicket({
      ...normalizeTicketQuery(searchForm.value as unknown as Record<string, unknown>),
      page_no: pageNo.value,
      page_size: pageSize.value,
    });
    const result = res.data?.data;
    data.value = (result?.items as TicketTable[]) || [];
    total.value = result?.total || 0;
  } catch {
    // ignore
  } finally {
    loading.value = false;
  }
}

function onPageSizeChange(size: number) {
  pageSize.value = size;
  pageNo.value = 1;
  fetchData();
}

function onPageCurrentChange(page: number) {
  pageNo.value = page;
  fetchData();
}

const columnChecks = ref<ColumnOption[]>([]);

async function handleSearchBarSearch(params: Record<string, unknown>) {
  searchForm.value = {
    title: (params.title as string) ?? "",
    ticket_type: (params.ticket_type as string) ?? "",
    status: params.status !== undefined ? Number(params.status) : undefined,
    created_id: params.created_id as number | undefined,
    updated_id: params.updated_id as number | undefined,
    assigned_id: params.assigned_id as number | undefined,
  };
  pageNo.value = 1;
  await fetchData();
}

async function onResetSearch() {
  searchForm.value = {
    title: "",
    ticket_type: "",
    status: undefined,
    created_id: undefined,
    updated_id: undefined,
    assigned_id: undefined,
  };
  pageNo.value = 1;
  await fetchData();
}

// ─── 类型/状态辅助 ───
const TYPE_ICONS: Record<string, string> = {
  suggestion: "ri:lightbulb-line",
  bug: "ri:bug-line",
  optimize: "ri:rocket-line",
  other: "ri:file-list-3-line",
};

const TYPE_ICON_CLASSES: Record<string, string> = {
  suggestion: "text-(--el-color-warning) bg-(--el-color-warning-light-9)",
  bug: "text-(--el-color-danger) bg-(--el-color-danger-light-9)",
  optimize: "text-(--el-color-success) bg-(--el-color-success-light-9)",
  other: "text-(--el-color-info) bg-(--el-color-info-light-9)",
};

function typeIcon(t: string) {
  return TYPE_ICONS[t] || TYPE_ICONS.other;
}

function typeIconClass(t: string) {
  return TYPE_ICON_CLASSES[t] || TYPE_ICON_CLASSES.other;
}

const TYPE_MAP: Record<string, string> = {
  suggestion: "建议",
  bug: "缺陷",
  optimize: "优化",
  other: "其他",
};

const STATUS_MAP: Record<number, string> = {
  0: "待处理",
  1: "处理中",
  2: "已完成",
  3: "已关闭",
};

function typeLabel(t: string) {
  return TYPE_MAP[t] || t || "其他";
}
function statusLabel(s: number) {
  return STATUS_MAP[s] || String(s);
}
function typeTag(t: string): any {
  return { suggestion: "success", bug: "danger", optimize: "warning", other: "info" }[t] || "info";
}
function statusTagType(s: string): "warning" | "info" | "success" | "danger" | undefined {
  const map: Record<number, "warning" | "info" | "success" | "danger"> = {
    0: "warning",
    1: "info",
    2: "success",
    3: "info",
  };
  return map[Number(s)];
}

// ─── 多选 ───
const selectedIds = ref<number[]>([]);
const batchDeleting = ref(false);

// ─── 对话框 ───
const { dialogVisible } = useCrudDialog();

const detailFormData = ref<TicketTable & { reply_content?: string }>(
  {} as TicketTable & { reply_content?: string }
);

const ticketDetailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] =
  [
    { label: "工单标题", prop: "title", span: 4 },
    { label: "工单类型", prop: "ticket_type", slot: "ticket_type" },
    { label: "状态", prop: "status", slot: "status" },
    { label: "处理人", prop: "assigned_by.name" },
    { label: "描述", prop: "description", span: 4 },
    { label: "详细内容", prop: "ticket_content", slot: "ticket_content", span: 4 },
    { label: "回复内容", prop: "reply", slot: "reply_content", span: 4 },
    { label: "创建人", prop: "created_by.name" },
    { label: "更新人", prop: "updated_by.name" },
    { label: "创建时间", prop: "created_time" },
    { label: "更新时间", prop: "updated_time" },
  ];

const detailContentHtml = computed({
  get: () => DOMPurify.sanitize(detailFormData.value.ticket_content ?? ""),
  set: (v: string) => {
    detailFormData.value.ticket_content = v;
  },
});

const sanitizedReply = computed(() => {
  const raw = detailFormData.value.reply ?? "";
  return raw ? DOMPurify.sanitize(raw) : "";
});

const detailHasRenderableContent = computed(() => {
  const raw = detailFormData.value.ticket_content ?? "";
  if (!raw.trim()) return false;
  const plain = raw
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return plain.length > 0;
});

const formData = ref<TicketForm & { reply_content?: string }>({
  id: undefined,
  title: "",
  ticket_type: "suggestion",
  ticket_content: "",
  status: 0,
  description: undefined,
  assigned_id: undefined,
  reply_content: undefined,
});

const rules = reactive({
  title: [{ required: true, message: "请输入工单标题", trigger: "blur" }],
  ticket_type: [{ required: true, message: "请选择工单类型", trigger: "blur" }],
  ticket_content: [{ required: true, message: "请输入工单内容", trigger: "blur" }],
  status: [{ required: true, message: "请选择状态", trigger: "blur" }],
});

const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const ticketFormRenderKey = ref(0);

const initialFormData: TicketForm & { reply_content?: string } = {
  id: undefined,
  title: "",
  ticket_type: "suggestion",
  ticket_content: "",
  status: 0,
  description: undefined,
  assigned_id: undefined,
  reply_content: undefined,
};

const {
  submitLoading,
  handleCloseDialog,
  handleOpenDialog,
  handleSubmit: crudHandleSubmit,
} = useCrudForm<TicketForm & { reply_content?: string }>({
  formData,
  initialFormData,
  dialogVisible,
  dataFormRef,
  formRenderKey: ticketFormRenderKey,
  detailApi: TicketAPI.detailTicket,
  createApi: TicketAPI.createTicket,
  updateApi: TicketAPI.updateTicket,
  titles: { create: "提交工单", update: "处理工单", detail: "工单详情" },
  detailFormData,
  onCreateSuccess: async () => {
    await fetchData();
  },
  onUpdateSuccess: async () => {
    await fetchData();
  },
  onSubmitSuccess: async () => {
    await fetchData();
  },
});

/** 对话框确认：创建走 crudHandleSubmit（含表单校验），处理直接调 API */
async function handleDialogConfirm() {
  if (dialogVisible.type === "create") {
    await crudHandleSubmit();
    return;
  }
  if (dialogVisible.type !== "update") {
    handleCloseDialog();
    return;
  }
  const id = formData.value.id;
  if (!id) return;
  submitLoading.value = true;
  try {
    const payload: Record<string, unknown> = {};
    if (formData.value.status !== undefined) payload.status = formData.value.status;
    if (formData.value.reply_content?.trim()) {
      payload.reply_content = formData.value.reply_content.trim();
    }
    await TicketAPI.updateTicket(id, payload);
    await fetchData();
    handleCloseDialog();
  } catch {
    // 接口错误由全局拦截器处理
  } finally {
    submitLoading.value = false;
  }
}

const ticketDialogFormItems = computed<FormItem[]>(() => [
  {
    label: "工单标题",
    key: "title",
    type: "input",
    span: 24,
    props: { placeholder: "请输入工单标题", maxlength: 200 },
  },
  {
    label: "工单类型",
    key: "ticket_type",
    type: "select",
    span: 12,
    props: { placeholder: "请选择类型", clearable: true },
  },
  {
    label: "处理人",
    key: "assigned_id",
    type: "input",
    span: 12,
    placeholder: "",
  },
  { key: "status", label: "状态", type: "radiogroup", span: 24 },
  {
    label: "详细描述",
    key: "ticket_content",
    type: "input",
    span: 24,
    placeholder: "",
  },
]);

// ─── 操作 ───
async function deleteTicketRow(id: number, name: string) {
  try {
    await confirmDelete(`确定删除「${name}」吗？`);
    await TicketAPI.deleteTicket([id]);
    await fetchData();
  } catch {
    // 用户取消
  }
}

async function closeTicket(id: number) {
  try {
    await ElMessageBox.confirm("确认关闭该工单?", "警告", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    await TicketAPI.updateTicket(id, { status: 3 });
    await fetchData();
  } catch {
    /* 用户取消或接口错误已由拦截器提示 */
  }
}

async function handleBatchDelete() {
  const ids = selectedIds.value;
  if (ids.length === 0) return;
  try {
    await confirmBatchDelete(
      ids.length,
      data.value.filter((r) => ids.includes(r.id!)).map((r) => String(r.title ?? r.id))
    );
    batchDeleting.value = true;
    selectedIds.value = [];
    await TicketAPI.deleteTicket(ids);
    await fetchData();
  } catch {
    // 用户取消
  } finally {
    batchDeleting.value = false;
  }
}

onMounted(() => {
  fetchData();
});

// ─── 评论 ───
const comments = ref<TicketCommentTable[]>([]);
const commentsTotal = ref(0);
const commentsLoading = ref(false);
const commentInput = ref("");
const commentSubmitting = ref(false);

// 打开详情时自动加载评论
watch(
  () => detailFormData.value.id,
  (newId) => {
    if (newId && dialogVisible.visible && dialogVisible.type === "detail") {
      loadComments(newId);
    }
  }
);

async function loadComments(ticketId: number) {
  commentsLoading.value = true;
  try {
    const res = await getTicketComments(ticketId, { page_no: 1, page_size: 50 });
    const result = res.data?.data;
    comments.value = (result?.items as TicketCommentTable[]) || [];
    commentsTotal.value = result?.total || 0;
  } catch {
    // ignore
  } finally {
    commentsLoading.value = false;
  }
}

function sanitizeComment(html: string): string {
  return DOMPurify.sanitize(html || "");
}

async function handleSubmitComment() {
  const tid = detailFormData.value.id;
  if (!tid || !commentInput.value.trim()) return;
  commentSubmitting.value = true;
  try {
    await createTicketComment(tid, { content: commentInput.value.trim() });
    commentInput.value = "";
    await loadComments(tid);
  } catch {
    // ignore
  } finally {
    commentSubmitting.value = false;
  }
}
</script>
