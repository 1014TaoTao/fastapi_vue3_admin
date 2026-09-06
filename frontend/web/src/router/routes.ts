/**
 * 静态路由定义
 *
 * 静态路由 = 首屏即注册的路由（Layout、登录页、404/500、iframe 占位等），
 * 不依赖菜单权限，用户未登录时即可访问。
 *
 * 动态路由由 `guards.ts` → `RouteRegistry` 在登录后根据不同角色的菜单列表动态 `addRoute`。
 *
 * @module router/routes
 */
import type { AppRouteRecordRaw } from "@utils";
import type { AppRouteRecord, RouteMeta } from "@/types/router";
import { defineComponent, h, KeepAlive, onMounted, ref, type VNode } from "vue";
import { RouterView, useRoute } from "vue-router";
import { $t } from "@/locales";
import { useWorktabStore } from "@stores";
import LayoutComponent from "@/layouts/index.vue";
import DashboardWorkplace from "@views/dashboard/workplace/index.vue";
import DashboardAnalysis from "@views/dashboard/analysis/index.vue";
import DashboardScreen from "@views/dashboard/screen/index.vue";
import RedirectView from "@views/redirect/index.vue";
import LoginView from "@views/module_system/auth/login/index.vue";
import Exception401 from "@views/exception/401/index.vue";
import Exception403 from "@views/exception/403/index.vue";
import Exception404 from "@views/exception/404/index.vue";
import Exception500 from "@views/exception/500/index.vue";
import DashboardHome from "@views/dashboard/home/index.vue";
import FastlinkProfile from "@views/fastlink/current/profile.vue";
import FastlinkChangelog from "@views/fastlink/changelog/index.vue";
import FastlinkPricing from "@views/fastlink/pricing/index.vue";
import FastlinkTutorial from "@views/fastlink/tutorial/index.vue";
import FastlinkFachat from "@views/fastlink/fachat/index.vue";

// ──────── IframeRouteManager ────────

/**
 * iframe 路由管理器（单例）
 *
 * 登录后将所有 iframe 路由存入 sessionStorage，F5 刷新后恢复。
 * IframeView 组件挂载时通过 findByPath 获取 iframe URL。
 */
export class IframeRouteManager {
  private static instance: IframeRouteManager;
  private iframeRoutes: AppRouteRecord[] = [];

  private constructor() {}

  /** 获取单例实例 */
  static getInstance(): IframeRouteManager {
    if (!IframeRouteManager.instance) {
      IframeRouteManager.instance = new IframeRouteManager();
    }
    return IframeRouteManager.instance;
  }

  /** 记录一个 iframe 路由（去重） */
  add(route: AppRouteRecord): void {
    if (!this.iframeRoutes.find((r) => r.path === route.path)) {
      this.iframeRoutes.push(route);
    }
  }

  /** 获取全部 iframe 路由 */
  getAll(): AppRouteRecord[] {
    return this.iframeRoutes;
  }

  /** 按路径查找（IframeView 组件挂载时用） */
  findByPath(path: string): AppRouteRecord | undefined {
    return this.iframeRoutes.find((route) => route.path === path);
  }

  /** 清空所有（退出登录时调用） */
  clear(): void {
    this.iframeRoutes = [];
  }

  /** 存入 sessionStorage（登录后动态路由注册完成时调用） */
  save(): void {
    if (this.iframeRoutes.length > 0) {
      sessionStorage.setItem("iframeRoutes", JSON.stringify(this.iframeRoutes));
    }
  }

  /** 从 sessionStorage 恢复（F5 刷新后调用） */
  load(): void {
    try {
      const data = sessionStorage.getItem("iframeRoutes");
      if (data) {
        this.iframeRoutes = JSON.parse(data);
      }
    } catch (error) {
      console.error("[IframeRouteManager] 加载 iframe 路由失败:", error);
      this.iframeRoutes = [];
    }
  }
}

// ──────── 壳层常量 ────────

/** 首页菜单配置（图标、缓存、固定标签） */
export const HOME_MENU_META: RouteMeta = {
  title: "menus.home.title",
  icon: "ri:home-smile-2-line",
  keepAlive: true,
  fixedTab: true,
};

/** 仪表盘父菜单配置 */
export const DASHBOARD_PARENT_META: RouteMeta = {
  title: "menus.dashboard.title",
  icon: "ri:pie-chart-line",
  alwaysShow: true,
};

/** Dashboard 静态子路由（唯一数据源，壳层补全和静态路由共用） */
export const dashboardLayoutChildren: AppRouteRecordRaw[] = [
  {
    path: "workplace",
    name: "DashboardWorkplace",
    component: DashboardWorkplace,
    meta: { title: "menus.dashboard.workplace", icon: "ri:bar-chart-box-line", keepAlive: true },
  },
  {
    path: "analysis",
    name: "DashboardAnalysis",
    component: DashboardAnalysis,
    meta: {
      title: "menus.dashboard.analysis",
      icon: "ri:align-item-bottom-line",
      keepAlive: false,
    },
  },
  {
    path: "screen",
    name: "DashboardScreen",
    component: DashboardScreen,
    meta: { title: "数据大屏", icon: "ri:tv-line", keepAlive: false, hidden: false },
  },
];

// ──────── 路由常量 ────────

/** 动态路由 addRoute 的父级 name（必须和静态路由 / 的 name 一致） */
export const ROOT_LAYOUT_ROUTE_NAME = "RootLayout" as const;

/** 首页子路由 name（面包屑组件会用） */
export const HOME_ROUTE_NAME = "Home" as const;

/** 纯 RouterView 占位组件 —— 多级目录只需要嵌一层，不需要实际页面 */
export const NestedRouterParent = defineComponent({
  name: "NestedRouterParent",
  setup() {
    const route = useRoute();
    const worktabStore = useWorktabStore();
    return () =>
      h(RouterView, null, {
        default: ({ Component }: { Component?: VNode }) => {
          if (!Component) return null;
          // 内层 KeepAlive（v-slot 模式）：按叶子组件名缓存，与工作栏 tab.name 一致，
          // 关闭标签时由 keepAliveExclude 精确清除；meta.keepAlive === false 时不缓存叶子
          if (route.meta.keepAlive !== false) {
            return h(
              KeepAlive,
              { exclude: worktabStore.keepAliveExclude },
              { default: () => h(Component) }
            );
          }
          return h(Component);
        },
      });
  },
});

/** 后端菜单中 component: "/index/index" = 使用 Layout 框架 */
export const ROUTE_COMPONENT_LAYOUT = "/index/index";

/** 多级目录父级占位 component */
export const ROUTE_COMPONENT_NESTED_PARENT = "/nested/router-view-parent";

/** 登录页的备用 path（守卫判断用） */
export const ROUTE_PATH_LOGIN_ALT = "/auth/login";

// ──────── IframeView 组件 ────────

/** iframe 子路由的 Vue 组件 —— 从 IframeRouteManager 获取链接，加载时显示 loading */
export const IframeView = defineComponent({
  name: "IframeView",
  setup() {
    const route = useRoute();
    const isLoading = ref(true);
    const iframeUrl = ref("");
    const iframeRef = ref<HTMLIFrameElement | null>(null);

    onMounted(() => {
      const iframeRoute = IframeRouteManager.getInstance().findByPath(route.path);
      iframeUrl.value = iframeRoute?.meta?.link || (route.meta.link as string) || "";
    });

    const handleIframeLoad = () => {
      isLoading.value = false;
    };

    return () =>
      h("div", { class: "box-border w-full h-full", "v-loading": isLoading.value }, [
        h("iframe", {
          ref: iframeRef,
          src: iframeUrl.value,
          frameborder: "0",
          class: "w-full h-full min-h-[calc(100vh-120px)] border-none",
          onLoad: handleIframeLoad,
        }),
      ]);
  },
});

// ──────── 静态路由配置 ────────

/**
 * 静态路由配置（不需要权限就能访问的路由）
 *
 * 注意事项：
 * 1、path、name 不要和动态路由冲突，否则会导致路由冲突无法访问
 * 2、静态路由不管是否登录都可以访问
 */
export const staticRoutes: AppRouteRecordRaw[] = [
  // 重定向中转页
  {
    path: "/redirect",
    meta: { hidden: true },
    component: LayoutComponent,
    children: [
      {
        path: "/redirect/:path(.*)",
        component: RedirectView,
      },
    ],
  },
  // 登录页
  {
    path: "/login",
    name: "Login",
    meta: { hidden: true, isHideTab: true, title: "menus.login.title" },
    component: LoginView,
  },
  // 异常页
  {
    path: "/401",
    name: "401",
    meta: { hidden: true, title: "401" },
    component: Exception401,
  },
  {
    path: "/403",
    name: "403",
    component: Exception403,
    meta: { hidden: true, title: "403" },
  },
  {
    path: "/404",
    name: "404",
    meta: { hidden: true, title: "404" },
    component: Exception404,
  },
  {
    path: "/500",
    name: "500",
    meta: { hidden: true, title: "500" },
    component: Exception500,
  },
  // 根 Layout：存放壳层路由（home/dashboard/fastlink）
  {
    path: "/",
    name: ROOT_LAYOUT_ROUTE_NAME,
    redirect: "/home",
    component: LayoutComponent,
    children: [
      {
        path: "home",
        name: HOME_ROUTE_NAME,
        component: DashboardHome,
        meta: HOME_MENU_META,
      },
      {
        path: "dashboard",
        name: "Dashboard",
        redirect: "/dashboard/workplace",
        component: NestedRouterParent,
        meta: DASHBOARD_PARENT_META,
        children: dashboardLayoutChildren,
      },
      // 隐藏的壳层路由：个人中心、更新日志、定价、教程、AI 聊天
      {
        path: "fastlink",
        name: "Fastlink",
        component: NestedRouterParent,
        meta: { hidden: true },
        children: [
          {
            path: "profile",
            name: "FastlinkProfile",
            meta: { title: $t("menus.system.userCenter"), icon: "ri:user-line", hidden: true },
            component: FastlinkProfile,
          },
          {
            path: "changelog",
            name: "FastlinkChangeLog",
            meta: {
              title: $t("menus.changelog.title"),
              icon: "ri:draft-line",
              hidden: true,
              keepAlive: true,
              isHideTab: true,
            },
            component: FastlinkChangelog,
          },
          {
            path: "pricing",
            name: "FastlinkPricing",
            meta: {
              title: $t("menus.dashboard.pricing"),
              icon: "ri:money-cny-box-line",
              hidden: true,
              keepAlive: true,
              isHideTab: true,
            },
            component: FastlinkPricing,
          },
          {
            path: "tutorial",
            name: "FastlinkTutorial",
            meta: {
              title: $t("menus.dashboard.tutorial"),
              icon: "ri:book-2-line",
              hidden: true,
              keepAlive: true,
              isHideTab: true,
            },
            component: FastlinkTutorial,
          },
          {
            path: "fachat",
            name: "FastlinkFachat",
            meta: {
              title: $t("menus.fachat.title"),
              icon: "ri:message-3-line",
              hidden: true,
              keepAlive: true,
              isHideTab: true,
            },
            component: FastlinkFachat,
          },
        ],
      },
    ],
  },
  // iframe 外部链接
  {
    path: "/outside",
    component: LayoutComponent,
    name: "Outside",
    meta: { title: "menus.outside.title" },
    children: [
      {
        path: "/outside/iframe/:path",
        name: "Iframe",
        component: IframeView,
        meta: { title: "iframe" },
      },
    ],
  },
  // 兜底 404（必须放最后）
  {
    path: "/:pathMatch(.*)*",
    name: "CatchAll404",
    component: Exception404,
    meta: { hidden: true, title: "404" },
  },
];
