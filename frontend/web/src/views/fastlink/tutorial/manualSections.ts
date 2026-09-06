/**
 * 功能验收手册：除「用户 / 角色」在 `index.vue` 中详述外，其余页用「完整性验收」结构展示。
 *
 * **何为完整性**：`notes` 与当前页**已实现**的界面与操作项对应，用于验收时逐条核对**是否漏项**（不评价交互好坏）。
 * **与后端菜单对齐**：标题与 `platform_menu` 初始化数据中菜单页 `component_path` 一致；壳层/静态页见各条说明。
 * **`path` 字段**：默认可视为 `src/views/` 下相对路径；`../layouts` 与 `locales` 等见各条。
 */
export type CompactManualPage = {
  anchor: string;
  title: string;
  path: string;
  notes: string[];
};

export type ManualModuleSection = {
  anchor: string;
  heading: string;
  pkgTag?: string;
  pages: CompactManualPage[];
};

/** 系统管理模块内、接在「角色管理」后的页面 */
export const MANUAL_SYSTEM_TAIL_PAGES: CompactManualPage[] = [
  {
    anchor: "page-menu",
    title: "菜单管理",
    path: "module_system/menu/index.vue",
    notes: [
      "检索：FaSearchBar（菜单名称等）。",
      "分区：Tab「PC 桌面菜单管理 / APP 移动端菜单管理」两套树数据。",
      "主区：树形表格（勾选、行点击）；展开/收起工具按钮。",
      "工具栏：新增、批量删除、批量更多(patch)、刷新、列配置、显示搜索栏。",
      "弹层：详情 Descriptions；新增/编辑 Drawer（目录 / 菜单 / 按钮 / 外链等类型与路由、图标、权限标识）。",
      "权限：`module_system:menu:create|delete|patch` + 行级 detail/update/delete。",
    ],
  },
  {
    anchor: "page-dept",
    title: "部门管理",
    path: "module_system/dept/index.vue",
    notes: [
      "检索：FaSearchBar。",
      "主区：树形表格（勾选）；展开/收起。",
      "工具栏：新增、批量删除、批量更多(patch)、刷新、列配置、搜索栏切换。",
      "弹层：详情；新增/编辑 Dialog（名称、编码、上级、状态等）。",
      "权限：`module_system:dept:create|delete|patch` + 行 detail/update/delete。",
    ],
  },
  {
    anchor: "page-position",
    title: "岗位管理",
    path: "module_system/position/index.vue",
    notes: [
      "检索：FaSearchBar（含创建人 FaUserTableSelect 槽）。",
      "主区：分页表格。",
      "工具栏：新增、导出、批量删除、批量更多(patch)、刷新、列配置。",
      "弹层：详情；新增/编辑 Dialog；导出 FaExportDialog。",
      "权限：`module_system:position:create|export|delete|patch` + 行 detail/update/delete。",
    ],
  },
  {
    anchor: "page-dict",
    title: "字典管理",
    path: "module_system/dict/index.vue",
    notes: [
      "检索：字典类型 FaSearchBar + 分页表。",
      "工具栏：新增类型、导出类型、批量删除、批量更多(patch)、刷新、列配置。",
      "类型弹层：详情 / 新增编辑 Dialog。",
      "子层：`DictDataPanel` 维护某字典类型下的字典数据项（二级）。",
      "权限：`module_system:dict_type:*` 与字典数据接口权限（见行内按钮）。",
    ],
  },
  {
    anchor: "page-param",
    title: "参数配置",
    path: "module_system/param/index.vue",
    notes: [
      "检索：FaSearchBar + 分页表。",
      "工具栏：新增、导出、批量删除、刷新、列配置（无 patch 批量入口）。",
      "弹层：详情；新增/编辑 Dialog；内置参数标识与表单校验。",
      "权限：`module_system:param:create|export|delete` + 行级权限。",
    ],
  },
  {
    anchor: "page-notice",
    title: "通知公告",
    path: "module_system/notice/index.vue",
    notes: [
      "检索：FaSearchBar（含创建人 FaUserTableSelect）。",
      "工具栏：新增、导出、批量删除、批量更多(patch)、刷新、列配置。",
      "弹层：详情；新增/编辑 Dialog；正文为富文本 `FaWangEditor`；HTML 预览。",
      "权限：`module_system:notice:create|export|delete|patch` + 行级操作。",
    ],
  },
  {
    anchor: "page-log",
    title: "操作日志",
    path: "module_system/log/index.vue",
    notes: [
      "检索：FaSearchBar（含创建人 FaUserTableSelect）；登录/操作日志类型在列或详情中区分。",
      "工具栏：导出、批量删除、刷新、列配置（无新增）。",
      "弹层：详情 Dialog（请求路径/方法、IP、状态码、耗时、入参出参等大字段）。",
      "权限：`module_system:log:export|delete` + 行级查看/删除。",
    ],
  },
  {
    anchor: "page-login",
    title: "登录页",
    path: "module_system/auth/login/index.vue",
    notes: [
      "面板切换：登录 / 注册 / 忘记密码（`setAuthPanel`）。",
      "登录：账号表单；验证码；记住我；登录成功后 `redirect` 解析跳转。",
      "静态路由：`/login`；与路由守卫白名单一致。",
      "其他：注册与忘记密码提交接口；左侧背景与主题组件（视模板）。",
    ],
  },
];

export const MANUAL_MODULES_AFTER_SYSTEM: ManualModuleSection[] = [
  {
    anchor: "mod-monitor",
    heading: "二、监控管理",
    pkgTag: "module_monitor",
    pages: [
      {
        anchor: "page-online",
        title: "在线用户",
        path: "module_monitor/online/index.vue",
        notes: [
          "检索：FaSearchBar（IP、用户名、登录地点等）。",
          "工具栏：「强退所有」（权限 `module_monitor:online:delete`）；刷新、列配置、搜索栏。",
          "行操作：单条会话「强退」。",
          "主区：分页表格（session_id 等列）；无批量勾选删除入口（仅有单条强退）。",
        ],
      },
      {
        anchor: "page-cache",
        title: "缓存管理",
        path: "module_monitor/cache/index.vue",
        notes: [
          "Tab「监控信息」：Redis 监控指标 Descriptions（版本、内存、CPU、Key 数量等）。",
          "Tab「缓存管理」：缓存列表/键值查看与按规则清理（与后端接口一致）。",
          "完整性：两 Tab 均需点开核对是否加载成功、清理是否有二次确认。",
        ],
      },
      {
        anchor: "page-server",
        title: "服务监控",
        path: "module_monitor/server/index.vue",
        notes: [
          "布局：多卡片 Dashboard（CPU、内存、磁盘、JVM/服务器信息等，依接口返回）。",
          "完整性：各卡片指标是否有数值；加载失败时占位或提示。",
        ],
      },
    ],
  },
  {
    anchor: "mod-task",
    heading: "三、任务管理",
    pkgTag: "module_task",
    pages: [
      {
        anchor: "page-cronjob",
        title: "调度器监控",
        path: "module_task/cronjob/job/index.vue",
        notes: [
          "顶部状态区：调度器运行状态、任务数量；按钮：启动/暂停/恢复/关闭/清空任务/控制台/同步/刷新（各 `module_task:cronjob:job:*`）。",
          "主区：任务卡片列表 — `getSchedulerJobs` 全量返回，名称与任务状态为前端筛选；单卡触发类型（Cron/间隔等）与暂停、恢复、调试、移除等行操作。",
          "抽屉：当前任务的执行日志 — `useTable` + `getJobLogList` 分页，日志检索栏，批量删日志等（见页面）。",
        ],
      },
      {
        anchor: "page-cronnode",
        title: "节点管理",
        path: "module_task/cronjob/node/index.vue",
        notes: [
          "检索：FaSearchBar + 分页表。",
          "工具栏：新增、批量删除、刷新、列配置。",
          "弹层：FaDialog + 分栏（表单 + 扩展配置区）；编辑节点连接与执行参数。",
          "权限：`module_task:cronjob:node:create|delete` + 行级 update/detail/delete。",
        ],
      },
      {
        anchor: "page-workflow",
        title: "流程管理",
        path: "module_task/storage/workflow/index.vue",
        notes: [
          "检索：FaSearchBar（可展开）。",
          "工具栏：新增、批量删除、刷新、列配置。",
          "流程定义：源节点 + 目标节点列表（parallel 多目标 / chain 链式），目标路径随行配置。",
          "权限：`module_task:storage:flow:create|delete|update` + 行级操作。",
        ],
      },
      {
        anchor: "page-workflow-node",
        title: "节点管理",
        path: "module_task/storage/node/index.vue",
        notes: [
          "检索：FaSearchBar（可展开）。",
          "节点即传输地址（存储源）：FTP/FTPS/SFTP/S3/OBS/OSS/COS/本地目录。",
          "行操作：打开（进入存储管理）、测试连接、详情、编辑、删除。",
          "权限：`module_task:storage:node:create|delete|update` + 行级操作。",
        ],
      },
      {
        anchor: "page-workflow-storage",
        title: "文件浏览",
        path: "module_task/storage/browse/index.vue",
        notes: [
          "多节点标签浏览各节点内部文件（类似 IDE 标签栏）。",
          "文件操作：上传、新建目录、下载、复制/移动、重命名、分享、删除。",
          "可从「节点管理」点击「打开」直接跳入对应节点。",
        ],
      },
      {
        anchor: "page-workflow-transfer",
        title: "传输任务",
        path: "module_task/storage/transfer/index.vue",
        notes: [
          "创建传输任务：可选「从流程自动填充」源节点与多目标，或手动指定。",
          "实时进度：WebSocket 推送任务/步骤状态与速度。",
          "详情：按步骤展示源 → 目标传输链路与错误信息。",
        ],
      },
    ],
  },
  {
    anchor: "mod-ai",
    heading: "四、AI 模块",
    pkgTag: "module_ai",
    pages: [
      {
        anchor: "page-ai-chat",
        title: "AI智能助手",
        path: "module_ai/chat/index.vue",
        notes: [
          "布局：左侧 `Sidebar`（会话列表、新建会话）；右侧 `ChatNavbar` + `ChatMessages` + `ChatInput`。",
          "连接：`toggleConnection`、连接状态展示；清空对话、侧栏折叠。",
          "完整性：发消息、收消息列表滚动、错误条展示与关闭；流式与否依赖后端/WebSocket 对接。",
        ],
      },
      {
        anchor: "page-ai-fachat",
        title: "会话聊天",
        path: "module_ai/fachat/index.vue",
        notes: [
          "布局：左侧联系人列表（搜索、排序下拉、在线点）；右侧头部「Art Bot」状态与语音/视频等图标按钮；中部消息气泡列表；底部输入框与发送。",
          "完整性：选人切换会话、发送消息、滚动消息区；当前多为演示数据与本地发送逻辑。",
        ],
      },
      {
        anchor: "page-ai-memory",
        title: "会话记忆",
        path: "module_ai/memory/index.vue",
        notes: [
          "检索：FaSearchBar + 分页表。",
          "工具栏：新增、批量删除、刷新、列配置；权限锚点 `module_ai:chat:create|delete`（与后端标识一致）。",
          "弹层：详情与表单 Drawer（会话记忆字段）；完整性：CRUD 与分页均需验证。",
        ],
      },
    ],
  },
  {
    anchor: "mod-generator",
    heading: "五、代码生成器",
    pkgTag: "module_generator",
    pages: [
      {
        anchor: "page-gencode",
        title: "代码生成",
        path: "module_generator/gencode/index.vue",
        notes: [
          "检索：FaSearchBar + 库表分页列表；勾选表格行。",
          "工具栏：创建表、导入库表、批量删除、批量生成（`module_generator:gencode:*`）。",
          "弹层：`CreateTableDialog`、导入 DB、`GenCodeDrawer` 多步（导入字段、生成配置、预览代码）。",
          "完整性：预览、下载 zip、生成到磁盘等按钮是否随权限显示且可点。",
        ],
      },
    ],
  },
  {
    anchor: "mod-app",
    heading: "六、应用管理",
    pkgTag: "module_application",
    pages: [
      {
        anchor: "page-portal",
        title: "插件市场",
        path: "module_application/portal/index.vue",
        notes: [
          "检索：FaSearchBar（含创建人、更新人 FaUserTableSelect）。",
          "工具栏：标题「应用市场」+「创建应用」（`module_application:portal:create`）；刷新、搜索栏。",
          "主区：卡片网格（图标、名称、状态、描述）；卡片脚编辑/删除（update/delete）；底部分页器。",
          "完整性：空列表 ElEmpty；卡片点击进入内部打开逻辑（见 `openAppInternal`）。",
        ],
      },
    ],
  },
  {
    anchor: "mod-example",
    heading: "七、示例模块",
    pkgTag: "module_example",
    pages: [
      {
        anchor: "page-demo",
        title: "示例管理",
        path: "module_example/demo/index.vue",
        notes: [
          "标准列表 CRUD 示例页：检索、分页表、工具栏、行操作、弹窗表单（与本项目其它模块同一套 Art 组件）。",
          "完整性：按页面可见按钮与表单字段逐项点验即可。",
        ],
      },
    ],
  },
  {
    anchor: "mod-dashboard",
    heading: "八、仪表盘",
    pkgTag: "dashboard",
    pages: [
      {
        anchor: "page-home",
        title: "首页",
        path: "dashboard/index.vue",
        notes: [
          "路由 `/home`：样式类 `workplace-page` — 问候与用户信息卡片、模块入口网格（按权限灰显）、其它工作台分区（与文件内组件一致）。",
          "完整性：模块卡片点击跳转、无权限入口禁用或提示；接口失败时有容错。",
        ],
      },
      {
        anchor: "page-profile",
        title: "个人中心",
        path: "current/profile.vue",
        notes: [
          "路由 `/profile`；左侧头像上传（ElUpload）、资料展示；右侧「基本设置」表单与「更改密码」三块。",
          "完整性：保存基本信息、修改密码、头像上传回调与校验均已接线。",
        ],
      },
      {
        anchor: "page-changelog",
        title: "更新日志",
        path: "changelog/index.vue",
        notes: [
          "静态路由 `/changelog`；列表遍历 mock `upgradeLogList`（版本、日期、明细、备注、需重登标签）。",
          "另有 `module_system/changelog` 视图未挂路由；完整性以本页为准。",
        ],
      },
      {
        anchor: "page-db-workplace",
        title: "工作台",
        path: "dashboard/workplace/index.vue",
        notes: [
          "仪表盘子路由 `dashboard/workplace`：独立 `dashboard-container` 布局（含 Github 角标、问候区、天气文案、统计卡片与图表等，以页面为准）。",
          "与 `/home` 所用 `dashboard/index.vue` 不是同一文件；完整性需单独打开该路由逐项看区块是否渲染。",
        ],
      },
      {
        anchor: "page-db-console",
        title: "控制台",
        path: "dashboard/console/index.vue",
        notes: [
          "控制台仪表盘分区（卡片/图表）；meta.fixedTab 等影响标签钉扎行为。",
          "完整性：各区块渲染与路由切换无报错。",
        ],
      },
      {
        anchor: "page-db-analysis",
        title: "分析页",
        path: "dashboard/analysis/index.vue",
        notes: ["图表与卡片布局演示页；完整性：各图表组件 mount 成功、无控制台报错。"],
      },
      {
        anchor: "page-db-ecommerce",
        title: "电子商务",
        path: "dashboard/ecommerce/index.vue",
        notes: ["电商风格区块演示；完整性：列表/卡片区块均可滚动与展示。"],
      },
      {
        anchor: "page-db-map",
        title: "地图",
        path: "dashboard/map/index.vue",
        notes: ["地图 SDK 示例；完整性：地图实例初始化、标记与交互事件可用。"],
      },
      {
        anchor: "page-db-pricing",
        title: "定价",
        path: "dashboard/pricing/index.vue",
        notes: ["定价页模板；完整性：价格表、按钮或跳转链接展示齐全。"],
      },
      {
        anchor: "page-db-article",
        title: "文章管理",
        path: "dashboard/article/list/index.vue",
        notes: [
          "文章列表（当前多为 mock `ArticleList`）；路由 path `dashboard/article/article-list`。",
          "meta.authList：新增/编辑类权限标记；完整性：列表、分页、抽屉或编辑入口覆盖文章 CRUD 流程。",
        ],
      },
      {
        anchor: "page-db-tutorial",
        title: "教程",
        path: "dashboard/tutorial/index.vue",
        notes: [
          "视频 Tab + 功能验收 Tab；正文含用户/角色详述与其余模块完整性清单。",
          "完整性：目录筛选、锚点滚动、手册内链跳转可用。",
        ],
      },
    ],
  },
  {
    anchor: "mod-layout",
    heading: "九、布局与通用功能",
    pkgTag: "layouts",
    pages: [
      {
        anchor: "layout-main",
        title: "主布局",
        path: "../layouts/index.vue",
        notes: [
          "RootLayout：嵌套 RouterView；组合侧栏、顶栏、工作区、设置抽屉等子布局组件。",
          "完整性：登录后进主壳、子路由 outlet 渲染、响应式收缩侧栏。",
        ],
      },
      {
        anchor: "layout-sidebar",
        title: "侧栏菜单",
        path: "../layouts/art-menus/**",
        notes: ["菜单折叠、搜索、递归子菜单；与路由 meta.icon/title 绑定。"],
      },
      {
        anchor: "layout-header",
        title: "顶栏",
        path: "../layouts/art-header-bar/**",
        notes: ["面包屑、快速入口、全屏、通知铃铛区域。"],
      },
      {
        anchor: "layout-worktab",
        title: "标签页",
        path: "../layouts/art-work-tab/**",
        notes: ["多标签打开、固定钉住、关闭其他；与 keep-alive 协同。"],
      },
      {
        anchor: "layout-settings",
        title: "设置面板",
        path: "../layouts/art-settings-panel/**",
        notes: ["主题、色弱、标签栏、菜单布局等本地偏好持久化。"],
      },
      {
        anchor: "layout-notification",
        title: "通知",
        path: "../layouts/art-notification/**",
        notes: ["通知下拉列表；已读状态；路由跳转。"],
      },
      {
        anchor: "layout-search",
        title: "全局搜索",
        path: "../layouts/art-global-search/**",
        notes: ["Ctrl/⌘+K 打开全局搜索（`art-global-search` 监听 keydown）。"],
      },
      {
        anchor: "layout-lock",
        title: "锁屏",
        path: "../layouts/art-screen-lock/index.vue",
        notes: [
          "锁屏全屏页；背景随明暗主题切换（`@imgs/lock` → `src/assets/images/lock`）；顶栏用户菜单进入。",
        ],
      },
      {
        anchor: "layout-user",
        title: "用户菜单",
        path: "../layouts/art-header-bar/**",
        notes: ["头像下拉：文档、教程、锁屏、退出等。"],
      },
      {
        anchor: "layout-theme",
        title: "主题切换",
        path: "../layouts/art-settings-panel/**",
        notes: ["明暗色、主题色；CSS 变量与 Element Plus 深色。"],
      },
      {
        anchor: "layout-lang",
        title: "语言切换",
        path: "../locales/langs/**",
        notes: ["`src/locales/langs/*.json` 与 i18n 实例；顶栏/设置内切换语言并持久化到本地存储。"],
      },
    ],
  },
  {
    anchor: "mod-exception",
    heading: "十、异常页",
    pkgTag: "exception",
    pages: [
      {
        anchor: "page-401",
        title: "401",
        path: "exception/401/index.vue",
        notes: [
          "静态路由 `/401`；页面含返回/登录入口（见模板）。",
          "完整性：守卫或 axios 拦截跳转至此页时按钮可用。",
        ],
      },
      {
        anchor: "page-403",
        title: "403",
        path: "exception/403/index.vue",
        notes: [
          "静态路由 `/403`；无权限提示与返回首页等操作。",
          "完整性：从路由 meta 或业务手动跳转后页面可退出。",
        ],
      },
      {
        anchor: "page-404",
        title: "404",
        path: "exception/404/index.vue",
        notes: [
          "独立 `/404` 与 CatchAll `CatchAll404` 共用组件文件（路由 name 不同）。",
          "完整性：非法路径落入 CatchAll、手动跳转 `/404` 均能展示。",
        ],
      },
      {
        anchor: "page-500",
        title: "500",
        path: "exception/500/index.vue",
        notes: [
          "静态路由 `/500`；服务端错误提示页。",
          "完整性：错误文案、返回或重试按钮（若有）可点击。",
        ],
      },
    ],
  },
  {
    anchor: "mod-swagger",
    heading: "十一、接口文档（API）",
    pkgTag: "module_swagger",
    pages: [
      {
        anchor: "page-swagger",
        title: "Swagger文档",
        path: "module_swagger/docs/index.vue",
        notes: [
          "父级菜单「接口管理」；默认 iframe `VITE_APP_BASE_API + /docs`，可由 `IframeRouteManager` 覆盖 link。",
          "完整性：iframe 加载、loading 消失；需后端文档地址可达。",
        ],
      },
      {
        anchor: "page-redoc",
        title: "Redoc文档",
        path: "module_swagger/redoc/index.vue",
        notes: [
          "Redoc 文档 iframe 页；链接来自 env 或 iframe 路由 meta（与同模块 docs 一致范式）。",
          "完整性：页面全高 iframe、加载完成。",
        ],
      },
      {
        anchor: "page-ljdoc",
        title: "LangJin文档",
        path: "module_swagger/ljdoc/index.vue",
        notes: [
          "LangJin 文档 iframe；platform_menu 中节点类型可为 4（菜单页）。",
          "完整性：同上，依赖后端或 meta 配置的文档 URL。",
        ],
      },
    ],
  },
];
