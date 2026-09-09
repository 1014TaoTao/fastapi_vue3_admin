---
name: "fastapiadmin-dev"
description: "FastapiAdmin full-stack dev guide: repo map, run/verify commands, backend module & frontend web conventions. Invoke before writing code, creating modules/pages, debugging, or running builds/tests in this repo."
---

# FastapiAdmin 全栈开发指南

在本仓库做任何开发、调试、构建之前，先按本 skill 对齐工程结构与约定，避免跨端改漏、命名错位。

## 1. 工程地图

| 目录 | 说明 | 技术栈 |
| --- | --- | --- |
| `backend/` | 后端服务（入口 `main.py`，本地端口见 `app/config/setting.py` 的 SERVER_PORT，通常 8001） | FastAPI + SQLAlchemy + Alembic + Redis + uv |
| `frontend/web/` | 管理后台（pnpm 包，Node >= 20） | Vue3 + Vite + TS + Element Plus + Tailwind4 + Pinia |
| `frontend/app/` | 小程序/移动端 | uni-app（有独立约定，见 `frontend/app/.agents/skills/wot-ui-*`） |
| `frontend/docs/` | 项目文档站（中英双语 `src/guide` 与 `src/en/guide`） | VitePress |
| `docker/` | 部署（backend/mysql/nginx/redis） | docker-compose |
| 根目录 | `README.md`、`REQUIREMENTS.md`、`CONTRIBUTING.md` | 需求与规范，做大功能前先读 |

### backend/app 关键位置

| 位置 | 说明 |
| --- | --- |
| `modules/<模块>/<功能>/` | 业务模块：controller/service/crud/model/schema + 模块根 `plugin.toml` |
| `plugin/` | 独立插件目录（如 `plugin/module_example/demo`），与 modules 同构、可插拔 |
| `api/v1/routers.py` | 全部路由的注册处 |
| `core/` | 基建：database、base_crud、base_model、security、permission、dependencies、exceptions、ap_scheduler（定时任务）、sse_manager、middlewares |
| `scripts/initialize.py` | 启动时自动执行迁移并导入 `sql/*.json` 种子数据 |
| `sql/*.json` | 菜单/角色/用户/部门/字典/参数等种子数据 |
| `templates/{python,ts,vue}/` | 代码生成器 jinja2 模板 |
| `tests/` | pytest（conftest 自建临时库并初始化数据） |
| `utils/` | crypto/password/excel/upload/xss 等工具函数 |

### frontend/web/src 关键位置

| 位置 | 说明 |
| --- | --- |
| `api/module_x/` | API 层，与后端模块一一对应 |
| `views/module_x/` | 业务页面；页面私有组件放同目录 `components/` |
| `components/` | 公共组件 FaXxx（forms/tables/charts/modal/display 等）——写页面前先找现成的 |
| `hooks/core/` | 开发套件：useTable、useCrudForm、useCrudDialog、useTableColumns、useAuth、useImportExport、useConfirm |
| `directives/permission/` | `v-hasPerm` 按钮权限指令 |
| `router/` | `routes.ts` 静态壳 + guards/MenuProcessor/RouteRegistry 动态路由管道 |
| `store/modules/` | pinia stores（user/worktab/menu/setting/dict…），持久化用 pinia-plugin-persistedstate |
| `locales/langs/` | i18n 词条（zh.json / en.json） |
| `utils/` | http(request 封装)、auth、storage、navigation、download、sse 等 |

## 2. 常用命令

后端（`cd backend`，优先用 uv）：

```bash
uv run main.py run --env=dev          # 启动（dev 默认，DEBUG=True 时自动 reload）
uv run main.py revision -m "说明"      # 生成 Alembic 迁移（autogenerate）
uv run main.py upgrade --env=dev      # 应用迁移到 head
uv run pytest                         # 跑 tests/
```

前端 web（`cd frontend/web`）：

```bash
pnpm i            # 安装
pnpm dev          # 开发
pnpm ts:check     # vue-tsc 类型检查（改完 TS/Vue 必跑）
pnpm lint         # eslint + prettier + stylelint
pnpm test         # vitest
pnpm build        # 构建
```

`frontend/app`、`frontend/docs` 各自目录内 `pnpm` 管理自己。

### 首次启动（新人跑通）

1. 复制 `backend/env/.env.example` 为 `.env.dev`，按文件头注释修改必改项（`DATABASE_PASSWORD` / `REDIS_PASSWORD` / `OPENAI_API_KEY`）；`DATABASE_TYPE` 支持 mysql / postgres / sqlite——本地体验用 sqlite 可零配置起跑
2. `uv sync && uv run main.py run --env=dev`：**启动时自动执行迁移并导入 `sql/*.json` 种子数据**（菜单/角色/用户/字典等），无需手动建表导数；dev 环境检测到模型变更还会自动生成并应用迁移
3. 前端：`frontend/web` 内 `pnpm install && pnpm dev`（小程序/App H5 调试用 `pnpm dev:h5`）
4. 默认账号：`super` / `admin` / `user`，密码均为 `123456`（已校验种子 bcrypt 哈希；官方文档见 `frontend/docs/src/guide/start.md`，部署后应立即修改）
5. 访问地址：Web 前端 `http://localhost:{VITE_PORT}`（`frontend/web/.env` 为 5180）；后端 `http://localhost:8001`、Swagger `http://localhost:8001/docs`、API 前缀 `/api/v1`
- Docker 一键部署：根目录 `./deploy.sh`（详见 `docker/README.md`）

前端代理：vite 将 `VITE_APP_BASE_API` 前缀代理到 `VITE_API_BASE_URL`（见 `vite.config.ts`），本地开发无 CORS 问题；AI WebSocket 用 `VITE_APP_WS_ENDPOINT` 直连后端（不走代理）。

## 3. 后端约定（backend/app）

- 模块结构：`app/modules/<模块>/<功能>/`，固定文件划分
  - `controller.py` 路由层、`service.py` 业务层、`crud.py` 数据层、`model.py` ORM、`schema.py` Pydantic
  - 模块根放 `plugin.toml`（name/title/version/description）
- 路由统一在 `app/api/v1/routers.py` 注册；路由类用 `OperationLogRoute`（自动操作日志）
- 权限：`Security(AuthPermission(["模块:资源:操作"]))`，如 `module_ai:chat:query`
- 响应：`SuccessResponse(data=..., msg=...)` + `response_model=ResponseSchema[T]`；业务错误抛 `CustomException`
- 基建都在 `app/core/`：`base_crud.py`、`base_model.py`、`base_schema.py`、`redis_crud.py`、`dependencies.py`、`exceptions.py`、`logger.py`（loguru，占位符用 `{}`)
- 配置：`app/config/setting.py` + `backend/env/.env`（模板见 `env/.env.example`）
- 改了 model 必须生成并执行 Alembic 迁移；初始菜单/角色等数据在 `backend/sql/*.json`
- 新模块两种放法：常规业务放 `app/modules/`，可插拔/示例性质放 `app/plugin/`（结构相同，都有 `plugin.toml`）
- 代码生成：`backend/templates/{python,ts,vue}/*.jinja2` 配合 generator 模块（后台「代码生成」功能可视化生成）

## 4. 前端 web 约定（frontend/web/src）

- API 层：`api/module_x/xxx.ts`，对象字面量方法 + `request`（来自 `@utils`），泛型用全局 `ApiResponse<T>` / `PageResult<T>`；URL 与后端 controller 对齐（如 `/system/dict/type/list`）
- 页面：`views/module_x/...`；页面私有子组件放同目录 `components/` 下，公共组件命名 `FaXxx`
- CRUD 页面优先复用现成套件：列表用 `useTable` + `FaTable` + `FaSearchBar`，弹窗表单用 `useCrudDialog`/`useCrudForm` + `FaDialog`，列定义用 `useTableColumns`，导入导出用 `useImportExport`——参考已有 `views/module_system/` 页面写法，不要手写 ElTable/ElDialog
- 权限控制：按钮级用 `v-hasPerm="'sys:user:add'"`（支持数组）；代码内判断用 `useAuth().hasAuth(...)`；后端标识 `模块:资源:操作` 三段式，前后端保持一致
- i18n：文案用 `$t('key')`，词条加到 `locales/langs/zh.json` 与 `en.json` 两份
- 自动导入：vue API（`ref`/`computed`/`watch`/`onMounted` 等）无需 import；Element Plus 组件模板内直接用；`ElMessage` 等按现有文件习惯可显式 import
- 路由：静态壳路由在 `router/routes.ts`；业务路由来自后端菜单（`guards.ts` → `MenuProcessor` → `RouteRegistry` 动态 addRoute）。新增页面要在「菜单管理」配置 route_path/route_name/component_path/keep_alive
- KeepAlive 与工作栏按「组件名」匹配：`defineOptions({ name })` 必须与菜单的 route_name 一致，否则页面缓存/缓存排除（exclude）会失灵
- 有副作用页面（WebSocket/定时器/全局事件监听）必须实现 `onActivated`/`onDeactivated`：deactivated 时释放资源，activated 时按需恢复。`onUnmounted` 只在缓存被驱逐时触发，不能作为唯一清理点（详见第 7 节）
- 缓存键默认 `name + params`；依赖 query 的页面用菜单 meta `remountOnFullPath`（见 `layouts/fa-page-content/index.vue` 的 `routeLeafCacheKey`）
- 环境变量：公共 `.env`（`VITE_APP_BASE_API=/api/v1` 请求前缀、`VITE_PORT=5180`）；`.env.development`（`VITE_API_BASE_URL=http://127.0.0.1:8001` 代理目标；AI WebSocket `VITE_APP_WS_ENDPOINT=ws://localhost:8001` 直连）
- WebSocket 鉴权（AI chat）：token 经 `Sec-WebSocket-Protocol` 传 `["access_token", "access_token." + jwt]`，后端在握手阶段 `websocket_authenticate` 校验
- 图标：`FaSvgIcon` + iconify（`ri:` / `ep:` / `line-md:`）；i18n 用 `$t(...)`

## 5. 新增一个业务功能（全栈流程）

1. 后端建模块（参考 `app/modules/system/dict/`；标准 CRUD 表可先用后台「代码生成」可视化产出，再调整）
2. `app/api/v1/routers.py` 注册路由
3. `uv run main.py revision` + `upgrade` 做迁移；菜单/按钮权限写入 sys_menu（后台「菜单管理」配置 route_path/route_name/component_path/keep_alive/按钮权限）
4. 前端新建 `api/module_x/xxx.ts` 与 `views/module_x/` 页面（复用 useTable/FaTable 套件）
5. 前后端权限标识保持一致（`模块:资源:操作`），页面按钮加 `v-hasPerm`
6. 验证：后端 `uv run pytest`；前端 `pnpm ts:check`、`pnpm lint`、`pnpm test`

## 6. 提交规范

- husky + commitlint + git-cz（`pnpm commit` 交互式生成）；type 用 feat/fix/refactor/chore/docs/test 等
- lint-staged 会自动格式化暂存文件，不要绕过 hook

## 7. KeepAlive 缓存与连接类资源（踩过坑，勿回退）

- KeepAlive 的 `include` 来自 worktab `opened`（`layouts/fa-page-content/index.vue`），`opened` 为空时 include 为 `undefined`——KeepAlive 对 undefined include **不做 prune**，不要以为「标签清了缓存就没了」
- KeepAlive 内部缓存无法从外部直接清空，唯一手段是改变 `include`/`exclude` 触发内部 prune。登出场景由 `worktab.store.ts` 的 `clearAll()` 把待删标签组件名写入 `keepAliveExclude` 驱逐旧实例（下次 `openTab` 的 `removeKeepAliveExclude` 自动移出），改 store 时勿删这段
- WebSocket 守卫必须覆盖握手期：`if (ws && ws.readyState !== WebSocket.CLOSED) return`。只挡 `OPEN` 会在 CONNECTING 期间重入时创建新连接并覆盖旧引用，泄漏的连接照样握手成功并弹提示（AI chat 曾因此登出→登录后出现多条 ws + 多条「连接成功」）
- 主动断开先摘 `onopen/onmessage/onerror/onclose` 回调再 `close()`，避免关闭竞态触发提示或状态回调
- 排查「重复弹窗/重复连接/重复请求」类 bug 的路径：先 grep 提示文案定位全库唯一来源（N 次弹窗 = N 个实例或 N 次重入）→ 查 KeepAlive include/exclude 计算与登出→登录导航链（登录守卫 404→replace 重定向会叠加竞态窗口）→ 菜单配置查 `backend/sql/sys_menu.json`（确认 route_name 唯一、keep_alive）排除后端

## 8. 已知注意点

- 跨端需求（web + 小程序）要同时评估 `frontend/web` 与 `frontend/app` 两套代码，API 层各自维护
- 小程序侧有自己的 skills（`frontend/app/.agents/skills/`），改小程序 UI 时遵循 wot-ui 约定
- 文档站改动记得中英两份（`src/guide/` 与 `src/en/guide/`）
