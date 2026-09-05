<!-- 定时任务节点：Art + useTable -->
<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="nodeSearchItems"
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
            :perm-create="['module_task:cronjob:node:create']"
            :perm-delete="['module_task:cronjob:node:delete']"
            :perm-patch="['module_task:cronjob:node:update']"
            :delete-loading="batchDeleting"
            :more-loading="moreLoading"
            :create-loading="createLoading"
            @add="handleAdd"
            @delete="handleBatchDelete"
            @more="handleBatchMoreStatus"
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
      />
    </ElCard>

    <FaDialog
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      width="1000px"
      @close="handleCloseDialog"
      @opened="handleDialogOpened"
    >
      <ElSplitter direction="horizontal" :style="'height: 500px'">
        <ElSplitterPanel size="300px" :min="200" :max="400">
          <ElScrollbar :style="'height: 100%'">
            <FaForm
              :key="nodeFormRenderKey"
              ref="dataFormRef"
              v-model="formData"
              :items="nodeDialogFormItems"
              :rules="rules"
              label-suffix=":"
              label-width="85px"
              :span="24"
              :gutter="16"
              :show-reset="false"
              :show-submit="false"
              class="crud-dialog-art-form node-splitter-art-form"
            >
              <template #jobstore>
                <ElSelect v-model="formData.jobstore" placeholder="请选择存储器">
                  <ElOption
                    v-for="item in jobStoreOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </ElSelect>
              </template>
              <template #executor>
                <ElSelect v-model="formData.executor" placeholder="请选择执行器">
                  <ElOption
                    v-for="item in jobExecutorOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </ElSelect>
              </template>
              <template #args>
                <div class="flex flex-col gap-2">
                  <div
                    v-for="(_item, index) in argsList"
                    :key="index"
                    class="flex gap-2 items-center [&_.el-input]:flex-1"
                  >
                    <ElInput v-model="argsList[index]" placeholder="参数值" />
                    <ElButton
                      type="danger"
                      :icon="Delete"
                      circle
                      @click="argsList.splice(index, 1)"
                    />
                  </div>
                  <ElButton type="primary" :icon="Plus" @click="argsList.push('')">
                    添加位置参数
                  </ElButton>
                </div>
              </template>
              <template #kwargs>
                <div class="flex flex-col gap-2">
                  <div
                    v-for="(item, index) in kwargsList"
                    :key="item.key || index"
                    class="flex gap-2 items-center [&_.el-input]:flex-1"
                  >
                    <ElInput v-model="item.key" placeholder="键" />
                    <ElInput v-model="item.value" placeholder="值" />
                    <ElButton
                      type="danger"
                      :icon="Delete"
                      circle
                      @click="kwargsList.splice(index, 1)"
                    />
                  </div>
                  <ElButton
                    type="primary"
                    :icon="Plus"
                    @click="kwargsList.push({ key: '', value: '' })"
                  >
                    添加关键词参数
                  </ElButton>
                </div>
              </template>
              <template #coalesce>
                <ElRadioGroup v-model="formData.coalesce">
                  <ElRadio :value="true">是</ElRadio>
                  <ElRadio :value="false">否</ElRadio>
                </ElRadioGroup>
              </template>
              <template #max_instances>
                <ElInputNumber
                  v-model="formData.max_instances"
                  controls-position="right"
                  :min="1"
                  :max="10"
                />
              </template>
              <template #trigger_args>
                <template v-if="formData.trigger === 'cron'">
                  <ElInput
                    v-model="formData.trigger_args"
                    placeholder="请输入 * * * * * ? *"
                    readonly
                    @click="openCron = true"
                  />
                  <FaDialog
                    v-model="openCron"
                    title="Cron 表达式"
                    width="min(700px, calc(100vw - 48px))"
                    append-to-body
                  >
                    <FaCron v-model="cronTempValue" />
                    <template #footer>
                      <ElButton @click="openCron = false">取消</ElButton>
                      <ElButton type="primary" @click="confirmCron">确定</ElButton>
                    </template>
                  </FaDialog>
                </template>
                <template v-else-if="formData.trigger === 'interval'">
                  <ElPopover
                    :visible="openInterval"
                    width="600px"
                    trigger="click"
                    :persistent="false"
                    placement="auto-end"
                  >
                    <template #reference>
                      <ElInput
                        v-model="formData.trigger_args"
                        placeholder="请点击设置间隔时间"
                        @click="openInterval = true"
                      />
                    </template>
                    <FaIntervalTab
                      :cron-value="formData.trigger_args"
                      @confirm="handleIntervalConfirm"
                      @cancel="openInterval = false"
                    />
                  </ElPopover>
                </template>
                <template v-else-if="formData.trigger === 'date'">
                  <ElDatePicker
                    v-model="formData.trigger_args"
                    type="datetime"
                    format="YYYY-MM-DD HH:mm:ss"
                    value-format="YYYY-MM-DD HH:mm:ss"
                    placeholder="请选择执行时间"
                    :style="'width: 100%'"
                  />
                </template>
              </template>
            </FaForm>
          </ElScrollbar>
        </ElSplitterPanel>

        <ElSplitterPanel>
          <div class="flex flex-col h-full pl-4">
            <div class="flex items-center justify-between py-2.5">
              <span class="text-sm font-semibold">处理器</span>
              <span class="text-xs">定义 handler(*args, **kwargs) 函数</span>
            </div>
            <Codemirror
              ref="codeEditorRef"
              v-model:value="formData.func"
              :options="codeEditorOptions"
              border
              height="calc(100% - 40px)"
              width="100%"
            />
          </div>
        </ElSplitterPanel>
      </ElSplitter>

      <template #footer>
        <div class="dialog-footer">
          <ElButton @click="handleCloseDialog">取消</ElButton>
          <ElButton type="primary" :loading="submitLoading" @click="handleSubmit">确定</ElButton>
        </div>
      </template>
    </FaDialog>
  </div>
</template>

<script lang="ts" setup>
defineOptions({
  name: "Node",
  inheritAttrs: false,
});

import NodeAPI, { type NodeTable, type NodeForm } from "@/api/module_task/cronjob/node";
import { confirmToggleStatus } from "@/hooks/core/useConfirm";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import FaForm from "@/components/forms/fa-form/index.vue";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import FaTable from "@/components/tables/fa-table/index.vue";
import FaDialog from "@/components/modal/fa-dialog/index.vue";
import { renderTableOperationCell, resolveStatusColumns, type TableOperationAction } from "@utils";
import { Delete, Plus } from "@element-plus/icons-vue";
import FaCron from "@/components/others/fa-cron/index.vue";
import Codemirror, { CmComponentRef } from "codemirror-editor-vue3";
import type { EditorConfiguration } from "codemirror";
import "codemirror/mode/python/python.js";
import "codemirror/theme/dracula.css";

/** 可选对象字面量 */
type OptionItem = { label: string; value: string };

/** 存储器选项（对应 ap_scheduler jobstores 配置，不再依赖字典） */
const jobStoreOptions: OptionItem[] = [
  { label: "默认(Redis)", value: "default" },
  { label: "数据库(Sqlalchemy)", value: "sqlalchemy" },
  { label: "内存(Memory)", value: "memory" },
];

/** 执行器选项（对应 ap_scheduler executors 配置，不再依赖字典） */
const jobExecutorOptions: OptionItem[] = [
  { label: "线程池", value: "default" },
  { label: "进程池", value: "processpool" },
];

type NodeSearchForm = {
  name?: string;
  code?: string;
  created_id?: number;
  updated_id?: number;
  created_time?: string[];
  updated_time?: string[];
};

function buildNodeReplaceParams(u: NodeSearchForm): Record<string, unknown> {
  return {
    name: u.name,
    code: u.code,
    created_id: u.created_id,
    updated_id: u.updated_id,
    created_time:
      Array.isArray(u.created_time) && u.created_time.length === 2 ? u.created_time : undefined,
    updated_time:
      Array.isArray(u.updated_time) && u.updated_time.length === 2 ? u.updated_time : undefined,
  };
}

const searchForm = ref<NodeSearchForm>({
  name: undefined,
  code: undefined,
  created_id: undefined,
  updated_id: undefined,
  created_time: undefined,
  updated_time: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const searchBarRules: Record<string, unknown> = {};

const nodeTriggerLabelMap: Record<string, string> = {
  cron: "Cron",
  interval: "间隔",
  date: "单次",
};

function formatNodeTriggerCell(row: NodeTable): string {
  const trigger = row.trigger;
  if (!trigger) return "不排程";
  const label = nodeTriggerLabelMap[trigger] ?? trigger;
  return row.trigger_args ? `${label} ${row.trigger_args}` : label;
}

const nodeSearchItems = computed<SearchFormItem[]>(() => [
  {
    label: "节点名称",
    key: "name",
    type: "input",
    placeholder: "请输入节点名称",
    clearable: true,
    span: 6,
  },
  {
    label: "节点编码",
    key: "code",
    type: "input",
    placeholder: "请输入节点编码",
    clearable: true,
    span: 6,
  },
  {
    label: "状态",
    key: "status",
    type: "select",
    props: {
      placeholder: "请选择状态",
      options: [
        { label: "启用", value: 0 },
        { label: "停用", value: 1 },
      ],
      clearable: true,
    },
    span: 6,
  },
]);

const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);
const selectedRows = ref<NodeTable[]>([]);
const selectedIds = computed(() =>
  selectedRows.value.map((r) => r.id).filter((id): id is number => typeof id === "number")
);
const batchDeleting = ref(false);
const moreLoading = ref(false);

function onTableSelectionChange(rows: NodeTable[]) {
  selectedRows.value = rows;
}

async function deleteNodeRow(id: number | undefined, name: string | number) {
  if (id == null) return;
  try {
    await confirmDelete(`确定删除节点「${name}」吗？`);
    await NodeAPI.deleteNode([id]);
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } catch {
    // 用户取消
  }
}

function buildNodeRowActions(row: NodeTable): TableOperationAction[] {
  const disabled = row.status === 1;
  const all: TableOperationAction[] = [
    {
      key: "execute",
      label: "立即执行",
      artType: "more",
      icon: "ri:play-circle-line",
      iconColor: "var(--el-color-primary)",
      perm: "module_task:cronjob:node:execute",
      run: () => {
        if (row.id != null) void handleExecuteOnce(row.id);
      },
    },
    {
      key: disabled ? "enable" : "disable",
      label: disabled ? "启用" : "停用",
      artType: "more",
      icon: disabled ? "ri:play-line" : "ri:pause-circle-line",
      iconColor: disabled ? "var(--el-color-success)" : "var(--el-color-warning)",
      perm: "module_task:cronjob:node:update",
      run: () => {
        if (row.id != null) void handleToggleRowStatus(row);
      },
    },
    {
      key: "edit",
      label: "编辑",
      artType: "edit",
      icon: "ri:edit-2-line",
      perm: "module_task:cronjob:node:update",
      run: () => {
        if (row.id != null) void handleOpenDialog("update", row.id);
      },
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      icon: "ri:delete-bin-4-line",
      perm: "module_task:cronjob:node:delete",
      run: () => {
        void deleteNodeRow(row.id, String(row?.name ?? row?.id ?? ""));
      },
    },
  ];
  return all;
}

/** 立即执行一次（走后端临时 job，不影响已保存的执行计划） */
async function handleExecuteOnce(id: number) {
  try {
    await NodeAPI.executeNode(id);
    await refreshData();
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error(error);
  }
}

/** 单行启停联动（后端会同步注册/卸载调度） */
async function handleToggleRowStatus(row: NodeTable) {
  if (row.id == null) return;
  const enable = row.status === 1;
  try {
    await confirmToggleStatus(enable ? "enable" : "disable");
    await NodeAPI.batchNode({ ids: [row.id], status: enable ? 0 : 1 });
    await refreshData();
  } catch {
    // 用户取消
  }
}

/** 批量启停联动 */
async function handleBatchMoreStatus(type: "enable" | "disable") {
  const ids = selectedIds.value;
  if (ids.length === 0) return;
  try {
    await confirmToggleStatus(type);
    moreLoading.value = true;
    await NodeAPI.batchNode({ ids, status: type === "enable" ? 0 : 1 });
    selectedRows.value = [];
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshData();
  } catch {
    // 用户取消
  } finally {
    moreLoading.value = false;
  }
}

function formatNodeOperationCell(row: NodeTable) {
  return renderTableOperationCell(buildNodeRowActions(row), {
    wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1 cronjob-node-table-actions",
  });
}

async function handleBatchDelete() {
  const ids = selectedIds.value;
  if (ids.length === 0) return;
  try {
    await confirmBatchDelete(
      ids.length,
      selectedRows.value.map((r) => String(r?.name ?? r?.id ?? ""))
    );
    batchDeleting.value = true;
    await NodeAPI.deleteNode(ids);
    selectedRows.value = [];
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
  refreshUpdate,
  refreshRemove,
} = useTable({
  core: {
    apiFn: NodeAPI.listNode,
    apiParams: {
      page_no: 1,
      page_size: 10,
    },
    columnsFactory: resolveStatusColumns<NodeTable>(() => [
      { type: "selection", width: 48, fixed: "left" },
      { type: "globalIndex", width: 56, label: "序号" },
      {
        prop: "name",
        label: "节点名称",
        minWidth: 140,
        showOverflowTooltip: true,
      },
      {
        prop: "code",
        label: "节点编码",
        minWidth: 100,
        showOverflowTooltip: true,
      },
      {
        prop: "trigger",
        label: "执行计划",
        minWidth: 160,
        showOverflowTooltip: true,
        formatter: formatNodeTriggerCell,
      },
      {
        prop: "status",
        label: "状态",
        width: 86,
        align: "center",
        status: {
          0: { type: "success", text: "启用" },
          1: { type: "danger", text: "停用" },
        },
      },
      {
        prop: "next_run_time",
        label: "下次运行",
        minWidth: 165,
        showOverflowTooltip: true,
      },
      {
        prop: "created_time",
        label: "创建时间",
        minWidth: 165,
        sortable: true,
        showOverflowTooltip: true,
      },
      {
        prop: "operation",
        label: "操作",
        width: 250,
        fixed: "right",
        align: "center",
        formatter: (row: NodeTable) => formatNodeOperationCell(row),
      },
    ]),
  },
});

async function handleSearchBarSearch(params: NodeSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildNodeReplaceParams(params));
  await getData();
}

async function onResetSearch() {
  searchForm.value = {
    name: undefined,
    code: undefined,
    created_id: undefined,
    updated_id: undefined,
    created_time: undefined,
    updated_time: undefined,
  };
  await resetSearchParams();
}

const codeEditorOptions: EditorConfiguration = {
  mode: "python",
  lineNumbers: true,
  smartIndent: true,
  indentUnit: 4,
  tabSize: 4,
  theme: "dracula",
  lineWrapping: true,
  autofocus: false,
};

const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const nodeFormRenderKey = ref(0);
const submitLoading = ref(false);
const createLoading = ref(false);
const openCron = ref(false);
const cronTempValue = ref("");
const confirmCron = () => {
  if (cronTempValue.value) formData.value.trigger_args = cronTempValue.value;
  openCron.value = false;
};
const openInterval = ref(false);
const codeEditorRef = ref<CmComponentRef>();

const defaultCodeBlock = `def handler(*args, **kwargs):
    """
    Demo: 调用工程中的方法处理数据

    演示如何:
    1. 从工程中导入方法
    2. 调用处理器处理数据
    3. 返回处理结果
    """

    # 从工程中导入方法
    from app.plugin.module_task.cronjob.node.handlers.demo_handler import (
        demo_handler,
        process_data
    )

    print("=" * 50)
    print("Demo 任务开始执行")
    print("=" * 50)

    # 1. 调用 demo_handler
    print("1. 调用 demo_handler:")
    result1 = demo_handler("参数1", "参数2", key="value")
    print(f"   返回: {result1}")

    # 2. 调用 process_data 计算平均值
    print("2. 数据处理 - 计算平均值:")
    numbers = [10, 20, 30, 40, 50]
    result2 = process_data(numbers, operation="avg")
    print(f"   输入: {numbers}")
    print(f"   结果: {result2}")

    # 3. 调用 process_data 计算总和
    print("3. 数据处理 - 计算总和:")
    result3 = process_data(numbers, operation="sum")
    print(f"   输入: {numbers}")
    print(f"   结果: {result3}")

    print("=" * 50)
    print("Demo 任务执行完成")
    print("=" * 50)

    return {
        "status": "success",
        "demo_result": result1,
        "avg_result": result2,
        "sum_result": result3
    }
`;

const formData = ref<NodeForm>({
  id: undefined,
  name: "",
  code: undefined,
  jobstore: "default",
  executor: "default",
  func: defaultCodeBlock,
  args: undefined,
  kwargs: undefined,
  coalesce: false,
  max_instances: 1,
  trigger: undefined,
  trigger_args: undefined,
  start_date: undefined,
  end_date: undefined,
});

const argsList = ref<string[]>([]);
const kwargsList = ref<{ key: string; value: string }[]>([]);

const dialogVisible = reactive({
  title: "",
  visible: false,
  type: "create" as "create" | "update" | "detail",
});

const rules = reactive({
  name: [{ required: true, message: "请输入节点名称", trigger: "blur" }],
  code: [{ required: true, message: "请输入节点编码", trigger: "blur" }],
  trigger_args: [{ required: true, message: "请先配置执行计划参数", trigger: "blur" }],
});

const nodeDialogFormItems = computed<FormItem[]>(() => {
  const trig = formData.value.trigger;
  let planArgsLabel = "执行计划参数";
  if (trig === "cron") planArgsLabel = "Cron表达式";
  else if (trig === "interval") planArgsLabel = "间隔时间";
  else if (trig === "date") planArgsLabel = "执行时间";
  const isRangePlan = trig === "cron" || trig === "interval";

  return [
    {
      label: "节点名称",
      key: "name",
      type: "input",
      span: 24,
      props: { placeholder: "请输入节点名称", maxlength: 50 },
    },
    {
      label: "节点编码",
      key: "code",
      type: "input",
      span: 24,
      props: { placeholder: "请输入节点编码", maxlength: 32 },
    },
    {
      label: "执行计划",
      key: "trigger",
      type: "select",
      span: 24,
      placeholder: "",
      props: {
        clearable: true,
        placeholder: "不排程：仅保存定义，可手动执行一次",
        options: [
          { label: "Cron表达式", value: "cron" },
          { label: "时间间隔", value: "interval" },
          { label: "固定时间", value: "date" },
        ],
      },
    },
    {
      label: planArgsLabel,
      key: "trigger_args",
      type: "input",
      span: 24,
      placeholder: "",
      hidden: !trig,
    },
    {
      label: "开始时间",
      key: "start_date",
      type: "datetime",
      span: 24,
      hidden: !isRangePlan,
      props: {
        type: "datetime",
        format: "YYYY-MM-DD HH:mm:ss",
        valueFormat: "YYYY-MM-DD HH:mm:ss",
        placeholder: "请选择开始时间（可选）",
        style: { width: "100%" },
      },
    },
    {
      label: "结束时间",
      key: "end_date",
      type: "datetime",
      span: 24,
      hidden: !isRangePlan,
      props: {
        type: "datetime",
        format: "YYYY-MM-DD HH:mm:ss",
        valueFormat: "YYYY-MM-DD HH:mm:ss",
        placeholder: "请选择结束时间（可选）",
        style: { width: "100%" },
      },
    },
    {
      label: "存储器",
      key: "jobstore",
      type: "select",
      span: 24,
      placeholder: "",
    },
    {
      label: "执行器",
      key: "executor",
      type: "select",
      span: 24,
      placeholder: "",
    },
    {
      label: "位置参数",
      key: "args",
      type: "input",
      span: 24,
      placeholder: "",
    },
    {
      label: "关键字参数",
      key: "kwargs",
      type: "input",
      span: 24,
      placeholder: "",
    },
    {
      label: "合并运行",
      key: "coalesce",
      type: "radiogroup",
      span: 24,
      placeholder: "",
    },
    {
      label: "最大实例数",
      key: "max_instances",
      type: "number",
      span: 24,
      props: {
        controlsPosition: "right",
        min: 1,
        max: 10,
      },
    },
  ];
});

const initialFormData: Partial<NodeForm> = {
  id: undefined,
  name: "",
  code: undefined,
  jobstore: "sqlalchemy",
  executor: "default",
  func: defaultCodeBlock,
  args: undefined,
  kwargs: undefined,
  coalesce: false,
  max_instances: 5,
  trigger: undefined,
  trigger_args: undefined,
  start_date: undefined,
  end_date: undefined,
};

async function resetForm() {
  dataFormRef.value?.resetFields();
  dataFormRef.value?.clearValidate();
  Object.assign(formData.value, initialFormData);
  argsList.value = [];
  kwargsList.value = [];
  openCron.value = false;
  openInterval.value = false;
}

async function handleCloseDialog() {
  dialogVisible.visible = false;
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

async function handleOpenDialog(type: "create" | "update", id?: number) {
  dialogVisible.type = type;
  if (id) {
    const response = await NodeAPI.detailNode(id);
    dialogVisible.title = "修改节点";
    Object.assign(formData.value, response.data.data);
    const data = response.data.data;
    argsList.value = data.args ? data.args.split(",").map((v: string) => v.trim()) : [];
    kwargsList.value = data.kwargs
      ? Object.entries(JSON.parse(data.kwargs)).map(([key, value]) => ({
          key,
          value: String(value),
        }))
      : [];
  } else {
    dialogVisible.title = "新增节点";
    formData.value.id = undefined;
    argsList.value = [];
    kwargsList.value = [];
  }
  nodeFormRenderKey.value += 1;
  dialogVisible.visible = true;
}

function handleDialogOpened() {
  nextTick(() => {
    setTimeout(() => {
      codeEditorRef.value?.refresh?.();
    }, 100);
  });
}

async function handleSubmit() {
  dataFormRef.value?.validate(async (valid: boolean) => {
    if (valid) {
      submitLoading.value = true;
      const id = formData.value.id;
      const trig = formData.value.trigger;
      const kvList = kwargsList.value.filter((v) => v.key.trim());
      try {
        // 显式组装：执行计划随节点定义一起保存，trigger 为空则不排程
        const submitData = {
          name: formData.value.name,
          code: formData.value.code || undefined,
          jobstore: formData.value.jobstore,
          executor: formData.value.executor,
          func: formData.value.func,
          coalesce: formData.value.coalesce,
          max_instances: formData.value.max_instances,
          args: argsList.value.filter((v) => v.trim()).join(",") || undefined,
          kwargs:
            kvList.length > 0
              ? JSON.stringify(Object.fromEntries(kvList.map((v) => [v.key, v.value])))
              : undefined,
          trigger: trig || undefined,
          trigger_args: trig ? formData.value.trigger_args || undefined : undefined,
          start_date:
            trig === "cron" || trig === "interval"
              ? formData.value.start_date || undefined
              : undefined,
          end_date:
            trig === "cron" || trig === "interval" ? formData.value.end_date || undefined : undefined,
        };
        if (id) {
          await NodeAPI.updateNode(id, submitData);
        } else {
          await NodeAPI.createNode(submitData);
        }
        dialogVisible.visible = false;
        await resetForm();
        if (id) {
          await refreshUpdate();
        } else {
          await refreshCreate();
        }
      } catch (error: unknown) {
        if (import.meta.env.DEV) console.error(error);
      } finally {
        submitLoading.value = false;
      }
    }
  });
}

const handleIntervalConfirm = (value: string) => {
  formData.value.trigger_args = value;
  openInterval.value = false;
};

watch(openCron, (val) => {
  if (val) cronTempValue.value = formData.value.trigger_args || "";
});
</script>

<style scoped lang="scss">
.node-splitter-art-form :deep(.el-row > .el-col:last-child) {
  display: none;
}

.node-splitter-art-form :deep(.el-form-item__content) {
  max-width: 100%;
}

.node-splitter-art-form :deep(section) {
  padding-right: 10px;
  padding-left: 10px;
}
</style>
