<!-- 布局内容 -->
<template>
  <div id="app-scroll-main" class="layout-content" :style="containerStyle">
    <div id="app-content-header">
      <!-- 节日滚动 -->
      <FaFestivalTextScroll />

      <!-- 路由信息调试 -->
      <div
        v-if="isOpenRouteInfo === 'true'"
        class="px-2 py-1.5 mb-3 text-sm text-g-500 bg-g-200 border border-(--default-border) rounded-md"
      >
        router meta：{{ route.meta }}
      </div>
    </div>

    <RouterView v-if="isRefresh" v-slot="{ Component, route: router }" :style="contentStyle">
      <Transition :name="actualTransition" mode="out-in">
        <div v-if="Component" class="route-view-shell flex min-h-0 min-w-0 w-full flex-1 flex-col">
          <!-- 是否缓存以后端菜单 keep_alive → meta.keepAlive 为准；此处 !== false 即包 KeepAlive（与 MenuProcessor 一致） -->
          <KeepAlive
            v-if="wrapPageWithKeepAlive"
            :max="10"
            :include="keepAliveInclude"
            :exclude="keepAliveExclude"
          >
            <component
              class="fa-page-view min-h-0 min-w-0 w-full flex-1"
              :is="Component"
              :key="routeLeafCacheKey(router)"
            />
          </KeepAlive>
          <component
            v-else
            class="fa-page-view min-h-0 min-w-0 w-full flex-1"
            :is="Component"
            :key="routeLeafCacheKey(router)"
          />
        </div>
      </Transition>
    </RouterView>

    <!-- 返回顶部：宽屏 #app-scroll-main；窄屏文档滚动 target 置空 -->
    <ElBacktop
      :key="backtopTargetKey"
      :target="backtopScrollTarget"
      :right="28"
      :bottom="28"
      class="z-90"
    >
      <FaSvgIcon icon="ri:arrow-up-circle-line" class="text-2xl text-theme" />
    </ElBacktop>
  </div>
</template>
<script setup lang="ts">
/**
 * 布局滚动容器 + 业务路由出口；与 settings.refresh 联动可整体重建 RouterView。
 *
 * 缓存开关数据源：后端菜单 `keep_alive` → MenuProcessor 写入 `meta.keepAlive`；工作栏 tab 随路由写入同一 meta。
 * include / wrapPageWithKeepAlive 均用 `!== false`，与静态路由里显式 `keepAlive: false`、后端布尔字段对齐。
 */
import type { CSSProperties } from "vue";
import { useMediaQuery } from "@vueuse/core";
import { useRoute, useRouter, type RouteLocationNormalizedLoaded } from "vue-router";
import { useSettingsStore, useWorktabStore } from "@stores";

defineOptions({ name: "FaPageContent" });

/**
 * KeepAlive / RouterView 子节点缓存键。
 * - `meta.remountOnFullPath === true`：整 URL 参与键（依赖 query 初值或须随 query 重建的页）。
 * - 有 `name`：`name` + `params`，同一路由仅 query 变化不换实例。
 * - 无 `name`：`path`（勿用 fullPath，否则仅 query 变化也会反复挂载）。
 */
function routeLeafCacheKey(r: RouteLocationNormalizedLoaded): string {
  if (r.meta.remountOnFullPath === true) {
    return r.fullPath;
  }
  if (r.name != null) {
    return `${String(r.name)}:${JSON.stringify(r.params ?? {})}`;
  }
  return r.path;
}

const route = useRoute();
const router = useRouter();
/** 动态菜单 meta.keepAlive（后端 keep_alive）；仅显式 false 时不包 KeepAlive */
const wrapPageWithKeepAlive = computed(() => route.meta.keepAlive !== false);

const isNarrowViewport = useMediaQuery("(max-width: 800px)");
const backtopScrollTarget = computed(() => (isNarrowViewport.value ? "" : "#app-content"));
const backtopTargetKey = computed(() => (isNarrowViewport.value ? "win" : "main"));

const { pageTransition, containerWidth, refresh, showWorkTab } = storeToRefs(useSettingsStore());
const { keepAliveExclude, opened } = storeToRefs(useWorktabStore());

/** 嵌套路由壳组件名：内层叶子缓存依赖壳实例存活，include 需一并纳入（对应 routes.ts 的 NestedRouterParent） */
const NESTED_PARENT_COMPONENT_NAME = "NestedRouterParent";

/** 判断路径是否命中嵌套路由（匹配链上存在 NestedRouterParent 壳） */
function isNestedRoutePath(path: string): boolean {
  try {
    return router
      .resolve({ path })
      .matched.some((m) => m.components?.default?.name === NESTED_PARENT_COMPONENT_NAME);
  } catch {
    return false;
  }
}

/**
 * 多标签开启时：仅已打开且允许缓存的标签组件名进入 include；关闭多标签时不传 include，避免 opened 过窄误伤缓存。
 * 嵌套路由额外把壳组件 NestedRouterParent 纳入 include，否则内层叶子缓存会随壳销毁而失效。
 */
const keepAliveInclude = computed(() => {
  if (!showWorkTab.value) return undefined;
  const names = new Set<string>();
  for (const t of opened.value) {
    if (t.name && t.keepAlive !== false) names.add(String(t.name));
    if (t.keepAlive !== false && isNestedRoutePath(t.path)) {
      names.add(NESTED_PARENT_COMPONENT_NAME);
    }
  }
  return names.size ? Array.from(names) : undefined;
});

const isRefresh = shallowRef(true);
const isOpenRouteInfo = import.meta.env.VITE_OPEN_ROUTE_INFO;

/** 浏览器首次进入：关闭路由过渡动画，避免首屏闪动 */
const isFirstLoad = ref(true);

const actualTransition = computed(() => {
  if (isFirstLoad.value) return "";
  return pageTransition.value;
});

const containerStyle = computed(
  (): CSSProperties => ({
    width: "100%",
    minWidth: 0,
    maxWidth: containerWidth.value,
    flex: "1",
    minHeight: "0",
    display: "flex",
    flexDirection: "column",
  })
);

/** 常规布局下由 `.layout-content` 承担纵向滚动，路由视图填满剩余高度 */
const contentStyle = computed(
  (): CSSProperties => ({ flex: "1", minHeight: "0", minWidth: 0, width: "100%" })
);

const reload = () => {
  isRefresh.value = false;
  nextTick(() => {
    isRefresh.value = true;
  });
};

watch(refresh, reload, { flush: "post" });

// 组件挂载后标记首次加载完成
onMounted(() => {
  // 延迟一帧，确保首次渲染完成
  nextTick(() => {
    isFirstLoad.value = false;
  });
});
</script>
