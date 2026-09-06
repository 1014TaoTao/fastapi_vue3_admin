/** User store. */
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { LanguageEnum } from "@/enums/appEnum";
import { router } from "@/router";
import { useWorktabStore } from "./worktab.store";
import { useMenuStore } from "./menu.store";
import { useConfigStore } from "./config.store";
import { Auth, setPageTitle, StorageConfig } from "@utils";
import AuthAPI, { type LoginFormData } from "@/api/module_system/auth";
import UserAPI from "@/api/module_system/user";
import type { MenuTable } from "@/api/module_system/menu";
import type { AppRouteRecord } from "@/types/router";
import { ElNotification } from "element-plus";
import { store, useDictStore } from "@stores";
import type { UserInfo } from "@/api/module_system/user";
import { ResultEnum } from "@/enums/api/result.enum";
import { resetRouteInitState, resetRouterState } from "@/router/refresh";

/** {@link useUserStore} 的 `logout` 可选参数 */
export interface LogoutOptions {
  /**
   * 为 false 时仅清理状态，不跳转登录（由调用方自行 next/router，如锁屏页 replace）
   * @default true
   */
  navigate?: boolean;
}

/**
 * 用户状态管理
 * 管理用户登录状态、个人信息、语言设置、搜索历史、锁屏状态等
 */
export const useUserStore = defineStore(
  "userStore",
  () => {
    // 语言设置
    const language = ref(LanguageEnum.ZH);
    // 登录状态
    const isLogin = ref(false);
    // 锁屏状态
    const isLock = ref(false);
    // 锁屏密码
    const lockPassword = ref("");
    // 用户信息
    const info = ref<Partial<UserInfo>>({});
    // 搜索历史记录
    const searchHistory = ref<AppRouteRecord[]>([]);
    // 访问令牌
    const accessToken = ref("");
    // 刷新令牌
    const refreshToken = ref("");
    // 路由列表
    const routeList = ref<MenuTable[]>([]);
    // 权限列表
    const prems = ref<string[]>([]);
    // 是否已获取路由
    const hasGetRoute = ref(false);
    // 记住我状态
    const rememberMe = ref(Auth.getRememberMe());
    /** info 扩展类型：兼容 API 返回 `user_id`（非标准 UserInfo 字段） */
    type UserInfoLike = Partial<UserInfo> & { user_id?: number; [key: string]: unknown };

    // 计算属性：基础用户信息
    const basicInfo = computed(() => info.value as UserInfoLike);
    /**
     * 设置用户信息
     * @param newInfo 新的用户信息
     */
    const setUserInfo = (newInfo: UserInfo) => {
      info.value = newInfo;
      // 设置用户信息后自动更新权限
      setPermissions([]);
    };

    /**
     * 设置登录状态
     * @param status 登录状态
     */
    const setLoginStatus = (status: boolean) => {
      isLogin.value = status;
    };

    /**
     * 设置语言
     * @param lang 语言枚举值
     */
    const setLanguage = (lang: LanguageEnum) => {
      setPageTitle(router.currentRoute.value);
      language.value = lang;
    };

    /**
     * 设置搜索历史
     * @param list 搜索历史列表
     */
    const setSearchHistory = (list: AppRouteRecord[]) => {
      searchHistory.value = list;
    };

    /**
     * 设置锁屏状态
     * @param status 锁屏状态
     */
    const setLockStatus = (status: boolean) => {
      isLock.value = status;
    };

    /**
     * 设置锁屏密码
     * @param password 锁屏密码
     */
    const setLockPassword = (password: string) => {
      lockPassword.value = password;
    };

    /**
     * 设置令牌
     * @param newAccessToken 访问令牌
     * @param newRefreshToken 刷新令牌（可选）
     */
    const setToken = (newAccessToken: string, newRefreshToken?: string) => {
      accessToken.value = newAccessToken;
      if (newRefreshToken) {
        refreshToken.value = newRefreshToken;
      }
    };

    /**
     * 检查并清理工作台标签页
     * 如果不是同一用户登录，清空工作台标签页
     * 应在登录成功后调用
     */
    const checkAndClearWorktabs = () => {
      const lastUserId = localStorage.getItem(StorageConfig.LAST_USER_ID_KEY);
      const ui = info.value as UserInfoLike;
      const currentUserId = ui.id || ui.user_id;

      // 无法获取当前用户 ID，跳过检查
      if (!currentUserId) return;

      // 首次登录或缓存已清除，保留现有标签页
      if (!lastUserId) {
        return;
      }

      // 不同用户登录：清空工作台标签（含 current，避免与路由脱节；并与持久化一致）
      if (String(currentUserId) !== String(lastUserId)) {
        useWorktabStore().clearAll();
      }

      // 清除临时存储
      localStorage.removeItem(StorageConfig.LAST_USER_ID_KEY);
    };

    /**
     * 获取用户信息
     */
    async function getUserInfo() {
      try {
        const response = await UserAPI.getCurrentUserInfo();
        const data = response.data.data;
        const menus: MenuTable[] = data?.menus || [];
        delete data?.menus;
        info.value = { ...info.value, ...data } as Partial<UserInfo>;
        setRoute(menus);
      } catch (error) {
        console.error("获取用户信息失败:", error);
        throw error;
      }
    }

    /**
     * 仅刷新权限/菜单（轻量模式，不加载用户嵌套数据）
     * 在菜单/角色 CRUD 操作后调用，替代 getUserInfo
     */
    async function refreshPermissions() {
      try {
        const response = await UserAPI.getCurrentUserInfo(false);
        const data = response.data.data;
        const menus: MenuTable[] = data?.menus || [];
        setRoute(menus);
      } catch (error) {
        console.error("刷新权限失败:", error);
      }
    }

    /**
     * 设置头像
     */
    function setAvatar(avatar: string) {
      info.value = { ...info.value, avatar };
    }

    /**
     * 设置路由
     */
    function setRoute(routers: MenuTable[]) {
      routeList.value = routers;
      hasGetRoute.value = true;
      setPermissions(routers);
    }

    /**
     * 设置权限
     */
    function setPermissions(menus: MenuTable[]) {
      prems.value = [];
      if (!info.value.roles) return;

      const roleMenus = info.value.roles
        .filter((role) => role.menus && role.menus.length > 0)
        .flatMap((role) => role.menus)
        .filter((menu): menu is MenuTable => menu !== undefined);

      const allMenus = [...menus, ...roleMenus];

      const permissionSet = new Set<string>();
      const collect = (items: MenuTable[]) => {
        items.forEach((item) => {
          if (item.permission) {
            permissionSet.add(item.permission);
          }
          if (item.children && item.children.length > 0) {
            collect(item.children.filter((child): child is MenuTable => child !== undefined));
          }
        });
      };

      collect(allMenus);
      prems.value = Array.from(permissionSet);
    }

    /**
     * 登录
     */
    async function login(loginForm: LoginFormData) {
      const response = await AuthAPI.login(loginForm);
      const data = response.data.data;
      if (response.data.code === ResultEnum.SUCCESS) {
        ElNotification({
          title: "通知",
          message: response.data.msg,
          type: "success",
        });
      }
      rememberMe.value = loginForm.remember ?? false;

      const accessToken = data?.access_token || "";
      const refreshToken = data?.refresh_token || "";
      if (!accessToken) {
        console.error("[Login Debug] ⚠️ 未获取到 access_token！字段名可能与后端不匹配");
      }

      // 清除上次会话里「动态路由初始化失败」标记，避免重新登录后侧栏/菜单不注册
      resetRouteInitState();
      Auth.setTokens(accessToken, refreshToken, rememberMe.value);
      setToken(accessToken, refreshToken);

      await getUserInfo();
      await useConfigStore().getConfig(true);
      setLoginStatus(true);
    }

    /**
     * 登出：有 token 时请求后端；统一清理状态；默认跳转登录页并带 redirect
     */
    async function logout(options?: LogoutOptions) {
      const shouldNavigate = options?.navigate !== false;

      const ui = info.value as UserInfoLike;
      const currentUserId = ui.id || ui.user_id;
      if (currentUserId) {
        localStorage.setItem(StorageConfig.LAST_USER_ID_KEY, String(currentUserId));
      }

      let apiError: unknown;
      const token = Auth.getAccessToken();
      if (token) {
        try {
          const response = await AuthAPI.logout(token);
          if (response.data.code === ResultEnum.SUCCESS) {
            ElNotification({
              title: "通知",
              message: response.data.msg,
              type: "success",
            });
          }
        } catch (e) {
          apiError = e;
        }
      }

      resetAllState();
      sessionStorage.removeItem("iframeRoutes");
      useMenuStore().setHomePath("");
      resetRouterState(500);

      if (shouldNavigate) {
        const currentRoute = router.currentRoute.value;
        const redirect = currentRoute.path !== "/login" ? currentRoute.fullPath : undefined;
        await router.push({
          name: "Login",
          query: redirect ? { redirect } : undefined,
        });
      }

      if (apiError) {
        throw apiError;
      }
    }

    /**
     * 重置所有状态
     */
    function resetAllState() {
      Auth.clearAuth();
      info.value = {};
      routeList.value = [];
      hasGetRoute.value = false;
      isLogin.value = false;
      isLock.value = false;
      lockPassword.value = "";
      accessToken.value = "";
      refreshToken.value = "";
      prems.value = [];
      /** 登出 / 认证失效：会话结束，工作栏与 KeepAlive exclude 一并清空（pinia 持久化随之写入） */
      useWorktabStore().clearAll();
    }

    /**
     * 清空用户信息
     */
    function clearUserInfo() {
      info.value = {};
      routeList.value = [];
      hasGetRoute.value = false;
    }

    /**
     * 刷新token
     */
    async function refreshTokenFn() {
      const currentRefreshToken = Auth.getRefreshToken();

      if (!currentRefreshToken) {
        throw new Error("没有有效的刷新令牌");
      }

      const response = await AuthAPI.refreshToken(currentRefreshToken);
      const data = response.data.data;
      // 更新令牌，保持当前记住我状态
      Auth.setTokens(data.access_token, data.refresh_token, Auth.getRememberMe());
      setToken(data.access_token, data.refresh_token);
    }

    /**
     * 完全重置所有状态（包括路由、标签页、字典等）
     */
    function fullResetAllState() {
      // 重置用户状态
      Auth.clearAuth();
      // 重置用户信息
      clearUserInfo();
      useWorktabStore().clearAll();
      // 重置字典
      useDictStore(store).clearDictData();

      return Promise.resolve();
    }

    return {
      language,
      isLogin,
      isLock,
      lockPassword,
      info,
      searchHistory,
      accessToken,
      routeList,
      prems,
      hasGetRoute,
      rememberMe,
      getUserInfo,
      refreshPermissions,
      basicInfo,
      setUserInfo,
      setLoginStatus,
      setLanguage,
      setSearchHistory,
      setLockStatus,
      setLockPassword,
      setToken,
      setAvatar,
      setRoute,
      setPermissions,
      login,
      logout,
      checkAndClearWorktabs,
      clearUserInfo,
      refreshTokenFn,
      resetAllState,
      fullResetAllState,
    };
  },
  {
    persist: {
      key: "user",
      storage: localStorage,
      pick: ["language", "isLogin", "searchHistory", "rememberMe"],
    },
  }
);

export function useUserStoreHook() {
  return useUserStore(store);
}
