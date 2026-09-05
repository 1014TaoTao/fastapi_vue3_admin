<!-- 版本管理 CRUD -->
<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      v-model="searchForm"
      :items="versionBusinessSearchItems"
      :is-expand="false"
      :show-expand="true"
      :show-reset="true"
      :show-search="true"
      :disabled-search="false"
      :default-expanded="false"
      @search="handleSearch"
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
          <ElButton type="primary" @click="handleAdd">
            <ElIcon><Plus /></ElIcon>
            新增版本
          </ElButton>
        </template>
      </FaTableHeader>

      <FaTable
        ref="faTableRef"
        :loading="loading"
        :data="data"
        :columns="columns"
        :pagination="pagination"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      />
    </ElCard>

    <FaDialog
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      width="1100px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      :form-mode="dialogVisible.type"
      :confirm-loading="submitLoading"
      @cancel="handleCloseDialog"
      @close="handleCloseDialog"
      @confirm="handleSubmit()"
    >
      <template v-if="dialogVisible.type === 'detail'">
        <FaDescriptions
          :column="4"
          :data="detailFormData"
          :items="versionDetailItems"
          label-width="120px"
          max-height="70vh"
        >
          <template #status="{ row }">
            <ElTag :type="statusTagType(String(row?.status ?? 0))" effect="plain">
              {{ statusLabel(String(row?.status ?? 0)) }}
            </ElTag>
          </template>
          <template #content="{ row }">
            <FaMarkdownRenderer
              v-if="row?.content"
              :content="String(row.content)"
              height="auto"
              max-height="260px"
            />
            <span v-else class="text-g-400">—</span>
          </template>
        </FaDescriptions>
      </template>
      <template v-else>
        <FaForm
          :key="versionFormRenderKey"
          scrollbar
          max-height="70vh"
          ref="dataFormRef"
          v-model="formData"
          :items="versionDialogFormItems"
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
          <template #status>
            <ElSelect v-model="formData.status" placeholder="请选择状态">
              <ElOption :value="0" label="草稿" />
              <ElOption :value="1" label="已发布" />
              <ElOption :value="2" label="已回滚" />
            </ElSelect>
          </template>
          <template #content>
            <FaWangEditor
              ref="versionEditorRef"
              v-model="versionEditorHtml"
              height="300px"
              placeholder="请输入更新内容..."
            />
          </template>
        </FaForm>
      </template>
    </FaDialog>

    <!-- 状态变更弹窗 -->
    <ElDialog
      v-model="statusDialog.visible"
      :title="`变更状态 - ${statusDialog.version}`"
      width="380px"
      @close="statusDialog.visible = false"
    >
      <ElRadioGroup v-model="statusDialog.value">
        <ElRadio v-for="opt in STATUS_OPTIONS" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </ElRadio>
      </ElRadioGroup>
      <template #footer>
        <ElButton @click="statusDialog.visible = false">取消</ElButton>
        <ElButton type="primary" :loading="statusDialog.loading" @click="confirmChangeStatus">
          确定
        </ElButton>
      </template>
    </ElDialog>
  </div>
</template>

<script setup lang="ts">
import { renderTableOperationCell, resolveStatusColumns, type TableOperationAction } from "@utils";
import VersionAPI, { type VersionForm, type VersionTable } from "@/api/module_system/version";
import { Plus } from "@element-plus/icons-vue";
import type { AuditSearchFormParams } from "@/components/forms/fa-search-bar/auditSearchFormItems";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import type { ColumnOption } from "@/types/component";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import FaTable from "@/components/tables/fa-table/index.vue";
import FaDialog from "@/components/modal/fa-dialog/index.vue";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import FaForm from "@/components/forms/fa-form/index.vue";

defineOptions({
  name: "Version",
  inheritAttrs: false,
});

// ─── 常量 ───
const STATUS_OPTIONS = [
  { label: "草稿", value: 0 },
  { label: "已发布", value: 1 },
  { label: "已回滚", value: 2 },
] as const;

const STATUS_MAP: Record<string, string> = {
  "0": "草稿",
  "1": "已发布",
  "2": "已回滚",
};

function statusLabel(s: string) {
  return STATUS_MAP[s] || s;
}

function statusTagType(s: string): "info" | "success" | "danger" | undefined {
  return { "0": "info" as const, "1": "success" as const, "2": "danger" as const }[s];
}

const createInitialFormData = (): VersionForm => ({
  id: undefined,
  version: "",
  title: "",
  date: undefined,
  content: "",
  description: undefined,
  status: 0,
  sort: 1,
});

// ─── 搜索 ───
type VersionSearchFormParams = { status?: number } & AuditSearchFormParams;

const searchForm = ref<VersionSearchFormParams>({
  status: undefined,
});

/** 搜索区域默认展开展示 */
const showSearchBar = ref(true);

const versionBusinessSearchItems = computed(() => [
  {
    label: "发布状态",
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

// ─── 表格 ───
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
  refreshUpdate,
  refreshRemove,
} = useTable({
  core: {
    apiFn: VersionAPI.getVersionList,
    apiParams: { page_no: 1, page_size: 10, status: undefined },
    columnsFactory: resolveStatusColumns((): ColumnOption<VersionTable>[] => [
      { type: "globalIndex", width: 56, label: "序号" },
      { prop: "version", label: "版本号", minWidth: 80, showOverflowTooltip: true },
      { prop: "title", label: "标题", minWidth: 160, showOverflowTooltip: true },
      {
        prop: "status",
        label: "状态",
        width: 100,
        status: {
          0: { type: "info", text: "草稿" },
          1: { type: "success", text: "已发布" },
          2: { type: "danger", text: "已回滚" },
        },
      },
      { prop: "date", label: "发布日期", width: 120, showOverflowTooltip: true },
      { prop: "sort", label: "排序", width: 80 },
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
        width: 340,
        fixed: "right",
        align: "center",
        formatter: (row: VersionTable) => renderVersionOperationCell(row),
      },
    ]),
  },
});

const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);

function buildVersionRowActions(row: VersionTable): TableOperationAction[] {
  return [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_system:version:detail",
      run: () => void openDetailDialog(row),
    },
    {
      key: "edit",
      label: "编辑",
      artType: "edit",
      perm: "module_system:version:update",
      run: () => void openEditDialog("edit", row),
    },
    {
      key: "status",
      label: "变更状态",
      artType: "more",
      icon: "ri:swap-line",
      perm: "module_system:version:update",
      run: () => void handleChangeStatus(row),
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      perm: "module_system:version:delete",
      run: () => void deleteVersionRow(row),
    },
  ];
}

function renderVersionOperationCell(row: VersionTable) {
  return renderTableOperationCell(buildVersionRowActions(row), {
    wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1",
  });
}

// ─── 对话框 ───
const { dialogVisible } = useCrudDialog();

const detailFormData = ref<VersionTable>({});

const versionDetailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] =
  [
    { label: "标题", prop: "title" },
    { label: "版本号", prop: "version" },
    { label: "状态", prop: "status", slot: "status" },
    { label: "发布日期", prop: "date" },
    { label: "排序", prop: "sort" },
    { label: "备注", prop: "description" },
    { label: "更新内容", prop: "content", slot: "content", span: 4 },
    { label: "创建时间", prop: "created_time" },
    { label: "更新时间", prop: "updated_time" },
  ];

const versionDialogFormItems: FormItem[] = [
  {
    key: "version",
    label: "版本号",
    type: "input",
    span: 8,
    props: { placeholder: "请输入版本号", maxlength: 50 },
  },
  {
    key: "title",
    label: "标题",
    type: "input",
    span: 8,
    props: { placeholder: "请输入标题", maxlength: 200 },
  },
  {
    key: "date",
    label: "发布日期",
    type: "date",
    span: 8,
    props: { placeholder: "请选择日期", valueFormat: "YYYY-MM-DD" },
  },
  {
    key: "status",
    label: "状态",
    type: "select",
    span: 8,
    props: { placeholder: "请选择状态" },
  },
  {
    key: "sort",
    label: "排序",
    type: "number",
    span: 8,
    props: { controlsPosition: "right", min: 0, max: 9999 },
  },
  {
    key: "description",
    label: "备注",
    type: "input",
    span: 8,
    props: { type: "textarea", rows: 3, placeholder: "请输入备注" },
  },
  { key: "content", label: "更新内容", type: "input", span: 24 },
];

const formData = ref<VersionForm>(createInitialFormData());

const rules = reactive({
  version: [{ required: true, message: "请输入版本号", trigger: "blur" }],
  title: [{ required: true, message: "请输入标题", trigger: "blur" }],
  date: [{ required: true, message: "请选择发布日期", trigger: "change" }],
});

const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);

const submitLoading = ref(false);
const versionFormRenderKey = ref(0);

/** FaWangEditor */
const versionEditorRef = ref();
const versionEditorHtml = ref("");

// ─── 搜索事件 ───
const handleSearch = async (params: VersionSearchFormParams) => {
  replaceSearchParams({
    status: params.status ?? undefined,
  } as Record<string, unknown>);
  await getData();
};

const onResetSearch = async () => {
  searchForm.value = {
    status: undefined,
  };
  await resetSearchParams();
};

// ─── 对话框事件 ───
async function openDetailDialog(row: VersionTable) {
  if (!row.id) return;
  const response = await VersionAPI.getVersionDetail(row.id);
  dialogVisible.type = "detail";
  dialogVisible.title = "版本详情";
  detailFormData.value = response.data.data ?? { ...row };
  dialogVisible.visible = true;
}

async function handleAdd() {
  await openEditDialog("add");
}

async function openEditDialog(type: "add" | "edit", row?: VersionTable) {
  dialogVisible.type = type === "add" ? "create" : "update";
  if (type === "add") {
    dialogVisible.title = "新增版本";
    Object.assign(formData.value, createInitialFormData());
    versionEditorHtml.value = "";
    versionEditorRef.value?.clear();
    versionFormRenderKey.value += 1;
  } else if (row?.id) {
    dialogVisible.title = "编辑版本";
    versionFormRenderKey.value += 1;
    const response = await VersionAPI.getVersionDetail(row.id);
    const data = response.data.data ?? {};
    Object.assign(formData.value, data);
    versionEditorHtml.value = data.content ?? "";
    // 编辑器需要 nextTick 后 setHtml
    await nextTick();
    versionEditorRef.value?.setHtml(versionEditorHtml.value);
  }
  dialogVisible.visible = true;
}

async function resetForm() {
  if (dataFormRef.value) {
    dataFormRef.value.resetFields();
    dataFormRef.value.clearValidate();
  }
  Object.assign(formData.value, createInitialFormData());
}

async function handleCloseDialog() {
  dialogVisible.visible = false;
  await resetForm();
}

async function handleSubmit() {
  const form = dataFormRef.value;
  if (!form) return;
  const valid = await (form.validate as () => Promise<boolean>)().catch(() => false);
  if (!valid) return;
  // 同步富文本编辑器内容到表单
  formData.value.content = versionEditorHtml.value;
  const id = formData.value.id;
  try {
    if (id) {
      await VersionAPI.updateVersion(id, formData.value);
      await refreshUpdate();
    } else {
      await VersionAPI.createVersion(formData.value);
      await refreshCreate();
    }
    dialogVisible.visible = false;
    await resetForm();
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error(error);
  }
}

// ─── 删除事件 ───
const deleteVersionRow = async (row: VersionTable) => {
  if (!row.id) return;
  try {
    await confirmDelete(`确定删除版本「${row.version ?? row.id}」吗？此操作不可恢复！`);
    await VersionAPI.deleteVersion([row.id!]);
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } catch {
    // 用户取消
  }
};

// ─── 状态变更 ───
const statusDialog = reactive({
  visible: false,
  loading: false,
  version: "",
  id: 0,
  value: 0,
});

const handleChangeStatus = (row: VersionTable) => {
  statusDialog.version = row.version ?? "";
  statusDialog.id = row.id ?? 0;
  statusDialog.value = row.status ?? 0;
  statusDialog.visible = true;
};

const confirmChangeStatus = async () => {
  statusDialog.loading = true;
  try {
    await VersionAPI.setVersionStatus(statusDialog.id, { status: statusDialog.value });
    statusDialog.visible = false;
    await refreshUpdate();
  } catch {
    // 错误已由全局拦截器处理
  } finally {
    statusDialog.loading = false;
  }
};
</script>
