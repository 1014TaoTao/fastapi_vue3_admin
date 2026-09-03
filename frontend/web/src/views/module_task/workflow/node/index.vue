<!-- 节点/存储源管理：存储源 CRUD + 连接测试 + 打开浏览（源项目风格） -->
<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="sourceSearchItems"
      :rules="searchBarRules"
      :is-expand="false"
      :show-expand="true"
      :show-reset="true"
      :show-search="true"
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
            :perm-create="['module_task:workflow:node:create']"
            :perm-delete="['module_task:workflow:node:delete']"
            :delete-loading="batchDeleting"
            :create-loading="createLoading"
            @add="handleAdd"
            @delete="handleBatchDelete"
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
      width="720px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      :form-mode="dialogVisible.type"
      :confirm-loading="submitLoading"
      @cancel="handleCloseDialog"
      @confirm="dialogVisible.type === 'detail' ? handleCloseDialog() : handleSubmit()"
    >
      <template v-if="dialogVisible.type === 'detail'">
        <FaDescriptions
          :column="2"
          :data="detailFormData"
          :items="sourceDetailItems"
          max-height="70vh"
        >
          <template #protocol="{ row }">
            <span>{{ protocolLabel((row as unknown as SourceTable)?.protocol) }}</span>
          </template>
          <template #is_default="{ row }">
            <FaStatusTag v-if="row?.is_default" type="success" label="默认" />
            <FaStatusTag v-else type="info" label="否" />
          </template>
          <template #is_secure="{ row }">
            <span>{{ row?.is_secure ? "是" : "否" }}</span>
          </template>
          <template #has_password="{ row }">
            <span>{{ row?.has_password ? "已配置" : "未配置" }}</span>
          </template>
        </FaDescriptions>
      </template>
      <template v-else>
        <FaForm
          :key="sourceFormRenderKey"
          scrollbar
          max-height="70vh"
          ref="dataFormRef"
          v-model="formData"
          :items="sourceDialogFormItems"
          :rules="rules"
          label-suffix=":"
          :label-width="110"
          label-position="right"
          :span="24"
          :gutter="16"
          :show-reset="false"
          :show-submit="false"
          class="crud-dialog-art-form"
        >
          <template #advanced_config>
            <ElCollapse
              v-if="currentAdvancedFields.length"
              v-model="advancedCollapseActive"
              class="w-full border-none"
            >
              <ElCollapseItem name="advanced">
                <template #title>
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium text-gray-800">SDK 高级设置</span>
                    <ElTag size="small" type="info" effect="plain">留空使用 SDK 默认值</ElTag>
                  </div>
                </template>
                <ElRow :gutter="16">
                  <ElCol
                    v-for="field in currentAdvancedFields"
                    :key="field.key"
                    :span="12"
                    class="mb-3"
                  >
                    <div class="mb-1.5 text-[13px] leading-5 text-gray-600">{{ field.label }}</div>
                    <ElInput
                      v-if="field.type === 'text'"
                      :model-value="(formData.advanced_config?.[field.key] as string) ?? ''"
                      :placeholder="`默认：${field.default ?? '-'}`"
                      clearable
                      @update:model-value="setAdvancedValue(field.key, $event)"
                    />
                    <ElInputNumber
                      v-else-if="field.type === 'number'"
                      :model-value="(formData.advanced_config?.[field.key] as number) ?? undefined"
                      :placeholder="`默认：${field.default ?? '-'}`"
                      controls-position="right"
                      class="w-full"
                      @update:model-value="setAdvancedValue(field.key, $event)"
                    />
                    <ElSwitch
                      v-else-if="field.type === 'boolean'"
                      :model-value="Boolean(formData.advanced_config?.[field.key])"
                      inline-prompt
                      active-text="开"
                      inactive-text="关"
                      @update:model-value="setAdvancedValue(field.key, $event)"
                    />
                    <ElSelect
                      v-else
                      :model-value="(formData.advanced_config?.[field.key] as string) ?? ''"
                      :placeholder="`默认：${field.default ?? '-'}`"
                      clearable
                      class="w-full"
                      @update:model-value="setAdvancedValue(field.key, $event)"
                    >
                      <ElOption v-for="opt in field.options" :key="opt" :label="opt" :value="opt" />
                    </ElSelect>
                  </ElCol>
                </ElRow>
              </ElCollapseItem>
            </ElCollapse>
          </template>
        </FaForm>
      </template>
      <template #footer>
        <div
          v-if="dialogVisible.type === 'detail'"
          class="fa-dialog-footer"
          style="padding-right: var(--el-dialog-padding-primary)"
        >
          <ElButton type="primary" @click="handleCloseDialog">关闭</ElButton>
        </div>
        <div
          v-else
          class="fa-dialog-footer"
          style="padding-right: var(--el-dialog-padding-primary)"
        >
          <ElButton :loading="testing" style="margin-right: auto" @click="handleTestConfig"
            >测试连接</ElButton
          >
          <ElButton type="primary" plain @click="handleCloseDialog">取消</ElButton>
          <ElButton type="primary" :loading="submitLoading" @click="handleSubmit">确定</ElButton>
        </div>
      </template>
    </FaDialog>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { ElTag } from "element-plus";
import { useCrudForm } from "@/hooks/core/useCrudForm";
import { resolveStatusColumns, renderTableOperationCell, type TableOperationAction } from "@utils";
import NodeAPI, {
  type AdvancedFieldDef,
  type SourceForm,
  type SourceTable,
} from "@/api/module_task/workflow/node";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import FaForm from "@/components/forms/fa-form/index.vue";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";

defineOptions({
  name: "WorkflowNode",
  inheritAttrs: false,
});

const router = useRouter();

// 协议选项：默认内置，挂载后经 /node/protocols 刷新（保留友好中文标签）
const PROTOCOL_LABELS: Record<string, string> = {
  ftp: "FTP",
  ftps: "FTPS",
  sftp: "SFTP",
  s3: "S3",
  obs: "OBS(华为云)",
  oss: "OSS(阿里云)",
  cos: "COS(腾讯云)",
  local: "本地目录",
};
const PROTOCOL_OPTIONS = ref([
  { label: "FTP", value: "ftp" },
  { label: "FTPS", value: "ftps" },
  { label: "SFTP", value: "sftp" },
  { label: "S3", value: "s3" },
  { label: "OBS(华为云)", value: "obs" },
  { label: "OSS(阿里云)", value: "oss" },
  { label: "COS(腾讯云)", value: "cos" },
  { label: "本地目录", value: "local" },
]);
async function loadProtocols() {
  const { data } = await NodeAPI.getProtocols();
  const items = data.data ?? [];
  PROTOCOL_OPTIONS.value = items.map((p) => ({
    label: PROTOCOL_LABELS[p.protocol] ?? p.name ?? p.protocol,
    value: p.protocol,
  }));
}
void loadProtocols();

const STATUS_OPTIONS = [
  { label: "启用", value: 0 },
  { label: "停用", value: 1 },
] as const;

const ENCRYPT_OPTIONS = [
  { label: "只要求明文", value: 0 },
  { label: "显式TLS(可用时)", value: 1 },
  { label: "要求显式TLS", value: 2 },
  { label: "要求隐式TLS", value: 3 },
] as const;

const CONNECTION_MODE_OPTIONS = [
  { label: "默认", value: 0 },
  { label: "主动 (PORT)", value: 1 },
  { label: "被动 (PASV)", value: 2 },
] as const;

// 各对象存储协议的区域字典（切换协议时自动带出默认区域）
const regionDict: Record<string, { options: string[]; default: string }> = {
  s3: {
    options: ["us-east-1", "us-west-2", "ap-northeast-1", "ap-southeast-1", "ap-south-1"],
    default: "us-east-1",
  },
  oss: {
    options: ["cn-hangzhou", "cn-beijing", "cn-shanghai", "cn-shenzhen", "cn-hongkong"],
    default: "cn-beijing",
  },
  cos: {
    options: ["ap-beijing", "ap-shanghai", "ap-guangzhou", "ap-chengdu", "ap-singapore"],
    default: "ap-beijing",
  },
  obs: { options: ["cn-north-1", "cn-north-4", "cn-east-2", "cn-south-1"], default: "cn-north-4" },
};

const isObjectStorageProtocol = (p?: string) => ["s3", "oss", "cos", "obs"].includes(p ?? "");
const isFtpLikeProtocol = (p?: string) => ["ftp", "ftps"].includes(p ?? "");

function protocolLabel(value?: string): string {
  const opt = PROTOCOL_OPTIONS.value.find((o) => o.value === value);
  return opt ? opt.label : (value ?? "-");
}

// 源项目风格：协议 → tag 颜色
const protocolTagType = (protocol?: string) => {
  const map: Record<string, "primary" | "success" | "warning" | "info" | "danger"> = {
    ftp: "primary",
    ftps: "success",
    sftp: "warning",
    s3: "info",
    oss: "danger",
    cos: "warning",
    obs: "success",
    local: "info",
  };
  return map[protocol ?? ""] ?? "info";
};

type SourceSearchForm = {
  name?: string;
  protocol?: string;
  status?: number;
  created_id?: number;
  updated_id?: number;
  created_time?: string[];
  updated_time?: string[];
};

function buildSourceReplaceParams(p: SourceSearchForm): Record<string, unknown> {
  return {
    name: p.name,
    protocol: p.protocol,
    status: p.status,
    created_id: p.created_id,
    updated_id: p.updated_id,
    created_time:
      Array.isArray(p.created_time) && p.created_time.length === 2 ? p.created_time : undefined,
    updated_time:
      Array.isArray(p.updated_time) && p.updated_time.length === 2 ? p.updated_time : undefined,
  };
}

function buildSourceRowActions(
  row: SourceTable,
  ctx: {
    onOpen: (row: SourceTable) => void;
    onTest: (id: number) => void;
    onDetail: (id: number) => void;
    onEdit: (id: number) => void;
    onDelete: (id: number, name: string) => void;
  }
): TableOperationAction[] {
  return [
    {
      key: "open",
      label: "打开",
      artType: "view",
      icon: "ri:folder-open-line",
      iconColor: "var(--el-color-success)",
      run: () => ctx.onOpen(row),
    },
    {
      key: "test",
      label: "测试连接",
      artType: "view",
      icon: "ri:link",
      iconColor: "var(--el-color-primary)",
      perm: "module_task:workflow:node:query",
      run: () => ctx.onTest(row.id!),
    },
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_task:workflow:node:query",
      run: () => ctx.onDetail(row.id!),
    },
    {
      key: "edit",
      label: "编辑",
      artType: "edit",
      icon: "ri:edit-2-line",
      perm: "module_task:workflow:node:update",
      run: () => ctx.onEdit(row.id!),
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      icon: "ri:delete-bin-4-line",
      perm: "module_task:workflow:node:delete",
      run: () => ctx.onDelete(row.id!, row.name ?? ""),
    },
  ];
}

function formatSourceOperationCell(
  row: SourceTable,
  ctx: Parameters<typeof buildSourceRowActions>[1]
) {
  return renderTableOperationCell(buildSourceRowActions(row, ctx), {
    wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1 source-table-actions",
  });
}

const searchForm = ref<SourceSearchForm>({
  name: undefined,
  protocol: undefined,
  status: undefined,
  created_id: undefined,
  updated_id: undefined,
  created_time: undefined,
  updated_time: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const searchBarRules: Record<string, unknown> = {};

const sourceSearchItems = computed<SearchFormItem[]>(() => [
  {
    label: "存储名称",
    key: "name",
    type: "input",
    placeholder: "请输入存储名称",
    clearable: true,
    span: 6,
  },
  {
    label: "协议",
    key: "protocol",
    type: "select",
    props: {
      placeholder: "请选择协议",
      options: PROTOCOL_OPTIONS.value,
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
]);

const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);

// ─── 表格多选 ───
const { selectedRows, selectedIds, batchDeleting, onTableSelectionChange } =
  useTableSelection<SourceTable>();

const createLoading = ref(false);

async function deleteSourceRow(id: number, name: string) {
  try {
    await confirmDelete(`确定删除「${name}」吗？`);
  } catch {
    return; // 用户取消
  }
  await NodeAPI.deleteNode([id]);
  faTableRef.value?.elTableRef?.clearSelection();
  await refreshRemove();
}

async function handleTest(id: number) {
  await NodeAPI.testNode(id);
}

// 打开浏览：跳转到文件管理并携带存储源信息
function handleOpen(row: SourceTable) {
  router.push({
    path: "/task/workflow/storage",
    query: { source_id: row.id, name: row.name, protocol: row.protocol },
  });
}

const testing = ref(false);

async function handleTestConfig() {
  testing.value = true;
  try {
    await NodeAPI.testNodeConfig({ ...formData.value, source_id: formData.value.id });
  } finally {
    testing.value = false;
  }
}

// ─── 对话框状态 ───
const { dialogVisible } = useCrudDialog();

const detailFormData = ref<SourceTable>({} as SourceTable);

const sourceDetailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] =
  [
    { label: "存储源名称", prop: "name" },
    { label: "协议", prop: "protocol", slot: "protocol" },
    { label: "主机地址", prop: "host" },
    { label: "端口", prop: "port" },
    { label: "用户名", prop: "username" },
    { label: "密码", prop: "has_password", slot: "has_password" },
    { label: "Bucket", prop: "bucket" },
    { label: "端点地址", prop: "endpoint" },
    { label: "区域", prop: "region" },
    { label: "路径前缀", prop: "path_prefix" },
    { label: "分片大小(MB)", prop: "multipart_part_size" },
    { label: "分片并发", prop: "multipart_concurrency" },
    { label: "内存预算(MB)", prop: "multipart_memory_budget" },
    { label: "TLS(FTPS)", prop: "is_secure", slot: "is_secure" },
    { label: "默认存储源", prop: "is_default", slot: "is_default" },
    {
      label: "状态",
      prop: "status",
      tag: { map: { 0: { type: "success", text: "启用" }, 1: { type: "danger", text: "停用" } } },
    },
    { label: "备注", prop: "description" },
    { label: "创建时间", prop: "created_time" },
    { label: "更新时间", prop: "updated_time" },
  ];

const initialFormData: SourceForm = {
  id: undefined,
  name: undefined,
  protocol: "ftp",
  host: undefined,
  port: undefined,
  username: undefined,
  password: undefined,
  bucket: undefined,
  endpoint: undefined,
  region: undefined,
  path_prefix: undefined,
  scheme: "https",
  encrypt_type: 1,
  connection_mode: 0,
  encoding: "UTF-8",
  is_secure: false,
  implicit_tls: false,
  multipart_part_size: 50,
  multipart_concurrency: 6,
  multipart_memory_budget: 512,
  advanced_config: {},
  is_default: false,
  status: 0,
  description: undefined,
};

const formData = ref<SourceForm>({ ...initialFormData });

// 主机地址仅非对象存储协议必填（对象存储用 endpoint 完整 URL）
const rules = computed(() => ({
  name: [{ required: true, message: "请输入存储源名称", trigger: "blur" }],
  ...(isObjectStorageProtocol(formData.value.protocol)
    ? {}
    : { host: [{ required: true, message: "请输入主机地址/根目录", trigger: "blur" }] }),
}));

const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const sourceFormRenderKey = ref(0);

// ─── CRUD 表单 ───
const { submitLoading, handleCloseDialog, handleOpenDialog, handleSubmit } =
  useCrudForm<SourceForm>({
    formData,
    initialFormData,
    dialogVisible,
    dataFormRef,
    formRenderKey: sourceFormRenderKey,
    detailApi: NodeAPI.detailNode,
    createApi: NodeAPI.createNode,
    updateApi: NodeAPI.updateNode,
    titles: { create: "新增存储源", update: "修改存储源", detail: "存储源详情" },
    detailFormData,
    onCreateSuccess: async () => {
      await refreshCreate();
    },
    onUpdateSuccess: async () => {
      await refreshUpdate();
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

// 切换协议：重置协议专属字段并带出该协议默认配置（区域等），避免旧协议配置交叉残留
function onProtocolChange(p: string) {
  // 仅复制协议专属字段，排除基础信息（ID/名称/备注/默认/状态），避免重置用户已填写内容
  const protocolSpecific = { ...initialFormData };
  delete protocolSpecific.id;
  delete protocolSpecific.name;
  delete protocolSpecific.description;
  delete protocolSpecific.is_default;
  delete protocolSpecific.status;
  Object.assign(formData.value, { ...protocolSpecific, protocol: p });
  // 对象存储自动带出默认区域（覆盖旧协议残留区域）
  const regionItem = regionDict[p];
  if (regionItem) formData.value.region = regionItem.default;
  formData.value.advanced_config = {};
  // 强制重渲染：清空旧协议字段的校验状态，刷新 SDK 高级设置
  sourceFormRenderKey.value++;
}

// ─── SDK 高级设置（按协议动态渲染折叠面板） ───
const advancedFields = ref<Record<string, AdvancedFieldDef[]>>({});
const advancedCollapseActive = ref<string[]>([]);

const currentAdvancedFields = computed<AdvancedFieldDef[]>(() => {
  const p = formData.value.protocol;
  return (p && advancedFields.value[p]) || [];
});

async function loadAdvancedFields() {
  const res = await NodeAPI.getAdvancedFields();
  advancedFields.value = res.data.data ?? {};
}
loadAdvancedFields();

function setAdvancedValue(key: string, value: string | number | boolean | undefined) {
  const cfg = (formData.value.advanced_config ??= {});
  if (value === undefined || value === null || value === "") {
    delete cfg[key]; // 留空即使用 SDK 默认值
  } else {
    cfg[key] = value;
  }
}

// ─── 动态表单：按协议分组渲染字段（源项目风格） ───
const sourceDialogFormItems = computed<FormItem[]>(() => {
  const p = formData.value.protocol ?? "ftp";
  const isObject = isObjectStorageProtocol(p);
  const isFtp = isFtpLikeProtocol(p);
  const items: FormItem[] = [
    {
      label: "存储源名称",
      key: "name",
      type: "input",
      span: 12,
      props: { placeholder: "请输入存储源名称", maxlength: 64, showWordLimit: true },
    },
    {
      label: "协议",
      key: "protocol",
      type: "select",
      span: 12,
      props: {
        placeholder: "请选择协议",
        options: PROTOCOL_OPTIONS.value,
        onChange: onProtocolChange,
      },
    },
  ];
  if (isObject) {
    items.push(
      {
        label: "端点地址",
        key: "endpoint",
        type: "input",
        span: 12,
        props: {
          placeholder:
            p === "cos"
              ? "完整接入点 URL（可留空，自动按区域拼接）"
              : "完整接入点 URL，如 https://oss-cn-beijing.aliyuncs.com（必填）",
          maxlength: 255,
        },
      },
      {
        label: "AccessKey",
        key: "username",
        type: "input",
        span: 12,
        props: { placeholder: "AccessKeyID (AK)", maxlength: 255 },
      },
      {
        label: "SecretKey",
        key: "password",
        type: "input",
        span: 12,
        props: {
          type: "password",
          showPassword: true,
          placeholder: "SecretKey (SK)，修改时留空则不修改",
        },
      },
      {
        label: "桶名",
        key: "bucket",
        type: "input",
        span: 12,
        props: { placeholder: "桶名 / 空间名（必填）", maxlength: 255 },
      },
      {
        label: "区域",
        key: "region",
        type: "select",
        span: 12,
        props: {
          placeholder: "请选择或输入区域",
          options: regionDict[p]?.options ?? [],
          filterable: true,
          allowCreate: true,
        },
      },
      {
        label: "路径前缀",
        key: "path_prefix",
        type: "input",
        span: 12,
        props: { placeholder: "统一路径前缀(可选)", maxlength: 255 },
      },
      // ── 分片传输参数（对象存储分片上传，每个端点独立配置） ──
      {
        label: "分片大小",
        key: "multipart_part_size",
        type: "number",
        span: 8,
        props: { controlsPosition: "right", min: 5, max: 5000, step: 1, placeholder: "单片(MB)" },
      },
      {
        label: "分片并发",
        key: "multipart_concurrency",
        type: "number",
        span: 8,
        props: { controlsPosition: "right", min: 1, max: 64, step: 1, placeholder: "路数" },
      },
      {
        label: "内存预算",
        key: "multipart_memory_budget",
        type: "number",
        span: 8,
        props: { controlsPosition: "right", min: 8, max: 10240, step: 1, placeholder: "MB" },
      }
    );
  } else {
    items.push(
      {
        label: "主机地址",
        key: "host",
        type: "input",
        span: 12,
        props: {
          placeholder: p === "local" ? "本地目录根路径，如 /data/storage" : "主机地址或 IP",
          maxlength: 255,
        },
      },
      {
        label: "端口",
        key: "port",
        type: "number",
        span: 12,
        props: {
          controlsPosition: "right",
          min: 0,
          max: 65535,
          placeholder: "留空使用协议默认端口",
        },
      }
    );
    if (p !== "local") {
      items.push(
        {
          label: "账号",
          key: "username",
          type: "input",
          span: 12,
          props: { placeholder: "账号（不填则为匿名）", maxlength: 255 },
        },
        {
          label: "密码",
          key: "password",
          type: "input",
          span: 12,
          props: { type: "password", showPassword: true, placeholder: "密码，修改时留空则不修改" },
        },
        {
          label: "路径前缀",
          key: "path_prefix",
          type: "input",
          span: 12,
          props: { placeholder: "统一路径前缀(可选)", maxlength: 255 },
        }
      );
    } else {
      items.push({
        label: "路径前缀",
        key: "path_prefix",
        type: "input",
        span: 12,
        props: { placeholder: "统一路径前缀(可选)", maxlength: 255 },
      });
    }
    if (isFtp) {
      items.push(
        {
          label: "传输模式",
          key: "connection_mode",
          type: "select",
          span: 12,
          props: { placeholder: "请选择传输模式", options: CONNECTION_MODE_OPTIONS },
        },
        {
          label: "编码",
          key: "encoding",
          type: "select",
          span: 12,
          props: {
            placeholder: "请选择编码",
            options: [
              { label: "UTF-8", value: "UTF-8" },
              { label: "GBK", value: "GBK" },
            ],
            filterable: true,
            allowCreate: true,
          },
        }
      );
    }
    if (p === "ftps") {
      items.push({
        label: "加密方式",
        key: "encrypt_type",
        type: "select",
        span: 12,
        props: {
          placeholder: "请选择加密方式",
          // FTPS 后端强制 encrypt_type>=1（明文请使用 FTP 协议），故过滤 0
          options: ENCRYPT_OPTIONS.filter((o) => o.value !== 0),
        },
      });
    }
  }
  items.push(
    {
      label: "默认存储源",
      key: "is_default",
      type: "switch",
      span: 12,
    },
    {
      label: "状态",
      key: "status",
      type: "radiogroup",
      span: 12,
      props: { options: STATUS_OPTIONS },
    },
    {
      label: "备注",
      key: "description",
      type: "input",
      span: 24,
      props: {
        type: "textarea",
        rows: 3,
        maxlength: 255,
        showWordLimit: true,
        placeholder: "请输入备注",
      },
    }
  );
  // SDK 高级设置：通过命名插槽渲染折叠面板（见模板 #advanced_config）
  items.push({
    key: "advanced_config",
    label: "",
    span: 24,
    hidden: currentAdvancedFields.value.length === 0,
  });
  return items;
});

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
    apiFn: NodeAPI.pageNode,
    apiParams: {
      page_no: 1,
      page_size: 10,
    },
    columnsFactory: resolveStatusColumns<SourceTable>(() => [
      { type: "selection", width: 48, fixed: "left" },
      { type: "globalIndex", width: 56, label: "序号" },
      { prop: "name", label: "存储源名称", minWidth: 140, showOverflowTooltip: true },
      {
        prop: "protocol",
        label: "协议",
        width: 110,
        // 源项目风格：协议彩色标签
        formatter: (row: SourceTable) =>
          h(ElTag, { type: protocolTagType(row.protocol), size: "small", effect: "plain" }, () =>
            protocolLabel(row.protocol)
          ),
      },
      { prop: "host", label: "主机地址", minWidth: 140, showOverflowTooltip: true },
      { prop: "port", label: "端口", width: 80 },
      { prop: "bucket", label: "Bucket", minWidth: 110, showOverflowTooltip: true },
      {
        prop: "is_default",
        label: "默认",
        width: 80,
        formatter: (row: SourceTable) => (row.is_default ? "是" : "否"),
      },
      {
        prop: "status",
        label: "状态",
        width: 80,
        status: {
          0: { type: "success", text: "启用" },
          1: { type: "danger", text: "停用" },
        },
      },
      { prop: "description", label: "备注", minWidth: 120, showOverflowTooltip: true },
      {
        prop: "created_time",
        label: "创建时间",
        width: 168,
        sortable: true,
        showOverflowTooltip: true,
      },
      {
        prop: "operation",
        label: "操作",
        width: 250,
        fixed: "right",
        align: "center",
        formatter: (row: SourceTable) => formatSourceOperationCell(row, opCtx),
      },
    ]),
  },
});

async function handleSearchBarSearch(params: SourceSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildSourceReplaceParams(params));
  await getData();
}

async function onResetSearch() {
  searchForm.value = {
    name: undefined,
    protocol: undefined,
    status: undefined,
    created_id: undefined,
    updated_id: undefined,
    created_time: undefined,
    updated_time: undefined,
  };
  await resetSearchParams();
}

async function handleBatchDelete() {
  const ids = selectedIds.value;
  if (ids.length === 0) return;
  try {
    await confirmBatchDelete(
      ids.length,
      selectedRows.value.map((r) => String(r.name ?? r.id))
    );
  } catch {
    return; // 用户取消
  }
  batchDeleting.value = true;
  try {
    await NodeAPI.deleteNode(ids);
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } finally {
    batchDeleting.value = false;
  }
}

const opCtx = {
  onOpen: handleOpen,
  onTest: handleTest,
  onDetail: (id: number) => void handleOpenDialog("detail", id),
  onEdit: (id: number) => void handleOpenDialog("update", id),
  onDelete: deleteSourceRow,
};
</script>
