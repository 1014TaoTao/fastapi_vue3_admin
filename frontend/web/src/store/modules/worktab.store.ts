/**
 * 工作标签页状态管理模块
 *
 * 提供多标签页功能的完整状态管理
 *
 * ## 主要功能
 *
 * - 标签页打开和关闭
 * - 标签页固定和取消固定
 * - 批量关闭（左侧、右侧、其他、全部）
 * - 标签页缓存管理（KeepAlive）
 * - 标签页标题自定义
 * - 标签页路由验证
 * - 动态路由参数处理
 *
 * ## 使用场景
 *
 * - 多标签页导航
 * - 页面缓存控制
 * - 标签页右键菜单
 * - 固定常用页面
 * - 批量关闭标签
 *
 * ## 核心特性
 *
 * - 标签以 path 标识；同一路由组件可对不同 path 多开
 * - 固定标签页保护（不可关闭）
 * - KeepAlive 缓存排除管理
 * - 路由有效性验证
 * - 首页自动保留
 *
 * ## 持久化
 * - 使用 localStorage 存储
 * - 存储键：sys-v{version}-worktab
 * - 刷新页面保持标签状态
 *
 * @module store/modules/worktab.store
 * @author FastapiAdmin Team
 */
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { router } from "@/router";
import type { LocationQueryRaw, Router } from "vue-router";
import type { WorkTab } from "@/types/store";

import { useCommon } from "@/hooks/core/useCommon";
import { ROUTE_PATH_LOGIN_ALT } from "@/router/routes";

interface WorktabState {
  current: Partial<WorkTab>;
  opened: WorkTab[];
  keepAliveExclude: string[];
}

/**
 * 工作台标签页管理 Store
 */
export const useWorktabStore = defineStore(
  "worktabStore",
  () => {
    // 状态定义
    const current = ref<Partial<WorkTab>>({});
    const opened = ref<WorkTab[]>([]);
    const keepAliveExclude = ref<string[]>([]);

    // 计算属性
    const hasOpenedTabs = computed(() => opened.value.length > 0);
    const hasMultipleTabs = computed(() => opened.value.length > 1);
    const currentTabIndex = computed(() =>
      current.value.path ? opened.value.findIndex((tab) => tab.path === current.value.path) : -1
    );

    /**
     * 查找标签页索引
     */
    const findTabIndex = (path: string): number => {
      return opened.value.findIndex((tab) => tab.path === path);
    };

    /**
     * 获取标签页
     */
    const getTab = (path: string): WorkTab | undefined => {
      return opened.value.find((tab) => tab.path === path);
    };

    /**
     * 检查标签页是否可关闭
     */
    const isTabClosable = (tab: WorkTab): boolean => {
      return !tab.fixedTab;
    };

    /**
     * 安全的路由跳转
     */
    const safeRouterPush = (tab: Partial<WorkTab>): void => {
      if (!tab.path) {
        if (import.meta.env.DEV) console.warn("尝试跳转到无效路径的标签页");
        return;
      }

      try {
        router.push({
          path: tab.path,
          query: tab.query as LocationQueryRaw,
        });
      } catch (error) {
        if (import.meta.env.DEV) console.error("路由跳转失败:", error);
      }
    };

    /**
     * 批量关标签后：若当前 URL 已不在 opened 中，则跳到 `current` 对应标签（避免路由与工作栏脱节）。
     */
    const ensureRouterMatchesOpenedTab = (): void => {
      if (!opened.value.length) return;
      const locPath = router.currentRoute.value.path;
      if (opened.value.some((t) => t.path === locPath)) return;
      const tab = current.value as Partial<WorkTab>;
      if (tab.path) {
        safeRouterPush(tab as WorkTab);
      }
    };

    /**
     * 打开或激活一个选项卡
     */
    const openTab = (tab: WorkTab): void => {
      if (!tab.path) {
        if (import.meta.env.DEV) console.warn("尝试打开无效的标签页");
        return;
      }

      // 从 keepAlive 排除列表中移除
      if (tab.name) {
        removeKeepAliveExclude(tab.name);
      }

      // 仅以 path 识别标签：同一 route_name（同一组件）可对不同 path 同时保留多条标签
      const existingIndex = findTabIndex(tab.path);

      if (existingIndex === -1) {
        // 新增标签页
        const insertIndex = tab.fixedTab ? findFixedTabInsertIndex() : opened.value.length;
        const newTab = { ...tab };

        if (tab.fixedTab) {
          opened.value.splice(insertIndex, 0, newTab);
        } else {
          opened.value.push(newTab);
        }

        current.value = newTab;
      } else {
        // 更新现有标签页（当动态路由参数或查询变更时，复用同一标签）
        const existingTab = opened.value[existingIndex]!;

        opened.value[existingIndex] = {
          ...existingTab,
          path: tab.path,
          params: tab.params,
          query: tab.query,
          title: tab.title || existingTab.title,
          fixedTab: tab.fixedTab ?? existingTab.fixedTab,
          keepAlive: tab.keepAlive ?? existingTab.keepAlive,
          name: tab.name || existingTab.name,
          icon: tab.icon || existingTab.icon,
        };

        current.value = opened.value[existingIndex]!;
      }
    };

    /**
     * 查找固定标签页的插入位置
     */
    const findFixedTabInsertIndex = (): number => {
      let insertIndex = 0;
      for (let i = 0; i < opened.value.length; i++) {
        if (opened.value[i]!.fixedTab) {
          insertIndex = i + 1;
        } else {
          break;
        }
      }
      return insertIndex;
    };

    /**
     * 关闭指定的选项卡
     */
    const removeTab = (path: string): void => {
      const targetTab = getTab(path);
      const targetIndex = findTabIndex(path);

      if (targetIndex === -1) {
        if (import.meta.env.DEV) console.warn(`尝试关闭不存在的标签页: ${path}`);
        return;
      }

      if (targetTab && !isTabClosable(targetTab)) {
        if (import.meta.env.DEV) console.warn(`尝试关闭固定标签页: ${path}`);
        return;
      }

      // 从标签页列表中移除
      opened.value.splice(targetIndex, 1);

      // 处理缓存排除
      if (targetTab?.name) {
        addKeepAliveExclude(targetTab);
      }

      const { homePath } = useCommon();

      // 如果关闭后无标签页，跳转首页
      if (!hasOpenedTabs.value) {
        if (path !== homePath.value) {
          current.value = {};
          safeRouterPush({ path: homePath.value });
        }
        return;
      }

      // 如果关闭的是当前激活标签，需要激活其他标签
      if (current.value.path === path) {
        const newIndex = targetIndex >= opened.value.length ? opened.value.length - 1 : targetIndex;
        const nextTab = opened.value[newIndex];
        if (!nextTab) return;
        current.value = nextTab;
        safeRouterPush(nextTab);
      }
    };

    /**
     * 关闭左侧选项卡
     */
    const removeLeft = (path: string): void => {
      const targetIndex = findTabIndex(path);

      if (targetIndex === -1) {
        if (import.meta.env.DEV) console.warn(`尝试关闭左侧标签页，但目标标签页不存在: ${path}`);
        return;
      }

      // 获取左侧可关闭的标签页
      const leftTabs = opened.value.slice(0, targetIndex);
      const closableLeftTabs = leftTabs.filter(isTabClosable);

      if (closableLeftTabs.length === 0) {
        if (import.meta.env.DEV) console.warn("左侧没有可关闭的标签页");
        return;
      }

      // 标记为缓存排除
      markTabsToRemove(closableLeftTabs);

      // 移除左侧可关闭的标签页
      opened.value = opened.value.filter(
        (tab, index) => index >= targetIndex || !isTabClosable(tab)
      );

      // 确保当前标签是激活状态
      const targetTab = getTab(path);
      if (targetTab) {
        current.value = targetTab;
      }
      ensureRouterMatchesOpenedTab();
    };

    /**
     * 关闭右侧选项卡
     */
    const removeRight = (path: string): void => {
      const targetIndex = findTabIndex(path);

      if (targetIndex === -1) {
        if (import.meta.env.DEV) console.warn(`尝试关闭右侧标签页，但目标标签页不存在: ${path}`);
        return;
      }

      // 获取右侧可关闭的标签页
      const rightTabs = opened.value.slice(targetIndex + 1);
      const closableRightTabs = rightTabs.filter(isTabClosable);

      if (closableRightTabs.length === 0) {
        if (import.meta.env.DEV) console.warn("右侧没有可关闭的标签页");
        return;
      }

      // 标记为缓存排除
      markTabsToRemove(closableRightTabs);

      // 移除右侧可关闭的标签页
      opened.value = opened.value.filter(
        (tab, index) => index <= targetIndex || !isTabClosable(tab)
      );

      // 确保当前标签是激活状态
      const targetTab = getTab(path);
      if (targetTab) {
        current.value = targetTab;
      }
      ensureRouterMatchesOpenedTab();
    };

    /**
     * 关闭其他选项卡
     */
    const removeOthers = (path: string): void => {
      const targetTab = getTab(path);

      if (!targetTab) {
        if (import.meta.env.DEV) console.warn(`尝试关闭其他标签页，但目标标签页不存在: ${path}`);
        return;
      }

      // 获取其他可关闭的标签页
      const otherTabs = opened.value.filter((tab) => tab.path !== path);
      const closableTabs = otherTabs.filter(isTabClosable);

      if (closableTabs.length === 0) {
        if (import.meta.env.DEV) console.warn("没有其他可关闭的标签页");
        return;
      }

      // 标记为缓存排除
      markTabsToRemove(closableTabs);

      // 只保留当前标签和固定标签
      opened.value = opened.value.filter((tab) => tab.path === path || !isTabClosable(tab));

      // 确保当前标签是激活状态
      current.value = targetTab;
      ensureRouterMatchesOpenedTab();
    };

    /**
     * 关闭所有可关闭的标签页
     */
    const removeAll = (): void => {
      const { homePath } = useCommon();
      const hasFixedTabs = opened.value.some((tab) => tab.fixedTab);

      // 获取可关闭的标签页
      const closableTabs = opened.value.filter((tab) => {
        if (!isTabClosable(tab)) return false;
        // 如果有固定标签，则所有可关闭的都可以关闭；否则保留首页
        return hasFixedTabs || tab.path !== homePath.value;
      });

      if (closableTabs.length === 0) {
        if (import.meta.env.DEV) console.warn("没有可关闭的标签页");
        return;
      }

      // 标记为缓存排除
      markTabsToRemove(closableTabs);

      // 保留不可关闭的标签页和首页（当没有固定标签时）
      opened.value = opened.value.filter((tab) => {
        return !isTabClosable(tab) || (!hasFixedTabs && tab.path === homePath.value);
      });

      // 处理激活状态
      if (!hasOpenedTabs.value) {
        current.value = {};
        safeRouterPush({ path: homePath.value });
        return;
      }

      // 选择激活的标签页：优先首页，其次第一个可用标签
      const homeTab = opened.value.find((tab) => tab.path === homePath.value);
      const targetTab = homeTab || opened.value[0];
      if (!targetTab) return;

      current.value = targetTab;
      safeRouterPush(targetTab as Partial<WorkTab>);
    };

    /**
     * KeepAlive 的 exclude 按「组件名」匹配，会一次性清掉所有同名实例。
     * 仅当 remaining 中已无任何同名标签时，才把该组件名加入 exclude（支持同 route_name 多 path 并存）。
     */
    const pushExcludeIfLastSiblingOfName = (
      name: string | undefined,
      remaining: WorkTab[],
      tab: Pick<WorkTab, "keepAlive">
    ): void => {
      if (!name || tab.keepAlive === false) return;
      if (remaining.some((t) => t.name === name)) return;
      if (!keepAliveExclude.value.includes(name)) {
        keepAliveExclude.value.push(name);
      }
    };

    /**
     * 将指定选项卡添加到 keepAlive 排除列表中。
     * 须与布局「keepAlive !== false 即缓存」一致：仅用 `=== false` 跳过（undefined/true 均应排除），
     * 否则关标签时无法剔除原先 meta 未显式写 keepAlive 的页的缓存。
     */
    const addKeepAliveExclude = (tab: WorkTab): void => {
      pushExcludeIfLastSiblingOfName(tab.name, opened.value, tab);
    };

    /**
     * 从 keepAlive 排除列表中移除指定组件名称
     */
    const removeKeepAliveExclude = (name: string): void => {
      if (!name) return;

      keepAliveExclude.value = keepAliveExclude.value.filter((item) => item !== name);
    };

    /**
     * 将传入的一组选项卡的组件名称标记为排除缓存
     */
    const markTabsToRemove = (tabs: WorkTab[]): void => {
      const removedPaths = new Set(tabs.map((t) => t.path));
      const futureOpened = opened.value.filter((t) => !removedPaths.has(t.path));
      for (const tab of tabs) {
        if (tab.name) {
          pushExcludeIfLastSiblingOfName(tab.name, futureOpened, tab);
        }
      }
    };

    /**
     * 切换指定标签页的固定状态
     */
    const toggleFixedTab = (path: string): void => {
      const targetIndex = findTabIndex(path);

      if (targetIndex === -1) {
        if (import.meta.env.DEV) console.warn(`尝试切换不存在标签页的固定状态: ${path}`);
        return;
      }

      const tab = { ...opened.value[targetIndex]! };
      tab.fixedTab = !tab.fixedTab;

      // 移除原位置
      opened.value.splice(targetIndex, 1);

      if (tab.fixedTab) {
        // 固定标签插入到所有固定标签的末尾
        const firstNonFixedIndex = opened.value.findIndex((t) => !t.fixedTab);
        const insertIndex = firstNonFixedIndex === -1 ? opened.value.length : firstNonFixedIndex;
        opened.value.splice(insertIndex, 0, tab);
      } else {
        // 非固定标签插入到所有固定标签后
        const fixedCount = opened.value.filter((t) => t.fixedTab).length;
        opened.value.splice(fixedCount, 0, tab);
      }

      // 更新当前标签引用
      if (current.value.path === path) {
        current.value = tab;
      }
    };

    /**
     * 验证工作台标签页的路由有效性
     */
    const validateWorktabs = (routerInstance: Router): void => {
      try {
        const allRoutes = routerInstance.getRoutes(); // 只调用一次，避免在循环中重复拷贝
        // 动态路由校验：优先使用路由 name 判断有效性；否则用 resolve 匹配参数化路径
        const isTabRouteValid = (tab: Partial<WorkTab>): boolean => {
          try {
            if (tab.name) {
              if (allRoutes.some((r) => r.name === tab.name)) return true;
            }
            if (tab.path) {
              const resolved = routerInstance.resolve({
                path: tab.path,
                query: (tab.query as LocationQueryRaw) || undefined,
              });
              return resolved.matched.length > 0;
            }
            return false;
          } catch {
            return false;
          }
        };

        /** 登录页不应出现在工作台标签（历史持久化可能残留） */
        const isLoginWorktab = (tab: Partial<WorkTab>): boolean =>
          tab.name === "Login" || tab.path === "/login" || tab.path === ROUTE_PATH_LOGIN_ALT;

        // 过滤出有效的标签页
        const validTabs = opened.value.filter(
          (tab) => isTabRouteValid(tab) && !isLoginWorktab(tab)
        );

        if (validTabs.length !== opened.value.length) {
          if (import.meta.env.DEV) console.warn("发现无效的标签页路由，已自动清理");
          const validPaths = new Set(validTabs.map((t) => t.path));
          // 未走 removeTab 批量剔除的标签：须同步 exclude；同名多标签时仅最后一条删尽才 exclude
          for (const tab of opened.value) {
            if (!validPaths.has(tab.path) && tab.name && tab.keepAlive !== false) {
              pushExcludeIfLastSiblingOfName(tab.name, validTabs, tab);
            }
          }
          opened.value = validTabs;
        }

        // 验证当前激活标签的有效性（登录页不应作为当前工作台标签）
        const isCurrentValid =
          current.value && isTabRouteValid(current.value) && !isLoginWorktab(current.value);

        if (!isCurrentValid && validTabs.length > 0) {
          if (import.meta.env.DEV) console.warn("当前激活标签无效，已自动切换");
          const firstValid = validTabs[0];
          if (firstValid) current.value = firstValid;
        } else if (!isCurrentValid) {
          current.value = {};
        }
      } catch (error) {
        if (import.meta.env.DEV) console.error("验证工作台标签页失败:", error);
      }
    };

    /**
     * 清空所有状态（用于登出等场景）
     *
     * 保留固定标签页（fixedTab: true），登出后重新登录时首页等常驻标签依然存在。
     */
    const clearAll = (): void => {
      const fixedTabs = opened.value.filter((tab) => tab.fixedTab);
      // 旧会话的 KeepAlive 缓存实例必须驱逐：
      // opened 清空后 include 会变为 undefined（KeepAlive 对 undefined include 不做 prune），
      // 旧实例会带着 WebSocket / 定时器等副作用跨会话存活。
      const removedTabs = fixedTabs.length > 0 ? opened.value.filter((tab) => !tab.fixedTab) : opened.value;
      const excludeNames = new Set<string>();
      for (const tab of removedTabs) {
        if (tab.name && tab.keepAlive !== false) excludeNames.add(String(tab.name));
      }
      if (fixedTabs.length > 0) {
        opened.value = fixedTabs;
        current.value = { ...fixedTabs[0] };
      } else {
        current.value = {};
        opened.value = [];
      }
      // 用「待删标签组件名」替换 exclude（而非清空）：KeepAlive 收到非空 exclude 会 prune 掉这些组件的缓存实例；
      // 下次 openTab 的 removeKeepAliveExclude 会自动将其移出，恢复正常缓存
      keepAliveExclude.value = Array.from(excludeNames);
    };

    /**
     * 获取状态快照（用于持久化存储）
     */
    const getStateSnapshot = (): WorktabState => {
      return {
        current: { ...current.value },
        opened: [...opened.value],
        keepAliveExclude: [...keepAliveExclude.value],
      };
    };

    /**
     * 获取标签页标题
     */
    const getTabTitle = (path: string): WorkTab | undefined => {
      const tab = getTab(path);
      return tab;
    };

    /**
     * 更新标签页标题
     */
    const updateTabTitle = (path: string, title: string): void => {
      const tab = getTab(path);
      if (tab) {
        tab.customTitle = title;
      }
    };

    /**
     * 重置标签页标题
     */
    const resetTabTitle = (path: string): void => {
      const tab = getTab(path);
      if (tab) {
        tab.customTitle = "";
      }
    };

    /**
     * 关闭「多标签栏」时：visited 不写入 `opened`（与 KeepAlive include 策略一致），
     * 但路由每次完成导航后应更新 `current`，避免持久化/内部状态与 `router` 真值脱节。
     */
    const syncCurrentFromRoute = (tab: {
      path: string;
      name: string;
      title: string;
      icon?: string;
      keepAlive: boolean;
      params?: object;
      query?: LocationQueryRaw;
    }): void => {
      current.value = {
        path: tab.path,
        name: tab.name,
        title: tab.title,
        icon: tab.icon,
        keepAlive: tab.keepAlive,
        params: tab.params,
        query: tab.query,
      };
    };

    return {
      // 状态
      current,
      opened,
      keepAliveExclude,

      // 计算属性
      hasOpenedTabs,
      hasMultipleTabs,
      currentTabIndex,

      // 方法
      openTab,
      removeTab,
      removeLeft,
      removeRight,
      removeOthers,
      removeAll,
      toggleFixedTab,
      validateWorktabs,
      clearAll,
      getStateSnapshot,

      // 工具方法
      findTabIndex,
      getTab,
      isTabClosable,
      addKeepAliveExclude,
      removeKeepAliveExclude,
      markTabsToRemove,
      getTabTitle,
      updateTabTitle,
      resetTabTitle,
      syncCurrentFromRoute,
    };
  },
  {
    persist: {
      key: "worktab",
      storage: localStorage,
    },
  }
);
