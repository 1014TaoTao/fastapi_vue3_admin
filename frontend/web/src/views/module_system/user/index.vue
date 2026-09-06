<!-- 用户管理：左部门树 + 右 Art 表格 -->
<template>
  <div class="fa-full-height user-manage-page">
    <ElSplitter :style="'height: 100%'">
      <ElSplitterPanel size="260px" :min="200" :max="400">
        <div class="user-dept-panel h-full pr-2">
          <ElCard class="tree-card fa-card-xs flex flex-col h-full mt-0" shadow="hover">
            <template #header>
              <b>部门</b>
            </template>
            <ElScrollbar class="dept-tree-scroll min-h-0 flex-1">
              <FaDeptTree
                v-model="deptFilterId"
                class="dept-tree-inner"
                @node-click="handleDeptNodeClick"
              />
            </ElScrollbar>
          </ElCard>
        </div>
      </ElSplitterPanel>

      <ElSplitterPanel :min="400">
        <div class="user-main-panel flex flex-col h-full min-w-0 min-h-0 pl-2">
          <FaSearchBar
            v-show="showSearchBar"
            ref="searchBarRef"
            v-model="searchForm"
            :items="userSearchItems"
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
                  :perm-create="['module_system:user:create']"
                  :perm-import="['module_system:user:import']"
                  :perm-export="['module_system:user:export']"
                  :perm-delete="['module_system:user:delete']"
                  :perm-patch="['module_system:user:patch']"
                  :import-loading="uploadLoading"
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
        </div>
      </ElSplitterPanel>
    </ElSplitter>

    <FaDrawer
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      append-to-body
      :size="drawerSize"
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
          :items="userDetailItems"
          :scrollbar="false"
        >
          <!-- 头像 → 自定义渲染 -->
          <template #avatar="{ row }">
            <ElAvatar v-if="row?.avatar" :src="row?.avatar as string" size="small" />
            <ElAvatar v-else icon="UserFilled" size="small" />
          </template>
          <!-- 性别 → 三种状态 Tag -->
          <template #gender="{ row }">
            <FaStatusTag v-if="row?.gender === '0'" type="success" label="男" />
            <FaStatusTag v-else-if="row?.gender === '1'" type="warning" label="女" />
            <FaStatusTag v-else type="info" label="未知" />
          </template>
          <!-- 角色 → 根据 IDs 从选项解析名称 -->
          <template #roles="{ row }">
            {{ resolveLabels((row as UserInfo).role_ids, roleOptions) }}
          </template>
          <!-- 岗位 → 根据 IDs 从选项解析名称 -->
          <template #positions="{ row }">
            {{ resolveLabels((row as UserInfo).position_ids, positionOptions) }}
          </template>
        </FaDescriptions>
      </template>
      <template v-else>
        <FaForm
          :key="userFormRenderKey"
          ref="dataFormRef"
          v-model="formData"
          :items="userDialogFormItems"
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
          <template #dept_id>
            <ElTreeSelect
              v-model="formData.dept_id"
              placeholder="请选择上级部门"
              :data="deptOptions"
              :props="{ children: 'children', label: 'label', disabled: 'disabled' }"
              filterable
              check-strictly
              :render-after-expand="false"
            />
          </template>
          <template #role_ids>
            <ElSelect v-model="formData.role_ids" multiple placeholder="请选择角色" filterable>
              <ElOption
                v-for="item in roleOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
                :disabled="item.disabled"
              />
            </ElSelect>
          </template>
          <template #position_ids>
            <ElSelect v-model="formData.position_ids" multiple placeholder="请选择岗位" filterable>
              <ElOption
                v-for="item in positionOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
                :disabled="item.disabled"
              />
            </ElSelect>
          </template>
        </FaForm>
      </template>
    </FaDrawer>

    <FaImportDialog
      v-model="importVisible"
      :content-config="userImportContentConfig"
      default-template-file-name="user_import_template.xlsx"
      :loading="uploadLoading"
      @upload="handleImportUpload"
    />

    <FaExportDialog
      v-model="exportVisible"
      :content-config="userExportContentConfig"
      :query-params="exportQueryParams"
      :page-data="data"
      :selection-data="selectedRows"
    />
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: "User",
  inheritAttrs: false,
});

import { UserFilled } from "@element-plus/icons-vue";

import { useAppStore } from "@stores";
import { DeviceEnum } from "@/enums/settings/device.enum";
import { confirmToggleStatus } from "@/hooks/core/useConfirm";

import UserAPI, {
  type UserForm,
  type UserInfo,
  type UserPageQuery,
} from "@/api/module_system/user";
import {
  formatTree,
  renderTableOperationCell,
  resolveStatusColumns,
  stripPaginationParams,
  cleanEmptyArrayParams,
  toCrudCols,
  type TableOperationAction,
} from "@utils";
import PositionAPI from "@/api/module_system/position";
import DeptAPI from "@/api/module_system/dept";
import RoleAPI from "@/api/module_system/role";
import { useUserStore } from "@stores";
import type { DescriptionsItem } from "@/components/display/fa-descriptions/index.vue";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import FaForm from "@/components/forms/fa-form/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import FaTable from "@/components/tables/fa-table/index.vue";
import FaDrawer from "@/components/modal/fa-drawer/index.vue";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import type { IContentConfig, IObject } from "@/components/modal/types";
import FaDeptTree from "./components/FaDeptTree.vue";
import { ElMessage, ElMessageBox } from "element-plus";

const userStore = useUserStore();

type UserSearchForm = {
  username?: string;
  name?: string;
  status?: number;
  created_id?: number;
  updated_id?: number;
  created_time?: string[];
  updated_time?: string[];
};

function buildUserReplaceParams(u: UserSearchForm): Record<string, unknown> {
  return {
    username: u.username,
    name: u.name,
    status: u.status,
    created_id: u.created_id,
    updated_id: u.updated_id,
    created_time:
      Array.isArray(u.created_time) && u.created_time.length === 2 ? u.created_time : undefined,
    updated_time:
      Array.isArray(u.updated_time) && u.updated_time.length === 2 ? u.updated_time : undefined,
  };
}

function fetchUserTableList(params: Record<string, unknown>) {
  return UserAPI.listUser({
    page_no: 1,
    page_size: 10,
    ...params,
    dept_id:
      deptFilterId.value !== undefined && deptFilterId.value !== null && deptFilterId.value !== ""
        ? Number(deptFilterId.value)
        : undefined,
  });
}

function buildUserRowActions(
  row: UserInfo,
  ctx: {
    onResetPwd: (row: UserInfo) => void;
    onDetail: (id: number) => void;
    onEdit: (id: number) => void;
    onDelete: (id: number, name: string) => void;
  }
): TableOperationAction[] {
  const sys = row.is_superuser === true;
  const all: TableOperationAction[] = [
    {
      key: "resetPwd",
      label: "重置密码",
      artType: "edit",
      icon: "ri:refresh-line",
      perm: "module_system:user:update",
      disabled: sys,
      run: () => {
        if (sys) return;
        ctx.onResetPwd(row);
      },
    },
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_system:user:detail",
      run: () => ctx.onDetail(row.id!),
    },
    {
      key: "edit",
      label: "编辑",
      artType: "edit",
      perm: "module_system:user:update",
      disabled: sys,
      run: () => {
        if (sys) return;
        ctx.onEdit(row.id!);
      },
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      perm: "module_system:user:delete",
      disabled: sys,
      run: () => {
        if (sys) return;
        ctx.onDelete(row.id!, row.name ?? row.username ?? "");
      },
    },
  ];
  return all;
}

function formatUserOperationCell(row: UserInfo, ctx: Parameters<typeof buildUserRowActions>[1]) {
  const actions = buildUserRowActions(row, ctx);
  return renderTableOperationCell(actions, {
    wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1 user-table-actions",
  });
}

const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const userFormRenderKey = ref(0);
const submitLoading = ref(false);
const uploadLoading = ref(false);
const createLoading = ref(false);
const moreLoading = ref(false);
const deptFilterId = ref<string | number | undefined>(undefined);

const appStore = useAppStore();
const drawerSize = computed(() => (appStore.device === DeviceEnum.DESKTOP ? "450px" : "90%"));
const deptOptions = ref<OptionType[]>();
const roleOptions = ref<Array<{ value: number; label: string; disabled?: boolean }>>();
const positionOptions = ref<Array<{ value: number; label: string; disabled?: boolean }>>();
const { importVisible, exportVisible, openImport, openExport } = useImportExport();
const detailFormData = ref<UserInfo>({});

interface OptionItem {
  value: number;
  label: string;
  disabled?: boolean;
}

function resolveLabels(
  ids: (number | undefined)[] | undefined,
  options: OptionItem[] | undefined
): string {
  if (!ids || !Array.isArray(ids) || !options) return "";
  return ids
    .filter((id): id is number => id !== undefined && id !== null)
    .map((id) => options.find((o) => o.value === id)?.label ?? String(id))
    .join("、");
}

// 用户详情描述项配置 —— 数据驱动 + 关键字段用具名插槽覆盖
const userDetailItems: DescriptionsItem[] = [
  { label: "编号", prop: "id" },
  { label: "头像", prop: "avatar", slot: "avatar" }, // 自定义插槽渲染
  { label: "账号", prop: "username" },
  { label: "用户名", prop: "name" },
  { label: "性别", prop: "gender", slot: "gender" }, // 三种状态 Tag
  { label: "部门", prop: "dept_name" },
  { label: "角色", prop: "roles", slot: "roles" }, // 数组 join 渲染
  { label: "岗位", prop: "positions", slot: "positions" }, // 数组 join 渲染
  { label: "邮箱", prop: "email" },
  { label: "手机号", prop: "mobile" },
  {
    label: "是否超管",
    prop: "is_superuser",
    tag: {
      map: { true: { type: "success", text: "是" }, false: { type: "info", text: "否" } },
    },
  },
  {
    label: "状态",
    prop: "status",
    tag: {
      map: { 0: { type: "success", text: "启用" }, 1: { type: "danger", text: "停用" } },
    },
  },
  { label: "上次登录时间", prop: "last_login" },
  { label: "创建人", prop: "created_by.name" },
  { label: "更新人", prop: "updated_by.name" },
  { label: "创建时间", prop: "created_time" },
  { label: "更新时间", prop: "updated_time" },
  { label: "描述", prop: "description", span: 4 },
];

// 用户新增/编辑表单配置 —— 三个复杂字段（部门树、角色多选、岗位多选）用插槽渲染
const userDialogFormItems = computed<FormItem[]>(() => [
  {
    key: "username",
    label: "账号",
    type: "input",
    props: { placeholder: "请输入账号", disabled: !!formData.value.id },
  },
  { key: "name", label: "用户名", type: "input", props: { placeholder: "请输入用户名" } },
  {
    key: "gender",
    label: "性别",
    type: "select",
    props: {
      placeholder: "请选择性别",
      options: [
        { label: "男", value: "0" },
        { label: "女", value: "1" },
        { label: "未知", value: "2" },
      ],
    },
  },
  {
    key: "mobile",
    label: "手机号",
    type: "input",
    props: { placeholder: "请输入手机号码", maxlength: 11 },
  },
  {
    key: "email",
    label: "邮箱",
    type: "input",
    props: { placeholder: "请输入邮箱", maxlength: 50 },
  },
  { key: "dept_id", label: "部门", type: "input" /* 实际渲染由 #dept_id 插槽接管 */ },
  { key: "role_ids", label: "角色", type: "input" /* 实际渲染由 #role_ids 插槽接管 */ },
  { key: "position_ids", label: "岗位", type: "input" /* 实际渲染由 #position_ids 插槽接管 */ },
  {
    key: "password",
    label: "密码",
    type: "input",
    hidden: !!formData.value.id,
    props: { placeholder: "请输入密码", type: "password", showPassword: true, clearable: true },
  },
  { key: "is_superuser", label: "是否超管", type: "switch" },
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
]);

const searchForm = ref<UserSearchForm>({
  username: undefined,
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

const userSearchItems = computed<SearchFormItem[]>(() => [
  {
    label: "账号",
    key: "username",
    type: "input",
    placeholder: "请输入账号",
    clearable: true,
    span: 6,
  },
  {
    label: "用户名",
    key: "name",
    type: "input",
    placeholder: "请输入用户名",
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
  useTableSelection<UserInfo>();

async function handleResetPassword(row: UserInfo) {
  try {
    const { value } = await ElMessageBox.prompt(
      `请输入用户【${row.username ?? ""}】的新密码`,
      "重置密码",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        inputType: "password",
        inputErrorMessage: "请输入密码",
        draggable: true,
      }
    );
    if (!value || value.length < 6) {
      ElMessage.warning("密码至少需要6位字符，请重新输入");
      return;
    }
    await UserAPI.resetUserPassword(row.id!, { password: value });
  } catch {
    // 用户取消
  }
}

async function deleteUserRow(id: number, name: string) {
  try {
    await confirmDelete(`确定删除「${name}」吗？`);
    await UserAPI.deleteUser([id]);
    const idSet = [id];
    if (userStore.basicInfo.id && idSet.includes(userStore.basicInfo.id)) {
      userStore.clearUserInfo();
    }
    // 成功 / 失败提示由 axios 拦截器统一处理
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } catch {
    // 用户取消
  }
}

const opCtx = {
  onResetPwd: handleResetPassword,
  onDetail: (id: number) => void handleOpenDialog("detail", id),
  onEdit: (id: number) => void handleOpenDialog("update", id),
  onDelete: deleteUserRow,
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
    apiFn: fetchUserTableList,
    apiParams: {
      page_no: 1,
      page_size: 20,
    },
    columnsFactory: resolveStatusColumns<UserInfo>(() => [
      { type: "selection", width: 48, fixed: "left" },
      { type: "globalIndex", width: 56, label: "序号" },
      {
        prop: "avatar",
        label: "头像",
        width: 72,
        align: "center",
        formatter: (row: UserInfo) =>
          h(
            ElAvatar,
            {
              size: 28,
              src: row.avatar || undefined,
            },
            () => (!row.avatar ? h(UserFilled) : undefined)
          ),
      },
      { prop: "username", label: "账号", minWidth: 100, showOverflowTooltip: true },
      { prop: "name", label: "用户名", minWidth: 100, showOverflowTooltip: true },
      {
        prop: "status",
        label: "状态",
        width: 88,
        status: {
          0: { type: "success", text: "启用" },
          1: { type: "danger", text: "停用" },
        },
      },
      {
        prop: "dept",
        label: "部门",
        minWidth: 100,
        formatter: (row: UserInfo) => row.dept_name ?? "—",
      },
      {
        prop: "gender",
        label: "性别",
        width: 88,
        status: {
          "0": { type: "success", text: "男" },
          "1": { type: "warning", text: "女" },
        },
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
        width: 280,
        fixed: "right",
        align: "center",
        formatter: (row: UserInfo) => formatUserOperationCell(row, opCtx),
      },
    ]),
  },
});

const userCrudCols = toCrudCols(columns);

const exportQueryParams = computed(() => {
  const sp = stripPaginationParams(searchParams);
  if (
    deptFilterId.value !== undefined &&
    deptFilterId.value !== null &&
    deptFilterId.value !== ""
  ) {
    (sp as Record<string, unknown>).dept_id = Number(deptFilterId.value);
  }
  const q = cleanEmptyArrayParams(sp) as Record<string, unknown>;
  if (typeof q.status === "string") {
    const s = q.status;
    if (s === "true" || s === "false") {
      q.status = s === "true";
    }
  }
  return q;
});

const userImportContentConfig = computed<IContentConfig>(() => ({
  permPrefix: "module_system:user",
  cols: userCrudCols.value,
  indexAction: async () => ({}),
  importTemplate: () => UserAPI.downloadTemplateUser(),
}));

const userExportContentConfig = computed(() => ({
  permPrefix: "module_system:user",
  cols: userCrudCols.value,
  exportsBlobAction: async (params: IObject) => {
    const merged = cleanEmptyArrayParams({
      ...(exportQueryParams.value as Record<string, unknown>),
      ...params,
    } as Record<string, unknown>) as Record<string, unknown>;
    if (typeof merged.status === "string") {
      const s = merged.status;
      if (s === "true" || s === "false") {
        merged.status = s === "true";
      }
    }
    const res = await UserAPI.exportUser(merged as unknown as UserPageQuery);
    return res.data as Blob;
  },
}));

const formData = ref<UserForm>({
  id: undefined,
  username: undefined,
  name: undefined,
  dept_id: undefined,
  dept_name: undefined,
  role_ids: undefined,
  role_names: undefined,
  position_ids: undefined,
  position_names: undefined,
  password: undefined,
  gender: undefined,
  email: undefined,
  mobile: undefined,
  is_superuser: false,
  status: 0,
  description: undefined,
});

const { dialogVisible } = useCrudDialog();

const rules = reactive({
  username: [
    { required: true, message: "请输入账号", trigger: "blur" },
    {
      pattern: /^[a-zA-Z][a-zA-Z0-9_.-]{1,31}$/,
      message: "账号需以字母开头，2-32位字母/数字/_.-",
      trigger: "blur",
    },
  ],
  name: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { max: 32, message: "用户名不能超过32位", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码不能少于6位", trigger: "blur" },
  ],
  gender: [{ required: false, message: "请选择性别", trigger: "blur" }],
  email: [
    {
      pattern: /\w[-\w.+]*@([A-Za-z0-9][-A-Za-z0-9]+\.)+[A-Za-z]{2,14}/,
      message: "请输入正确的邮箱地址",
      trigger: "blur",
    },
  ],
  mobile: [
    {
      pattern: /^1[3-9]\d{9}$/,
      message: "请输入正确的手机号码",
      trigger: "blur",
    },
  ],
  is_superuser: [{ required: true, message: "请选择是否超管", trigger: "blur" }],
  status: [{ required: true, message: "请选择状态", trigger: "blur" }],
});

const initialFormData: UserForm = {
  id: undefined,
  username: undefined,
  name: undefined,
  dept_id: undefined,
  dept_name: undefined,
  role_ids: undefined,
  role_names: undefined,
  position_ids: undefined,
  position_names: undefined,
  password: undefined,
  gender: undefined,
  email: undefined,
  mobile: undefined,
  is_superuser: false,
  status: 0,
  description: undefined,
};

async function handleSearchBarSearch(params: UserSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildUserReplaceParams(params));
  await getData();
}

async function onResetSearch() {
  searchForm.value = {
    username: undefined,
    name: undefined,
    status: undefined,
    created_id: undefined,
    updated_id: undefined,
    created_time: undefined,
    updated_time: undefined,
  };
  deptFilterId.value = undefined;
  await resetSearchParams();
}

async function handleDeptNodeClick() {
  await getData();
}

async function handleImportUpload(formDataUpload: FormData) {
  uploadLoading.value = true;
  try {
    await UserAPI.importUser(formDataUpload);
    importVisible.value = false;
    await refreshData();
    // 失败分支提示由 axios 拦截器统一处理
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error(error);
    // 接口错误已由拦截器提示
  } finally {
    uploadLoading.value = false;
  }
}

async function resetForm() {
  if (dataFormRef.value) {
    dataFormRef.value.resetFields();
    dataFormRef.value.clearValidate();
  }
  Object.assign(formData.value, initialFormData);
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

async function handleOpenDialog(type: "create" | "update" | "detail", id?: number) {
  dialogVisible.type = type;
  if (id) {
    const response = await UserAPI.detailUser(id);
    if (type === "detail") {
      dialogVisible.title = "用户详情";
      Object.assign(detailFormData.value, response.data.data ?? {});
    } else if (type === "update") {
      dialogVisible.title = "修改用户";
      Object.assign(formData.value, response.data.data);
      formData.value.role_ids = (response.data.data.role_ids ?? []) as number[];
      formData.value.position_ids = (response.data.data.position_ids ?? []) as number[];
    }
  } else {
    dialogVisible.title = "新增用户";
    Object.assign(formData.value, initialFormData);
    formData.value.id = undefined;
    userFormRenderKey.value += 1;
  }
  dialogVisible.visible = true;
  await nextTick();
  if (dataFormRef.value) {
    dataFormRef.value.clearValidate();
  }

  const deptResponse = await DeptAPI.listDept({});
  deptOptions.value = formatTree(deptResponse.data.data);

  const [roleRes, positionRes] = await Promise.all([
    RoleAPI.getRoleOptions(),
    PositionAPI.getPositionOptions(),
  ]);
  roleOptions.value = (roleRes.data.data ?? []) as typeof roleOptions.value;
  positionOptions.value = (positionRes.data.data ?? []) as typeof positionOptions.value;
}

async function handleSubmit() {
  const form = dataFormRef.value;
  if (!form) return;
  const valid = await (form.validate as () => Promise<boolean>)().catch(() => false);
  if (!valid) return;
  submitLoading.value = true;
  const id = formData.value.id;
  try {
    if (id) {
      await UserAPI.updateUser(id, formData.value);
      await refreshUpdate();
    } else {
      await UserAPI.createUser(formData.value);
      await refreshCreate();
    }
    dialogVisible.visible = false;
    await resetForm();
    if (id === userStore.basicInfo.id) {
      await userStore.getUserInfo();
    }
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error(error);
  } finally {
    submitLoading.value = false;
  }
}

async function handleBatchDelete() {
  const ids = selectedIds.value;
  if (ids.length === 0) return;
  try {
    await confirmBatchDelete(
      ids.length,
      selectedRows.value.map((r) => String(r.name ?? r.username ?? r.id))
    );
    batchDeleting.value = true;
    await UserAPI.deleteUser(ids);
    if (userStore.basicInfo.id && ids.includes(userStore.basicInfo.id)) {
      userStore.clearUserInfo();
    } else {
      console.info(`删除 ${ids.length} 条数据`);
    }
    selectedRows.value = [];
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
    await UserAPI.batchUser({ ids, status });
    await refreshData();
  } catch {
    // 用户取消
  } finally {
    moreLoading.value = false;
  }
}
</script>

<style lang="scss" scoped>
/* 左侧部门树内容区：card body 纵向 flex + 滚动条占满剩余高度（布局在 index，内边距在 DeptTree） */
.tree-card :deep(.el-card__body) {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
  padding: 0;
}
</style>
