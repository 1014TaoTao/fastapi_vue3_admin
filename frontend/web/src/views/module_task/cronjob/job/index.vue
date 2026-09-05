<!-- 调度任务：主区调度器状态 + 任务卡片列表（getSchedulerJobs 全量、前端筛选）；抽屉内执行日志表用 useTable 分页 -->
<template>
  <div class="fa-full-height job-page flex flex-col min-h-0">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="jobSearchItems"
      :rules="searchBarRules"
      :is-expand="false"
      :show-expand="true"
      :show-reset="true"
      :show-search="true"
      :disabled-search="false"
      :default-expanded="false"
      include-audit
      :audit-item-options="{ showCreatedBy: false, showUpdatedBy: false }"
      @search="handleSearchBarSearch"
      @reset="onResetSearch"
    />

    <ElCard
      class="flex flex-1 min-h-0 flex-col fa-table-card job-page-card"
      :style="{ 'margin-top': showSearchBar ? '12px' : '0' }"
    >
      <FaTableHeader
        v-model:columns="jobColumnChecks"
        v-model:showSearchBar="showSearchBar"
        layout="search,refresh"
        :loading="jobLoading"
        @refresh="refreshJobList"
      >
        <template #left>
          <div class="flex flex-wrap gap-1 items-center">
            <div class="flex gap-1 items-center">
              <div class="flex items-center gap-1 whitespace-nowrap">
                <span class="text-xs text-(--el-text-color-secondary)">调度器</span>
                <ElTag
                  :type="getSchedulerStatusType(schedulerStatus.status)"
                  size="small"
                  effect="dark"
                >
                  {{ getSchedulerStatusLabel(schedulerStatus.status) }}
                </ElTag>
              </div>
              <ElDivider direction="vertical" />
              <div class="flex items-center gap-1 whitespace-nowrap">
                <span class="text-xs text-(--el-text-color-secondary)">运行中</span>
                <ElTag
                  :type="schedulerStatus.is_running ? 'success' : 'info'"
                  size="small"
                  effect="dark"
                >
                  {{ schedulerStatus.is_running ? "是" : "否" }}
                </ElTag>
              </div>
              <ElDivider direction="vertical" />
              <div class="flex items-center gap-1 whitespace-nowrap">
                <span class="text-xs text-(--el-text-color-secondary)">任务</span>
                <span class="text-sm font-bold text-(--el-color-warning)">{{
                  schedulerStatus.job_count
                }}</span>
              </div>
            </div>
            <ElDivider direction="vertical" />
            <div class="flex flex-wrap gap-1 items-center">
              <ElButton
                v-hasPerm="['module_task:cronjob:job:scheduler']"
                type="success"
                :icon="VideoPlay"
                :disabled="schedulerStatus.status !== '停止'"
                size="small"
                @click="handleStartScheduler"
              >
                启动
              </ElButton>
              <ElButton
                v-hasPerm="['module_task:cronjob:job:scheduler']"
                type="warning"
                :icon="VideoPause"
                :disabled="schedulerStatus.status !== '运行中'"
                size="small"
                @click="handlePauseScheduler"
              >
                暂停
              </ElButton>
              <ElButton
                v-hasPerm="['module_task:cronjob:job:scheduler']"
                type="primary"
                :icon="RefreshRight"
                :disabled="schedulerStatus.status !== '暂停'"
                size="small"
                @click="handleResumeScheduler"
              >
                恢复
              </ElButton>
              <ElButton
                v-hasPerm="['module_task:cronjob:job:scheduler']"
                type="danger"
                :icon="SwitchButton"
                :disabled="schedulerStatus.status === '停止'"
                size="small"
                @click="handleShutdownScheduler"
              >
                关闭
              </ElButton>
              <ElDivider direction="vertical" />
              <ElButton
                v-hasPerm="['module_task:cronjob:job:task']"
                type="danger"
                :icon="Delete"
                :disabled="schedulerStatus.job_count === 0"
                size="small"
                plain
                @click="handleClearAllJobs"
              >
                清空任务
              </ElButton>
              <ElButton
                v-hasPerm="['module_task:cronjob:job:query']"
                type="info"
                :icon="Monitor"
                size="small"
                @click="handleOpenConsole"
              >
                控制台
              </ElButton>
            </div>
          </div>
        </template>
      </FaTableHeader>

      <!-- 卡片骨架：初始加载时显示 -->
      <ElSkeleton v-if="jobLoading && (!jobList || jobList.length === 0)" animated class="mt-3">
        <template #template>
          <div class="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-4">
            <div v-for="i in 12" :key="i" class="h-50">
              <ElSkeletonItem
                variant="rect"
                style="width: 100%; height: 100%; border-radius: var(--custom-radius)"
              />
            </div>
          </div>
        </template>
      </ElSkeleton>

      <ElScrollbar v-else class="job-cards-container mt-3 min-h-0 flex-1">
        <ElEmpty
          v-if="!jobLoading && (!jobList || jobList.length === 0)"
          :image-size="80"
          description="暂无数据"
        />
        <ElRow v-else :gutter="16">
          <ElCol
            v-for="job in jobList"
            :key="job.id"
            :xs="24"
            :sm="12"
            :md="6"
            :lg="4"
            class="mb-4"
          >
            <ElCard
              shadow="hover"
              :class="`fa-card job-card job-card--${getJobStatusClass(job.status)}`"
            >
              <template #header>
                <div class="job-card-title">
                  <span
                    class="job-card-dot"
                    :class="`job-card-dot--${getJobStatusClass(job.status)}`"
                  />
                  <ElTooltip :content="job.name" placement="top">
                    <span class="job-card-name">{{ job.name }}</span>
                  </ElTooltip>
                  <ElTag :type="getJobStatusType(job.status)" size="small" effect="dark">
                    {{ getJobStatusLabel(job.status) }}
                  </ElTag>
                </div>
              </template>

              <div class="job-card-body cursor-pointer" @click="handleOpenExecutionLogDrawer(job)">
                <div class="job-card-body-row">
                  <FaSvgIcon :icon="getTriggerIcon(job.trigger)" class="job-card-meta-icon" />
                  <span class="job-card-meta-text">{{ formatTrigger(job.trigger) }}</span>
                </div>
                <div class="job-card-body-row">
                  <FaSvgIcon icon="ri:time-line" class="job-card-meta-icon" />
                  <span class="job-card-meta-text">{{ job.next_run_time || "暂无" }}</span>
                </div>
              </div>

              <template #footer>
                <ElRow :gutter="8">
                  <ElCol :span="6">
                    <ElButton
                      v-hasPerm="['module_task:cronjob:job:task']"
                      :type="job.status === 1 ? 'primary' : 'warning'"
                      size="small"
                      plain
                      class="w-full"
                      :icon="job.status === 1 ? VideoPlay : VideoPause"
                      :disabled="job.status !== 1 && job.status !== 0"
                      @click="job.status === 1 ? handleResumeJob(job.id) : handlePauseJob(job.id)"
                    >
                      {{ job.status === 1 ? "恢复" : "暂停" }}
                    </ElButton>
                  </ElCol>
                  <ElCol :span="6">
                    <ElButton
                      v-hasPerm="['module_task:cronjob:job:task']"
                      type="success"
                      size="small"
                      plain
                      class="w-full"
                      :icon="CaretRight"
                      :disabled="job.status === 2 || job.status === 3"
                      @click="handleRunJobNow(job.id)"
                    >
                      调试
                    </ElButton>
                  </ElCol>
                  <ElCol :span="6">
                    <ElButton
                      v-hasPerm="['module_task:cronjob:job:task']"
                      type="primary"
                      size="small"
                      plain
                      class="w-full"
                      :icon="Edit"
                      :disabled="job.status === 3"
                      @click="handleOpenModifyDialog(job)"
                    >
                      编辑
                    </ElButton>
                  </ElCol>
                  <ElCol :span="6">
                    <ElButton
                      v-hasPerm="['module_task:cronjob:job:task']"
                      type="danger"
                      size="small"
                      plain
                      class="w-full"
                      :icon="Close"
                      :disabled="job.status === 3"
                      @click="handleRemoveJob(job.id, job.name)"
                    >
                      移除
                    </ElButton>
                  </ElCol>
                </ElRow>
              </template>
            </ElCard>
          </ElCol>
        </ElRow>
      </ElScrollbar>
    </ElCard>

    <FaDialog v-model="consoleVisible" title="调度器控制台" width="900px">
      <div class="terminal-wrapper">
        <Terminal name="scheduler-console" :show-header="false" theme="dark" />
      </div>
      <template #footer>
        <ElButton @click="handleRefreshConsole">刷新</ElButton>
        <ElButton @click="handleClearConsole">清空</ElButton>
        <ElButton type="primary" @click="consoleVisible = false">关闭</ElButton>
      </template>
    </FaDialog>

    <FaDrawer v-model="executionLogDrawerVisible" title="执行记录" direction="rtl" size="80%">
      <div class="flex flex-col min-h-0 h-full">
        <FaSearchBar
          ref="logSearchBarRef"
          v-model="logSearchForm"
          :items="logSearchItems"
          :rules="logSearchBarRules"
          :is-expand="false"
          :show-expand="false"
          :show-reset="true"
          :show-search="true"
          :disabled-search="false"
          :default-expanded="false"
          @search="handleLogSearchBarSearch"
          @reset="onLogResetSearch"
        />
        <ElCard class="fa-table-card mt-3 flex flex-1 min-h-0 flex-col">
          <FaTableHeader
            v-model:columns="logColumnChecks"
            layout="search,refresh"
            :loading="logLoading"
            @refresh="refreshLogData"
          >
            <template #left>
              <FaTableHeaderLeft
                :remove-ids="logSelectedIds"
                :perm-delete="['module_task:cronjob:job:delete']"
                :delete-loading="logBatchDeleting"
                @delete="handleLogBatchDelete"
              />
            </template>
          </FaTableHeader>
          <FaTable
            ref="logfaTableRef"
            row-key="id"
            :loading="logLoading"
            :data="logTableData"
            :columns="logColumns"
            :pagination="logPaginationBind"
            @selection-change="onLogTableSelectionChange"
            @pagination:size-change="logHandleSizeChange"
            @pagination:current-change="logHandleCurrentChange"
          >
          </FaTable>
        </ElCard>
      </div>
    </FaDrawer>

    <FaDialog v-model="jobStateVisible" title="执行元数据" width="800px">
      <FaJsonPretty :value="jobStateData" height="400px" />
      <template #footer>
        <ElButton type="primary" @click="jobStateVisible = false">关闭</ElButton>
      </template>
    </FaDialog>

    <!-- 修改任务弹窗 -->
    <FaDialog
      v-model="modifyDialog.visible"
      :title="`修改任务 - ${modifyDialog.jobName}`"
      width="480px"
      :confirm-loading="modifyDialog.loading"
      @confirm="handleModifyJob"
      @close="modifyDialog.visible = false"
    >
      <ElForm :model="modifyForm" label-width="100px" label-suffix=":">
        <ElFormItem label="任务名称">
          <ElInput v-model="modifyForm.name" placeholder="请输入任务名称" />
        </ElFormItem>
        <ElFormItem label="合并运行">
          <ElRadioGroup v-model="modifyForm.coalesce">
            <ElRadio :value="true">是</ElRadio>
            <ElRadio :value="false">否</ElRadio>
          </ElRadioGroup>
        </ElFormItem>
        <ElFormItem label="最大实例数">
          <ElInputNumber
            v-model="modifyForm.max_instances"
            :min="1"
            :max="10"
            controls-position="right"
            style="width: 100%"
          />
        </ElFormItem>
      </ElForm>
    </FaDialog>

    <!-- 执行记录详情弹窗 -->
    <FaDialog
      v-model="logDetailDialog.visible"
      title="执行记录详情"
      width="720px"
      form-mode="detail"
      @close="logDetailDialog.visible = false"
    >
      <FaDescriptions
        :column="4"
        :data="logDetailFormData"
        :items="logDetailItems"
        max-height="70vh"
      />
    </FaDialog>
  </div>
</template>

<script lang="ts" setup>
defineOptions({
  name: "Job",
  inheritAttrs: false,
});

import JobAPI, {
  type SchedulerStatus,
  type SchedulerJob,
  type JobLogTable,
} from "@/api/module_task/cronjob/job";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import FaTable from "@/components/tables/fa-table/index.vue";
import FaDialog from "@/components/modal/fa-dialog/index.vue";
import FaDrawer from "@/components/modal/fa-drawer/index.vue";
import {
  VideoPlay,
  VideoPause,
  RefreshRight,
  SwitchButton,
  Delete,
  Monitor,
  CaretRight,
  Edit,
  Close,
} from "@element-plus/icons-vue";
import { renderTableOperationCell, type TableOperationAction } from "@utils";
import { Terminal, TerminalApi } from "vue-web-terminal";
import type { ColumnOption } from "@/types/component";

const schedulerStatus = ref<SchedulerStatus>({
  status: "未知",
  is_running: false,
  job_count: 0,
});

type JobSearchForm = {
  name?: string;
  status?: number;
};

const searchForm = ref<JobSearchForm>({
  name: undefined,
  status: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const searchBarRules: Record<string, unknown> = {};

const jobSearchItems = computed<SearchFormItem[]>(() => [
  {
    label: "任务名称",
    key: "name",
    type: "input",
    placeholder: "请输入任务名称",
    clearable: true,
    span: 6,
  },
  {
    label: "任务状态",
    key: "status",
    type: "select",
    props: {
      placeholder: "请选择状态",
      clearable: true,
      options: [
        { label: "运行中", value: 0 },
        { label: "暂停中", value: 1 },
        { label: "已停止", value: 2 },
      ],
    },
    span: 6,
  },
]);

async function loadSchedulerStatus() {
  try {
    const statusRes = await JobAPI.getSchedulerStatus();
    schedulerStatus.value = statusRes.data.data;
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error(error);
  }
}

/** 调度器任务列表为全量列表接口，无分页；筛选在前端完成 */
const jobList = ref<SchedulerJob[]>([]);
const jobLoading = ref(false);
/** 主区域为卡片列表无表格列配置，仅占位满足 FaTableHeader v-model */
const jobColumnChecks = ref<ColumnOption<SchedulerJob>[]>([]);

function matchesJobStatusFilter(jobStatus: number | undefined, filter?: number): boolean {
  if (filter === undefined) return true;
  const map: Record<number, number[]> = {
    0: [0], // 运行中
    1: [1], // 暂停
    2: [2], // 停止
  };
  const allowed = map[filter];
  if (!allowed) return true;
  return allowed.includes(jobStatus ?? -1);
}

async function fetchSchedulerJobs() {
  jobLoading.value = true;
  try {
    const res = await JobAPI.getSchedulerJobs();
    const raw = res.data?.data;
    const list: SchedulerJob[] = Array.isArray(raw) ? raw : [];
    const nameQ = searchForm.value.name?.trim();
    const statusQ = searchForm.value.status;
    jobList.value = list.filter((j) => {
      if (nameQ && !(j.name ?? "").includes(nameQ)) return false;
      if (!matchesJobStatusFilter(j.status, statusQ)) return false;
      return true;
    });
    await loadSchedulerStatus();
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error(error);
    jobList.value = [];
  } finally {
    jobLoading.value = false;
  }
}

const refreshJobList = fetchSchedulerJobs;

async function handleSearchBarSearch() {
  await searchBarRef.value?.validate?.();
  await fetchSchedulerJobs();
}

async function onResetSearch() {
  searchForm.value = {
    name: undefined,
    status: undefined,
  };
  await fetchSchedulerJobs();
}

onMounted(() => {
  void fetchSchedulerJobs();
});

type LogSearchForm = {
  status?: number;
  trigger_type?: string;
  created_time?: string[];
  updated_time?: string[];
};

function buildLogReplaceParams(u: LogSearchForm): Record<string, unknown> {
  return {
    status: u.status,
    trigger_type: u.trigger_type,
    created_time:
      Array.isArray(u.created_time) && u.created_time.length === 2 ? u.created_time : undefined,
    updated_time:
      Array.isArray(u.updated_time) && u.updated_time.length === 2 ? u.updated_time : undefined,
  };
}

const logSearchForm = ref<LogSearchForm>({
  status: undefined,
  trigger_type: undefined,
  created_time: undefined,
  updated_time: undefined,
});

const logSearchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const logSearchBarRules: Record<string, unknown> = {};

const logSearchItems = computed<SearchFormItem[]>(() => [
  {
    label: "执行状态",
    key: "status",
    type: "select",
    props: {
      placeholder: "请选择状态",
      clearable: true,
      options: [
        { label: "待执行", value: "pending" },
        { label: "执行中", value: "running" },
        { label: "成功", value: "success" },
        { label: "失败", value: "failed" },
        { label: "超时", value: "timeout" },
        { label: "已取消", value: "cancelled" },
      ],
    },
    span: 8,
  },
  {
    label: "触发方式",
    key: "trigger_type",
    type: "select",
    props: {
      placeholder: "请选择",
      clearable: true,
      options: [
        { label: "Cron表达式", value: "cron" },
        { label: "时间间隔", value: "interval" },
        { label: "固定日期", value: "date" },
        { label: "一次性任务", value: "manual" },
      ],
    },
    span: 8,
  },
]);

const currentLogJobId = ref<string | undefined>(undefined);
function buildLogRowActions(row: JobLogTable): TableOperationAction[] {
  const all: TableOperationAction[] = [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_task:cronjob:job:detail",
      run: () => handleOpenLogDetail(row),
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      perm: "module_task:cronjob:job:delete",
      run: () => deleteLogRow(row.id, String(row?.job_name ?? row?.id ?? "")),
    },
  ];
  return all;
}

function formatLogOperationCell(row: JobLogTable) {
  return renderTableOperationCell(buildLogRowActions(row));
}

const logfaTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);
const logSelectedRows = ref<JobLogTable[]>([]);
const logSelectedIds = computed(() =>
  logSelectedRows.value.map((r) => r.id).filter((id): id is number => typeof id === "number")
);
const logBatchDeleting = ref(false);

function onLogTableSelectionChange(rows: JobLogTable[]) {
  logSelectedRows.value = rows;
}

const {
  columns: logColumns,
  columnChecks: logColumnChecks,
  data: logTableData,
  loading: logLoading,
  pagination: logPagination,
  getData: getLogData,
  replaceSearchParams: replaceLogSearchParams,
  resetSearchParams: resetLogSearchParams,
  handleSizeChange: logHandleSizeChange,
  handleCurrentChange: logHandleCurrentChange,
  refreshData: refreshLogData,
  refreshRemove: refreshLogRemove,
} = useTable({
  core: {
    apiFn: JobAPI.getJobLogList,
    immediate: false,
    apiParams: {
      page_no: 1,
      page_size: 10,
      job_id: "",
      status: undefined,
      trigger_type: undefined,
    },
    columnsFactory: (): ColumnOption<JobLogTable>[] => [
      { type: "selection", width: 48, fixed: "left" },
      { type: "globalIndex", width: 56, label: "序号" },
      {
        prop: "job_id",
        label: "任务ID",
        minWidth: 80,
        showOverflowTooltip: true,
      },
      {
        prop: "job_name",
        label: "任务名称",
        minWidth: 140,
        showOverflowTooltip: true,
      },
      {
        prop: "trigger_type",
        label: "触发方式",
        minWidth: 120,
        status: {
          cron: { type: "info", text: "Cron表达式" },
          interval: { type: "info", text: "时间间隔" },
          date: { type: "info", text: "固定日期" },
          manual: { type: "info", text: "一次性任务" },
        },
      },
      {
        prop: "status",
        label: "状态",
        minWidth: 80,
        status: {
          pending: { type: "info", text: "待执行" },
          running: { type: "primary", text: "执行中" },
          success: { type: "success", text: "成功" },
          failed: { type: "danger", text: "失败" },
          timeout: { type: "warning", text: "超时" },
          cancelled: { type: "info", text: "已取消" },
        },
      },
      {
        prop: "next_run_time",
        label: "下次执行时间",
        minWidth: 200,
        showOverflowTooltip: true,
      },
      {
        prop: "result",
        label: "执行结果",
        minWidth: 100,
        showOverflowTooltip: true,
      },
      {
        prop: "error",
        label: "错误信息",
        minWidth: 100,
        showOverflowTooltip: true,
      },
      {
        prop: "job_state",
        label: "执行元数据",
        minWidth: 100,
        formatter: (row: JobLogTable) => {
          if (!row.job_state) return h("span", null, "—");
          return h(
            ElButton,
            { type: "primary", size: "small", link: true, onClick: () => handleViewJobState(row) },
            () => "查看"
          );
        },
      },
      {
        prop: "created_time",
        label: "创建时间",
        minWidth: 160,
        sortable: true,
        showOverflowTooltip: true,
      },
      {
        prop: "updated_time",
        label: "更新时间",
        minWidth: 160,
        sortable: true,
        showOverflowTooltip: true,
      },
      {
        prop: "operation",
        label: "操作",
        width: 88,
        fixed: "right",
        align: "center",
        formatter: (row: JobLogTable) => formatLogOperationCell(row),
      },
    ],
  },
});

async function deleteLogRow(id: number | undefined, name: string | number) {
  if (id == null) return;
  try {
    await confirmDelete(`确定删除执行记录「${name}」吗？`);
    await JobAPI.deleteJobLog([id]);
    logfaTableRef.value?.elTableRef?.clearSelection();
    await refreshLogRemove();
  } catch {
    // 用户取消
  }
}

async function handleLogBatchDelete() {
  const ids = logSelectedIds.value;
  if (ids.length === 0) return;
  try {
    await confirmBatchDelete(
      ids.length,
      logSelectedRows.value.map((r) => String(r?.job_name ?? r?.id ?? ""))
    );
    logBatchDeleting.value = true;
    await JobAPI.deleteJobLog(ids);
    logSelectedRows.value = [];
    await refreshLogRemove();
  } catch {
    // 用户取消
  } finally {
    logBatchDeleting.value = false;
  }
}

const logPaginationBind = computed(() => {
  const p = logPagination as unknown as {
    current?: number;
    size?: number;
    total?: number;
    page_no?: number;
    page_size?: number;
  };
  return {
    current: p.current ?? p.page_no ?? 1,
    size: p.size ?? p.page_size ?? 10,
    total: p.total ?? 0,
  };
});

async function handleLogSearchBarSearch(params: LogSearchForm) {
  await logSearchBarRef.value?.validate?.();
  if (!currentLogJobId.value) return;
  replaceLogSearchParams({
    ...buildLogReplaceParams(params),
    job_id: currentLogJobId.value,
  });
  await getLogData();
}

async function onLogResetSearch() {
  logSearchForm.value = {
    status: undefined,
    trigger_type: undefined,
    created_time: undefined,
    updated_time: undefined,
  };
  await resetLogSearchParams();
  if (currentLogJobId.value) {
    replaceLogSearchParams({ job_id: currentLogJobId.value });
    await getLogData();
  }
}

const consoleVisible = ref(false);

const executionLogDrawerVisible = ref(false);
const jobStateVisible = ref(false);
const jobStateData = ref<string | Record<string, unknown> | undefined>(undefined);

// ─── 修改任务弹窗 ───
const modifyDialog = reactive({
  visible: false,
  loading: false,
  jobId: "",
  jobName: "",
});
const modifyForm = reactive({
  name: "",
  coalesce: true,
  max_instances: 5,
});

function handleOpenModifyDialog(job: SchedulerJob) {
  modifyDialog.jobId = job.id;
  modifyDialog.jobName = job.name;
  modifyForm.name = job.name;
  modifyForm.coalesce = true;
  modifyForm.max_instances = 5;
  modifyDialog.visible = true;
}

async function handleModifyJob() {
  modifyDialog.loading = true;
  try {
    await JobAPI.modifyJob(modifyDialog.jobId, { ...modifyForm });
    modifyDialog.visible = false;
    await refreshJobList();
  } catch {
    /* 已由全局拦截器提示 */
  } finally {
    modifyDialog.loading = false;
  }
}

// ─── 执行记录详情弹窗 ───
const logDetailDialog = reactive({
  visible: false,
});
const logDetailFormData = ref<JobLogTable>({} as JobLogTable);

const logDetailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] =
  [
    { label: "任务ID", prop: "job_id" },
    { label: "任务名称", prop: "job_name" },
    { label: "触发方式", prop: "trigger_type" },
    { label: "执行状态", prop: "status" },
    { label: "下次执行时间", prop: "next_run_time" },
    { label: "执行结果", prop: "result", span: 4 },
    { label: "错误信息", prop: "error", span: 4 },
    { label: "创建时间", prop: "created_time" },
    { label: "更新时间", prop: "updated_time" },
  ];

async function handleOpenLogDetail(row: JobLogTable) {
  if (row.id == null) return;
  try {
    const res = await JobAPI.getJobLogDetail(row.id);
    Object.assign(logDetailFormData.value, res.data.data ?? {});
    logDetailDialog.visible = true;
  } catch {
    /* 已由全局拦截器提示 */
  }
}

function getSchedulerStatusType(status: string) {
  switch (status) {
    case "运行中":
      return "success";
    case "暂停":
      return "warning";
    case "停止":
      return "danger";
    default:
      return "info";
  }
}

function getSchedulerStatusLabel(status: string) {
  return status || "未知";
}

function getJobStatusType(status: number) {
  switch (status) {
    case 0:
      return "success";
    case 1:
      return "warning";
    case 2:
      return "danger";
    case 3:
      return "info";
    default:
      return "info";
  }
}

function getJobStatusLabel(status: number) {
  switch (status) {
    case 0:
      return "运行中";
    case 1:
      return "暂停中";
    case 2:
      return "已停止";
    case 3:
      return "未知";
    default:
      return status;
  }
}

function formatTrigger(trigger: string) {
  if (!trigger) {
    return "-";
  }

  if (trigger.includes("cron")) {
    const match = trigger.match(/cron\[([^\]]+)\]/);
    if (match) {
      const params = match[1]!;
      // 提取关键参数
      const month = params.match(/month='([^']+)'/);
      const day = params.match(/day='([^']+)'/);
      const hour = params.match(/hour='([^']+)'/);
      const minute = params.match(/minute='([^']+)'/);
      const second = params.match(/second='([^']+)'/);
      const dayOfWeek = params.match(/day_of_week='([^']+)'/);

      // 构建简化的 cron 表达式
      const parts = [];
      if (second && second[1] !== "'*'") parts.push(`秒:${second[1]}`);
      if (minute && minute[1] !== "'*'") parts.push(`分:${minute[1]}`);
      if (hour && hour[1] !== "'*'") parts.push(`时:${hour[1]}`);
      if (day && day[1] !== "'*'") parts.push(`日:${day[1]}`);
      if (month && month[1] !== "'*'") parts.push(`月:${month[1]}`);
      if (dayOfWeek && dayOfWeek[1] !== "'*'") parts.push(`周:${dayOfWeek[1]}`);

      if (parts.length === 0) {
        return "Cron: 每分钟";
      }
      return `Cron: ${parts.join(" ")}`;
    }
    return trigger;
  }

  if (trigger.includes("interval")) {
    const match = trigger.match(/interval\[([^\]]+)\]/);
    return match ? `间隔时长: ${match[1]}` : trigger;
  }

  if (trigger.includes("date")) {
    const match = trigger.match(/date\[([^\]]+)\]/);
    return match ? `执行日期: ${match[1]}` : trigger;
  }

  return trigger;
}

async function handleStartScheduler() {
  try {
    await JobAPI.startScheduler();
    await refreshJobList();
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error(error);
  }
}

async function handlePauseScheduler() {
  try {
    await JobAPI.pauseScheduler();
    await refreshJobList();
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error(error);
  }
}

async function handleResumeScheduler() {
  try {
    await JobAPI.resumeScheduler();
    await refreshJobList();
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error(error);
  }
}

async function handleShutdownScheduler() {
  try {
    await confirmDelete("确定要关闭调度器吗？");
    await JobAPI.shutdownScheduler();
    await refreshJobList();
  } catch (error: unknown) {
    if (error !== "cancel") {
      if (import.meta.env.DEV) console.error(error);
    }
  }
}

async function handleClearAllJobs() {
  try {
    await confirmDelete(
      "确定要清空所有任务吗？此操作会将所有待执行任务的日志标记为已取消，不会删除历史执行记录。"
    );
    await JobAPI.clearAllJobs();
    await refreshJobList();
  } catch (error: unknown) {
    if (error !== "cancel") {
      if (import.meta.env.DEV) console.error(error);
    }
  }
}

async function handleOpenConsole() {
  consoleVisible.value = true;
  await handleRefreshConsole();
}

async function handleRefreshConsole() {
  try {
    const response = await JobAPI.getSchedulerConsole();
    const data = response.data.data || "暂无任务信息";
    TerminalApi.pushMessage("scheduler-console", {
      type: "normal",
      content: data,
    });
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error(error);
    TerminalApi.pushMessage("scheduler-console", {
      type: "normal",
      class: "error",
      content: "获取控制台信息失败",
    });
  }
}

function handleClearConsole() {
  TerminalApi.clear("scheduler-console");
}

async function handlePauseJob(jobId: string) {
  try {
    await JobAPI.pauseJob(jobId);
    await refreshJobList();
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error(error);
  }
}

async function handleResumeJob(jobId: string) {
  try {
    await JobAPI.resumeJob(jobId);
    await refreshJobList();
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error(error);
  }
}

async function handleRunJobNow(jobId: string) {
  try {
    await JobAPI.runJobNow(jobId);
    await refreshJobList();
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error(error);
  }
}

async function handleRemoveJob(jobId: string, name: string) {
  try {
    await confirmDelete(`确定移除任务「${name}」吗？`);
    await JobAPI.removeJob(jobId);
    await refreshJobList();
  } catch {
    // 用户取消
  }
}

async function handleOpenExecutionLogDrawer(job: SchedulerJob) {
  currentLogJobId.value = job.id;
  logSearchForm.value = {
    status: undefined,
    trigger_type: undefined,
    created_time: undefined,
    updated_time: undefined,
  };
  executionLogDrawerVisible.value = true;
  await nextTick();
  replaceLogSearchParams({
    job_id: job.id,
    page_no: 1,
    page_size: 10,
  });
  getLogData();
}

function getJobStatusClass(status: number) {
  switch (status) {
    case 0:
      return "running";
    case 1:
      return "paused";
    case 2:
      return "stopped";
    default:
      return "unknown";
  }
}

function getTriggerIcon(trigger: string | undefined) {
  const t = (trigger ?? "").toLowerCase();
  if (t.includes("cron")) return "ri:timer-line";
  if (t.includes("interval")) return "ri:repeat-line";
  if (t.includes("date")) return "ri:calendar-event-line";
  return "ri:flashlight-line";
}

function handleViewJobState(row: JobLogTable) {
  const jobState = row.job_state;
  if (jobState) {
    try {
      jobStateData.value = JSON.parse(jobState);
    } catch {
      jobStateData.value = jobState;
    }
    jobStateVisible.value = true;
  }
}
</script>

<style scoped lang="scss">
.job-page :deep(.data-table) {
  height: 100%;
}

.terminal-wrapper {
  height: 500px;
}

.job-page-card {
  :deep(.el-card__body) {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
  }
}

.job-card {
  :deep(.el-card__header) {
    padding: 8px 16px;
  }

  :deep(.el-card__body) {
    padding: 8px 16px;
  }

  :deep(.el-card__footer) {
    padding: 8px 16px;
  }
}

.job-card-title {
  display: flex;
  gap: 6px;
  align-items: center;
  min-width: 0;
}

.job-card-dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;

  &--running {
    background: var(--el-color-success);
  }

  &--paused {
    background: var(--el-color-warning);
  }

  &--stopped {
    background: var(--el-color-danger);
  }

  &--unknown {
    background: var(--el-color-info);
  }
}

.job-card-body {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
  overflow: hidden;

  &-row {
    display: flex;
    gap: 4px;
    align-items: center;
    min-width: 0;
    overflow: hidden;
  }
}

.job-card-name {
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}

.job-card-meta-icon {
  flex-shrink: 0;
  font-size: 13px;
  color: var(--el-color-primary-light-3);
}

.job-card-meta-text {
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.execution-log-drawer :deep(.el-card.data-table) {
  flex: 1;
  min-height: 0;
}
</style>
