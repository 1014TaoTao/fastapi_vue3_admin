<!-- 菜单管理：Art + 树形表格；操作列最多 3 个外露，其余「更多」 -->
<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="menuSearchItems"
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

    <ElSegmented
      class="mt-3"
      v-model="menuClientTab"
      :options="menuSegmentedOptions"
      @change="handleMenuClientTabChange"
    />

    <ElCard
      class="fa-table-card"
      :style="{ 'margin-top': showSearchBar ? '12px' : '0', transition: 'margin-top 0.2s ease' }"
    >
      <FaTableHeader
        v-model:columns="columnChecks"
        v-model:showSearchBar="showSearchBar"
        :loading="loading"
        @refresh="loadMenuData"
      >
        <template #left>
          <div class="inline-flex flex-wrap items-center gap-2">
            <FaTableHeaderLeft
              :remove-ids="selectedIds"
              :perm-create="['module_system:menu:create']"
              :perm-delete="['module_system:menu:delete']"
              :perm-patch="['module_system:menu:patch']"
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
        @row-click="handleRowClick"
      />
    </ElCard>

    <FaDrawer
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      :size="drawerSize"
      :form-mode="dialogVisible.type"
      :confirm-loading="submitLoading"
      @cancel="handleCloseDialog"
      @close="handleCloseDialog"
      @confirm="handleSubmit()"
    >
      <!-- 详情 -->
      <template v-if="dialogVisible.type === 'detail'">
        <FaDescriptions
          :column="4"
          :data="detailFormData"
          :items="menuDetailItems"
          :scrollbar="false"
        >
          <template #type="{ row }">
            <FaStatusTag v-if="row?.type === MenuTypeEnum.CATALOG" type="warning" label="目录" />
            <FaStatusTag v-if="row?.type === MenuTypeEnum.MENU" type="success" label="菜单" />
            <FaStatusTag v-if="row?.type === MenuTypeEnum.BUTTON" type="danger" label="按钮" />
            <FaStatusTag v-if="row?.type === MenuTypeEnum.EXTLINK" type="info" label="外链" />
          </template>
          <template #scope="{ row }">
            <FaStatusTag v-if="row?.scope === MenuClientEnum.PC" type="primary" label="PC" />
            <FaStatusTag v-else-if="row?.scope === MenuClientEnum.APP" type="success" label="APP" />
            <FaStatusTag v-else type="info" :label="(row?.scope as string) || '—'" />
          </template>
          <template #icon="{ row }">
            <template v-if="row?.icon">
              <FaMenuRouteIcon :icon="row?.icon as string" :style="'vertical-align: -0.15em'" />
            </template>
          </template>
        </FaDescriptions>
      </template>

      <!-- 新增、编辑表单 -->
      <template v-else>
        <FaForm
          :key="menuFormRenderKey"
          ref="dataFormRef"
          v-model="formData"
          :items="menuDialogFormItems"
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
          <!-- 父级菜单(条件显示) -->
          <template #parent_id>
            <ElTreeSelect
              v-model="formData.parent_id"
              placeholder="选择上级菜单"
              :data="menuOptions"
              node-key="value"
              filterable
              check-strictly
              :render-after-expand="false"
              :disabled="createParentLocked"
            />
            <ElText v-if="createParentLocked" type="info" size="small" class="block mt-1">
              在菜单下仅可新增按钮，父级已固定
            </ElText>
          </template>

          <!-- 菜单类型(动态枚举按钮组) -->
          <template #type>
            <ElRadioGroup v-model="formData.type" @change="handleMenuTypeChange">
              <ElRadio
                v-if="allowedMenuTypeValues.includes(MenuTypeEnum.CATALOG)"
                :value="MenuTypeEnum.CATALOG"
              >
                目录
              </ElRadio>
              <ElRadio
                v-if="allowedMenuTypeValues.includes(MenuTypeEnum.MENU)"
                :value="MenuTypeEnum.MENU"
              >
                菜单
              </ElRadio>
              <ElRadio
                v-if="allowedMenuTypeValues.includes(MenuTypeEnum.BUTTON)"
                :value="MenuTypeEnum.BUTTON"
              >
                按钮
              </ElRadio>
              <ElRadio
                v-if="allowedMenuTypeValues.includes(MenuTypeEnum.EXTLINK)"
                :value="MenuTypeEnum.EXTLINK"
              >
                外链
              </ElRadio>
            </ElRadioGroup>
          </template>

          <!-- 终端(禁用态+提示) -->
          <template #scope>
            <ElSelect
              v-model="formData.scope"
              :disabled="createParentLocked"
              placeholder="请选择终端"
              style="width: 100%"
            >
              <ElOption :value="MenuClientEnum.PC" label="PC 桌面" />
              <ElOption :value="MenuClientEnum.APP" label="APP 移动" />
            </ElSelect>
            <ElText v-if="createParentLocked" type="info" size="small" class="block mt-1">
              子级终端与父菜单一致
            </ElText>
          </template>

          <!-- 组件路径 -->
          <template #component_path>
            <ElInput
              v-model="formData.component_path"
              placeholder="请输入组件路径，如system/user/index"
              :style="'width: 95%'"
            >
              <template #prepend>src/views/</template>
              <template #append>.vue</template>
            </ElInput>
          </template>

          <!-- 路由参数(动态键值编辑器) -->
          <template #params>
            <template
              v-if="
                !formData.params || (Array.isArray(formData.params) && formData.params.length === 0)
              "
            >
              <ElButton type="success" plain @click="formData.params = [{ key: '', value: '' }]">
                添加路由参数
              </ElButton>
            </template>
            <template v-else>
              <div v-for="item in formData.params" :key="item.key">
                <ElInput v-model="item.key" placeholder="参数名" :style="'width: 100px'" />
                <span class="mx-1">=</span>
                <ElInput v-model="item.value" placeholder="参数值" :style="'width: 100px'" />
                <ElIcon
                  v-if="formData.params.indexOf(item) === formData.params.length - 1"
                  class="ml-2 cursor-pointer color-[var(--el-color-success)]"
                  :style="'vertical-align: -0.15em'"
                  @click="formData.params.push({ key: '', value: '' })"
                >
                  <CirclePlusFilled />
                </ElIcon>
                <ElIcon
                  class="ml-2 cursor-pointer color-[var(--el-color-danger)]"
                  :style="'vertical-align: -0.15em'"
                  @click="formData.params.splice(formData.params.indexOf(item), 1)"
                >
                  <DeleteFilled />
                </ElIcon>
              </div>
            </template>
          </template>
          <!-- 图标 -->
          <template #icon>
            <FaIconSelect v-model="formData.icon" />
          </template>

          <!-- 重定向(动态placeholder) -->
          <template #redirect>
            <ElInput
              v-model="formData.redirect"
              :placeholder="
                formData.type === MenuTypeEnum.CATALOG
                  ? '目录必填，一般为默认子路由 path，如 /system/user'
                  : '可选，请输入重定向路由'
              "
            />
          </template>
        </FaForm>
      </template>
    </FaDrawer>
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: "SysMenu",
  inheritAttrs: false,
});

import { CirclePlusFilled, DeleteFilled } from "@element-plus/icons-vue";
import { useUserStore, useAppStore } from "@stores";
import { useTableColumns } from "@/hooks/core/useTableColumns";
import { DeviceEnum } from "@/enums/settings/device.enum";
import MenuAPI, {
  type MenuForm,
  type MenuPageQuery,
  type MenuTable,
} from "@/api/module_system/menu";
import { MenuClientEnum, MenuTypeEnum } from "@/enums/system/menu.enum";
import { formatTree } from "@utils/common";
import { renderTableOperationCell, resolveStatusColumns, type TableOperationAction } from "@utils";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import FaForm from "@/components/forms/fa-form/index.vue";
import FaMenuRouteIcon from "@/components/navigation/fa-menu-route-icon/index.vue";
import { ElMessage } from "element-plus";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";

const userStore = useUserStore();

type MenuSearchForm = {
  name?: string;
  status?: number;
  created_time?: string[];
  updated_time?: string[];
};

function buildMenuListQuery(p: MenuSearchForm): MenuPageQuery {
  return {
    name: p.name,
    status: p.status,
    created_time:
      Array.isArray(p.created_time) && p.created_time.length === 2 ? p.created_time : undefined,
    updated_time:
      Array.isArray(p.updated_time) && p.updated_time.length === 2 ? p.updated_time : undefined,
  };
}

function buildMenuRowActions(
  row: MenuTable,
  ctx: {
    onAdd?: (r: MenuTable) => void;
    onDetail: (id: number) => void;
    onEdit: (id: number) => void;
    onDelete: (id: number, name: string) => void;
  }
): TableOperationAction[] {
  const actions: TableOperationAction[] = [];
  if (ctx.onAdd && (row.type === MenuTypeEnum.CATALOG || row.type === MenuTypeEnum.MENU)) {
    actions.push({
      key: "add",
      label: "新增",
      artType: "add",
      perm: "module_system:menu:create",
      run: () => ctx.onAdd!(row),
    });
  }
  actions.push({
    key: "detail",
    label: "详情",
    artType: "view",
    perm: "module_system:menu:detail",
    run: () => ctx.onDetail(row.id!),
  });
  actions.push({
    key: "edit",
    label: "编辑",
    artType: "edit",
    perm: "module_system:menu:update",
    run: () => ctx.onEdit(row.id!),
  });
  actions.push({
    key: "delete",
    label: "删除",
    artType: "delete",
    perm: "module_system:menu:delete",
    run: () => ctx.onDelete(row.id!, row.title ?? row.name ?? ""),
  });
  return actions;
}

function formatMenuOperationCell(row: MenuTable, ctx: Parameters<typeof buildMenuRowActions>[1]) {
  const actions = buildMenuRowActions(row, ctx);
  return renderTableOperationCell(actions, {
    wrapperClass:
      "inline-flex flex-wrap items-center justify-end gap-1 menu-table-actions align-middle",
  });
}
const menuClientTab = ref<"pc" | "app">("pc");
const menuSegmentedOptions = [
  { label: "Web 菜单", value: "pc" },
  { label: "APP 菜单", value: "app" },
];
const searchForm = ref<MenuSearchForm>({
  name: undefined,
  status: undefined,
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

const menuSearchItems = computed<SearchFormItem[]>(() => [
  {
    label: "菜单名称",
    key: "name",
    type: "input",
    placeholder: "请输入菜单名称",
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
  elTableRef?: { toggleRowExpansion: (row: MenuTable, expanded?: boolean) => void };
} | null>(null);
const tableData = ref<MenuTable[]>([]);
const loading = ref(false);
const isExpanded = ref(false);
const selectedRows = ref<MenuTable[]>([]);
const selectedIds = computed(() =>
  selectedRows.value.map((r) => r.id).filter((id): id is number => id != null && !Number.isNaN(id))
);
const batchDeleting = ref(false);
const submitLoading = ref(false);
const createLoading = ref(false);
const moreLoading = ref(false);

const menuOptions = ref<OptionType[]>([]);
const fullMenuTree = ref<MenuTable[]>([]);
const createParentLocked = ref(false);

const detailFormData = ref<MenuTable>({});

const menuDetailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] =
  [
    { label: "编号", prop: "id" },
    { label: "菜单名称", prop: "name" },
    { label: "菜单类型", prop: "type", slot: "type" },
    { label: "终端", prop: "scope", slot: "scope" },
    { label: "图标", prop: "icon", slot: "icon" },
    { label: "权限标识", prop: "permission" },
    { label: "路由名称", prop: "route_name" },
    { label: "路由路径", prop: "route_path" },
    { label: "组件路径", prop: "component_path" },
    { label: "激活菜单路径", prop: "active_path" },
    { label: "重定向", prop: "redirect" },
    { label: "外链地址", prop: "link" },
    { label: "父级编号", prop: "parent_id" },
    { label: "父级菜单", prop: "parent_name" },
    {
      label: "是否缓存",
      prop: "keep_alive",
      tag: {
        map: { true: { type: "success", text: "是" }, false: { type: "danger", text: "否" } },
      },
    },
    {
      label: "是否显示",
      prop: "hidden",
      tag: {
        map: { true: { type: "success", text: "是" }, false: { type: "danger", text: "否" } },
      },
    },
    {
      label: "是否显示根路由",
      prop: "always_show",
      tag: {
        map: { true: { type: "success", text: "是" }, false: { type: "danger", text: "否" } },
      },
    },
    { label: "菜单标题", prop: "title" },
    { label: "路由参数", prop: "params" },
    {
      label: "是否固定路由",
      prop: "affix",
      tag: {
        map: { true: { type: "success", text: "是" }, false: { type: "danger", text: "否" } },
      },
    },
    {
      label: "嵌入iframe",
      prop: "is_iframe",
      tag: {
        map: { true: { type: "success", text: "是" }, false: { type: "danger", text: "否" } },
      },
    },
    {
      label: "隐藏标签页",
      prop: "is_hide_tab",
      tag: {
        map: { true: { type: "success", text: "是" }, false: { type: "danger", text: "否" } },
      },
    },
    {
      label: "显示红点角标",
      prop: "show_badge",
      tag: {
        map: { true: { type: "success", text: "是" }, false: { type: "danger", text: "否" } },
      },
    },
    { label: "文字角标内容", prop: "show_text_badge" },
    {
      label: "状态",
      prop: "status",
      tag: {
        map: { 0: { type: "success", text: "启用" }, 1: { type: "danger", text: "停用" } },
      },
    },
    { label: "排序", prop: "order" },
    { label: "创建时间", prop: "created_time" },
    { label: "更新时间", prop: "updated_time" },
    { label: "描述", prop: "description", span: 4 },
  ];

// 菜单新增/编辑表单 —— 条件控制走 hidden，布局走 span:12(半宽)/24(全宽)
const menuDialogFormItems = computed<FormItem[]>(() => {
  const t = formData.value.type as MenuTypeEnum;
  return [
    { key: "type", label: "菜单类型", type: "radiogroup" },
    {
      key: "parent_id",
      label: "父级菜单",
      type: "input",
      hidden: t === MenuTypeEnum.CATALOG,
    },
    { key: "name", label: "菜单名称", type: "input", props: { placeholder: "请输入菜单名称" } },
    { key: "title", label: "菜单标题", type: "input", props: { placeholder: "请输入菜单标题" } },
    { key: "icon", label: "图标", type: "input", hidden: t === MenuTypeEnum.BUTTON },
    {
      key: "link",
      label: "外链地址",
      type: "input",
      hidden: t !== MenuTypeEnum.EXTLINK,
      props: { placeholder: "请输入外链完整路径" },
    },
    {
      key: "route_name",
      label: "路由名称",
      type: "input",
      hidden: t === MenuTypeEnum.BUTTON,
      props: { placeholder: "请输入路由名称" },
    },
    {
      key: "permission",
      label: "权限标识",
      type: "input",
      hidden: t !== MenuTypeEnum.BUTTON && t !== MenuTypeEnum.MENU,
      props: { placeholder: "请输入权限标识，如sys:user:add" },
    },
    {
      key: "route_path",
      label: "路由路径",
      type: "input",
      hidden: t !== MenuTypeEnum.CATALOG && t !== MenuTypeEnum.MENU,
      props: { placeholder: "请输入路由路径，如 system" },
    },
    {
      key: "component_path",
      label: "组件路径",
      type: "input",
      hidden: t !== MenuTypeEnum.MENU,
    },
    {
      key: "active_path",
      label: "激活菜单路径",
      type: "input",
      hidden: t !== MenuTypeEnum.CATALOG && t !== MenuTypeEnum.MENU,
      props: { placeholder: "请输入激活菜单路径，用于高亮父级菜单" },
    },
    {
      key: "redirect",
      label: "重定向",
      type: "input",
      hidden: t !== MenuTypeEnum.CATALOG && t !== MenuTypeEnum.MENU,
    },
    { key: "scope", label: "终端", type: "select", props: { options: MenuClientEnum } },
    { key: "order", label: "排序", type: "number", props: { controlsPosition: "right", min: 1 } },
    {
      key: "is_iframe",
      label: "嵌入iframe",
      type: "radiogroup",
      hidden: t !== MenuTypeEnum.EXTLINK,
      props: {
        options: [
          { label: "是", value: true },
          { label: "否", value: false },
        ],
      },
    },
    {
      key: "status",
      label: "状态",
      type: "radiogroup",
      props: {
        options: [
          { label: "启用", value: 0 },
          { label: "禁用", value: 1 },
        ],
      },
    },
    {
      key: "hidden",
      label: "是否隐藏",
      type: "radiogroup",
      hidden: t === MenuTypeEnum.BUTTON,
      props: {
        options: [
          { label: "是", value: true },
          { label: "否", value: false },
        ],
      },
    },
    {
      key: "always_show",
      label: "始终显示",
      type: "radiogroup",
      hidden: t !== MenuTypeEnum.CATALOG && t !== MenuTypeEnum.MENU,
      props: {
        options: [
          { label: "是", value: true },
          { label: "否", value: false },
        ],
      },
    },
    {
      key: "keep_alive",
      label: "缓存页面",
      type: "radiogroup",
      hidden: t !== MenuTypeEnum.MENU,
      props: {
        options: [
          { label: "开启", value: true },
          { label: "关闭", value: false },
        ],
      },
    },
    {
      key: "affix",
      label: "常驻标签栏",
      type: "radiogroup",
      hidden: t === MenuTypeEnum.BUTTON,
      props: {
        options: [
          { label: "是", value: true },
          { label: "否", value: false },
        ],
      },
    },
    {
      key: "is_hide_tab",
      label: "隐藏标签页",
      type: "radiogroup",
      hidden: t === MenuTypeEnum.BUTTON,
      props: {
        options: [
          { label: "是", value: true },
          { label: "否", value: false },
        ],
      },
    },
    {
      key: "show_badge",
      label: "显示红点角标",
      type: "radiogroup",
      hidden: t === MenuTypeEnum.BUTTON,
      props: {
        options: [
          { label: "是", value: true },
          { label: "否", value: false },
        ],
      },
    },
    {
      key: "show_text_badge",
      label: "文字角标内容",
      type: "input",
      hidden: t === MenuTypeEnum.BUTTON || !formData.value.show_badge,
      props: { placeholder: "请输入文字角标内容" },
    },
    {
      key: "params",
      label: "路由参数",
      type: "input",
      span: 24,
      hidden: t !== MenuTypeEnum.MENU,
    },
    {
      key: "description",
      label: "描述",
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
  ];
});

const formData = ref<MenuForm>({
  id: undefined,
  name: undefined,
  type: MenuTypeEnum.CATALOG,
  icon: undefined,
  order: 999,
  permission: "",
  route_name: "",
  route_path: "",
  component_path: undefined,
  redirect: undefined,
  parent_id: undefined,
  keep_alive: false,
  hidden: false,
  always_show: false,
  title: "",
  params: undefined,
  affix: false,
  link: undefined,
  is_iframe: false,
  is_hide_tab: false,
  active_path: undefined,
  show_badge: false,
  show_text_badge: undefined,
  status: 0,
  description: undefined,
  scope: MenuClientEnum.PC,
});

const dialogVisible = reactive({
  title: "",
  visible: false,
  type: "create" as "create" | "update" | "detail",
});

const appStore = useAppStore();
const drawerSize = computed(() => (appStore.device === DeviceEnum.DESKTOP ? "900px" : "90%"));

function typesAllowedUnderParent(parentType: MenuTypeEnum): MenuTypeEnum[] {
  switch (parentType) {
    case MenuTypeEnum.CATALOG:
      return [MenuTypeEnum.CATALOG, MenuTypeEnum.MENU, MenuTypeEnum.EXTLINK];
    case MenuTypeEnum.MENU:
      return [MenuTypeEnum.BUTTON];
    case MenuTypeEnum.BUTTON:
    case MenuTypeEnum.EXTLINK:
      return [];
    default:
      return [MenuTypeEnum.CATALOG, MenuTypeEnum.MENU, MenuTypeEnum.EXTLINK];
  }
}

function findMenuNodeById(
  id: number | undefined,
  nodes: MenuTable[] = fullMenuTree.value
): MenuTable | null {
  if (id == null) return null;
  for (const n of nodes) {
    if (n.id === id) return n;
    if (n.children?.length) {
      const f = findMenuNodeById(id, n.children);
      if (f) return f;
    }
  }
  return null;
}

function filterMenuTypes(nodes: MenuTable[]): MenuTable[] {
  return nodes
    .filter((node) => node.type === MenuTypeEnum.CATALOG || node.type === MenuTypeEnum.MENU)
    .map((node: MenuTable & { children?: MenuTable[] }) => ({
      ...node,
      children: node.children ? filterMenuTypes(node.children) : [],
    }));
}

async function loadMenuData() {
  loading.value = true;
  try {
    const res = await MenuAPI.listMenu({
      ...buildMenuListQuery(searchForm.value),
      scope: menuClientTab.value === "pc" ? "web" : ("app" as const),
    });
    const tree = res.data.data || [];
    fullMenuTree.value = tree;
    tableData.value = tree;
    menuOptions.value = formatTree(filterMenuTypes(tree));
  } catch (e: unknown) {
    if (import.meta.env.DEV) console.error(e);
  } finally {
    loading.value = false;
  }
}

async function handleMenuClientTabChange(name: string | number) {
  menuClientTab.value = name === "app" ? "app" : "pc";
  await loadMenuData();
}

async function handleSearchBarSearch(params: MenuSearchForm) {
  await searchBarRef.value?.validate?.();
  searchForm.value = { ...params };
  await loadMenuData();
}

async function onResetSearch() {
  searchForm.value = {
    name: undefined,
    status: undefined,
    created_time: undefined,
    updated_time: undefined,
  };
  await loadMenuData();
}

function onTableSelectionChange(rows: MenuTable[]) {
  selectedRows.value = rows;
}

function toggleExpand() {
  isExpanded.value = !isExpanded.value;
  nextTick(() => {
    const el = tableRef.value?.elTableRef;
    if (!el || !tableData.value.length) return;
    const walk = (rows: MenuTable[]) => {
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

async function deleteMenuRow(id: number, name: string) {
  try {
    await confirmDelete(`确定删除「${name}」吗？`);
    await MenuAPI.deleteMenu([id]);
    await userStore.refreshPermissions();
    selectedRows.value = [];
    await loadMenuData();
  } catch {
    // 用户取消
  }
}

/**
 * 打开菜单详情弹窗：先加载数据再打开对话框，避免抖动
 */
async function handleOpenMenuDetail(id: number) {
  dialogVisible.title = "菜单详情";
  dialogVisible.type = "detail";
  const response = await MenuAPI.detailMenu(id);
  const data = response.data.data;
  if (data) {
    detailFormData.value = { ...data };
  }
  dialogVisible.visible = true;
}

const opCtx = {
  onAdd: (r: MenuTable) => void handleOpenDialog("create", undefined, r),
  onDetail: (id: number) => void handleOpenMenuDetail(id),
  onEdit: (id: number) => void handleOpenDialog("update", id),
  onDelete: deleteMenuRow,
};

const { columnChecks, columns } = useTableColumns<MenuTable>(
  resolveStatusColumns(() => [
    { type: "selection", width: 48, fixed: "left" },
    { type: "globalIndex", width: 56, label: "序号" },
    // ─── 基础信息 ───
    {
      prop: "name",
      label: "菜单名称",
      minWidth: 220,
      showOverflowTooltip: true,
      formatter: (row: MenuTable) => {
        const isButton = row.type === MenuTypeEnum.BUTTON;
        if (isButton || !row.icon) return row.name ?? "—";
        const iconVNode = h(FaMenuRouteIcon, {
          icon: row.icon,
          style: { verticalAlign: "-0.15em", marginRight: "6px" },
        });
        return h("span", null, [iconVNode, row.name]);
      },
    },
    {
      prop: "type",
      label: "类型",
      width: 80,
      align: "center",
      status: {
        1: { type: "warning", text: "目录" },
        2: { type: "success", text: "菜单" },
        3: { type: "danger", text: "按钮" },
        4: { type: "info", text: "外链" },
      },
    },
    { prop: "title", label: "菜单标题", minWidth: 120, showOverflowTooltip: true },
    { prop: "permission", label: "权限标识", minWidth: 160, showOverflowTooltip: true },
    {
      prop: "scope",
      label: "终端",
      width: 80,
      align: "center",
      status: {
        web: { type: "primary", text: "Web" },
        app: { type: "success", text: "App" },
      },
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
    { prop: "order", label: "排序", width: 72 },
    // ─── 路由配置 ───
    { prop: "route_name", label: "路由名称", minWidth: 100, showOverflowTooltip: true },
    { prop: "route_path", label: "路由路径", minWidth: 140, showOverflowTooltip: true },
    {
      prop: "component_path",
      label: "组件路径",
      minWidth: 140,
      showOverflowTooltip: true,
      visible: false,
    },
    {
      prop: "active_path",
      label: "激活路径",
      minWidth: 110,
      showOverflowTooltip: true,
      visible: false,
    },
    { prop: "redirect", label: "重定向", minWidth: 110, showOverflowTooltip: true, visible: false },
    { prop: "link", label: "外链地址", minWidth: 140, showOverflowTooltip: true, visible: false },
    {
      prop: "params",
      label: "路由参数",
      minWidth: 100,
      showOverflowTooltip: true,
      visible: false,
      formatter: (row: MenuTable) =>
        row.params == null
          ? "—"
          : typeof row.params === "object"
            ? JSON.stringify(row.params)
            : String(row.params),
    },
    // ─── 功能开关 ───
    {
      prop: "keep_alive",
      label: "缓存",
      width: 72,
      align: "center",
      visible: false,
      status: {
        true: { type: "success", text: "是" },
        false: { type: "danger", text: "否" },
      },
    },
    {
      prop: "hidden",
      label: "隐藏",
      width: 72,
      align: "center",
      visible: false,
      status: {
        true: { type: "success", text: "是" },
        false: { type: "danger", text: "否" },
      },
    },
    {
      prop: "always_show",
      label: "常显",
      width: 72,
      align: "center",
      visible: false,
      status: {
        true: { type: "success", text: "是" },
        false: { type: "danger", text: "否" },
      },
    },
    {
      prop: "affix",
      label: "固定标签",
      width: 88,
      align: "center",
      visible: false,
      status: {
        true: { type: "success", text: "是" },
        false: { type: "danger", text: "否" },
      },
    },
    {
      prop: "is_iframe",
      label: "iframe",
      width: 80,
      align: "center",
      visible: false,
      status: {
        true: { type: "success", text: "是" },
        false: { type: "danger", text: "否" },
      },
    },
    {
      prop: "is_hide_tab",
      label: "隐藏标签",
      width: 88,
      align: "center",
      visible: false,
      status: {
        true: { type: "success", text: "是" },
        false: { type: "danger", text: "否" },
      },
    },
    {
      prop: "show_badge",
      label: "红点",
      width: 72,
      align: "center",
      visible: false,
      status: {
        true: { type: "success", text: "是" },
        false: { type: "danger", text: "否" },
      },
    },
    {
      prop: "show_text_badge",
      label: "角标文字",
      width: 90,
      showOverflowTooltip: true,
      visible: false,
    },
    // ─── 元信息 ───
    {
      prop: "description",
      label: "描述",
      minWidth: 140,
      showOverflowTooltip: true,
      visible: false,
    },
    {
      prop: "created_time",
      label: "创建时间",
      width: 168,
      sortable: true,
      showOverflowTooltip: true,
      visible: false,
    },
    {
      prop: "updated_time",
      label: "更新时间",
      width: 168,
      sortable: true,
      showOverflowTooltip: true,
      visible: false,
    },
    // ─── 操作 ───
    {
      prop: "operation",
      label: "操作",
      width: 220,
      fixed: "right",
      align: "center",
      formatter: (row: MenuTable) => formatMenuOperationCell(row, opCtx),
    },
  ])
);

const rules = reactive({
  name: [
    { required: true, message: "请输入菜单名称", trigger: "blur" },
    { min: 2, max: 50, message: "长度 2 到 50 个字符", trigger: "blur" },
  ],
  // 父级菜单：顶级节点允许为空（后端 parent_id 可空），无需强制必填
  type: [{ required: true, message: "请选择菜单类型", trigger: "blur" }],
  order: [{ required: true, message: "请输入排序", trigger: "blur" }],
  permission: [
    {
      validator: (_rule: unknown, value: string | undefined, callback: (e?: Error) => void) => {
        // 仅按钮/菜单类型需要权限标识，目录/外链不校验（与表单 hidden 条件一致）
        const t = formData.value.type as MenuTypeEnum;
        if ((t === MenuTypeEnum.BUTTON || t === MenuTypeEnum.MENU) && !String(value ?? "").trim()) {
          callback(new Error("请输入权限标识"));
          return;
        }
        callback();
      },
      trigger: "blur",
    },
  ],
  route_name: [{ required: true, message: "请输入路由名称", trigger: "blur" }],
  route_path: [{ required: true, message: "请输入路由路径", trigger: "blur" }],
  component_path: [
    {
      validator: (_rule: unknown, value: string | undefined, callback: (e?: Error) => void) => {
        // 仅菜单类型需要组件路径，目录/按钮/外链不校验（与表单 hidden 条件一致）
        const t = formData.value.type as MenuTypeEnum;
        if (t === MenuTypeEnum.MENU && !String(value ?? "").trim()) {
          callback(new Error("请输入组件路径"));
          return;
        }
        callback();
      },
      trigger: "blur",
    },
  ],
  title: [
    { required: true, message: "请输入菜单标题", trigger: "blur" },
    { min: 2, max: 50, message: "长度 2 到 50 个字符", trigger: "blur" },
  ],
  keep_alive: [{ required: true, message: "请选择是否缓存", trigger: "change" }],
  hidden: [{ required: true, message: "请选择是否隐藏", trigger: "change" }],
  always_show: [{ required: true, message: "请选择始终显示", trigger: "change" }],
  status: [{ required: true, message: "请选择状态", trigger: "change" }],
  redirect: [
    {
      validator: (_rule: unknown, value: string | undefined, callback: (e?: Error) => void) => {
        if (formData.value.type === MenuTypeEnum.CATALOG) {
          if (value === undefined || value === null || String(value).trim() === "") {
            callback(new Error("目录类型必须填写重定向地址"));
            return;
          }
        }
        callback();
      },
      trigger: "blur",
    },
  ],
});

const selectedMenuId = ref<number | undefined>();

const initialFormData: MenuForm = {
  id: undefined,
  name: undefined,
  type: MenuTypeEnum.MENU,
  icon: undefined,
  order: 1,
  permission: "",
  route_name: "",
  route_path: "",
  component_path: "",
  redirect: "",
  parent_id: undefined,
  keep_alive: false,
  hidden: false,
  always_show: false,
  title: "",
  params: [] as { key: string; value: string }[],
  affix: false,
  link: undefined,
  is_iframe: false,
  is_hide_tab: false,
  active_path: undefined,
  show_badge: false,
  show_text_badge: undefined,
  status: 0,
  description: undefined,
  scope: MenuClientEnum.PC,
};

const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const menuFormRenderKey = ref(0);

async function resetForm() {
  if (dataFormRef.value) {
    dataFormRef.value.resetFields();
    dataFormRef.value.clearValidate();
  }
  Object.assign(formData.value, initialFormData);
}

async function handleRowClick(row: MenuTable) {
  selectedMenuId.value = row.id;
}

const allowedMenuTypeValues = computed(() => {
  const pid = formData.value.parent_id;
  const parentNode = findMenuNodeById(pid);
  if (!parentNode?.type) {
    return [MenuTypeEnum.CATALOG, MenuTypeEnum.MENU, MenuTypeEnum.EXTLINK];
  }
  return typesAllowedUnderParent(parentNode.type as MenuTypeEnum);
});

async function handleCloseDialog() {
  dialogVisible.visible = false;
  createParentLocked.value = false;
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

async function handleOpenDialog(
  type: "create" | "update" | "detail",
  id?: number,
  parentRow?: MenuTable
) {
  dialogVisible.type = type;
  createParentLocked.value = false;
  if (id) {
    const response = await MenuAPI.detailMenu(id);
    if (type === "detail") {
      dialogVisible.title = "菜单详情";
      Object.assign(detailFormData.value, response.data.data ?? {});
    } else if (type === "update") {
      dialogVisible.title = "修改菜单";
      Object.assign(formData.value, response.data.data ?? {});
    }
  } else {
    dialogVisible.title = "新增菜单";
    formData.value = { ...initialFormData };
    menuFormRenderKey.value += 1;
    if (parentRow?.id != null) {
      formData.value.parent_id = parentRow.id;
      formData.value.scope =
        (parentRow.scope as MenuClientEnum) || (menuClientTab.value === "pc" ? "web" : "app");
      if (parentRow.type === MenuTypeEnum.MENU) {
        createParentLocked.value = true;
        formData.value.type = MenuTypeEnum.BUTTON;
      } else if (parentRow.type === MenuTypeEnum.CATALOG) {
        formData.value.type = MenuTypeEnum.MENU;
      }
    } else {
      formData.value.scope = menuClientTab.value === "pc" ? "web" : "app";
    }
  }
  dialogVisible.visible = true;
}

function handleMenuTypeChange() {
  if (formData.value.type === MenuTypeEnum.MENU) {
    formData.value.component_path = "";
  }
  nextTick(() => {
    dataFormRef.value?.clearValidate("redirect");
    if (formData.value.type === MenuTypeEnum.CATALOG) {
      dataFormRef.value?.validateField("redirect")?.catch(() => {});
    }
  });
}

async function handleSubmit() {
  const id = formData.value.id;
  // 仅在新增时校验类型是否合法，编辑时类型是已存的无需变更
  if (!id) {
    const allowed = allowedMenuTypeValues.value;
    if (!allowed.length) return;
    const t = formData.value.type as MenuTypeEnum;
    if (!allowed.includes(t)) {
      formData.value.type = allowed[0] as MenuForm["type"];
    }
  }
  const form = dataFormRef.value;
  if (!form) return;
  const valid = await (form.validate as () => Promise<boolean>)().catch(() => false);
  if (!valid) return;
  submitLoading.value = true;
  try {
    if (id) {
      await MenuAPI.updateMenu(id, { id, ...formData.value });
    } else {
      await MenuAPI.createMenu(formData.value);
    }
    dialogVisible.visible = false;
    await resetForm();
    await loadMenuData();
    await userStore.refreshPermissions();
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
      selectedRows.value.map((r) => String(r.title ?? r.name ?? r.id))
    );
    batchDeleting.value = true;
    await MenuAPI.deleteMenu(ids);
    await userStore.refreshPermissions();
    selectedRows.value = [];
    await loadMenuData();
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
    await MenuAPI.batchMenu({ ids, status });
    await loadMenuData();
  } catch {
    // 用户取消
  } finally {
    moreLoading.value = false;
  }
}

onMounted(() => {
  void loadMenuData();
});
</script>
