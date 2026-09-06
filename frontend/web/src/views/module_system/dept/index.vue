<!-- 部门配置：FA + 树形表格（对齐 system/menu 模版） -->
<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="deptSearchItems"
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
        @refresh="loadDeptData"
      >
        <template #left>
          <div class="inline-flex flex-wrap items-center gap-2">
            <FaTableHeaderLeft
              :remove-ids="selectedIds"
              :perm-create="['module_system:dept:create']"
              :perm-delete="['module_system:dept:delete']"
              :perm-patch="['module_system:dept:patch']"
              :delete-loading="batchDeleting"
              :create-loading="createLoading"
              :more-loading="moreLoading"
              @add="handleAdd"
              @delete="handleBatchDelete"
              @more="handleMoreClick"
            />
            <ElButton @click="toggleExpand" v-ripple>{{ isExpanded ? "收起" : "展开" }}</ElButton>
          </div>
        </template>
      </FaTableHeader>

      <FaTable
        ref="tableRef"
        row-key="id"
        :loading="loading"
        :columns="columns"
        :data="tableData"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        :default-expand-all="false"
        @selection-change="onTableSelectionChange"
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
          :items="deptDetailItems"
          max-height="70vh"
        />
      </template>
      <template v-else>
        <FaForm
          :key="deptFormRenderKey"
          scrollbar
          max-height="70vh"
          ref="dataFormRef"
          v-model="formData"
          :items="deptDialogFormItems"
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
  </div>
</template>

<script setup lang="ts">
import DeptAPI, {
  type DeptForm,
  type DeptPageQuery,
  type DeptTable,
} from "@/api/module_system/dept";
import { useUserStore } from "@stores";
import {
  formatTree,
  renderTableOperationCell,
  resolveStatusColumns,
  type TableOperationAction,
} from "@utils";
import type { AuditSearchFormParams } from "@/components/forms/fa-search-bar/auditSearchFormItems";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import FaForm from "@/components/forms/fa-form/index.vue";
import { ElMessage } from "element-plus";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";

defineOptions({
  name: "Dept",
  inheritAttrs: false,
});

const userStore = useUserStore();

type DeptSearchForm = {
  name?: string;
  status?: number;
} & AuditSearchFormParams;

function buildDeptQuery(p: DeptSearchForm): DeptPageQuery {
  return {
    name: p.name,
    status: p.status,
    created_time:
      Array.isArray(p.created_time) && p.created_time.length === 2 ? p.created_time : undefined,
    created_id: p.created_id ?? undefined,
    updated_id: p.updated_id ?? undefined,
    updated_time:
      Array.isArray(p.updated_time) && p.updated_time.length === 2 ? p.updated_time : undefined,
  };
}

function buildDeptRowActions(
  row: DeptTable,
  ctx: {
    onAddChild: (parentId: number) => void;
    onDetail: (id: number) => void;
    onEdit: (id: number) => void;
    onDelete: (id: number, name: string) => void;
  }
): TableOperationAction[] {
  const all: TableOperationAction[] = [
    {
      key: "add",
      label: "新增",
      artType: "add",
      perm: "module_system:dept:create",
      run: () => ctx.onAddChild(row.id!),
    },
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_system:dept:detail",
      run: () => ctx.onDetail(row.id!),
    },
    {
      key: "edit",
      label: "编辑",
      artType: "edit",
      perm: "module_system:dept:update",
      run: () => ctx.onEdit(row.id!),
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      perm: "module_system:dept:delete",
      run: () => ctx.onDelete(row.id!, row.name ?? ""),
    },
  ];
  return all;
}

function formatDeptOperationCell(row: DeptTable, ctx: Parameters<typeof buildDeptRowActions>[1]) {
  const actions = buildDeptRowActions(row, ctx);
  return renderTableOperationCell(actions, {
    wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1 dept-table-actions",
  });
}

const searchForm = ref<DeptSearchForm>({
  name: undefined,
  status: undefined,
  created_time: undefined,
  created_id: undefined,
  updated_id: undefined,
  updated_time: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const searchBarRules: Record<string, unknown> = {};

const STATUS_OPTIONS = [
  { label: "启用", value: 0 },
  { label: "停用", value: 1 },
] as const;

const deptSearchItems = computed<SearchFormItem[]>(() => [
  {
    label: "部门名称",
    key: "name",
    type: "input",
    placeholder: "请输入部门名称",
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

const tableRef = ref<{
  elTableRef?: {
    toggleRowExpansion: (row: DeptTable, expanded?: boolean) => void;
    clearSelection: () => void;
  };
} | null>(null);
const tableData = ref<DeptTable[]>([]);
const loading = ref(false);
const isExpanded = ref(false);
const deptOptions = ref<OptionType[]>([]);

// ─── 表格多选 ───
const { selectedRows, selectedIds, batchDeleting, onTableSelectionChange } =
  useTableSelection<DeptTable>();

const createLoading = ref(false);
const moreLoading = ref(false);

async function loadDeptData() {
  loading.value = true;
  try {
    const res = await DeptAPI.listDept(buildDeptQuery(searchForm.value));
    const tree = res.data.data || [];
    tableData.value = tree;
    deptOptions.value = formatTree(tree);
  } catch (e: unknown) {
    if (import.meta.env.DEV) console.error(e);
  } finally {
    loading.value = false;
  }
}

async function deleteDeptRow(id: number, name: string) {
  try {
    await confirmDelete(`确定删除「${name}」吗？`);
    await DeptAPI.deleteDept([id]);
    await userStore.getUserInfo();
    tableRef.value?.elTableRef?.clearSelection();
    await loadDeptData();
  } catch {
    // 用户取消
  }
}

// ─── 对话框状态 ───
const { dialogVisible } = useCrudDialog();

const detailFormData = ref<DeptTable>({ code: "" });

const deptDetailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] =
  [
    { label: "部门名称", prop: "name" },
    { label: "部门编码", prop: "code" },
    { label: "上级部门", prop: "parent_name" },
    {
      label: "状态",
      prop: "status",
      tag: {
        map: { "0": { type: "success", text: "启用" }, "1": { type: "danger", text: "停用" } },
      },
    },
    { label: "排序", prop: "order" },
    { label: "创建时间", prop: "created_time" },
    { label: "更新时间", prop: "updated_time" },
    { label: "创建人", prop: "created_by.name" },
    { label: "更新人", prop: "updated_by.name" },
    { label: "描述", prop: "description", span: 4 },
  ];

const formData = ref<DeptForm>({
  id: undefined,
  name: undefined,
  code: "",
  order: 1,
  parent_id: undefined,
  status: 0,
  description: undefined,
});

const CODE_PATTERN = /^[A-Za-z][A-Za-z0-9_]{1,15}$/;

const rules = reactive({
  name: [{ required: true, message: "请输入部门名称", trigger: "blur" }],
  code: [
    { required: true, message: "请输入部门编码", trigger: "blur" },
    {
      pattern: CODE_PATTERN,
      message: "字母开头，2-16位字母/数字/下划线",
      trigger: "blur",
    },
  ],
  order: [{ required: true, message: "请输入排序", trigger: "blur" }],
  status: [{ required: true, message: "请选择状态", trigger: "blur" }],
});

function createInitialFormData(): DeptForm {
  return {
    id: undefined,
    name: undefined,
    code: "",
    order: 1,
    parent_id: undefined,
    status: 0,
    description: undefined,
  };
}

const initialFormData = createInitialFormData();

const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const deptFormRenderKey = ref(0);

// ─── CRUD 表单 ───
const { submitLoading, handleCloseDialog, handleOpenDialog, handleSubmit } = useCrudForm<DeptForm>({
  formData,
  initialFormData,
  dialogVisible,
  dataFormRef,
  formRenderKey: deptFormRenderKey,
  detailApi: DeptAPI.detailDept,
  createApi: DeptAPI.createDept,
  updateApi: DeptAPI.updateDept,
  titles: { create: "新增部门", update: "修改部门", detail: "部门详情" },
  detailFormData,
  onCreateSuccess: async () => {
    await loadDeptData();
  },
  onUpdateSuccess: async () => {
    await loadDeptData();
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

async function handleOpenDeptDetail(id: number) {
  dialogVisible.title = "部门详情";
  dialogVisible.type = "detail";
  const response = await DeptAPI.detailDept(id);
  Object.assign(detailFormData.value, response.data.data ?? {});
  dialogVisible.visible = true;
}

const opCtx = {
  onAddChild: (parentId: number) =>
    void handleOpenDialog("create", undefined, { parent_id: parentId }),
  onDetail: (id: number) => void handleOpenDeptDetail(id),
  onEdit: (id: number) => void handleOpenDialog("update", id),
  onDelete: deleteDeptRow,
};

const { columnChecks, columns } = useTableColumns<DeptTable>(
  resolveStatusColumns(() => [
    { type: "selection", width: 48, fixed: "left" },
    { type: "globalIndex", width: 56, label: "序号" },
    { prop: "name", label: "部门名称", minWidth: 120, showOverflowTooltip: true },
    { prop: "code", label: "部门编码", minWidth: 120, showOverflowTooltip: true },
    {
      prop: "status",
      label: "状态",
      width: 88,
      status: {
        0: { type: "success", text: "启用" },
        1: { type: "danger", text: "停用" },
      },
    },
    { prop: "order", label: "排序", width: 88, showOverflowTooltip: true },
    { prop: "description", label: "描述", minWidth: 100, showOverflowTooltip: true },
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
      width: 220,
      fixed: "right",
      align: "center",
      formatter: (row: DeptTable) => formatDeptOperationCell(row, opCtx),
    },
  ])
);

const deptDialogFormItems = computed<FormItem[]>(() => [
  {
    label: "部门名称",
    key: "name",
    type: "input",
    props: { placeholder: "请输入部门名称", maxlength: 50 },
  },
  {
    label: "部门编码",
    key: "code",
    type: "input",
    props: {
      placeholder: "字母开头，2-16位字母/数字/下划线",
      maxlength: 16,
      showWordLimit: true,
    },
  },
  {
    label: "上级部门",
    key: "parent_id",
    type: "treeselect",
    props: {
      placeholder: "请选择上级部门",
      data: deptOptions.value,
      filterable: true,
      checkStrictly: true,
      renderAfterExpand: false,
    },
  },
  {
    label: "排序",
    key: "order",
    type: "number",
    props: {
      controlsPosition: "right",
      min: 1,
      max: 999,
    },
  },
  {
    label: "状态",
    key: "status",
    type: "radiogroup",
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
    props: {
      type: "textarea",
      rows: 4,
      maxlength: 100,
      showWordLimit: true,
      placeholder: "请输入描述",
    },
  },
]);

async function handleSearchBarSearch(params: DeptSearchForm) {
  await searchBarRef.value?.validate?.();
  searchForm.value = { ...params };
  await loadDeptData();
}

async function onResetSearch() {
  searchForm.value = {
    name: undefined,
    status: undefined,
    created_time: undefined,
    created_id: undefined,
    updated_id: undefined,
    updated_time: undefined,
  };
  await loadDeptData();
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
    await DeptAPI.deleteDept(ids);
    await userStore.getUserInfo();
    tableRef.value?.elTableRef?.clearSelection();
    await loadDeptData();
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
    await DeptAPI.batchDept({ ids, status });
    await loadDeptData();
    await userStore.getUserInfo();
  } catch {
    // 用户取消或操作失败
  } finally {
    moreLoading.value = false;
  }
}

function toggleExpand() {
  isExpanded.value = !isExpanded.value;
  nextTick(() => {
    const el = tableRef.value?.elTableRef;
    if (!el || !tableData.value.length) return;
    const walk = (rows: DeptTable[]) => {
      rows.forEach((row) => {
        if (row.children?.length) {
          el.toggleRowExpansion(row, isExpanded.value);
          walk(row.children);
        }
      });
    };
    walk(tableData.value);
  });
}

onMounted(() => {
  void loadDeptData();
});
</script>
