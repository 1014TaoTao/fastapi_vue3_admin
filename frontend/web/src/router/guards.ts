/**
 * 路由守卫
 *
 * - beforeEach：登录校验、动态路由加载、权限检查、404 回落
 * - afterEach：页面前进回退不刷新、NProgress 关闭、loading 关闭
 *
 * @module router/guards
 */
import type { Router, RouteLocationNormalized } from "vue-router";
import type { AppRouteRecord } from "@/types/router";
import { ref } from "vue";
import { useUserStore, useMenuStore, useWorktabStore } from "@/store";
import { IframeRouteManager, ROUTE_PATH_LOGIN_ALT } from "./routes";
import { router, HOME_PAGE_PATH } from "./index";
import { setPageTitle, setWorktab } from "@utils/navigation";
import { MenuProcessor } from "./MenuProcessor";
import { NProgress } from "@utils/ui";
import { Auth } from "@utils/auth";
import { isHttpError, ApiStatus } from "@utils/http";
import { refreshState } from "./refresh";

/** 全局 loading 状态（用于路由切换时显示加载遮罩） */
const globalLoading = ref(false);

// ──────── 工具函数 ────────

/** 公开页面路径正则列表（无需登录即可访问） */
const ANONYMOUS_PUBLIC_REGEXPS = [
  /^\/401$/,
  /^\/403$/,
  /^\/404$/,
  /^\/500$/,
  /^\/redirect/,
  /^\/login$/,
];
function isAnonymousPublicPath(path: string): boolean {
  return ANONYMOUS_PUBLIC_REGEXPS.some((regexp) => regexp.test(path));
}

/** 登录页路由 */
function isLoginRoute(to: RouteLocationNormalized): boolean {
  return to.path === "/login" || to.path === ROUTE_PATH_LOGIN_ALT;
}
// ──────── 前置守卫 ────────

/**
 * 前置守卫：导航前检查登录状态、动态路由加载、权限校验
 */
export function setupBeforeEachGuard(router: Router): void {
  router.beforeEach(async (to) => {
    // 初始化守卫状态
    if (globalLoading.value) globalLoading.value = false;
    NProgress.start();

    // 存储失效检查（localStorage 异常时直接登出）
    const storageFailed = checkStorageHealth();
    if (storageFailed) {
      await handleStorageFailure();
      return "/login";
    }

    // 处理登录路由和公开路径
    if (!(await handleLoginStatus(to))) {
      return isLoginRoute(to) ? true : "/login";
    }

    // 路由初始化失败 → 跳转 500
    if (refreshState.routeInitFailed && !isAnonymousPublicPath(to.path)) {
      return "/500";
    }

    // 已登录、动态路由未注册 → 加载
    if (!refreshState.dynamicRoutesRegistered && !isAnonymousPublicPath(to.path)) {
      // 正在加载中 → 跳转首页，避免进入后路由未注册导致 404
      if (refreshState.pendingLoading) {
        return { path: HOME_PAGE_PATH, replace: true };
      }
      const redirect = await handleDynamicRoutes(to);
      if (redirect) return redirect;
      refreshState.dynamicRoutesRegistered = true;

      // 注册动态路由后，若原导航被 catch-all 404 捕获（F5 刷新场景），重定向触发重新解析
      if (to.matched.some((r) => r.name === "CatchAll404")) {
        return { path: to.path, replace: true };
      }
    }

    // 访问根路径 → 跳转首页
    if (to.path === "/") {
      return { path: HOME_PAGE_PATH, replace: true };
    }
  });
}

// ──────── 登录状态处理 ────────

/**
 * 处理登录状态
 * - 已登录：禁止访问登录页 → 重定向首页
 * - 未登录：公开路径放行，否则阻止
 */
async function handleLoginStatus(to: RouteLocationNormalized): Promise<boolean> {
  const isLoggedIn = Auth.isLoggedIn();

  if (isLoggedIn) {
    if (isLoginRoute(to)) {
      await router.push({ path: HOME_PAGE_PATH, replace: true });
      return false;
    }
    return true;
  }

  // 未登录：公开路径放行
  if (isAnonymousPublicPath(to.path)) {
    return true;
  }

  return false;
}

// ──────── 动态路由加载 ────────

/**
 * 加载动态路由
 * 1. 异常检测：空菜单修复
 * 2. 拉用户信息（附带菜单）
 * 3. 注册动态路由
 * 4. 校验目标路径权限
 * 5. 返回 redirect 路径或 undefined
 */
async function handleDynamicRoutes(
  to: RouteLocationNormalized
): Promise<undefined | string | { path: string; replace: boolean }> {
  if (refreshState.pendingLoading) return;
  refreshState.pendingLoading = true;

  try {
    // 异常恢复：菜单空了但路由还在，做反注册
    repairDynamicRoutesIfMenuEmpty();

    // 拉用户信息（F5 刷新后为空需重新获取；登录流程已获取过则跳过）
    const userStore = useUserStore();
    if (!userStore.info?.username || userStore.routeList.length === 0) {
      await userStore.getUserInfo();
    }

    // 获取菜单
    const menuProcessor = new MenuProcessor();
    const menuList = await menuProcessor.getMenuList();

    // 更新侧栏菜单列表（含壳层路由补全）
    useMenuStore().setMenuList(menuList);

    // 注册动态路由
    const { RouteRegistry } = await import("./route-loader");
    const routeRegistry = new RouteRegistry(router);
    routeRegistry.register(menuList);

    // 保存路由清理函数到 menuStore（供 logout/menu-refresh 卸载用）
    useMenuStore().addRemoveRouteFns(routeRegistry.getRemoveRouteFns());

    // 验证并清理持久化标签页中的无效/残留路由（菜单变更后）
    useWorktabStore().validateWorktabs(router);

    // 保存 iframe 路由到 sessionStorage（F5 刷新恢复）
    IframeRouteManager.getInstance().save();

    // 校验目标路由是否有权限
    const { path: safePath, hasPermission } = RoutePermissionValidator.validatePath(
      to.path,
      menuList,
      HOME_PAGE_PATH
    );

    if (!hasPermission) {
      console.warn(`[路由守卫] 无权限访问: ${to.path}，重定向至首页`);
    }

    // 权限检查后跳转到安全路径
    if (safePath !== to.path) {
      return { path: safePath, replace: true };
    }

    return undefined;
  } catch (error) {
    console.error("[路由守卫] 路由初始化失败:", error);
    // 认证失败（如生产环境部署后旧 token 失效）跳转登录页，不标记为路由初始化失败
    if (
      isHttpError(error) &&
      (error.code === ApiStatus.unauthorized || error.code === ApiStatus.forbidden)
    ) {
      refreshState.dynamicRoutesRegistered = false;
      return "/login";
    }
    refreshState.routeInitFailed = true;
    return "/500";
  } finally {
    refreshState.pendingLoading = false;
  }
}

/**
 * 异常恢复：如果 menuStore 中的菜单列表为空但动态路由已经注册了，
 * 尝试恢复到已注册状态，防止重复拉菜单。
 */
function repairDynamicRoutesIfMenuEmpty(): void {
  const menuStore = useMenuStore();
  const removeRouteFns = menuStore.removeRouteFns;
  if (menuStore.menuList.length === 0 && removeRouteFns.length > 0) {
    console.warn("[路由守卫] 检测到菜单为空但路由已注册，尝试恢复状态");
  }
}

// ──────── 内存存储健康检查 ────────

/**
 * 检查 localStorage / sessionStorage 是否可正常写入
 * 用户关闭了第三方 cookie 或处于无痕模式下可能异常
 */
function checkStorageHealth(): boolean {
  try {
    const testKey = "__storage_test__";
    localStorage.setItem(testKey, "1");
    localStorage.removeItem(testKey);
    return false;
  } catch {
    return true;
  }
}

/** 存储失效时的降级处理 */
async function handleStorageFailure(): Promise<void> {
  const userStore = useUserStore();
  userStore.$reset();
  IframeRouteManager.getInstance().clear();
}

// ──────── 权限校验 ────────

/**
 * 路由权限校验器
 *
 * 检查用户是否有权访问指定路径。
 * 守卫中用于 404 回落判定，防止无权用户通过输入 URL 绕过菜单访问。
 */
export class RoutePermissionValidator {
  /** 已被 RouteRegistry 注册为静态壳层的路由第一段（不在后端菜单中，始终放行） */
  private static readonly SHELL_SEGMENTS = new Set(["home", "dashboard", "fastlink"]);

  /** 判断用户是否有权限访问 targetPath（/ 和壳层路由始终放行） */
  static hasPermission(targetPath: string, menuList: AppRouteRecord[]): boolean {
    if (targetPath === "/") return true;
    if (this.isShellPath(targetPath)) return true;
    return this.matchRoute(targetPath, menuList);
  }

  /** 判断是否已知静态壳层路径（不在后端菜单里，无需权限校验） */
  private static isShellPath(targetPath: string): boolean {
    const firstSegment = targetPath.split("/").filter(Boolean)[0] ?? "";
    return this.SHELL_SEGMENTS.has(firstSegment);
  }

  /** 递归匹配路由路径（支持动态路由参数 /user/:id） */
  static matchRoute(targetPath: string, routes: AppRouteRecord[]): boolean {
    if (!Array.isArray(routes) || routes.length === 0) return false;
    for (const route of routes) {
      if (!route.path) continue;
      const routePath = route.path.startsWith("/") ? route.path : `/${route.path}`;
      // 精确匹配 / 前缀匹配 / 动态路由匹配
      if (
        routePath === targetPath ||
        this.isDynamicRouteMatch(targetPath, routePath) ||
        targetPath.startsWith(`${routePath}/`)
      )
        return true;
      if (route.children?.length && this.matchRoute(targetPath, route.children)) return true;
    }
    return false;
  }

  /** 动态路由匹配：/user/:id → /user/5 */
  static isDynamicRouteMatch(targetPath: string, routePath: string): boolean {
    if (!routePath.includes(":")) return false;
    const pattern = routePath
      .replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
      .replace(/:([^/]+)/g, "[^/]+")
      .replace(/\\\*/g, ".*");
    return new RegExp(`^${pattern}$`).test(targetPath);
  }

  /**
   * 路径校验入口
   * - 有权 → 返回原路径
   * - 无权 → 返回首页
   */
  static validatePath(
    targetPath: string,
    menuList: AppRouteRecord[],
    homePath: string = "/"
  ): { path: string; hasPermission: boolean } {
    const hasPermission = this.hasPermission(targetPath, menuList);
    return hasPermission
      ? { path: targetPath, hasPermission: true }
      : { path: homePath, hasPermission: false };
  }
}

// ──────── 后置守卫 ────────

/**
 * 后置守卫
 * - 同步标签栏（setWorktab）
 * - 更新浏览器标题（setPageTitle）
 * - 新标签页 → 滚动到顶部
 * - 关闭 NProgress 进度条
 * - 关闭全局 loading
 */
export function setupAfterEachGuard(router: Router): void {
  router.afterEach((to) => {
    setWorktab(to);
    setPageTitle(to);
    document.querySelector(".el-scrollbar__wrap")?.scrollTo(0, 0);
    window.scrollTo(0, 0);
    NProgress.done();
    if (globalLoading.value) globalLoading.value = false;
  });
}
