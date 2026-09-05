<!-- 字典数据面板（内嵌版）：替换原来的 DataDrawer，直接嵌入页面右侧 -->
<template>
  <div class="dict-data-panel flex-1 flex flex-col min-h-0 overflow-hidden">
    <!-- 未选择字典类型时的占位提示 -->
    <div
      v-if="!dictTypeId"
      class="flex-1 flex flex-col items-center justify-center text-gray-400 select-none"
    >
      <div class="text-6xl mb-4 opacity-30">
        <svg
          width="80"
          height="80"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          <line x1="8" y1="9" x2="16" y2="9" />
          <line x1="8" y1="13" x2="14" y2="13" />
        </svg>
      </div>
      <p class="text-sm">请在左侧选择一个字典类型</p>
      <p class="text-xs mt-1 opacity-50">选择后将在右侧展示该字典的数据列表</p>
    </div>
    <template v-else>
      <ElCard class="fa-table-card" :style="{ 'margin-top': '0' }">
        <template #header>
          <div class="flex items-center">
            <span class="text-base font-medium">字典数据【{{ dictLabel }}】</span>
            <span class="text-gray-400 ml-1">({{ dictType }})</span>
          </div>
        </template>

        <div class="mb-3">
          <FaSearchBar
            v-show="showSearchBar"
            ref="searchBarRef"
            v-model="searchForm"
            :items="dictDataSearchItems"
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
        </div>

        <FaTableHeader
          v-model:columns="columnChecks"
          v-model:showSearchBar="showSearchBar"
          :loading="loading"
          @refresh="refreshData"
        >
          <template #left>
            <ElButton
              v-hasPerm="['module_system:dict_data:create']"
              type="primary"
              @click="handleAdd"
            >
              新增</ElButton
            >
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
        width="720px"
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
            :items="dictDataDetailItems"
            max-height="70vh"
          />
        </template>
        <template v-else>
          <FaForm
            :key="dictDataFormRenderKey"
            scrollbar
            max-height="70vh"
            ref="dataFormRef"
            v-model="formData"
            :items="dictDataDialogFormItems"
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
            <template #css_class>
              <ElSelect
                v-model="formData.css_class"
                placeholder="请选择常用颜色或输入自定义"
                clearable
                filterable
                allow-create
                default-first-option
              >
                <ElOption value="primary" label="主要(primary)">
                  <span class="tag-option-preview" :style="getTagPreviewStyle('primary')">
                    主要(primary)
                  </span>
                </ElOption>
                <ElOption value="success" label="成功(success)">
                  <span class="tag-option-preview" :style="getTagPreviewStyle('success')">
                    成功(success)
                  </span>
                </ElOption>
                <ElOption value="warning" label="警告(warning)">
                  <span class="tag-option-preview" :style="getTagPreviewStyle('warning')">
                    警告(warning)
                  </span>
                </ElOption>
                <ElOption value="danger" label="危险(danger)">
                  <span class="tag-option-preview" :style="getTagPreviewStyle('danger')">
                    危险(danger)
                  </span>
                </ElOption>
                <ElOption value="info" label="信息(info)">
                  <span class="tag-option-preview" :style="getTagPreviewStyle('info')">
                    信息(info)
                  </span>
                </ElOption>
              </ElSelect>
            </template>
            <template #list_class>
              <ElSelect v-model="formData.list_class" placeholder="请选择列表类样式" clearable>
                <ElOption value="default" label="默认(default)">
                  <span class="tag-option-preview tag-option-preview--default">默认(default)</span>
                </ElOption>
                <ElOption value="primary" label="主要(primary)">
                  <span class="tag-option-preview" :style="getTagPreviewStyle('primary')">
                    主要(primary)
                  </span>
                </ElOption>
                <ElOption value="success" label="成功(success)">
                  <span class="tag-option-preview" :style="getTagPreviewStyle('success')">
                    成功(success)
                  </span>
                </ElOption>
                <ElOption value="warning" label="警告(warning)">
                  <span class="tag-option-preview" :style="getTagPreviewStyle('warning')">
                    警告(warning)
                  </span>
                </ElOption>
                <ElOption value="danger" label="危险(danger)">
                  <span class="tag-option-preview" :style="getTagPreviewStyle('danger')">
                    危险(danger)
                  </span>
                </ElOption>
                <ElOption value="info" label="信息(info)">
                  <span class="tag-option-preview" :style="getTagPreviewStyle('info')">
                    信息(info)
                  </span>
                </ElOption>
              </ElSelect>
            </template>
          </FaForm>
        </template>
      </FaDialog>
    </template>
  </div>
</template>

<script setup lang="ts">
import DictAPI, {
  type DictDataForm,
  type DictDataPageQuery,
  type DictDataTable,
} from "@/api/module_system/dict";
import { renderTableOperationCell, resolveStatusColumns, type TableOperationAction } from "@utils";
import { useDictStore } from "@stores";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import FaForm from "@/components/forms/fa-form/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";

defineOptions({ name: "DictDataPanel", inheritAttrs: false });

const props = defineProps<{
  dictType: string;
  dictLabel: string;
  dictTypeId: number;
}>();

const TAG_TYPE_STYLE_MAP: Record<string, { background: string; color: string; border: string }> = {
  primary: {
    background: "var(--el-color-primary-light-9)",
    color: "var(--el-color-primary)",
    border: "var(--el-color-primary-light-7)",
  },
  success: {
    background: "var(--el-color-success-light-9)",
    color: "var(--el-color-success)",
    border: "var(--el-color-success-light-7)",
  },
  warning: {
    background: "var(--el-color-warning-light-9)",
    color: "var(--el-color-warning)",
    border: "var(--el-color-warning-light-7)",
  },
  danger: {
    background: "var(--el-color-danger-light-9)",
    color: "var(--el-color-danger)",
    border: "var(--el-color-danger-light-7)",
  },
  info: {
    background: "var(--el-color-info-light-9)",
    color: "var(--el-color-info)",
    border: "var(--el-color-info-light-7)",
  },
};

const dictStore = useDictStore();

function getTagPreviewStyle(value?: string) {
  const preset = value ? TAG_TYPE_STYLE_MAP[value] : undefined;
  if (preset) {
    return {
      backgroundColor: preset.background,
      color: preset.color,
      borderColor: preset.border,
    };
  }
  if (!value) return {};
  return {
    backgroundColor: value,
    color: "#fff",
    borderColor: value,
  };
}

type DictDataSearchForm = {
  dict_label?: string;
  status?: number;
  created_time?: string[];
};

async function fetchDictDataListMerged(params: Record<string, unknown>) {
  const q: DictDataPageQuery = {
    page_no: Number(params.current) || Number(params.page_no) || 1,
    page_size: Number(params.size) || Number(params.page_size) || 20,
    dict_label: params.dict_label as string | undefined,
    dict_type: props.dictType,
    dict_type_id: props.dictTypeId,
    status:
      params.status !== undefined && params.status !== null ? Number(params.status) : undefined,
  };
  return DictAPI.listDictData(q);
}

const searchForm = ref<DictDataSearchForm>({
  dict_label: undefined,
  status: undefined,
  created_time: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const searchBarRules: Record<string, unknown> = {};

const STATUS_OPTIONS = [
  { label: "启用", value: 0 },
  { label: "停用", value: 1 },
] as const;

const dictDataSearchItems = computed<SearchFormItem[]>(() => [
  {
    label: "字典标签",
    key: "dict_label",
    type: "input",
    placeholder: "请输入字典标签",
    clearable: true,
    span: 9,
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
    span: 9,
  },
]);

const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);

const statusUpdating = ref<Set<number>>(new Set());

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
    apiFn: fetchDictDataListMerged,
    apiParams: {
      page_no: 1,
      page_size: 20,
      dict_type: props.dictType,
      dict_type_id: props.dictTypeId,
    },
    columnsFactory: resolveStatusColumns<DictDataTable>(() => [
      { type: "globalIndex", width: 56, label: "序号" },
      { prop: "dict_label", label: "标签", minWidth: 150, showOverflowTooltip: true },
      { prop: "dict_value", label: "值", minWidth: 100, showOverflowTooltip: true },
      { prop: "dict_sort", label: "排序", width: 72 },
      {
        prop: "is_default",
        label: "是否默认",
        width: 100,
        status: {
          true: { type: "success", text: "是" },
          false: { type: "danger", text: "否" },
        },
      },
      {
        prop: "status",
        label: "状态",
        width: 80,
        formatter: (row: DictDataTable) =>
          h(ElSwitch, {
            modelValue: row.status ?? 0,
            "onUpdate:modelValue": (val: string | number | boolean) =>
              handleStatusChange(row.id!, Number(val)),
            activeValue: 0,
            inactiveValue: 1,
            loading: statusUpdating.value.has(row.id!),
            inlinePrompt: true,
          }),
      },
      {
        prop: "operation",
        label: "操作",
        width: 220,
        fixed: "right",
        align: "center",
        formatter: (row: DictDataTable) => formatDictDataOperationCell(row),
      },
    ]),
  },
});

const { dialogVisible } = useCrudDialog();

const detailFormData = ref<DictDataTable>({});

const dictDataDetailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] =
  [
    { label: "数据标签", prop: "dict_label" },
    { label: "数据类型", prop: "dict_type" },
    { label: "数据值", prop: "dict_value" },
    {
      label: "是否默认",
      prop: "is_default",
      tag: {
        map: { true: { type: "success", text: "是" }, false: { type: "danger", text: "否" } },
      },
    },
    {
      label: "状态",
      prop: "status",
      tag: {
        map: { "0": { type: "success", text: "启用" }, "1": { type: "danger", text: "停用" } },
      },
    },
    { label: "排序", prop: "dict_sort" },
    { label: "描述", prop: "description" },
  ];

const formData = ref<DictDataForm>({
  id: undefined,
  dict_sort: 1,
  dict_label: "",
  dict_value: "",
  dict_type: "",
  css_class: "",
  list_class: undefined,
  is_default: false,
  status: 0,
  description: "",
  dict_type_id: undefined,
});

const rules = reactive({
  dict_label: [{ required: true, message: "请输入字典标签", trigger: "blur" }],
  dict_type: [{ required: true, message: "请输入字典类型", trigger: "blur" }],
  dict_value: [{ required: true, message: "请输入字典键值", trigger: "blur" }],
  status: [{ required: true, message: "请选择状态", trigger: "blur" }],
  dict_sort: [{ required: true, message: "请输入排序", trigger: "blur" }],
  is_default: [{ required: true, message: "请选择是否默认", trigger: "blur" }],
});

const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const dictDataFormRenderKey = ref(0);

const dictDataDialogFormItems = computed<FormItem[]>(() => [
  {
    label: "数据类型",
    key: "dict_type",
    type: "input",
    props: {
      placeholder: "请输入数据类型",
      maxlength: 50,
      disabled: true,
    },
  },
  {
    label: "数据标签",
    key: "dict_label",
    type: "input",
    props: { placeholder: "请输入数据标签", maxlength: 255 },
  },
  {
    label: "数据值",
    key: "dict_value",
    type: "input",
    props: { placeholder: "请输入数据值", maxlength: 255 },
  },
  {
    label: "样式属性",
    key: "css_class",
    type: "input",
  },
  {
    label: "列表类样式",
    key: "list_class",
    type: "input",
  },
  {
    label: "是否默认",
    key: "is_default",
    type: "radiogroup",
    props: {
      options: [
        { label: "是", value: true },
        { label: "否", value: false },
      ],
    },
  },
  {
    label: "排序",
    key: "dict_sort",
    type: "number",
    props: {
      controlsPosition: "right",
      min: 1,
      style: { width: "100px" },
    },
  },
  {
    label: "状态",
    key: "status",
    type: "switch",
    props: {
      activeValue: 0,
      inactiveValue: 1,
      inlinePrompt: true,
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

function createInitialFormData(): DictDataForm {
  return {
    id: undefined,
    dict_sort: 1,
    dict_label: "",
    dict_value: "",
    dict_type: "",
    css_class: "",
    list_class: undefined,
    is_default: false,
    status: 0,
    description: "",
    dict_type_id: props.dictTypeId,
  };
}

const initialFormData = createInitialFormData();

const { submitLoading, handleCloseDialog, handleOpenDialog, handleSubmit } =
  useCrudForm<DictDataForm>({
    formData,
    initialFormData,
    dialogVisible,
    dataFormRef,
    formRenderKey: dictDataFormRenderKey,
    detailApi: DictAPI.detailDictData,
    createApi: DictAPI.createDictData,
    updateApi: DictAPI.updateDictData,
    titles: { create: "新增字典数据", update: "修改字典数据", detail: "字典数据详情" },
    detailFormData,
    onCreateSuccess: async () => {
      await refreshCreate();
      dictStore.clearDictData();
      if (props.dictType) await dictStore.getDict([props.dictType]);
    },
    onUpdateSuccess: async () => {
      await refreshUpdate();
      dictStore.clearDictData();
      if (props.dictType) await dictStore.getDict([props.dictType]);
    },
  });

onMounted(() => {
  if (props.dictTypeId) getData();
});

async function handleSearchBarSearch(params: DictDataSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams({
    dict_label: params.dict_label,
    status: params.status,
    dict_type: props.dictType,
    dict_type_id: props.dictTypeId,
  } as Record<string, unknown>);
  await getData();
}

function onResetSearch() {
  searchForm.value = {
    dict_label: undefined,
    status: undefined,
    created_time: undefined,
  };
  void resetSearchParams();
}

async function handleAdd() {
  await handleOpenDialog("create", undefined, {
    dict_type: props.dictType,
    dict_type_id: props.dictTypeId,
  });
}

function buildDictDataRowActions(row: DictDataTable): TableOperationAction[] {
  const all: TableOperationAction[] = [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_system:dict_data:detail",
      run: () => void handleOpenDialog("detail", row.id),
    },
    {
      key: "edit",
      label: "编辑",
      artType: "edit",
      icon: "ri:edit-2-line",
      perm: "module_system:dict_data:update",
      run: () => void handleOpenDialog("update", row.id),
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      icon: "ri:delete-bin-4-line",
      perm: "module_system:dict_data:delete",
      run: () => {
        if (row.id != null) deleteDictDataRow(row.id, row.dict_label ?? "");
      },
    },
  ];
  return all;
}

function formatDictDataOperationCell(row: DictDataTable) {
  return renderTableOperationCell(buildDictDataRowActions(row), {
    wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1 dict-data-drawer-actions",
  });
}

async function deleteDictDataRow(id: number, name: string) {
  try {
    await confirmDelete(`确定删除「${name}」吗？`);
    await DictAPI.deleteDictData([id]);
    dictStore.clearDictData();
    if (props.dictType) await dictStore.getDict([props.dictType]);
    await refreshRemove();
  } catch {
    // 用户取消
  }
}

async function handleStatusChange(id: number, newStatus: number) {
  statusUpdating.value = new Set([...statusUpdating.value, id]);
  try {
    await DictAPI.batchDictData({ ids: [id], status: newStatus });
    await refreshData();
    dictStore.clearDictData();
    if (props.dictType) await dictStore.getDict([props.dictType]);
  } catch {
    await refreshData();
  } finally {
    const next = new Set(statusUpdating.value);
    next.delete(id);
    statusUpdating.value = next;
  }
}
</script>

<style lang="scss" scoped>
.tag-option-preview {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 120px;
  padding: 4px 10px;
  font-size: 12px;
  line-height: 18px;
  text-align: center;
  border: 1px solid transparent;
  border-radius: 4px;
}

.tag-option-preview--default {
  color: var(--el-text-color-regular);
  background: var(--el-fill-color-light);
  border-color: var(--el-border-color-lighter);
}
</style>
