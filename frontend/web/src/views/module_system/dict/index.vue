<!-- 字典管理：左侧字典类型列表 + 右侧字典数据面板 -->
<template>
  <div class="fa-full-height">
    <ElSplitter :style="'height: 100%'">
      <!-- Left: Dict Type -->
      <ElSplitterPanel size="30%" :min="320">
        <div class="flex flex-col h-full overflow-hidden pr-2">
          <FaSearchBar
            v-show="showSearchBar"
            ref="searchBarRef"
            v-model="searchForm"
            :items="dictTypeSearchItems"
            :rules="searchBarRules"
            :is-expand="false"
            :show-expand="true"
            :show-reset="true"
            :show-search="true"
            :disabled-search="false"
            :default-expanded="false"
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
                  :perm-create="['module_system:dict_type:create']"
                  @add="handleAdd"
                />
              </template>
            </FaTableHeader>

            <FaTable
              ref="faTableRef"
              :loading="loading"
              :data="data"
              :columns="columns"
              :pagination="pagination"
              :row-class-name="dictTypeRowClassName"
              @row-click="handleDictTypeRowClick"
              @pagination:size-change="handleSizeChange"
              @pagination:current-change="handleCurrentChange"
            />
          </ElCard>
        </div>
      </ElSplitterPanel>

      <!-- Right: Dict Data -->
      <ElSplitterPanel :min="300">
        <div class="flex flex-col h-full overflow-hidden pl-2">
          <DictDataPanel
            :key="currentDictTypeId"
            :dict-type="currentDictType"
            :dict-label="currentDictLabel"
            :dict-type-id="currentDictTypeId"
          />
        </div>
      </ElSplitterPanel>
    </ElSplitter>

    <!-- Dict Type CRUD Dialogs -->
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
          :items="dictDetailItems"
          max-height="70vh"
        >
          <template #dict_type="{ row }">
            <FaStatusTag type="primary" :label="(row as unknown as DictTable)?.dict_type" />
          </template>
        </FaDescriptions>
      </template>
      <template v-else>
        <FaForm
          :key="dictFormRenderKey"
          scrollbar
          max-height="70vh"
          ref="dataFormRef"
          v-model="formData"
          :items="dictDialogFormItems"
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
import { useCrudForm } from "@/hooks/core/useCrudForm";
import DictAPI, { type DictForm, type DictTable } from "@/api/module_system/dict";
import { useDictStore } from "@stores";
import { renderTableOperationCell, resolveStatusColumns, type TableOperationAction } from "@utils";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import FaForm from "@/components/forms/fa-form/index.vue";
import DictDataPanel from "./components/DictDataPanel.vue";
import FaStatusTag from "@/components/display/fa-status-tag/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";

defineOptions({
  name: "Dict",
  inheritAttrs: false,
});

type DictTypeSearchForm = {
  dict_name?: string;
  dict_type?: string;
};

const dictStore = useDictStore();

const searchForm = ref<DictTypeSearchForm>({
  dict_name: undefined,
  dict_type: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const searchBarRules: Record<string, unknown> = {};

const dictTypeSearchItems = computed<SearchFormItem[]>(() => [
  {
    label: "字典名称",
    key: "dict_name",
    type: "input",
    placeholder: "请输入字典名称",
    clearable: true,
    span: 8,
  },
  {
    label: "字典类型",
    key: "dict_type",
    type: "input",
    placeholder: "请输入字典类型",
    clearable: true,
    span: 8,
  },
]);

const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);

const createLoading = ref(false);
const statusUpdating = ref<Set<number>>(new Set());

// ─── 对话框状态 ───
const { dialogVisible } = useCrudDialog();

const detailFormData = ref<DictTable>({});

const dictDetailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] =
  [
    { label: "字典名称", prop: "dict_name" },
    { label: "字典类型", prop: "dict_type", slot: "dict_type" },
    {
      label: "状态",
      prop: "status",
      tag: {
        map: { "0": { type: "success", text: "启用" }, "1": { type: "danger", text: "停用" } },
      },
    },
    { label: "描述", prop: "description" },
    { label: "创建时间", prop: "created_time" },
    { label: "更新时间", prop: "updated_time" },
  ];

const formData = ref<DictForm>({
  id: undefined,
  dict_name: "",
  dict_type: "",
  status: 0,
  description: undefined,
});

const rules = reactive({
  dict_name: [{ required: true, message: "请输入字典名称", trigger: "blur" }],
  dict_type: [{ required: true, message: "请选择字典类型", trigger: "blur" }],
  status: [{ required: true, message: "请选择字典状态", trigger: "blur" }],
});

const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const dictFormRenderKey = ref(0);

function createInitialFormData(): DictForm {
  return {
    id: undefined,
    dict_name: "",
    dict_type: "",
    status: 0,
    description: undefined,
  };
}

const initialFormData = createInitialFormData();

// ─── CRUD 表单 ───
const { submitLoading, handleCloseDialog, handleOpenDialog, handleSubmit } = useCrudForm<DictForm>({
  formData,
  initialFormData,
  dialogVisible,
  dataFormRef,
  formRenderKey: dictFormRenderKey,
  detailApi: DictAPI.detailDictType,
  createApi: DictAPI.createDictType,
  updateApi: DictAPI.updateDictType,
  titles: { create: "新增字典", update: "修改字典", detail: "字典详情" },
  detailFormData,
  onCreateSuccess: async () => {
    await refreshCreate();
  },
  onUpdateSuccess: async () => {
    await refreshUpdate();
  },
  onSubmitSuccess: async () => {
    dictStore.clearDictData();
    if (formData.value.dict_type) {
      await dictStore.getDict([formData.value.dict_type]);
    }
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

const dictDialogFormItems = computed<FormItem[]>(() => [
  {
    label: "字典名称",
    key: "dict_name",
    type: "input",
    props: { placeholder: "请输入字典名称", maxlength: 50 },
  },
  {
    label: "字典类型",
    key: "dict_type",
    type: "input",
    props: { placeholder: "请输入字典类型", maxlength: 50 },
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
    apiFn: DictAPI.listDictType,
    apiParams: {
      page_no: 1,
      page_size: 10,
    },
    columnsFactory: resolveStatusColumns<DictTable>(() => [
      { type: "globalIndex", width: 56, label: "序号" },
      { prop: "dict_name", label: "字典名称", minWidth: 100, showOverflowTooltip: true },
      {
        prop: "dict_type",
        label: "字典类型",
        minWidth: 120,
        formatter: (row: DictTable) =>
          h(FaStatusTag, { type: "primary", label: row.dict_type ?? "" }),
      },
      {
        prop: "status",
        label: "状态",
        width: 80,
        formatter: (row: DictTable) =>
          h(ElSwitch, {
            modelValue: row.status ?? 0,
            "onUpdate:modelValue": (val: string | number | boolean) =>
              handleDictTypeStatusChange(row.id!, Number(val)),
            activeValue: 0,
            inactiveValue: 1,
            loading: statusUpdating.value.has(row.id!),
            inlinePrompt: true,
          }),
      },
      {
        prop: "operation",
        label: "操作",
        width: 180,
        fixed: "right",
        align: "center",
        formatter: (row: DictTable) => formatDictOperationCell(row),
      },
    ]),
  },
});

// ─── 右侧面板状态 ───
const currentDictType = ref("");
const currentDictLabel = ref("");
const currentDictTypeId = ref(0);
const hasAutoSelected = ref(false);
const selectedDictRowId = ref<number | null>(null);

function dictTypeRowClassName({ row }: { row: DictTable }) {
  return row?.id === selectedDictRowId.value ? "dict-type-row-selected" : "";
}

function handleDictTypeRowClick(row: DictTable) {
  selectedDictRowId.value = row.id ?? null;
  currentDictType.value = row.dict_type || "";
  currentDictLabel.value = row.dict_name || "";
  currentDictTypeId.value = row.id ?? 0;
}

async function handleSearchBarSearch(params: DictTypeSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams({
    dict_name: params.dict_name,
    dict_type: params.dict_type,
  } as Record<string, unknown>);
  await getData();
}

function onResetSearch() {
  searchForm.value = {
    dict_name: undefined,
    dict_type: undefined,
  };
  void resetSearchParams();
}

async function handleOpenDictTypeDetail(id: number) {
  dialogVisible.title = "字典详情";
  dialogVisible.type = "detail";
  const res = await DictAPI.detailDictType(id);
  const data = (res.data?.data ?? {}) as DictTable;
  Object.assign(detailFormData.value, data);
  dialogVisible.visible = true;
}

function buildDictRowActions(row: DictTable): TableOperationAction[] {
  const all: TableOperationAction[] = [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_system:dict_type:detail",
      run: () => void handleOpenDictTypeDetail(row.id!),
    },
    {
      key: "edit",
      label: "编辑",
      artType: "edit",
      icon: "ri:edit-2-line",
      perm: "module_system:dict_type:update",
      run: () => void handleOpenDialog("update", row.id),
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      icon: "ri:delete-bin-4-line",
      perm: "module_system:dict_type:delete",
      run: () => {
        if (row.id != null) deleteDictTypeRow(row.id, row.dict_name ?? "");
      },
    },
  ];
  return all;
}

function formatDictOperationCell(row: DictTable) {
  return renderTableOperationCell(buildDictRowActions(row), {
    wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1 dict-table-actions",
  });
}

async function deleteDictTypeRow(id: number, name: string) {
  try {
    await confirmDelete(`确定删除「${name}」吗？`);
    await DictAPI.deleteDictType([id]);
    dictStore.clearDictData();
    const dictTypes = Object.keys(dictStore.dictData);
    if (dictTypes.length > 0) await dictStore.getDict(dictTypes);

    // 如果删的是当前选中的行，清空右侧面板
    if (id === currentDictTypeId.value) {
      currentDictTypeId.value = 0;
      currentDictType.value = "";
      currentDictLabel.value = "";
      selectedDictRowId.value = null;
    }

    await refreshRemove();
  } catch {
    // 用户取消
  }
}

async function handleDictTypeStatusChange(id: number, newStatus: number) {
  statusUpdating.value = new Set([...statusUpdating.value, id]);
  try {
    await DictAPI.batchDictType({ ids: [id], status: newStatus });
    await refreshData();
    dictStore.clearDictData();
    const dictTypes = Object.keys(dictStore.dictData);
    if (dictTypes.length > 0) await dictStore.getDict(dictTypes);
  } catch {
    await refreshData();
  } finally {
    const next = new Set(statusUpdating.value);
    next.delete(id);
    statusUpdating.value = next;
  }
}

// 初始加载后自动选中第一行
watch(data, (newData) => {
  if (newData && newData.length > 0 && !hasAutoSelected.value) {
    const firstRow = newData[0]!;
    handleDictTypeRowClick(firstRow);
    hasAutoSelected.value = true;
  }
  if (newData && newData.length === 0) {
    currentDictTypeId.value = 0;
    currentDictType.value = "";
    currentDictLabel.value = "";
    selectedDictRowId.value = null;
  }
});
</script>
