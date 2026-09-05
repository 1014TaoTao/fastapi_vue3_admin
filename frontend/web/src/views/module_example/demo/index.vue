<!-- 示例 CRUD：与角色页同一套 Fa 布局；弹窗与 Crud 一致（FaDialog + crud-embed-dialog） -->
<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="demoBusinessSearchItems"
      :rules="searchBarRules"
      :is-expand="false"
      :show-expand="true"
      :show-reset="true"
      :show-search="true"
      :disabled-search="false"
      :default-expanded="false"
      include-audit
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
          <FaTableHeaderLeft
            :remove-ids="selectedIds"
            :perm-create="['module_example:demo:create']"
            :perm-import="['module_example:demo:import']"
            :perm-export="['module_example:demo:export']"
            :perm-delete="['module_example:demo:delete']"
            :perm-patch="['module_example:demo:patch']"
            :delete-loading="batchDeleting"
            :create-loading="createLoading"
            :more-loading="moreLoading"
            @add="handleAdd"
            @import="openImport"
            @export="openExport"
            @delete="handleBatchDelete"
            @more="handleMoreClick"
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

    <FaDialog
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      width="920px"
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
          :items="demoDetailItems"
          max-height="70vh"
        >
          <template #json_val="{ row }">
            <FaJsonPretty v-if="row?.json_val != null" :value="row?.json_val" height="140px" />
          </template>
        </FaDescriptions>
      </template>
      <template v-else>
        <FaForm
          :key="demoFormRenderKey"
          scrollbar
          max-height="70vh"
          ref="dataFormRef"
          v-model="formData"
          :items="demoDialogFormItems"
          :rules="rules"
          label-suffix=":"
          :label-width="100"
          label-position="right"
          :span="12"
          :gutter="16"
          :show-reset="false"
          :show-submit="false"
          class="crud-dialog-art-form"
        >
          <template #json_val>
            <div class="flex flex-col gap-2">
              <div
                v-for="(item, index) in metadataList"
                :key="item.key"
                class="flex items-center gap-2"
              >
                <ElInput v-model="item.key" placeholder="键" />
                <ElInput v-model="item.value" placeholder="值" />
                <ElButton
                  type="primary"
                  :icon="Plus"
                  circle
                  @click="metadataList.push({ key: '', value: '' })"
                />
                <ElButton
                  type="danger"
                  :icon="Delete"
                  circle
                  @click="metadataList.splice(index, 1)"
                />
              </div>
              <ElButton
                v-if="metadataList.length === 0"
                type="primary"
                :icon="Plus"
                @click="metadataList.push({ key: '', value: '' })"
              >
                添加元数据
              </ElButton>
            </div>
          </template>
        </FaForm>
      </template>
    </FaDialog>

    <FaImportDialog
      v-model="importVisible"
      :content-config="demoImportContentConfig"
      default-template-file-name="demo_import_template.xlsx"
      @upload="handleCrudImportUpload"
    />

    <FaExportDialog
      v-model="exportVisible"
      :content-config="demoExportContentConfig"
      :query-params="exportQueryParams"
      :page-data="data"
      :selection-data="selectedRows"
    />
  </div>
</template>

<script setup lang="ts">
import { Plus, Delete } from "@element-plus/icons-vue";
import {
  renderTableOperationCell,
  resolveStatusColumns,
  stripPaginationParams,
  toCrudCols,
  type TableOperationAction,
} from "@utils";
import { useCrudForm } from "@/hooks/core/useCrudForm";
import { ResultEnum } from "@/enums/api/result.enum";
import type { IContentConfig, IObject } from "@/components/modal/types";
import type { AuditSearchFormParams } from "@/components/forms/fa-search-bar/auditSearchFormItems";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import DemoAPI, {
  type DemoForm,
  type DemoPageQuery,
  type DemoTable,
} from "@/api/module_example/demo";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import FaForm from "@/components/forms/fa-form/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";

defineOptions({
  name: "Demo",
  inheritAttrs: false,
});

// 常量定义
const STATUS_OPTIONS = [
  { label: "启用", value: 0 },
  { label: "停用", value: 1 },
] as const;

const createInitialFormData = (): DemoForm => ({
  id: undefined,
  name: "",
  status: 0,
  description: undefined,
  int_val: undefined,
  bigint_val: undefined,
  float_val: undefined,
  bool_val: true,
  date_val: undefined,
  time_val: undefined,
  datetime_val: undefined,
  text_val: undefined,
  json_val: undefined,
});

type DemoSearchFormParams = {
  name?: string;
  status?: number;
} & AuditSearchFormParams;

const searchForm = ref<DemoSearchFormParams>({
  name: undefined,
  status: undefined,
  created_id: undefined,
  updated_id: undefined,
  created_time: [],
  updated_time: [],
});

/** 搜索区域默认展开展示 */
const showSearchBar = ref(true);

const searchBarRef = ref<{ validate: () => Promise<boolean> } | null>(null);
const searchBarRules: Record<string, unknown> = {};

/** 名称、状态；创建人/更新人/时间由 FaSearchBar 的 includeAudit 属性追加 */
const demoBusinessSearchItems = computed(() => [
  {
    label: "名称",
    key: "name",
    type: "input",
    placeholder: "请输入名称",
    clearable: true,
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

const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);
const { selectedRows, selectedIds, batchDeleting, onTableSelectionChange } =
  useTableSelection<DemoTable>();

const createLoading = ref(false);
const moreLoading = ref(false);

const {
  columns,
  columnChecks,
  data,
  loading,
  pagination,
  searchParams,
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
    apiFn: DemoAPI.listDemo,
    apiParams: {
      page_no: 1,
      page_size: 10,
    },
    columnsFactory: resolveStatusColumns<DemoTable>(() => [
      { type: "selection", width: 48, fixed: "left" },
      { type: "globalIndex", width: 56, label: "序号" },
      { prop: "name", label: "名称", minWidth: 120, showOverflowTooltip: true },
      {
        prop: "status",
        label: "状态",
        width: 88,
        status: {
          0: { type: "success", text: "启用" },
          1: { type: "danger", text: "停用" },
        },
      },
      { prop: "int_val", label: "整数", minWidth: 88, showOverflowTooltip: true },
      { prop: "bigint_val", label: "大整数", minWidth: 100, showOverflowTooltip: true },
      { prop: "float_val", label: "浮点数", minWidth: 88, showOverflowTooltip: true },
      {
        prop: "bool_val",
        label: "布尔",
        width: 80,
        status: {
          true: { type: "success", text: "是" },
          false: { type: "danger", text: "否" },
        },
      },
      { prop: "date_val", label: "日期", minWidth: 112, showOverflowTooltip: true },
      { prop: "time_val", label: "时间", minWidth: 96, showOverflowTooltip: true },
      { prop: "datetime_val", label: "日期时间", minWidth: 168, showOverflowTooltip: true },
      { prop: "text_val", label: "长文本", minWidth: 120, showOverflowTooltip: true },
      { prop: "description", label: "描述", minWidth: 120, showOverflowTooltip: true },
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
        prop: "created_id",
        label: "创建人",
        minWidth: 100,
        formatter: (row: DemoTable) => row.created_by?.name ?? "—",
      },
      {
        prop: "updated_id",
        label: "更新人",
        minWidth: 100,
        formatter: (row: DemoTable) => row.updated_by?.name ?? "—",
      },
      {
        prop: "operation",
        label: "操作",
        width: 180,
        fixed: "right",
        align: "center",
        formatter: (row: DemoTable) => formatDemoOperationCell(row),
      },
    ]),
  },
});

/** 供 CrudImportModal / CrudExportModal 的列配置（与 CrudContent.cols 结构一致） */
const demoCrudCols = toCrudCols(columns);

const exportQueryParams = computed(() => {
  return stripPaginationParams(searchParams as Record<string, unknown>);
});

const demoImportContentConfig = computed<IContentConfig>(() => ({
  permPrefix: "module_example:demo",
  cols: demoCrudCols.value,
  indexAction: async () => ({}),
  importTemplate: () => DemoAPI.downloadTemplateDemo(),
}));

const demoExportContentConfig = computed(() => ({
  permPrefix: "module_example:demo",
  cols: demoCrudCols.value,
  exportsBlobAction: async (params: IObject) => {
    const merged = {
      ...(exportQueryParams.value as unknown as Record<string, unknown>),
      ...params,
    } as unknown as DemoPageQuery;
    const res = await DemoAPI.exportDemo(merged);
    return res.data as Blob;
  },
}));

const { dialogVisible } = useCrudDialog();

const detailFormData = ref<DemoTable>({});

const demoDetailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] =
  [
    { label: "名称", prop: "name" },
    { label: "UUID", prop: "uuid" },
    {
      label: "状态",
      prop: "status",
      tag: {
        map: { "0": { type: "success", text: "启用" }, "1": { type: "danger", text: "停用" } },
      },
    },
    { label: "整数", prop: "int_val" },
    { label: "大整数", prop: "bigint_val" },
    { label: "浮点数", prop: "float_val" },
    {
      label: "布尔值",
      prop: "bool_val",
      tag: {
        map: { true: { type: "success", text: "是" }, false: { type: "danger", text: "否" } },
      },
    },
    { label: "日期", prop: "date_val" },
    { label: "时间", prop: "time_val" },
    { label: "日期时间", prop: "datetime_val" },
    { label: "长文本", prop: "text_val" },
    { label: "元数据", prop: "json_val", slot: "json_val" },
    { label: "描述", prop: "description" },
    { label: "创建人", prop: "created_by.name" },
    { label: "更新人", prop: "updated_by.name" },
    { label: "创建时间", prop: "created_time" },
    { label: "更新时间", prop: "updated_time" },
  ];

// 示例页新增/编辑表单 —— 元数据字段用具名插槽渲染
const demoDialogFormItems: FormItem[] = [
  {
    key: "name",
    label: "名称",
    type: "input",
    props: { placeholder: "请输入名称", maxlength: 50 },
  },
  {
    key: "status",
    label: "状态",
    type: "radiogroup",
    props: {
      options: [
        { label: "启用", value: 0 },
        { label: "停用", value: 1 },
      ],
    },
  },
  { key: "int_val", label: "整数", type: "number", props: { placeholder: "请输入整数" } },
  { key: "bigint_val", label: "大整数", type: "number", props: { placeholder: "请输入大整数" } },
  {
    key: "float_val",
    label: "浮点数",
    type: "number",
    props: { placeholder: "请输入浮点数", step: 0.01, precision: 2 },
  },
  { key: "bool_val", label: "布尔值", type: "switch" },
  {
    key: "date_val",
    label: "日期",
    type: "date",
    props: { placeholder: "请选择日期", valueFormat: "YYYY-MM-DD", style: "width: 100%" },
  },
  {
    key: "time_val",
    label: "时间",
    type: "timepicker",
    props: { placeholder: "请选择时间", valueFormat: "HH:mm:ss", style: "width: 100%" },
  },
  {
    key: "datetime_val",
    label: "日期时间",
    type: "datetime",
    props: {
      placeholder: "请选择日期时间",
      valueFormat: "YYYY-MM-DD HH:mm:ss",
      style: "width: 100%",
    },
  },
  {
    key: "text_val",
    label: "长文本",
    type: "input",
    props: { type: "textarea", rows: 4, placeholder: "请输入长文本" },
  },
  {
    key: "description",
    label: "描述",
    type: "input",
    props: {
      type: "textarea",
      rows: 4,
      maxlength: 100,
      showWordLimit: true,
      placeholder: "请输入描述",
    },
  },
  { key: "json_val", label: "元数据", type: "input" /* 由 #json_val 插槽接管 */ },
];

const formData = ref<DemoForm>(createInitialFormData());

const rules = reactive({
  name: [{ required: true, message: "请输入名称", trigger: "blur" }],
  status: [{ required: true, message: "请选择状态", trigger: "blur" }],
});

const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const demoFormRenderKey = ref(0);
const metadataList = ref<{ key: string; value: string }[]>([]);

const crud = useCrudForm<DemoForm>({
  formData,
  initialFormData: createInitialFormData(),
  dialogVisible,
  dataFormRef,
  formRenderKey: demoFormRenderKey,
  detailApi: DemoAPI.detailDemo,
  createApi: DemoAPI.createDemo,
  updateApi: DemoAPI.updateDemo,
  titles: { create: "新增", update: "修改", detail: "详情" },
  detailFormData,
  onCreateSuccess: async () => {
    await refreshCreate();
  },
  onUpdateSuccess: async () => {
    await refreshUpdate();
  },
});

const { submitLoading } = crud;

/** json_val → metadataList（打开修改弹窗时回填） */
function syncJsonValToMetadataList(val: unknown) {
  if (val && typeof val === "object") {
    metadataList.value = Object.entries(val).map(([key, value]) => ({
      key,
      value: String(value),
    }));
  } else {
    metadataList.value = [];
  }
}

/** metadataList → json_val（提交前转换） */
function buildJsonValFromMetadataList(): Record<string, string> | undefined {
  const entries = metadataList.value.filter((item) => item.key.trim());
  if (entries.length === 0) return undefined;
  const obj: Record<string, string> = {};
  entries.forEach((item) => {
    obj[item.key.trim()] = item.value;
  });
  return obj;
}

async function handleOpenDialog(type: "create" | "update" | "detail", id?: number) {
  if (type === "create") {
    metadataList.value = [];
  }
  await crud.handleOpenDialog(type, id);
  if (type === "update") {
    syncJsonValToMetadataList(formData.value.json_val);
  }
}

async function handleCloseDialog() {
  metadataList.value = [];
  await crud.handleCloseDialog();
}

async function handleSubmit() {
  formData.value.json_val = buildJsonValFromMetadataList();
  await crud.handleSubmit();
}

const { importVisible, exportVisible, openImport, openExport } = useImportExport();

const handleSearch = async (params: DemoSearchFormParams) => {
  await searchBarRef.value?.validate();
  replaceSearchParams({
    name: params.name,
    status: params.status,
    created_id: params.created_id ?? undefined,
    updated_id: params.updated_id ?? undefined,
    created_time:
      Array.isArray(params.created_time) && params.created_time.length === 2
        ? params.created_time
        : undefined,
    updated_time:
      Array.isArray(params.updated_time) && params.updated_time.length === 2
        ? params.updated_time
        : undefined,
  } as Record<string, unknown>);
  await getData();
};

const onResetSearch = async () => {
  searchForm.value = {
    name: undefined,
    status: undefined,
    created_id: undefined,
    updated_id: undefined,
    created_time: [],
    updated_time: [],
  };
  await resetSearchParams();
};

function buildDemoRowActions(row: DemoTable): TableOperationAction[] {
  const all: TableOperationAction[] = [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_example:demo:detail",
      run: () => void handleOpenDialog("detail", row.id),
    },
    {
      key: "edit",
      label: "编辑",
      artType: "edit",
      icon: "ri:edit-2-line",
      perm: "module_example:demo:update",
      run: () => void handleOpenDialog("update", row.id),
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      icon: "ri:delete-bin-4-line",
      perm: "module_example:demo:delete",
      run: () => deleteDemoRow(row),
    },
  ];
  return all;
}

function formatDemoOperationCell(row: DemoTable) {
  return renderTableOperationCell(buildDemoRowActions(row), {
    wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1",
  });
}

async function handleAdd() {
  createLoading.value = true;
  try {
    await handleOpenDialog("create");
  } finally {
    createLoading.value = false;
  }
}

const deleteDemoRow = async (row: DemoTable) => {
  if (!row.id) return;
  try {
    await confirmDelete(`确定删除「${row.name ?? row.id}」吗？此操作不可恢复！`);
    await DemoAPI.deleteDemo([row.id!]);
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } catch {
    // 用户取消
  }
};

async function handleBatchDelete() {
  const ids = selectedIds.value;
  if (ids.length === 0) return;
  try {
    await confirmBatchDelete(
      ids.length,
      (data.value as DemoTable[])
        .filter((r) => ids.includes(r.id!))
        .map((r) => String(r.name ?? r.id))
    );
    batchDeleting.value = true;
    await DemoAPI.deleteDemo(ids);
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } catch {
    // 用户取消
  } finally {
    batchDeleting.value = false;
  }
}

async function handleMoreClick(value: "enable" | "disable") {
  const ids = selectedIds.value;
  if (ids.length === 0) {
    ElMessage.warning("请先在列表中勾选数据");
    return;
  }
  try {
    await confirmToggleStatus(value);
    moreLoading.value = true;
    const status = value === "enable" ? 0 : 1;
    await DemoAPI.batchDemo({ ids, status });
    // 成功 / 失败提示由 axios 拦截器统一处理
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshData();
  } catch {
    // 用户取消或操作失败
  } finally {
    moreLoading.value = false;
  }
}

async function handleCrudImportUpload(formData: FormData) {
  try {
    const res = await DemoAPI.importDemo(formData);
    if (res.data.code === ResultEnum.SUCCESS) {
      ElMessage.success(res.data.msg || "导入成功");
      importVisible.value = false;
      await refreshData();
    }
    // 非 SUCCESS 分支提示由 axios 拦截器统一处理
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error("[Import]", error);
    /* 接口错误已由拦截器提示 */
  }
}
</script>
