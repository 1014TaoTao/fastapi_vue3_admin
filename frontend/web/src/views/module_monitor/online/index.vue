<!-- 在线用户：Art + useTable -->
<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="onlineSearchItems"
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
          <ElButton
            v-hasPerm="['module_monitor:online:delete']"
            type="danger"
            plain
            :loading="clearAllLoading"
            @click="handleClearAll"
          >
            强退所有
          </ElButton>
        </template>
      </FaTableHeader>

      <FaTable
        row-key="session_id"
        :loading="loading"
        :data="data"
        :columns="columns"
        :pagination="pagination"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      />
    </ElCard>
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: "OnlineUser",
  inheritAttrs: false,
});

import OnlineAPI, { type OnlineUserTable } from "@/api/module_monitor/online";
import { renderTableOperationCell, type TableOperationAction } from "@utils";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import FaCopyButton from "@/components/actions/fa-copy-button/index.vue";
import type { ColumnOption } from "@/types/component";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";

type OnlineSearchForm = {
  ipaddr?: string;
  name?: string;
  login_location?: string;
};

function buildOnlineReplaceParams(u: OnlineSearchForm): Record<string, unknown> {
  return {
    ipaddr: u.ipaddr,
    name: u.name,
    login_location: u.login_location,
  };
}

const searchForm = ref<OnlineSearchForm>({
  ipaddr: undefined,
  name: undefined,
  login_location: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const searchBarRules: Record<string, unknown> = {};

const onlineSearchItems = computed<SearchFormItem[]>(() => [
  {
    label: "IP地址",
    key: "ipaddr",
    type: "input",
    placeholder: "请输入IP地址",
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
    label: "登录位置",
    key: "login_location",
    type: "input",
    placeholder: "请输入登录位置",
    clearable: true,
    span: 6,
  },
]);

const clearAllLoading = ref(false);

async function kickSession(sessionId: string) {
  try {
    await confirmDelete(`确认强制退出会话 ${sessionId}?`);
    await OnlineAPI.deleteOnline(sessionId);
    // 成功 / 失败提示由 axios 拦截器统一处理
    await refreshData();
  } catch {
    // 用户取消或操作失败
  }
}

function buildOnlineRowActions(row: OnlineUserTable): TableOperationAction[] {
  const all: TableOperationAction[] = [
    {
      key: "kick",
      label: "强退",
      artType: "delete",
      perm: "module_monitor:online:delete",
      run: () => kickSession(row.session_id),
    },
  ];
  return all;
}

function formatOnlineOperationCell(row: OnlineUserTable) {
  return renderTableOperationCell(buildOnlineRowActions(row));
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
} = useTable({
  core: {
    apiFn: OnlineAPI.listOnline,
    apiParams: {
      page_no: 1,
      page_size: 10,
    },
    columnsFactory: (): ColumnOption<OnlineUserTable>[] => [
      { type: "globalIndex", width: 56, label: "序号" },
      {
        prop: "session_id",
        label: "会话编号",
        minWidth: 250,
        showOverflowTooltip: true,
      },
      {
        prop: "login_type",
        label: "登录类型",
        minWidth: 100,
        showOverflowTooltip: true,
      },
      {
        prop: "ipaddr",
        label: "IP地址",
        minWidth: 150,
        formatter: (row: OnlineUserTable) =>
          h("span", { class: "inline-flex items-center gap-0.5 whitespace-nowrap" }, [
            row.ipaddr ?? "",
            row.ipaddr
              ? h(FaCopyButton, {
                  text: row.ipaddr,
                  style: { marginLeft: "2px" },
                })
              : null,
          ]),
      },
      {
        prop: "name",
        label: "用户名",
        minWidth: 100,
        showOverflowTooltip: true,
      },
      {
        prop: "user_name",
        label: "账号",
        minWidth: 100,
        showOverflowTooltip: true,
      },
      {
        prop: "login_location",
        label: "登录位置",
        minWidth: 220,
        showOverflowTooltip: true,
      },
      {
        prop: "os",
        label: "操作系统",
        minWidth: 120,
        showOverflowTooltip: true,
      },
      {
        prop: "login_time",
        label: "登录时间",
        width: 180,
        showOverflowTooltip: true,
      },
      {
        prop: "operation",
        label: "操作",
        width: 88,
        fixed: "right",
        align: "center",
        formatter: (row: OnlineUserTable) => formatOnlineOperationCell(row),
      },
    ],
  },
});

async function handleSearchBarSearch(params: OnlineSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildOnlineReplaceParams(params));
  getData();
}

async function onResetSearch() {
  searchForm.value = {
    ipaddr: undefined,
    name: undefined,
    login_location: undefined,
  };
  await resetSearchParams();
}

async function handleClearAll() {
  try {
    await confirmDelete("确认强制退出所有用户?");
    clearAllLoading.value = true;
    await OnlineAPI.clearOnline();
    // 成功 / 失败提示由 axios 拦截器统一处理
    await refreshData();
  } catch {
    // 用户取消
  } finally {
    clearAllLoading.value = false;
  }
}

// 列表数据在页面挂载时加载一次，不自动轮询
onMounted(() => {
  refreshData();
});
</script>

<style lang="scss" scoped></style>
