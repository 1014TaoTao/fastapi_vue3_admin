import type { App } from "vue";
import { createRouter, createWebHashHistory, type RouteRecordRaw } from "vue-router";
export const Layout = () => import("@/layouts/index.vue");
/**
 * 静态路由
 */
export const constantRoutes: RouteRecordRaw[] = [
  {
    path: "/redirect",
    meta: { hidden: true },
    component: Layout,
    children: [
      {
        path: "/redirect/:path(.*)",
        component: () => import("@/views/redirect/index.vue"),
      },
    ],
  },
  {
    path: "/login",
    name: "Login",
    meta: { hidden: true },
    component: () => import("@/views/system/auth/index.vue"),
  },
  {
    path: "/401",
    name: "401",
    meta: { hidden: true, title: "401" },
    component: () => import("@/views/error/401.vue"),
  },
  {
    path: "/404",
    name: "404",
    meta: { hidden: true, title: "404" },
    component: () => import("@/views/error/404.vue"),
  },
  {
    path: "/500",
    name: "500",
    meta: { hidden: true, title: "500" },
    component: () => import("@/views/error/500.vue"),
  },
  {
    path: "/:pathMatch(.*)*",
    component: () => import('@/views/error/404.vue'),
    meta: { hidden: true, title: "404" },
  },
  // 以下内容必须放在后面
  {
    path: "/",
    name: "/Index",
    redirect: "/dashboard/workplace",
    component: Layout,
    children: [
      {
        path: "profile",
        name: "Profile",
        meta: { title: "个人中心", icon: "user", hidden: true },
        component: () => import("@/views/current/profile.vue"),
      },
      // 应用内部打开页面
      {
        path: "internal-app/:appId",
        name: "InternalApp",
        meta: { title: "内部应用", icon: "Monitor", hidden: true, keepAlive: false },
        component: () => import("@/views/application/myapp/components/InternalApp.vue"),
      },
      // // 临时构建后面要删除掉
      // {
      //   path: "form-builder",
      //   name: "FormBuilder",
      //   meta: { title: "表单构建", icon: "document" },
      //   component: () => import("@/views/codegen/build/index.vue"),
      // }
    ],
  },
];

/**
 * 创建路由
 */
const router = createRouter({
  history: createWebHashHistory(),
  routes: constantRoutes,
  // 刷新时，滚动条位置还原
  scrollBehavior: () => ({ left: 0, top: 0 }),
});

// 全局注册 router
// 为了捕获并处理全局错误，在注册路由时添加错误处理
export function setupRouter(app: App<Element>) {
  app.config.errorHandler = (err, instance, info) => {
    console.error('全局错误捕获:', err, '实例:', instance, '信息:', info);
  };
  app.use(router);
}

export default router;
