<template>
  <div class="fa-full-height">
    <ElTabs v-model="activeTab" class="fa-tabs-fill">
      <!-- 监控信息 Tab -->
      <ElTabPane label="监控信息" name="0">
        <div class="flex flex-col gap-4 h-full min-h-0">
          <ElRow :gutter="16">
            <ElCol :span="24">
              <ElCard shadow="hover" class="fa-card">
                <template #header>
                  <div class="flex items-center gap-2">
                    <FaSvgIcon icon="ri:database-2-line" class="text-lg" />
                    <span class="font-medium">Redis监控信息</span>
                  </div>
                </template>
                <ElDescriptions :column="descColumns" border>
                  <ElDescriptionsItem label="Redis版本">
                    {{ cache.info?.redis_version || "-" }}
                  </ElDescriptionsItem>
                  <ElDescriptionsItem label="运行模式">
                    {{ cache.info?.redis_mode === "standalone" ? "单机" : "集群" }}
                  </ElDescriptionsItem>
                  <ElDescriptionsItem label="端口">
                    {{ cache.info?.tcp_port || "-" }}
                  </ElDescriptionsItem>
                  <ElDescriptionsItem label="客户端数">
                    {{ cache.info?.connected_clients || 0 }}
                  </ElDescriptionsItem>
                  <ElDescriptionsItem label="运行时间(天)">
                    {{ cache.info?.uptime_in_days || 0 }}
                  </ElDescriptionsItem>
                  <ElDescriptionsItem label="使用内存">
                    {{ cache.info?.used_memory_human || "-" }}
                  </ElDescriptionsItem>
                  <ElDescriptionsItem label="使用CPU">
                    {{
                      cache.info?.used_cpu_user_children
                        ? parseFloat(cache.info.used_cpu_user_children).toFixed(2)
                        : "-"
                    }}
                  </ElDescriptionsItem>
                  <ElDescriptionsItem label="内存配置">
                    {{ cache.info?.maxmemory_human || "-" }}
                  </ElDescriptionsItem>
                  <ElDescriptionsItem label="AOF">
                    {{ cache.info?.aof_enabled === "0" ? "关闭" : "开启" }}
                  </ElDescriptionsItem>
                  <ElDescriptionsItem label="RDB状态">
                    {{ cache.info?.rdb_last_bgsave_status || "-" }}
                  </ElDescriptionsItem>
                  <ElDescriptionsItem label="Key数量">
                    {{ cache.db_size || 0 }}
                  </ElDescriptionsItem>
                  <ElDescriptionsItem label="网络IO">
                    {{ cache.info?.instantaneous_input_kbps || 0 }}kps/
                    {{ cache.info?.instantaneous_output_kbps || 0 }}kps
                  </ElDescriptionsItem>
                </ElDescriptions>
              </ElCard>
            </ElCol>
          </ElRow>

          <ElRow :gutter="16" class="flex-1 min-h-0">
            <ElCol :xs="24" :sm="12" class="mb-5">
              <ElCard shadow="hover" class="fa-card flex-1 flex flex-col chart-card">
                <template #header>
                  <div class="flex items-center gap-2">
                    <FaSvgIcon icon="ri:bar-chart-2-line" class="text-lg" />
                    <span class="font-medium">命令统计</span>
                  </div>
                </template>
                <div ref="commandstats" class="flex flex-1 items-center justify-center min-h-75" />
              </ElCard>
            </ElCol>
            <ElCol :xs="24" :sm="12" class="mb-5">
              <ElCard shadow="hover" class="fa-card flex-1 flex flex-col chart-card">
                <template #header>
                  <div class="flex items-center gap-2">
                    <FaSvgIcon icon="ri:pie-chart-2-line" class="text-lg" />
                    <span class="font-medium">内存信息</span>
                  </div>
                </template>
                <div ref="usedmemory" class="flex flex-1 items-center justify-center min-h-75" />
              </ElCard>
            </ElCol>
          </ElRow>
        </div>
      </ElTabPane>

      <!-- 缓存管理 Tab -->
      <ElTabPane label="缓存管理" name="1">
        <div class="grid grid-cols-3 gap-4 h-150">
          <!-- 缓存列表 -->
          <ElCard
            :loading="loading"
            shadow="hover"
            class="fa-card flex flex-col min-h-0"
            body-class="flex flex-col flex-1 min-h-0 overflow-hidden"
          >
            <template #header>
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <FaSvgIcon icon="ri:list-unordered" class="text-lg" />
                  <span class="font-medium">缓存列表</span>
                </div>
                <ElButton
                  v-hasPerm="['module_monitor:cache:query']"
                  type="primary"
                  link
                  :icon="RefreshRight"
                  @click="getCacheNameList"
                />
              </div>
            </template>
            <ElScrollbar class="flex-1 min-h-0">
              <ElTable :loading="loading" :data="cacheNames" row-key="cache_name">
                <template #empty>
                  <ElEmpty :image-size="80" description="暂无数据" />
                </template>
                <ElTableColumn prop="cache_name" label="缓存名称" show-overflow-tooltip>
                  <template #default="{ row }">
                    <ElButton
                      v-hasPerm="['module_monitor:cache:query']"
                      type="primary"
                      link
                      @click="getCacheKeyList(row as CacheInfo)"
                    >
                      {{ row.cache_name }}
                    </ElButton>
                  </template>
                </ElTableColumn>
                <ElTableColumn prop="remark" label="备注" width="200" show-overflow-tooltip />
                <ElTableColumn label="操作" width="100" align="center" fixed="right">
                  <template #default="{ row }">
                    <ElPopconfirm
                      :title="`确认删除缓存 ${row.cache_name} 吗？`"
                      placement="top"
                      @confirm="handleClearCacheName(row as CacheInfo)"
                    >
                      <template #reference>
                        <ElButton
                          v-hasPerm="['module_monitor:cache:delete']"
                          type="danger"
                          size="small"
                          link
                          :icon="Delete"
                        />
                      </template>
                    </ElPopconfirm>
                  </template>
                </ElTableColumn>
              </ElTable>
            </ElScrollbar>
          </ElCard>

          <!-- 键名列表 -->
          <ElCard
            :loading="loading"
            shadow="hover"
            class="fa-card flex flex-col min-h-0"
            body-class="flex flex-col flex-1 min-h-0 overflow-hidden"
          >
            <template #header>
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <FaSvgIcon icon="ri:key-2-line" class="text-lg" />
                  <span class="font-medium">键名列表</span>
                </div>
                <ElButton
                  v-hasPerm="['module_monitor:cache:query']"
                  type="primary"
                  link
                  :icon="RefreshRight"
                  @click="getCacheKeyList()"
                />
              </div>
            </template>
            <ElScrollbar class="flex-1 min-h-0">
              <ElTable
                :loading="subLoading"
                :data="cacheKeys.map((key) => ({ cacheKey: key }))"
                row-key="cacheKey"
              >
                <template #empty>
                  <ElEmpty :image-size="80" description="暂无数据" />
                </template>
                <ElTableColumn prop="cacheKey" label="缓存键名" show-overflow-tooltip>
                  <template #default="{ row }">
                    <ElButton
                      v-hasPerm="['module_monitor:cache:detail']"
                      type="primary"
                      link
                      @click="handleCacheValue(row.cacheKey)"
                    >
                      {{ row.cacheKey }}
                    </ElButton>
                  </template>
                </ElTableColumn>
                <ElTableColumn label="操作" width="100" fixed="right" align="center">
                  <template #default="{ row }">
                    <ElPopconfirm
                      :title="`确认删除键 ${row.cacheKey} 吗？`"
                      placement="top"
                      @confirm="handleClearCacheKey(row.cacheKey as string)"
                    >
                      <template #reference>
                        <ElButton
                          v-hasPerm="['module_monitor:cache:delete']"
                          type="danger"
                          size="small"
                          link
                          :icon="Delete"
                        />
                      </template>
                    </ElPopconfirm>
                  </template>
                </ElTableColumn>
              </ElTable>
            </ElScrollbar>
          </ElCard>

          <!-- 缓存内容 -->
          <ElCard
            :loading="loading"
            shadow="hover"
            class="fa-card flex flex-col min-h-0"
            body-class="flex flex-col flex-1 min-h-0 overflow-hidden"
          >
            <template #header>
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <FaSvgIcon icon="ri:file-text-line" class="text-lg" />
                  <span class="font-medium">缓存内容</span>
                </div>
                <ElButton
                  v-hasPerm="['module_monitor:cache:delete']"
                  type="danger"
                  link
                  :icon="Delete"
                  @click="handleClearCacheAll"
                >
                  清理全部
                </ElButton>
              </div>
            </template>
            <ElScrollbar class="flex-1 min-h-0">
              <ElForm :model="cacheForm" label-suffix=":" label-position="top">
                <ElFormItem label="缓存名称">
                  <ElInput v-model="cacheForm.cache_name" readonly placeholder="缓存名称" />
                </ElFormItem>
                <ElFormItem label="缓存键名">
                  <ElInput v-model="cacheForm.cache_key" readonly placeholder="缓存键名" />
                </ElFormItem>
                <ElFormItem label="缓存内容" class="cache-value-item">
                  <ElInput
                    v-model="cacheForm.cache_value"
                    type="textarea"
                    readonly
                    placeholder="缓存内容"
                    :rows="10"
                  />
                </ElFormItem>
              </ElForm>
            </ElScrollbar>
          </ElCard>
        </div>
      </ElTabPane>
    </ElTabs>
  </div>
</template>

<script lang="ts" setup>
import { ElMessageBox } from "element-plus";
import { RefreshRight, Delete } from "@element-plus/icons-vue";
import CacheAPI, {
  type CacheInfo,
  type CacheForm,
  type CacheMonitor,
  type RedisInfo,
} from "@/api/module_monitor/cache";
import { echarts } from "@/plugins/echarts";
import { useWindowSize } from "@vueuse/core";

defineOptions({ name: "CacheMonitor" });

const activeTab = ref("0");

const { width: winWidth } = useWindowSize();
const descColumns = computed(() => (winWidth.value < 768 ? 2 : 6));

const cacheNames = ref<CacheInfo[]>([]);
const cacheKeys = ref<string[]>([]);
const loading = ref(true);
const subLoading = ref(false);
const nowCacheName = ref("");

const commandstats = ref<HTMLElement | null>(null);
const usedmemory = ref<HTMLElement | null>(null);
const cache = ref<CacheMonitor>({
  info: {} as RedisInfo,
  command_stats: [],
  db_size: 0,
});
const cacheForm = ref<CacheForm>({
  cache_name: "",
  cache_key: "",
  cache_value: "",
});

let commandstatsInstance: echarts.ECharts | null = null;
let usedmemoryInstance: echarts.ECharts | null = null;

const resetCacheForm = () => {
  cacheKeys.value = [];
  cacheForm.value = { cache_name: "", cache_key: "", cache_value: "" };
};

const getCacheNameList = async () => {
  try {
    loading.value = true;
    const response = await CacheAPI.getCacheNames();
    cacheNames.value = response.data.data;
    resetCacheForm();
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error("获取缓存列表出错:", error);
  } finally {
    loading.value = false;
  }
};

const handleClearCacheName = async (row: CacheInfo) => {
  try {
    await CacheAPI.deleteCacheName(row.cache_name);
    getCacheNameList();
    ElMessage.success("缓存已清理");
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error("清理缓存名称出错:", error);
  }
};

const getCacheKeyList = async (row?: CacheInfo) => {
  try {
    const cacheName = row?.cache_name || nowCacheName.value;
    if (!cacheName) return;
    subLoading.value = true;
    const response = await CacheAPI.getCacheKeys(cacheName);
    cacheKeys.value = response.data.data;
    nowCacheName.value = cacheName;
    cacheForm.value = { cache_name: cacheName, cache_key: "", cache_value: "" };
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error("获取缓存键名列表出错:", error);
  } finally {
    subLoading.value = false;
  }
};

async function handleClearCacheKey(cacheKey: string) {
  try {
    await CacheAPI.deleteCacheKey(cacheKey);
    getCacheKeyList();
    ElMessage.success("缓存键已清理");
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error("清理缓存键名出错:", error);
    ElMessage.error("清理缓存键失败，请稍后重试");
  }
}

async function handleCacheValue(cacheKey: string) {
  try {
    loading.value = true;
    const response = await CacheAPI.getCacheValue(nowCacheName.value, cacheKey);
    const data = response.data.data;
    cacheForm.value = {
      ...data,
      cache_value:
        typeof data.cache_value === "string"
          ? data.cache_value
          : JSON.stringify(data.cache_value, null, 2),
    };
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error("获取缓存内容失败:", error);
    ElMessage.error("获取缓存内容失败，请稍后重试");
  } finally {
    loading.value = false;
  }
}

const handleClearCacheAll = async () => {
  try {
    await ElMessageBox.confirm("确定要清理全部缓存吗？", "危险！", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    await CacheAPI.deleteCacheAll();
    getCacheNameList();
    ElMessage.success("全部缓存已清理");
  } catch (error: unknown) {
    if (error !== "cancel") {
      if (import.meta.env.DEV) console.error("清理全部缓存失败:", error);
      ElMessage.error("清理全部缓存失败，请稍后重试");
    }
  }
};

const getInfo = async () => {
  try {
    loading.value = true;
    const response = await CacheAPI.getCacheInfo();
    cache.value = response.data.data || { info: {}, command_stats: [], db_size: 0 };
    void initCharts();
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error("获取缓存监控数据失败:", error);
    ElMessage.error("获取缓存监控数据失败");
  } finally {
    loading.value = false;
  }
};

/** 等待容器完成布局（路由过渡/首次渲染时 clientWidth/Height 可能为 0），避免 ECharts "Can't get DOM width or height" 警告 */
const waitForSize = (el: HTMLElement): Promise<void> =>
  new Promise((resolve) => {
    const check = () => {
      // 组件卸载后 template ref 置 null，此时 ref 不再指向 el，直接结束避免悬挂循环
      if (
        (commandstats.value !== el && usedmemory.value !== el) ||
        (el.clientWidth > 0 && el.clientHeight > 0)
      ) {
        resolve();
        return;
      }
      requestAnimationFrame(check);
    };
    check();
  });

const initCharts = async () => {
  if (!commandstats.value || !usedmemory.value) return;
  await Promise.all([waitForSize(commandstats.value), waitForSize(usedmemory.value)]);
  if (!commandstats.value || !usedmemory.value) return; // 等待期间组件被卸载

  commandstatsInstance = echarts.init(commandstats.value, "macarons");
  usedmemoryInstance = echarts.init(usedmemory.value, "macarons");

  commandstatsInstance.setOption({
    tooltip: { trigger: "item", formatter: "{a} <br/>{b} : {c} ({d}%)" },
    series: [
      {
        name: "命令",
        type: "pie",
        roseType: "radius",
        radius: ["20%", "70%"],
        center: ["50%", "50%"],
        data: cache.value.command_stats || [],
        animationEasing: "cubicInOut",
        animationDuration: 1000,
        label: {
          fontSize: 14,
        },
      },
    ],
  });

  const usedMemory = cache.value.info?.used_memory_human || "0";
  usedmemoryInstance.setOption({
    tooltip: { formatter: `{b} <br/>{a} : ${usedMemory}` },
    series: [
      {
        name: "峰值",
        type: "gauge",
        min: 0,
        max: 1000,
        radius: "70%",
        detail: { formatter: usedMemory, fontSize: 16 },
        data: [{ value: parseFloat(usedMemory) || 0, name: "内存消耗" }],
        axisLabel: {
          fontSize: 12,
        },
      },
    ],
  });

  void nextTick(() => {
    commandstatsInstance?.resize();
    usedmemoryInstance?.resize();
  });
};

const handleChartResize = () => {
  commandstatsInstance?.resize();
  usedmemoryInstance?.resize();
};

onMounted(() => {
  getCacheNameList();
  getInfo();
  window.addEventListener("resize", handleChartResize);
});

watch(activeTab, (tab) => {
  if (tab === "0") {
    nextTick(() => void initCharts());
  }
});

onUnmounted(() => {
  window.removeEventListener("resize", handleChartResize);
  commandstatsInstance?.dispose();
  usedmemoryInstance?.dispose();
});
</script>
