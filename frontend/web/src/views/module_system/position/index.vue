<!-- 岗位管理：FA + useTable；操作列前 3 个为 FaButtonTable，其余收入「更多」下拉 -->
<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="positionSearchItems"
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
            :perm-create="['module_system:position:create']"
            :perm-export="['module_system:position:export']"
            :perm-delete="['module_system:position:delete']"
            :perm-patch="['module_system:position:patch']"
            :delete-loading="batchDeleting"
            :create-loading="createLoading"
            :more-loading="moreLoading"
            @add="handleAdd"
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
      width="640px"
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
          :items="positionDetailItems"
          max-height="70vh"
        />
      </template>
      <template v-else>
        <FaForm
          scrollbar
          max-height="70vh"
          :key="positionFormRenderKey"
          ref="dataFormRef"
          v-model="formData"
          :items="positionDialogFormItems"
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
        </FaForm>
      </template>
    </FaDialog>

    <FaExportDialog
      v-model="exportVisible"
      :content-config="positionExportContentConfig"
      :query-params="exportQueryParams"
      :page-data="data"
      :selection-data="selectedRows"
    />
  </div>
</template>

<script setup lang="ts">
import PositionAPI, {
  type PositionForm,
  type PositionPageQuery,
  type PositionTable,
} from "@/api/module_system/position";
import { useUserStore } from "@stores";
import type { IObject } from "@/components/modal/types";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import FaForm from "@/components/forms/fa-form/index.vue";
import { ElMessage } from "element-plus";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import {
  renderTableOperationCell,
  resolveStatusColumns,
  stripPaginationParams,
  cleanEmptyArrayParams,
  toCrudCols,
  type TableOperationAction,
} from "@utils";

defineOptions({
  name: "Position",
  inheritAttrs: false,
});

const userStore = useUserStore();

type PositionSearchForm = {
  name?: string;
  status?: number;
  created_id?: number;
  updated_id?: number;
  created_time?: string[];
  updated_time?: string[];
};

function normalizePositionQuery(params: Record<string, unknown>): PositionPageQuery {
  return cleanEmptyArrayParams({ ...params }) as unknown as PositionPageQuery;
}

function buildPositionReplaceParams(p: PositionSearchForm): Record<string, unknown> {
  return {
    name: p.name,
    status: p.status,
    created_id: p.created_id,
    updated_id: p.updated_id,
    created_time:
      Array.isArray(p.created_time) && p.created_time.length === 2 ? p.created_time : undefined,
    updated_time:
      Array.isArray(p.updated_time) && p.updated_time.length === 2 ? p.updated_time : undefined,
  };
}

function buildPositionRowActions(
  row: PositionTable,
  ctx: {
    onDetail: (id: number) => void;
    onEdit: (id: number) => void;
    onDelete: (id: number, name: string) => void;
  }
): TableOperationAction[] {
  const all: TableOperationAction[] = [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_system:position:detail",
      run: () => ctx.onDetail(row.id!),
    },
    {
      key: "edit",
      label: "编辑",
      artType: "edit",
      perm: "module_system:position:update",
      run: () => ctx.onEdit(row.id!),
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      perm: "module_system:position:delete",
      run: () => ctx.onDelete(row.id!, row.name ?? ""),
    },
  ];
  return all;
}

function formatPositionOperationCell(
  row: PositionTable,
  ctx: Parameters<typeof buildPositionRowActions>[1]
) {
  return renderTableOperationCell(buildPositionRowActions(row, ctx), {
    wrapperClass:
      "inline-flex flex-wrap items-center justify-end gap-1 position-table-actions align-middle",
  });
}

const searchForm = ref<PositionSearchForm>({
  name: undefined,
  status: undefined,
  created_id: undefined,
  updated_id: undefined,
  created_time: undefined,
  updated_time: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const searchBarRules: Record<string, unknown> = {};

const STATUS_OPTIONS = [
  { label: "启用", value: 0 },
  { label: "停用", value: 1 },
] as const;

const positionSearchItems = computed<SearchFormItem[]>(() => [
  {
    label: "岗位名称",
    key: "name",
    type: "input",
    placeholder: "请输入岗位名称",
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
  useTableSelection<PositionTable>();

const createLoading = ref(false);
const moreLoading = ref(false);

const opCtx = {
  onDetail: (id: number) => void handleOpenDialog("detail", id),
  onEdit: (id: number) => void handleOpenDialog("update", id),
  onDelete: deletePositionRow,
};

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
    apiFn: PositionAPI.listPosition,
    apiParams: {
      page_no: 1,
      page_size: 10,
    },
    columnsFactory: resolveStatusColumns<PositionTable>(() => [
      { type: "selection", width: 48, fixed: "left" },
      { type: "globalIndex", width: 56, label: "序号" },
      { prop: "name", label: "岗位名称", minWidth: 100, showOverflowTooltip: true },
      {
        prop: "status",
        label: "状态",
        width: 88,
        status: {
          0: { type: "success", text: "启用" },
          1: { type: "danger", text: "停用" },
        },
      },
      { prop: "order", label: "岗位排序", width: 100, showOverflowTooltip: true },
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
        formatter: (row: PositionTable) => row.created_by?.name ?? "—",
      },
      {
        prop: "updated_id",
        label: "更新人",
        minWidth: 100,
        formatter: (row: PositionTable) => row.updated_by?.name ?? "—",
      },
      {
        prop: "operation",
        label: "操作",
        width: 200,
        fixed: "right",
        align: "center",
        formatter: (row: PositionTable) => formatPositionOperationCell(row, opCtx),
      },
    ]),
  },
});

const positionCrudCols = toCrudCols(columns);

const exportQueryParams = computed(() => {
  return normalizePositionQuery(stripPaginationParams(searchParams)) as unknown as Record<
    string,
    unknown
  >;
});

const positionExportContentConfig = computed(() => ({
  permPrefix: "module_system:position",
  cols: positionCrudCols.value,
  exportsBlobAction: async (params: IObject) => {
    const merged = normalizePositionQuery({
      ...(exportQueryParams.value as Record<string, unknown>),
      ...params,
    } as Record<string, unknown>);
    const res = await PositionAPI.exportPosition(merged as PositionPageQuery);
    return res.data as Blob;
  },
}));

const detailFormData = ref<PositionTable>({});

const positionDetailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] =
  [
    { label: "岗位名称", prop: "name" },
    { label: "排序", prop: "order" },
    {
      label: "状态",
      prop: "status",
      tag: {
        map: { 0: { type: "success", text: "启用" }, 1: { type: "danger", text: "停用" } },
      },
    },
    { label: "创建人", prop: "created_by.name" },
    { label: "更新人", prop: "updated_by.name" },
    { label: "创建时间", prop: "created_time" },
    { label: "更新时间", prop: "updated_time" },
    { label: "描述", prop: "description", span: 4 },
  ];

const formData = ref<PositionForm>({
  id: undefined,
  name: undefined,
  code: undefined,
  order: 1,
  status: 0,
  description: undefined,
});

const { dialogVisible } = useCrudDialog();

const rules = reactive({
  name: [{ required: true, message: "请输入岗位名称", trigger: "blur" }],
  code: [{ required: true, message: "请输入岗位编码", trigger: "blur" }],
  order: [{ required: true, message: "请输入岗位排序", trigger: "blur" }],
  status: [{ required: true, message: "请选择岗位状态", trigger: "blur" }],
});

const initialFormData: PositionForm = {
  id: undefined,
  name: undefined,
  code: undefined,
  order: 1,
  status: 0,
  description: undefined,
};

const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const positionFormRenderKey = ref(0);

// ─── CRUD 表单 ───
const { submitLoading, handleCloseDialog, handleOpenDialog, handleSubmit } =
  useCrudForm<PositionForm>({
    formData,
    initialFormData,
    dialogVisible,
    dataFormRef,
    formRenderKey: positionFormRenderKey,
    detailApi: PositionAPI.detailPosition,
    createApi: PositionAPI.createPosition,
    updateApi: PositionAPI.updatePosition,
    titles: { create: "新增岗位", update: "修改岗位", detail: "岗位详情" },
    detailFormData,
    onCreateSuccess: async () => {
      await refreshCreate();
    },
    onUpdateSuccess: async () => {
      await refreshUpdate();
    },
    onSubmitSuccess: async () => {
      await userStore.getUserInfo();
    },
  });

async function handleAdd() {
  createLoading.value = true;
  try {
    await handleOpenDialog("create");
  } finally {
    createLoading.value = false;
  }
}

const positionDialogFormItems = computed<FormItem[]>(() => [
  {
    label: "岗位名称",
    key: "name",
    type: "input",
    span: 24,
    props: { placeholder: "请输入岗位名称", maxlength: 50 },
  },
  {
    label: "岗位编码",
    key: "code",
    type: "input",
    span: 24,
    props: { placeholder: "请输入岗位编码", maxlength: 64 },
  },
  {
    label: "排序",
    key: "order",
    type: "number",
    span: 24,
    props: { controlsPosition: "right", min: 1 },
  },
  {
    label: "状态",
    key: "status",
    type: "radiogroup",
    span: 24,
    props: {
      options: [
        { label: "启用", value: 0 },
        { label: "停用", value: 1 },
      ],
    },
  },
  {
    label: "描述",
    key: "description",
    type: "input",
    span: 24,
    props: {
      type: "textarea",
      rows: 4,
      maxlength: 100,
      showWordLimit: true,
      placeholder: "请输入描述",
    },
  },
]);
const { exportVisible, openExport } = useImportExport();

async function handleSearchBarSearch(params: PositionSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildPositionReplaceParams(params));
  await getData();
}

async function onResetSearch() {
  searchForm.value = {
    name: undefined,
    status: undefined,
    created_id: undefined,
    updated_id: undefined,
    created_time: undefined,
    updated_time: undefined,
  };
  await resetSearchParams();
}

async function deletePositionRow(id: number, name: string) {
  try {
    await confirmDelete(`确定删除「${name}」吗？`);
    await PositionAPI.deletePosition([id]);
    await userStore.getUserInfo();
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
      selectedRows.value.map((r) => String(r.name ?? r.id))
    );
    batchDeleting.value = true;
    await PositionAPI.deletePosition(ids);
    await userStore.getUserInfo();
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
  if (!ids.length) {
    ElMessage.warning("请先选择要操作的数据");
    return;
  }
  try {
    await confirmToggleStatus(value);
    moreLoading.value = true;
    const status = value === "enable" ? 0 : 1;
    await PositionAPI.batchPosition({ ids, status });
    await refreshData();
    await userStore.getUserInfo();
  } catch {
    // 用户取消
  } finally {
    moreLoading.value = false;
  }
}
</script>
