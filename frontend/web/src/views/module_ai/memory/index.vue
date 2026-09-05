<!-- AI 会话记录：Art + useTable -->
<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="memorySearchItems"
      :rules="searchBarRules"
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
        @refresh="refreshData"
      >
        <template #left>
          <FaTableHeaderLeft
            :remove-ids="selectedIds"
            :perm-create="['module_ai:chat:create']"
            :perm-delete="['module_ai:chat:delete']"
            :delete-loading="batchDeleting"
            :create-loading="createLoading"
            @add="handleAdd"
            @delete="handleBatchDelete"
          />
        </template>
      </FaTableHeader>

      <FaTable
        ref="faTableRef"
        row-key="id"
        :loading="loading"
        :data="data"
        :columns="columns"
        :pagination="pagination"
        @selection-change="onTableSelectionChange"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      >
        <template #memory-title="{ row }">
          <ElInput
            v-if="editingRowId === row.id"
            ref="titleInputRef"
            v-model="editingTitle"
            size="small"
            @blur="handleSaveTitle(row)"
            @keyup.enter="handleSaveTitle(row)"
          />
          <ElTooltip v-else content="点击编辑" placement="top">
            <span class="editable-cell" @click="handleEditTitle(row)">
              {{ row.title || "未命名会话" }}
              <ElIcon class="edit-icon"><Edit /></ElIcon>
            </span>
          </ElTooltip>
        </template>
      </FaTable>
    </ElCard>

    <FaDialog
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      width="920px"
      dialog-class="session-detail-dialog"
      modal-class="session-detail-dialog"
      :form-mode="dialogVisible.type"
      :confirm-loading="submitLoading"
      @cancel="handleCloseDialog"
      @close="handleCloseDialog"
      @confirm="handleSubmit()"
    >
      <template v-if="dialogVisible.type === 'detail'">
        <ElScrollbar max-height="70vh" :view-style="{ overflowX: 'hidden' }">
          <FaDescriptions
            :column="4"
            :data="detailFormData"
            :items="memoryDetailItems"
            :scrollbar="false"
          >
            <template #metadata="{ row }">
              <pre v-if="row?.metadata">{{ JSON.stringify(row?.metadata, null, 2) }}</pre>
              <span v-else>无</span>
            </template>
          </FaDescriptions>

          <ElDivider content-position="left">消息记录</ElDivider>
          <ElTimeline v-if="detailFormData.messages && detailFormData.messages.length > 0">
            <ElTimelineItem
              v-for="msg in detailFormData.messages"
              :key="msg.id"
              :type="msg.role === 'user' ? 'primary' : 'success'"
              :icon="msg.role === 'user' ? 'User' : 'ChatDotRound'"
            >
              <div class="message-item">
                <div class="message-header">
                  <ElTag size="small" :type="msg.role === 'user' ? 'primary' : 'success'">
                    {{ msg.role === "user" ? "用户" : "助手" }}
                  </ElTag>
                  <span v-if="msg.created_at" class="message-time">
                    {{ formatMsgTime(msg.created_at) }}
                  </span>
                </div>
                <div class="message-content">{{ msg.content }}</div>
              </div>
            </ElTimelineItem>
          </ElTimeline>
          <ElEmpty v-else description="暂无消息记录" :image-size="60" />
        </ElScrollbar>
      </template>
      <template v-else>
        <FaForm
          :key="memoryFormRenderKey"
          ref="dataFormRef"
          v-model="formData"
          :items="memoryDialogFormItems"
          :rules="rules"
          label-suffix=":"
          :label-width="100"
          label-position="right"
          :span="24"
          :gutter="16"
          :show-reset="false"
          :show-submit="false"
          class="crud-dialog-art-form"
        />
      </template>
    </FaDialog>
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: "ChatSession",
  inheritAttrs: false,
});

import { Edit } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import AiChatAPI, { type ChatSession, type ChatSessionDetail } from "@/api/module_ai/chat";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import type FaForm from "@/components/forms/fa-form/index.vue";
import { formatToDateTime, renderTableOperationCell, type TableOperationAction } from "@utils";
import type { ColumnOption } from "@/types/component";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import FaTable from "@/components/tables/fa-table/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";

type MemorySearchForm = {
  title?: string;
  created_at?: string[];
  updated_at?: string[];
};

function buildMemoryReplaceParams(u: MemorySearchForm): Record<string, unknown> {
  return {
    title: u.title,
    created_at: Array.isArray(u.created_at) && u.created_at.length === 2 ? u.created_at : undefined,
    updated_at: Array.isArray(u.updated_at) && u.updated_at.length === 2 ? u.updated_at : undefined,
  };
}

const searchForm = ref<MemorySearchForm>({
  title: undefined,
  created_at: undefined,
  updated_at: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const searchBarRules: Record<string, unknown> = {};

const memorySearchItems = computed<SearchFormItem[]>(() => [
  {
    label: "会话标题",
    key: "title",
    type: "input",
    placeholder: "请输入标题",
    clearable: true,
    span: 6,
  },
]);

const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const submitLoading = ref(false);
const memoryFormRenderKey = ref(0);

const memoryDialogFormItems = computed<FormItem[]>(() => [
  {
    label: "标题",
    key: "title",
    type: "input",
    span: 24,
    props: { placeholder: "请输入标题", maxlength: 100 },
  },
]);
const titleInputRef = ref();
const editingRowId = ref<string | null>(null);
const editingTitle = ref("");

const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);
const { selectedRows, selectedIds, batchDeleting, onTableSelectionChange } =
  useTableSelection<ChatSession>();

const createLoading = ref(false);

async function deleteSessionRow(id: string, name: string) {
  try {
    await confirmDelete(`确定删除「${name}」吗？`);
    await AiChatAPI.deleteSession([id]);
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } catch {
    // 用户取消
  }
}

async function handleBatchDelete() {
  const ids = selectedIds.value;
  if (ids.length === 0) return;
  try {
    await confirmBatchDelete(
      ids.length,
      selectedRows.value.map((r) => (r as any)?.name ?? r?.title ?? r?.id)
    );
    batchDeleting.value = true;
    await AiChatAPI.deleteSession(ids as unknown as string[]);
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } catch {
    // 用户取消
  } finally {
    batchDeleting.value = false;
  }
}

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
  refreshCreate,
  refreshRemove,
} = useTable({
  core: {
    apiFn: AiChatAPI.getSessionList,
    apiParams: {
      page_no: 1,
      page_size: 10,
    },
    columnsFactory: (): ColumnOption<ChatSession>[] => [
      { type: "selection", width: 48, fixed: "left" },
      { type: "globalIndex", width: 56, label: "序号" },
      {
        prop: "session_id",
        label: "会话ID",
        minWidth: 180,
        showOverflowTooltip: true,
      },
      {
        prop: "title",
        label: "标题",
        minWidth: 200,
        useSlot: true,
        slotName: "memory-title",
      },
      {
        prop: "user_id",
        label: "用户ID",
        minWidth: 120,
        visible: false,
      },
      {
        prop: "team_id",
        label: "团队ID",
        minWidth: 120,
        visible: false,
      },
      {
        prop: "team_name",
        label: "部门名称",
        minWidth: 120,
        showOverflowTooltip: true,
      },
      {
        prop: "agent_id",
        label: "Agent ID",
        minWidth: 120,
        showOverflowTooltip: true,
        visible: false,
      },
      {
        prop: "summary",
        label: "会话摘要",
        minWidth: 200,
        showOverflowTooltip: true,
        visible: false,
      },
      {
        prop: "message_count",
        label: "消息数量",
        width: 100,
        align: "center",
      },
      {
        prop: "created_time",
        label: "创建时间",
        width: 168,
        sortable: true,
        showOverflowTooltip: true,
      },
      {
        prop: "updated_time",
        label: "更新时间",
        width: 168,
        sortable: true,
        showOverflowTooltip: true,
      },
      {
        prop: "operation",
        label: "操作",
        width: 160,
        fixed: "right",
        align: "center",
        formatter: (row: ChatSession) => formatMemoryOperationCell(row),
      },
    ],
  },
});

const formData = ref({
  id: undefined as string | undefined,
  title: "",
});

const { dialogVisible, closeDialog } = useCrudDialog();

const detailFormData = ref<Partial<ChatSessionDetail>>({});

const memoryDetailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] =
  [
    { label: "会话ID", prop: "session_id" },
    { label: "标题", prop: "title" },
    { label: "用户ID", prop: "user_id", span: 1 },
    { label: "团队ID", prop: "team_id", span: 1 },
    { label: "部门名称", prop: "team_name", span: 1 },
    { label: "Agent ID", prop: "agent_id", span: 1 },
    { label: "创建时间", prop: "created_time", span: 1 },
    { label: "更新时间", prop: "updated_time", span: 1 },
    { label: "消息数量", prop: "message_count", span: 1 },
    { label: "会话摘要", prop: "summary" },
    { label: "元数据", prop: "metadata", slot: "metadata" },
  ];

const rules = reactive({
  title: [{ required: true, message: "请输入标题", trigger: "blur" }],
});

const initialFormData = {
  id: undefined as string | undefined,
  title: "",
};

function formatMsgTime(timestamp: number | null): string {
  if (!timestamp) return "";
  return formatToDateTime(new Date(timestamp * 1000));
}

async function handleSearchBarSearch(params: MemorySearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildMemoryReplaceParams(params));
  getData();
}

async function onResetSearch() {
  searchForm.value = {
    title: undefined,
    created_at: undefined,
    updated_at: undefined,
  };
  await resetSearchParams();
}

async function resetForm() {
  dataFormRef.value?.resetFields();
  dataFormRef.value?.clearValidate();
  Object.assign(formData.value, initialFormData);
}

async function handleCloseDialog() {
  closeDialog();
  await resetForm();
}

async function handleAdd() {
  createLoading.value = true;
  try {
    await handleOpenDialog("create");
  } finally {
    createLoading.value = false;
  }
}

async function handleOpenMemoryDetail(id: string) {
  dialogVisible.title = "详情";
  dialogVisible.type = "detail";
  try {
    const response = await AiChatAPI.getSessionDetail(id);
    detailFormData.value = response.data.data ?? {};
    dialogVisible.visible = true;
  } catch {
    /* 已由全局拦截器提示 */
  }
}

async function handleOpenDialog(type: "create" | "detail", id?: string) {
  await resetForm();
  dialogVisible.type = type;
  if (id) {
    try {
      const response = await AiChatAPI.getSessionDetail(id);
      if (type === "detail") {
        dialogVisible.title = "详情";
        detailFormData.value = response.data.data ?? {};
      }
    } catch {
      /* 已由全局拦截器提示 */
      return;
    }
  } else {
    dialogVisible.title = "新增会话";
    formData.value.id = undefined;
  }
  memoryFormRenderKey.value += 1;
  dialogVisible.visible = true;
}

function buildMemoryRowActions(row: ChatSession): TableOperationAction[] {
  const all: TableOperationAction[] = [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_ai:chat:detail",
      run: () => {
        void handleOpenMemoryDetail(row.id);
      },
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      icon: "ri:delete-bin-4-line",
      perm: "module_ai:chat:delete",
      run: () => {
        deleteSessionRow(row.id, (row as any)?.name ?? row?.title ?? row?.id);
      },
    },
  ];
  return all;
}

function formatMemoryOperationCell(row: ChatSession) {
  return renderTableOperationCell(buildMemoryRowActions(row), {
    wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1 memory-table-actions",
  });
}

function handleEditTitle(row: ChatSession) {
  editingRowId.value = row.id;
  editingTitle.value = row.title || "";
  nextTick(() => {
    titleInputRef.value?.focus?.();
  });
}

async function handleSaveTitle(row: ChatSession) {
  if (editingRowId.value !== row.id) return;

  const newTitle = editingTitle.value.trim();
  if (!newTitle) {
    ElMessage.warning("标题不能为空");
    return;
  }

  if (newTitle === row.title) {
    editingRowId.value = null;
    return;
  }

  try {
    await AiChatAPI.updateSession(row.id, { title: newTitle });
    row.title = newTitle;
    editingRowId.value = null;
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error(error);
  }
}

async function handleSubmit() {
  const form = dataFormRef.value;
  if (!form) return;
  const valid = await (form.validate as () => Promise<boolean>)().catch(() => false);
  if (!valid) return;
  try {
    await AiChatAPI.createSession({ title: formData.value.title });
    dialogVisible.visible = false;
    await resetForm();
    await refreshCreate();
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error(error);
  }
}
</script>

<style lang="scss" scoped>
.edit-icon {
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}

.editable-cell {
  display: flex;
  gap: 8px;
  align-items: center;
  cursor: pointer;

  &:hover {
    color: var(--el-color-primary);

    .edit-icon {
      opacity: 1;
    }
  }
}

.message-item {
  .message-header {
    display: flex;
    gap: 8px;
    align-items: center;
    margin-bottom: 8px;
  }

  .message-time {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  .message-content {
    padding: 8px 12px;
    word-break: break-all;
    white-space: pre-wrap;
    background: var(--el-fill-color-light);
    border-radius: 4px;
  }
}

pre {
  max-height: 200px;
  padding: 8px;
  margin: 0;
  overflow: auto;
  font-size: 12px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
}

:deep(.session-detail-dialog .el-dialog__body) {
  max-height: 60vh;
  padding: 20px;
  overflow-y: auto;
}
</style>
