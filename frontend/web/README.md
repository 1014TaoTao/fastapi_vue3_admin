# FastAPI Admin · 前端工程（web）

基于 **Vue 3 + Vite + TypeScript + Element Plus** 的后台管理前端，与 FastAPI Admin 后端配套使用。状态管理为 **Pinia**，样式以 **Tailwind CSS 4** 与 **SCSS** 为主，接口请求使用 **Axios**。

> **与仓库根文档的关系**：项目总览、一键前后端启动、演示账号、Docker 部署等请以 [根目录 README.md](../../README.md) 为准；**本文档**侧重 `frontend/web/` 目录结构、环境变量与前端开发约定。

## 快速开始

### 环境准备

| 工具    | 版本要求                                               |
| ------- | ------------------------------------------------------ |
| Node.js | ≥ 20.19（见 `package.json` → `engines`）               |
| pnpm    | ≥ 8.8，推荐 **pnpm 9**（与 `packageManager` 字段一致） |

未安装 pnpm 时可执行：`corepack enable && corepack prepare pnpm@9.15.3 --activate`（版本可按项目 `packageManager` 调整）。

### 安装依赖并启动

```bash
cd frontend/web
pnpm install
pnpm dev
```

默认开发端口由 **`.env`** 中的 **`VITE_PORT`** 决定（当前模板为 **5173**）。

### 与后端联调

1. 先启动 **FastAPI Admin 后端**，监听地址与 **`.env.dev`** 里 **`VITE_API_BASE_URL`** 一致（模板默认为 **`http://127.0.0.1:8001`**）。
2. 前端开发时，浏览器请求发往当前页面同源路径，由 **Vite `server.proxy`** 把 **`VITE_APP_BASE_API`**（如 `/api/v1`）转发到上述后端。
3. 若页面提示「连接被拒绝」，检查后端是否启动、端口是否一致，或把 **`VITE_API_BASE_URL`** 改成你的实际后端地址。

## 架构概览

```
main.ts 启动
  └─ initPlugins(app)  ← 插件注册（Pinia → Router → 指令 → i18n → Element Plus）
      └─ mount("#app")
          └─ App.vue
              ├─ onBeforeMount: 主题初始化
              └─ onMounted: bootstrap() → 存储检查/版本升级/站点配置
                  └─ 路由守卫 beforeEach
                      ├─ 存储失效检测
                      ├─ 登录态校验
                      ├─ 动态路由注册（菜单 → addRoute）
                      └─ 标签/标题同步
```

路由采用 **Hash 模式**，静态路由（Layout/登录/404）首屏注册，业务路由由守卫根据菜单权限延迟 `addRoute`。HTTP 拦截器支持 **Token 静默续期**（401 时自动 refresh，失败后跳转登录）。

## 技术栈

| 类别   | 选型                                                   |
| ------ | ------------------------------------------------------ |
| 框架   | Vue 3（Composition API / `<script setup>`）            |
| 构建   | Vite 7                                                 |
| 语言   | TypeScript                                             |
| UI     | Element Plus                                           |
| 路由   | Vue Router 4（Hash；静态路由 + 守卫内动态 `addRoute`） |
| 状态   | Pinia + pinia-plugin-persistedstate                    |
| 样式   | Tailwind CSS 4、SCSS                                   |
| HTTP   | Axios                                                  |
| 国际化 | vue-i18n                                               |

## 常用脚本

| 命令                                          | 说明                                                          |
| --------------------------------------------- | ------------------------------------------------------------- |
| `pnpm dev`                                    | 本地开发（读取 `.env` + `.env.dev`）                          |
| `pnpm dev:force`                              | 强制预打包依赖后启动（缓存异常时）                            |
| `pnpm build`                                  | `vue-tsc` 类型检查 + 生产构建，产物在 **`dist/`**             |
| `pnpm build:dev` / `build:test` / `build:pro` | 按 mode 构建（需对应 env 文件）                               |
| `pnpm preview`                                | 本地预览构建结果                                              |
| `pnpm type-check`                             | 仅 TypeScript 检查                                            |
| `pnpm lint`                                   | ESLint + Prettier + Stylelint                                 |
| `pnpm clean:dev`                              | 执行 `scripts/clean-dev.ts`（清理演示等，使用前阅读脚本说明） |
| `pnpm clean:cache`                            | 清理 Vite 等缓存                                              |

## 目录结构（src）

```
src/
├── api/              # 按业务模块划分的接口封装
├── assets/           # 图片、字体、全局样式等
├── components/       # 通用与业务组件
├── config/           # 应用配置（fastEnter、headerBar 等）
├── enums/            # 枚举
├── hooks/            # 组合式函数
├── layouts/          # 布局壳（art-* 顶栏、侧栏、Tab、设置抽屉等）
├── locales/          # i18n（如 langs/zh.json）
├── plugins/          # Vue 插件注册（入口：plugins/index.ts → initPlugins）
├── router/           # staticRoutes、动态路由、守卫、MenuProcessor
├── store/            # Pinia 模块
├── types/            # TypeScript 类型
├── utils/            # 工具（含 `@utils`）
├── views/            # 页面（module_* / dashboard 等）
├── App.vue
└── main.ts           # 入口
```

## 路径别名

| 别名               | 指向         |
| ------------------ | ------------ |
| `@`                | `src/`       |
| `@views`           | `src/views`  |
| `@stores`          | `src/store`  |
| `@utils`           | `src/utils`  |
| `@styles`          | `src/styles` |
| `@imgs` / `@icons` | 图片与 SVG   |

与 **`vite.config.ts`**、`tsconfig.json` 中 `paths` 保持一致。

## 环境变量

只有以 **`VITE_`** 开头的变量会注入前端代码：

| 变量                   | 作用                                             |
| ---------------------- | ------------------------------------------------ |
| `VITE_PORT`            | 开发服务器端口                                   |
| `VITE_BASE_URL`        | 部署基础路径（子目录部署时形如 `/admin/`）       |
| `VITE_APP_BASE_API`    | 接口路径前缀，与 Vite 代理匹配                   |
| `VITE_API_URL`         | 浏览器侧发出的 API 根前缀（开发时常为 `/`）      |
| `VITE_API_BASE_URL`    | **代理目标**：后端 HTTP 根地址                   |
| `VITE_ACCESS_MODE`     | `frontend` / `backend` / `mixed`，菜单与路由来源 |
| `VITE_APP_WS_ENDPOINT` | WebSocket（如 AI 对话）                          |
| `VITE_APP_TITLE`       | 页面标题（可被后端参数配置覆盖）                 |

完整列表以仓库内 **`.env`**、**`.env.dev`** 为准；模板说明见 **`.env.example`**。修改任一 env 后需 **重启** `pnpm dev`。

## 路由与菜单

| 文件                          | 职责                                              |
| ----------------------------- | ------------------------------------------------- |
| `src/router/staticRoutes.ts`  | 静态路由、`dashboardLayoutChildren`、壳层菜单合并 |
| `src/router/dynamicRoutes.ts` | 菜单驱动的动态路由                                |
| `src/router/beforeEach.ts`    | 权限与动态挂载                                    |
| `src/router/MenuProcessor.ts` | 后端菜单 → 前端路由记录                           |

新增业务页：一般需要 **视图 +（可选）静态或动态路由 + 后端菜单/i18n**，三者路径与 **name** 保持一致。

## 常见问题

| 现象                      | 建议                                                                                    |
| ------------------------- | --------------------------------------------------------------------------------------- |
| `ECONNREFUSED` / 网络错误 | 后端未启动或 **`VITE_API_BASE_URL`** 端口错误                                           |
| 接口 401 / 频繁跳转登录   | Token 失效或未登录；清除站点本地存储后重新登录                                          |
| 修改 `.env` 不生效        | 必须 **重启** `pnpm dev`                                                                |
| 依赖异常、热更新怪异      | 尝试 **`pnpm clean:cache`** 后再 **`pnpm dev`**；仍不行可 **`pnpm dev:force`**          |
| 类型报错                  | 运行 **`pnpm type-check`**；自动生成类型见 `src/types/import/`（勿手改自动生成的 d.ts） |

## 构建与部署

- 输出目录：**`dist/`**
- 部署在子路径时配置 **`VITE_BASE_URL`**，并配置网关/Nginx 将前端资源与 `/api` 等转发到后端
- 生产构建可能移除部分 `console`（见 **`vite.config.ts`** 中 `terserOptions`）

## 代码规范与 Git

- **格式化与校验**：`pnpm lint`
- **提交**：husky、lint-staged、commitlint；可使用 **`pnpm commit`**（Commitizen / cz-git）

element-plus 组件库
基础组件：
el-button 按钮
el-container 容器
el-header 头部
el-aside 侧边栏
el-main 主体
el-footer 底部
el-icon 图标
el-row 行布局
el-col 列布局单元
el-link 链接
el-text 文本内容
el-scrollbar 滚动条
el-space 空格
el-splitter、el-splitter-panel 分割面板
Typography 排版
配置组件：
el-config-provider 全局配置
Form表单组件：
el-autocomplete 自动补全
el-cascader 级联选择器
el-checkbox 多选框
el-color-picker-panel 颜色选择器面板
el-color-picker 颜色选择器
el-date-picker-panel 日期选择器面板
el-radio-group、el-radio-button 日期选择器
el-date-picker 日期时间选择器
el-time-picker 时间选择器
el-time-select 时间选择
el-form、el-form-item 表单
el-input 输入框
el-input-number 数字输入框
el-input-tag 标签输入框
el-input-otp 一次性密码输入框
el-mention 提及
el-radio-group、el-radio 单选框
el-rate 评分
el-select、el-option 选择器
el-select-v2 虚拟化选择器
el-slider 滑块
el-switch 开关按钮
el-transfer 穿梭框
el-tree-select 树形选择
el-upload 上传器
Data数据展示组件：
el-avatar 头像
el-badge 徽章
el-calendar 日历
el-card 卡片
el-carousel 走马灯
el-collapse、el-collapse-item 折叠面板
el-descriptions、el-descriptions-item 描述列表.
el-empty 空状态
el-image 图片
Infinite Scroll 无限滚动：在要实现滚动加载的列表上添加v-infinite-scroll，并赋值相应的加载方法，可实现滚动到底部时自动执行加载方法。
el-pagination 分页
el-progress 进度条
el-result 结果
el-skeleton 骨架屏
el-table、el-table-col 表格
el-table-v2 虚拟化表格
el-tag 标签
el-timeline、el-timeline-item 时间线
el-tour、el-tour-step 漫游式引导
el-tree 树形控件
el-tree-v2 虚拟化树形控件
el-statistic 统计组件
el-segmented 分段控制器
导航类组件：
el-affix 固钉
el-anchor、el-anchor-link 锚点
el-backtop 回到顶部按钮
el-breadcrumb、el-breadcrumb-item 面包屑
el-dropdown、el-dropdown-menu、el-dropdown-item 下拉菜单
el-menu、el-sub-menu、el-menu-item-group、el-menu-item 菜单
el-page-header 页头
el-steps、el-step 步骤条
el-tabs、el-tab-pane 标签页
Feedback 反馈组件：
el-alert 提示
el-dialog 对话框
el-drawer 抽屉
loading：Element Plus 提供了两种调用 Loading 的方法：指令和服务。
对于自定义指令 v-loading，只需要绑定 boolean 值即可。
默认状况下，Loading 遮罩会插入到绑定元素的子节点。
通过添加 body 修饰符，可以使遮罩插入至 Dom 中的 body 上。
ElMessage 消息:与 Notification 的区别是后者更多用于系统级通知的被动提醒,默认情况下在顶部显示并在 3 秒后消失。
ElMessageBox 消息弹框：
ElMessageBox.confirm 方法以打开 confirm 框。它模拟了系统的 confirm 方法。
ElMessageBox.prompt 方法以打开 prompt 框。它模拟了系统的 prompt 方法。
ElNotification 通知
el-popconfirm 气泡确认框
el-popover 弹出框
el-tooltip 文字提示
Others 其他组件：
el-divider 分割线
el-watermark 水印
