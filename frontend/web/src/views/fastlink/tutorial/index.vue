<!-- 操作手册：视频演示 + 全功能验收正文 -->
<template>
  <div class="page-content manual-page">
    <div class="manual-page__inner mx-auto max-w-300 px-4 pb-8">
      <!-- 标题 -->
      <h1 class="mb-2 text-2xl font-medium text-g-900 dark:text-g-50">
        {{ t("manualPage.title") }}
      </h1>
      <p class="mb-6 text-sm text-g-600 dark:text-g-400">
        {{ t("manualPage.intro") }}
      </p>

      <!-- Tab 切换：视频 / 手册 -->
      <ElTabs v-model="activeTab" class="manual-page__tabs">
        <!-- 视频演示 Tab -->
        <ElTabPane :label="t('manualPage.videoTab')" name="video">
          <div class="fa-card-sm mt-2 p-5">
            <p class="mb-4 text-sm text-g-600 dark:text-g-400">
              {{ t("manualPage.videoHint") }}
            </p>
            <div class="manual-page__player max-w-full">
              <FaVideoPlayer
                :player-id="PLAYER_ID"
                :video-url="videoUrl"
                :poster-url="posterUrl"
                :autoplay="false"
                :volume="1"
                :playback-rates="[0.5, 1, 1.5, 2]"
              />
            </div>
          </div>
        </ElTabPane>

        <!-- 功能验收手册 Tab -->
        <ElTabPane :label="t('manualPage.manualTab')" name="manual">
          <p class="mb-3 mt-2 text-sm text-g-600 dark:text-g-400">
            {{ t("manualPage.manualHint") }}
          </p>

          <div class="manual-feature-body">
            <!-- 工具栏：筛选 -->
            <div class="manual-feature-body__toolbar">
              <ElInput
                v-model="tocFilter"
                clearable
                placeholder="筛选目录…"
                :prefix-icon="Search"
                class="manual-feature-body__filter"
              />
            </div>

            <!-- 主体布局：侧边导航 + 内容区 -->
            <ElSplitter :style="'height: min(78vh, 880px)'">
              <ElSplitterPanel size="220px" :min="180" :max="400">
                <aside class="manual-feature-body__aside h-full">
                  <nav v-if="filteredToc.length" class="manual-nav">
                    <div v-for="mod in filteredToc" :key="mod.anchor" class="manual-nav__module">
                      <ElButton
                        link
                        type="primary"
                        class="manual-nav__mod-title h-auto! min-h-0 justify-start px-0 py-1"
                        @click="scrollToAnchor(mod.anchor)"
                      >
                        {{ mod.title }}
                      </ElButton>
                      <div class="manual-nav__pages">
                        <ElButton
                          v-for="p in mod.pages"
                          :key="p.anchor"
                          link
                          size="small"
                          class="manual-nav__page h-auto! min-h-0 justify-start px-2 py-1"
                          @click="scrollToAnchor(p.anchor)"
                        >
                          {{ p.title }}
                        </ElButton>
                      </div>
                    </div>
                  </nav>
                  <div v-else class="manual-nav manual-nav--empty">
                    <ElEmpty description="无匹配目录" :image-size="64" />
                  </div>
                </aside>
              </ElSplitterPanel>

              <!-- 右侧内容区（滚动） -->
              <ElSplitterPanel :min="300">
                <ElScrollbar
                  ref="scrollbarRef"
                  class="manual-feature-body__scrollbar fa-card-sm rounded-custom-sm h-full"
                  max-height="min(78vh, 880px)"
                >
                  <!-- 功能验收手册正文内容 -->
                  <div class="manual-html" @click.capture="handleAnchorClick">
                    <div class="manual-html__inner">
                      <h1>
                        FastapiAdmin 功能点清单
                        <small>用于全功能测试验收，按模块逐页列出所有可操作元素</small>
                      </h1>

                      <!-- 目录 -->
                      <ElCard id="toc" shadow="never" class="toc mb-6">
                        <template #header>
                          <span class="text-base font-medium">📋 目录</span>
                        </template>
                        <ul>
                          <li>
                            <ElLink href="#mod-system" type="primary" underline="never">
                              一、系统管理
                            </ElLink>
                            <div class="toc-l2">
                              <ElLink href="#page-user" type="primary" underline="never">
                                用户管理
                              </ElLink>
                              ·
                              <ElLink href="#page-role" type="primary" underline="never">
                                角色管理
                              </ElLink>
                              ·
                              <ElLink href="#page-menu" type="primary" underline="never">
                                菜单管理
                              </ElLink>
                              ·
                              <ElLink href="#page-dept" type="primary" underline="never">
                                部门管理
                              </ElLink>
                              ·
                              <ElLink href="#page-position" type="primary" underline="never">
                                岗位管理
                              </ElLink>
                              ·
                              <ElLink href="#page-dict" type="primary" underline="never">
                                字典管理
                              </ElLink>
                              ·
                              <ElLink href="#page-param" type="primary" underline="never">
                                参数配置
                              </ElLink>
                              ·
                              <ElLink href="#page-notice" type="primary" underline="never">
                                通知公告
                              </ElLink>
                              ·
                              <ElLink href="#page-log" type="primary" underline="never">
                                操作日志
                              </ElLink>
                              ·
                              <ElLink href="#page-login" type="primary" underline="never">
                                登录页
                              </ElLink>
                            </div>
                          </li>
                          <li>
                            <ElLink href="#mod-monitor" type="primary" underline="never">
                              二、监控管理
                            </ElLink>
                            <div class="toc-l2">
                              <ElLink href="#page-online" type="primary" underline="never">
                                在线用户
                              </ElLink>
                              ·
                              <ElLink href="#page-cache" type="primary" underline="never">
                                缓存管理
                              </ElLink>
                              ·
                              <ElLink href="#page-resource" type="primary" underline="never">
                                文件管理
                              </ElLink>
                              ·
                              <ElLink href="#page-server" type="primary" underline="never">
                                服务监控
                              </ElLink>
                            </div>
                          </li>
                          <li>
                            <ElLink href="#mod-task" type="primary" underline="never">
                              三、任务管理
                            </ElLink>
                            <div class="toc-l2">
                              <ElLink href="#page-cronjob" type="primary" underline="never">
                                调度器监控
                              </ElLink>
                              ·
                              <ElLink href="#page-cronnode" type="primary" underline="never">
                                节点管理
                              </ElLink>
                              ·
                              <ElLink href="#page-workflow" type="primary" underline="never">
                                流程编排
                              </ElLink>
                              ·
                              <ElLink href="#page-nodetype" type="primary" underline="never">
                                节点类型
                              </ElLink>
                            </div>
                          </li>
                          <li>
                            <ElLink href="#mod-ai" type="primary" underline="never">
                              四、AI 模块
                            </ElLink>
                            <div class="toc-l2">
                              <ElLink href="#page-ai-chat" type="primary" underline="never">
                                AI智能助手
                              </ElLink>
                              ·
                              <ElLink href="#page-ai-fachat" type="primary" underline="never">
                                会话聊天
                              </ElLink>
                              ·
                              <ElLink href="#page-ai-memory" type="primary" underline="never">
                                会话记忆
                              </ElLink>
                            </div>
                          </li>
                          <li>
                            <ElLink href="#mod-generator" type="primary" underline="never">
                              五、代码生成器
                            </ElLink>
                            <div class="toc-l2">
                              <ElLink href="#page-gencode" type="primary" underline="never">
                                代码生成
                              </ElLink>
                            </div>
                          </li>
                          <li>
                            <ElLink href="#mod-app" type="primary" underline="never">
                              六、应用管理
                            </ElLink>
                            <div class="toc-l2">
                              <ElLink href="#page-portal" type="primary" underline="never">
                                插件市场
                              </ElLink>
                            </div>
                          </li>
                          <li>
                            <ElLink href="#mod-example" type="primary" underline="never">
                              七、示例模块
                            </ElLink>
                            <div class="toc-l2">
                              <ElLink href="#page-demo" type="primary" underline="never">
                                示例管理
                              </ElLink>
                            </div>
                          </li>
                          <li>
                            <ElLink href="#mod-dashboard" type="primary" underline="never">
                              八、仪表盘
                            </ElLink>
                            <div class="toc-l2">
                              <ElLink href="#page-home" type="primary" underline="never"
                                >首页</ElLink
                              >
                              ·
                              <ElLink href="#page-profile" type="primary" underline="never">
                                个人中心
                              </ElLink>
                              ·
                              <ElLink href="#page-changelog" type="primary" underline="never">
                                更新日志
                              </ElLink>
                              ·
                              <ElLink href="#page-db-workplace" type="primary" underline="never">
                                工作台
                              </ElLink>
                              ·
                              <ElLink href="#page-db-console" type="primary" underline="never">
                                控制台
                              </ElLink>
                              ·
                              <ElLink href="#page-db-analysis" type="primary" underline="never">
                                分析页
                              </ElLink>
                              ·
                              <ElLink href="#page-db-ecommerce" type="primary" underline="never">
                                电子商务
                              </ElLink>
                              ·
                              <ElLink href="#page-db-map" type="primary" underline="never">
                                地图
                              </ElLink>
                              ·
                              <ElLink href="#page-db-pricing" type="primary" underline="never">
                                定价
                              </ElLink>
                              ·
                              <ElLink href="#page-db-article" type="primary" underline="never">
                                文章管理
                              </ElLink>
                              ·
                              <ElLink href="#page-db-tutorial" type="primary" underline="never">
                                教程
                              </ElLink>
                            </div>
                          </li>
                          <li>
                            <ElLink href="#mod-layout" type="primary" underline="never">
                              九、布局与通用功能
                            </ElLink>
                            <div class="toc-l2">
                              <ElLink href="#layout-main" type="primary" underline="never">
                                主布局
                              </ElLink>
                              ·
                              <ElLink href="#layout-sidebar" type="primary" underline="never">
                                侧栏菜单
                              </ElLink>
                              ·
                              <ElLink href="#layout-header" type="primary" underline="never">
                                顶栏
                              </ElLink>
                              ·
                              <ElLink href="#layout-worktab" type="primary" underline="never">
                                标签页
                              </ElLink>
                              ·
                              <ElLink href="#layout-settings" type="primary" underline="never">
                                设置面板
                              </ElLink>
                              ·
                              <ElLink href="#layout-notification" type="primary" underline="never">
                                通知
                              </ElLink>
                              ·
                              <ElLink href="#layout-search" type="primary" underline="never">
                                全局搜索
                              </ElLink>
                              ·
                              <ElLink href="#layout-lock" type="primary" underline="never">
                                锁屏
                              </ElLink>
                              ·
                              <ElLink href="#layout-user" type="primary" underline="never">
                                用户菜单
                              </ElLink>
                              ·
                              <ElLink href="#layout-theme" type="primary" underline="never">
                                主题切换
                              </ElLink>
                              ·
                              <ElLink href="#layout-lang" type="primary" underline="never">
                                语言切换
                              </ElLink>
                            </div>
                          </li>
                          <li>
                            <ElLink href="#mod-exception" type="primary" underline="never">
                              十、异常页
                            </ElLink>
                            <div class="toc-l2">
                              <ElLink href="#page-401" type="primary" underline="never">401</ElLink>
                              ·
                              <ElLink href="#page-403" type="primary" underline="never">403</ElLink>
                              ·
                              <ElLink href="#page-404" type="primary" underline="never">404</ElLink>
                              ·
                              <ElLink href="#page-500" type="primary" underline="never">500</ElLink>
                            </div>
                          </li>
                          <li>
                            <ElLink href="#mod-swagger" type="primary" underline="never">
                              十一、接口文档（API）
                            </ElLink>
                            <div class="toc-l2">
                              <ElLink href="#page-swagger" type="primary" underline="never">
                                Swagger文档
                              </ElLink>
                              ·
                              <ElLink href="#page-redoc" type="primary" underline="never">
                                Redoc文档
                              </ElLink>
                              ·
                              <ElLink href="#page-ljdoc" type="primary" underline="never">
                                LangJin文档
                              </ElLink>
                            </div>
                          </li>
                        </ul>
                      </ElCard>

                      <!-- 一、系统管理 -->
                      <div class="module" id="mod-system">
                        <h2>
                          一、系统管理
                          <ElTag type="primary" effect="dark" size="small" class="shrink-0">
                            module_system
                          </ElTag>
                        </h2>

                        <!-- 用户管理 -->
                        <div class="page" id="page-user">
                          <h3>
                            1.1 用户管理
                            <ElText tag="span" size="small" type="info" class="path font-mono">
                              module_system/user/index.vue
                            </ElText>
                          </h3>

                          <div class="section">
                            <ElDivider content-position="left" class="my-3!"
                              >API 权限标识</ElDivider
                            >
                            <p>
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                module_system:user
                              </ElTag>
                              — 含
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                create
                              </ElTag>
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                delete
                              </ElTag>
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                update
                              </ElTag>
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                detail
                              </ElTag>
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                import
                              </ElTag>
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                export
                              </ElTag>
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                patch
                              </ElTag>
                            </p>
                          </div>

                          <div class="section">
                            <ElDivider content-position="left" class="my-3!">
                              🔍 搜索/筛选表单（5字段）
                            </ElDivider>
                            <ElCard shadow="never" class="mb-3 overflow-x-auto">
                              <table class="manual-doc-table w-full border-collapse text-sm">
                                <thead>
                                  <tr>
                                    <th>备注</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  <tr>
                                    <td>文本·账号</td>
                                  </tr>
                                  <tr>
                                    <td>文本·用户名</td>
                                  </tr>
                                  <tr>
                                    <td>下拉·启用/停用</td>
                                  </tr>
                                  <tr>
                                    <td>创建人（FaUserTableSelect 弹窗选用户）</td>
                                  </tr>
                                  <tr>
                                    <td>创建时间·日期时间范围</td>
                                  </tr>
                                </tbody>
                              </table>
                            </ElCard>
                          </div>

                          <div class="section">
                            <ElDivider content-position="left" class="my-3!">📊 表格列</ElDivider>
                            <ElCard shadow="never" class="mb-3 overflow-x-auto">
                              <table class="manual-doc-table w-full border-collapse text-sm">
                                <thead>
                                  <tr>
                                    <th>渲染</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  <tr>
                                    <td>固定左侧</td>
                                  </tr>
                                  <tr>
                                    <td>ElAvatar</td>
                                  </tr>
                                  <tr>
                                    <td>溢出省略</td>
                                  </tr>
                                  <tr>
                                    <td>溢出省略</td>
                                  </tr>
                                  <tr>
                                    <td>
                                      <span class="tag tag-success">启用</span>
                                      <span class="tag tag-danger">停用</span>
                                    </td>
                                  </tr>
                                  <tr>
                                    <td>row.dept?.name</td>
                                  </tr>
                                  <tr>
                                    <td>
                                      <span class="tag tag-success">男</span>
                                      <span class="tag tag-warning">女</span>
                                      <span class="tag tag-info">未知</span>
                                    </td>
                                  </tr>
                                  <tr>
                                    <td></td>
                                  </tr>
                                  <tr>
                                    <td></td>
                                  </tr>
                                  <tr>
                                    <td>固定右侧</td>
                                  </tr>
                                </tbody>
                              </table>
                            </ElCard>
                          </div>

                          <div class="section">
                            <ElDivider content-position="left" class="my-3!"
                              >🔘 工具栏按钮</ElDivider
                            >
                            <ElSpace wrap size="small" class="mb-2">
                              <ElButton type="primary" size="small" plain class="manual-doc-btn">
                                新增
                              </ElButton>
                              <ElButton type="success" size="small" plain class="manual-doc-btn">
                                导入
                              </ElButton>
                              <ElButton type="warning" size="small" plain class="manual-doc-btn">
                                导出
                              </ElButton>
                              <ElButton type="danger" size="small" plain class="manual-doc-btn">
                                删除
                              </ElButton>
                              <ElButton type="info" size="small" plain class="manual-doc-btn">
                                更多(批量启/停用)
                              </ElButton>
                              <ElButton size="small" plain class="manual-doc-btn">刷新</ElButton>
                              <ElButton size="small" plain class="manual-doc-btn">列配置</ElButton>
                            </ElSpace>
                          </div>

                          <div class="section">
                            <ElDivider content-position="left" class="my-3!"
                              >🔘 行操作按钮</ElDivider
                            >
                            <ElSpace wrap size="small" class="mb-2">
                              <ElButton type="warning" size="small" plain class="manual-doc-btn">
                                重置密码
                              </ElButton>
                              <ElButton type="info" size="small" plain class="manual-doc-btn">
                                详情
                              </ElButton>
                              <ElButton type="primary" size="small" plain class="manual-doc-btn">
                                编辑
                              </ElButton>
                              <ElButton type="danger" size="small" plain class="manual-doc-btn">
                                删除
                              </ElButton>
                            </ElSpace>
                          </div>

                          <div class="section">
                            <ElDivider content-position="left" class="my-3!"
                              >📋 弹窗/抽屉</ElDivider
                            >
                            <ul class="feature-list">
                              <li>
                                <strong>详情 Drawer</strong>
                                —
                                编号、头像、账号、用户名、性别(标签)、部门、角色(逗号拼接)、岗位(逗号拼接)、邮箱、手机号、是否超管(标签)、状态(标签)、上次登录时间、创建人、更新人、创建时间、更新时间、描述
                              </li>
                              <li>
                                <strong>新增/编辑 Drawer</strong>
                                (450px) —
                                账号(username,编辑时禁用)、用户名(name)、性别、手机号(正则校验)、邮箱(正则校验)、部门(ElTreeSelect)、角色(多选)、岗位(多选)、密码(仅新增)、是否超管(Switch)、状态(Radio)、描述(textarea)
                              </li>
                              <li>
                                <strong>导入弹窗</strong>
                                — FaImportDialog, 模板 user_import_template.xlsx
                              </li>
                              <li>
                                <strong>导出弹窗</strong>
                                — FaExportDialog
                              </li>
                              <li>
                                <strong>重置密码弹窗</strong>
                                — 输入新密码, 至少6位
                              </li>
                            </ul>
                          </div>

                          <div class="section">
                            <ElDivider content-position="left" class="my-3!">✨ 特殊功能</ElDivider>
                            <ul class="feature-list">
                              <li>左侧部门树联动筛选(点击树节点过滤列表)</li>
                              <li>批量删除(确认对话框)</li>
                              <li>批量启用/停用</li>
                              <li>若删除自己则清除登录信息登出</li>
                            </ul>
                          </div>
                        </div>

                        <!-- 角色管理 -->
                        <div class="page" id="page-role">
                          <h3>
                            1.2 角色管理
                            <ElText tag="span" size="small" type="info" class="path font-mono">
                              module_system/role/index.vue
                            </ElText>
                          </h3>

                          <div class="section">
                            <ElDivider content-position="left" class="my-3!"
                              >API 权限标识</ElDivider
                            >
                            <p>
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                module_system:role
                              </ElTag>
                              — 含
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                create
                              </ElTag>
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                delete
                              </ElTag>
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                update
                              </ElTag>
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                detail
                              </ElTag>
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                export
                              </ElTag>
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                patch
                              </ElTag>
                              <ElTag effect="plain" type="info" size="small" class="mr-1 font-mono">
                                permission
                              </ElTag>
                            </p>
                          </div>

                          <div class="section">
                            <ElDivider content-position="left" class="my-3!">
                              🔍 搜索表单（3字段）
                            </ElDivider>
                            <ElCard shadow="never" class="mb-3 overflow-x-auto">
                              <table class="manual-doc-table w-full border-collapse text-sm">
                                <thead>
                                  <tr>
                                    <th>类型</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  <tr>
                                    <td>文本输入</td>
                                  </tr>
                                  <tr>
                                    <td>下拉(启用/停用, value="true"/"false")</td>
                                  </tr>
                                  <tr>
                                    <td>日期时间范围</td>
                                  </tr>
                                </tbody>
                              </table>
                            </ElCard>
                          </div>

                          <div class="section">
                            <ElDivider content-position="left" class="my-3!">📊 表格列</ElDivider>
                            <ElCard shadow="never" class="mb-3 overflow-x-auto">
                              <table class="manual-doc-table w-full border-collapse text-sm">
                                <thead>
                                  <tr>
                                    <th>渲染</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  <tr>
                                    <td>固定左侧</td>
                                  </tr>
                                  <tr>
                                    <td>溢出省略</td>
                                  </tr>
                                  <tr>
                                    <td>
                                      <span class="tag tag-success">启用</span>
                                      <span class="tag tag-danger">停用</span>
                                    </td>
                                  </tr>
                                  <tr>
                                    <td>溢出省略</td>
                                  </tr>
                                  <tr>
                                    <td>固定右侧</td>
                                  </tr>
                                </tbody>
                              </table>
                            </ElCard>
                          </div>

                          <div class="section">
                            <ElDivider content-position="left" class="my-3!"
                              >🔘 工具栏按钮</ElDivider
                            >
                            <ElSpace wrap size="small" class="mb-2">
                              <ElButton type="primary" size="small" plain class="manual-doc-btn">
                                新增
                              </ElButton>
                              <ElButton type="warning" size="small" plain class="manual-doc-btn">
                                导出
                              </ElButton>
                              <ElButton type="danger" size="small" plain class="manual-doc-btn">
                                删除
                              </ElButton>
                              <ElButton size="small" plain class="manual-doc-btn">刷新</ElButton>
                              <ElButton size="small" plain class="manual-doc-btn">列配置</ElButton>
                            </ElSpace>
                          </div>

                          <div class="section">
                            <ElDivider content-position="left" class="my-3!"
                              >🔘 行操作按钮</ElDivider
                            >
                            <ElSpace wrap size="small" class="mb-2">
                              <ElButton type="info" size="small" plain class="manual-doc-btn">
                                权限
                              </ElButton>
                              <ElButton type="primary" size="small" plain class="manual-doc-btn">
                                编辑
                              </ElButton>
                              <ElButton type="danger" size="small" plain class="manual-doc-btn">
                                删除
                              </ElButton>
                            </ElSpace>
                          </div>

                          <div class="section">
                            <ElDivider content-position="left" class="my-3!"
                              >📋 弹窗/抽屉</ElDivider
                            >
                            <ul class="feature-list">
                              <li>
                                <strong>新增/编辑 Drawer</strong>
                                (450px) — 名称、标识(编辑时禁用)、排序、状态(Radio)、权限树(ElTree,
                                勾选)、备注(textarea)
                              </li>
                              <li>
                                <strong>权限 Drawer</strong>
                                (600px) — 权限菜单树(ElTree, 勾选, 支持展开/收起)
                              </li>
                              <li>
                                <strong>导出弹窗</strong>
                                — FaExportDialog
                              </li>
                            </ul>
                          </div>
                        </div>

                        <!-- 系统管理：其余页面（完整性验收要点，与实现对齐便于漏项检查） -->
                        <div
                          v-for="p in manualSystemTailPages"
                          :key="p.anchor"
                          class="page"
                          :id="p.anchor"
                        >
                          <h3>
                            {{ p.title }}
                            <ElText tag="span" size="small" type="info" class="path font-mono">
                              {{ p.path }}
                            </ElText>
                          </h3>
                          <div class="section">
                            <ElDivider content-position="left" class="my-3!">
                              功能完整性验收
                            </ElDivider>
                            <ul class="feature-list">
                              <li v-for="(line, idx) in p.notes" :key="idx">{{ line }}</li>
                            </ul>
                          </div>
                        </div>
                      </div>

                      <!-- 二～十一：其余业务模块 -->
                      <div
                        v-for="mod in manualModulesAfterSystem"
                        :key="mod.anchor"
                        class="module"
                        :id="mod.anchor"
                      >
                        <h2>
                          {{ mod.heading }}
                          <ElTag
                            v-if="mod.pkgTag"
                            type="primary"
                            effect="dark"
                            size="small"
                            class="shrink-0"
                          >
                            {{ mod.pkgTag }}
                          </ElTag>
                        </h2>
                        <div v-for="p in mod.pages" :key="p.anchor" class="page" :id="p.anchor">
                          <h3>
                            {{ p.title }}
                            <ElText tag="span" size="small" type="info" class="path font-mono">
                              {{ p.path }}
                            </ElText>
                          </h3>
                          <div class="section">
                            <ElDivider content-position="left" class="my-3!">
                              功能完整性验收
                            </ElDivider>
                            <ul class="feature-list">
                              <li v-for="(line, idx) in p.notes" :key="idx">{{ line }}</li>
                            </ul>
                          </div>
                        </div>
                      </div>

                      <div
                        class="manual-footer-note mt-10 border-t border-g-200 pt-6 text-center text-xs text-g-500 dark:border-g-700 dark:text-g-400"
                      >
                        <p>
                          FastapiAdmin 功能点清单（完整性）—
                          与当前代码中已实现界面项对齐，用于逐项核对是否漏测，不评价体验优劣。
                        </p>
                      </div>
                    </div>
                  </div>
                </ElScrollbar>
              </ElSplitterPanel>
            </ElSplitter>
          </div>
        </ElTabPane>

        <!-- 组件展示 Tab -->
        <ElTabPane :label="t('manualPage.widgetsTab')" name="widgets">
          <div class="page-content mb-5">
            <!-- 完整工具栏编辑器 -->
            <ElCard class="editor-card">
              <template #header>
                <div class="card-header">
                  <span>🛠️ 完整工具栏编辑器</span>
                  <div class="header-buttons">
                    <ElButton size="small" @click="clearFullEditor">清空</ElButton>
                    <ElButton size="small" @click="getFullEditorContent">获取内容</ElButton>
                    <ElButton size="small" @click="setFullEditorDemo">设置示例</ElButton>
                  </div>
                </div>
              </template>

              <FaWangEditor
                ref="fullEditorRef"
                v-model="fullEditorHtml"
                height="400px"
                placeholder="请输入内容，体验完整的编辑功能..."
                :exclude-keys="[]"
              />
            </ElCard>

            <!-- 简化工具栏编辑器 -->
            <ElCard class="editor-card">
              <template #header>
                <div class="card-header">
                  <span>✨ 简化工具栏编辑器</span>
                  <div class="header-buttons">
                    <ElButton size="small" @click="clearSimpleEditor">清空</ElButton>
                    <ElButton size="small" @click="getSimpleEditorContent">获取内容</ElButton>
                    <ElButton size="small" @click="setSimpleEditorDemo">设置示例</ElButton>
                  </div>
                </div>
              </template>

              <FaWangEditor
                ref="simpleEditorRef"
                v-model="simpleEditorHtml"
                height="400px"
                placeholder="请输入内容，体验简化的编辑功能..."
                :toolbar-keys="simpleToolbarKeys"
              />
            </ElCard>

            <!-- 内容对比预览 -->
            <ElCard class="preview-card">
              <template #header>
                <span>📖 内容预览对比</span>
              </template>

              <ElRow :gutter="20">
                <ElCol :span="12">
                  <h3>完整编辑器内容</h3>
                  <ElTabs v-model="fullActiveTab">
                    <ElTabPane label="渲染效果" name="preview">
                      <div
                        class="content-preview"
                        v-html="DOMPurify.sanitize(fullEditorHtml)"
                      ></div>
                    </ElTabPane>
                    <ElTabPane label="HTML源码" name="html">
                      <ElInput
                        v-model="fullEditorHtml"
                        type="textarea"
                        :rows="8"
                        placeholder="HTML源码"
                        readonly
                      />
                    </ElTabPane>
                  </ElTabs>
                </ElCol>

                <ElCol :span="12">
                  <h3>简化编辑器内容</h3>
                  <ElTabs v-model="simpleActiveTab">
                    <ElTabPane label="渲染效果" name="preview">
                      <div
                        class="content-preview"
                        v-html="DOMPurify.sanitize(simpleEditorHtml)"
                      ></div>
                    </ElTabPane>
                    <ElTabPane label="HTML源码" name="html">
                      <ElInput
                        v-model="simpleEditorHtml"
                        type="textarea"
                        :rows="8"
                        placeholder="HTML源码"
                        readonly
                      />
                    </ElTabPane>
                  </ElTabs>
                </ElCol>
              </ElRow>
            </ElCard>

            <!-- 使用说明 -->
            <ElCard class="usage-card">
              <template #header>
                <span>📚 使用说明</span>
              </template>

              <ElCollapse v-model="activeCollapse">
                <ElCollapseItem title="基础用法" name="basic">
                  <pre><code class="language-vue">&lt;template&gt;
                  &lt;ArtWangEditor v-model="content" /&gt;
                  &lt;/template&gt;

                  &lt;script setup lang="ts"&gt;
                  import { ref } from 'vue'

                  const content = ref('&lt;p&gt;初始内容&lt;/p&gt;')
                  &lt;/script&gt;</code></pre>
                </ElCollapseItem>

                <ElCollapseItem title="完整工具栏配置" name="full">
                  <pre><code class="language-vue">&lt;template&gt;
                  &lt;!-- 显示所有工具，不排除任何功能 --&gt;
                  &lt;ArtWangEditor
                  v-model="content"
                  :exclude-keys="[]"
                  /&gt;
                  &lt;/template&gt;</code></pre>
                </ElCollapseItem>

                <ElCollapseItem title="简化工具栏配置" name="simple">
                  <pre><code class="language-vue">&lt;template&gt;
                  &lt;!-- 只显示基础编辑工具 --&gt;
                  &lt;ArtWangEditor
                  v-model="content"
                  :toolbar-keys="[
                  'bold', 'italic', 'underline', '|',
                  'bulletedList', 'numberedList', '|',
                  'insertLink', 'insertImage', '|',
                  'undo', 'redo'
                  ]"
                  /&gt;
                  &lt;/template&gt;</code></pre>
                </ElCollapseItem>

                <ElCollapseItem title="自定义配置" name="config">
                  <pre><code class="language-vue">&lt;template&gt;
                  &lt;ArtWangEditor
                  v-model="content"
                  height="600px"
                  placeholder="请输入您的内容..."
                  :exclude-keys="['fontFamily', 'fontSize']"
                  :upload-config="{
                  maxFileSize: 5 * 1024 * 1024,
                  maxNumberOfFiles: 5
                  }"
                  /&gt;
                  &lt;/template&gt;</code></pre>
                </ElCollapseItem>

                <ElCollapseItem title="组件方法调用" name="methods">
                  <pre><code class="language-vue">&lt;template&gt;
                  &lt;ArtWangEditor ref="editorRef" v-model="content" /&gt;
                  &lt;el-button @click="handleClear"&gt;清空&lt;/el-button&gt;
                  &lt;el-button @click="handleFocus"&gt;聚焦&lt;/el-button&gt;
                  &lt;el-button @click="handleGetContent"&gt;获取内容&lt;/el-button&gt;
                  &lt;/template&gt;

                  &lt;script setup lang="ts"&gt;
                  import { ref } from 'vue'

                  const editorRef = ref()
                  const content = ref('')

                  const handleClear = () =&gt; {
                  editorRef.value?.clear()
                  }

                  const handleFocus = () =&gt; {
                  editorRef.value?.focus()
                  }

                  const handleGetContent = () =&gt; {
                  const html = editorRef.value?.getHtml()
                  console.log('编辑器内容:', html)
                  }
                  &lt;/script&gt;</code></pre>
                </ElCollapseItem>

                <ElCollapseItem title="工具栏配置说明" name="toolbar-config">
                  <div class="toolbar-explanation">
                    <h4>完整工具栏 vs 简化工具栏</h4>
                    <ElRow :gutter="16">
                      <ElCol :span="12">
                        <h5>✅ 完整工具栏包含：</h5>
                        <ul>
                          <li>文本格式：加粗、斜体、下划线、字体颜色、背景色</li>
                          <li>段落格式：标题、引用、对齐方式、缩进</li>
                          <li>列表：有序列表、无序列表、待办事项</li>
                          <li>插入：链接、图片、表格、分割线、表情</li>
                          <li>代码：代码块、行内代码</li>
                          <li>操作：撤销、重做、全屏、清除格式</li>
                        </ul>
                      </ElCol>
                      <ElCol :span="12">
                        <h5>⚡ 简化工具栏包含：</h5>
                        <ul>
                          <li>基础格式：加粗、斜体、下划线</li>
                          <li>列表：有序列表、无序列表</li>
                          <li>插入：链接、图片</li>
                          <li>操作：撤销、重做</li>
                        </ul>
                        <p class="note">适用于简单的文本编辑场景，界面更清爽。</p>
                      </ElCol>
                    </ElRow>
                  </div>
                </ElCollapseItem>
              </ElCollapse>
            </ElCard>
          </div>
        </ElTabPane>
      </ElTabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Search } from "@element-plus/icons-vue";
import { computed, ref } from "vue";
import lockImg from "@imgs/lock/bg_dark.webp";
import { MANUAL_MODULES_AFTER_SYSTEM, MANUAL_SYSTEM_TAIL_PAGES } from "./manualSections";
import { manualModuleMatchesQuery, manualPageMatchesQuery } from "./manualTocSearch";
import DOMPurify from "dompurify";

defineOptions({ name: "DashboardTutorial" });

const { t } = useI18n();

const manualSystemTailPages = MANUAL_SYSTEM_TAIL_PAGES;
const manualModulesAfterSystem = MANUAL_MODULES_AFTER_SYSTEM;

// ============ 类型定义 ============
type ManualPageLink = {
  anchor: string;
  title: string;
};

type ManualModule = {
  anchor: string;
  title: string;
  pages: ManualPageLink[];
};

// ============ 配置常量 ============

/** 手册目录结构 */
const MANUAL_TOC: ManualModule[] = [
  {
    anchor: "mod-system",
    title: "一、系统管理",
    pages: [
      { anchor: "page-user", title: "用户管理" },
      { anchor: "page-role", title: "角色管理" },
      { anchor: "page-menu", title: "菜单管理" },
      { anchor: "page-dept", title: "部门管理" },
      { anchor: "page-position", title: "岗位管理" },
      { anchor: "page-dict", title: "字典管理" },
      { anchor: "page-param", title: "参数配置" },
      { anchor: "page-notice", title: "通知公告" },
      { anchor: "page-log", title: "操作日志" },
      { anchor: "page-login", title: "登录页" },
    ],
  },
  {
    anchor: "mod-monitor",
    title: "二、监控管理",
    pages: [
      { anchor: "page-online", title: "在线用户" },
      { anchor: "page-cache", title: "缓存管理" },
      { anchor: "page-resource", title: "文件管理" },
      { anchor: "page-server", title: "服务监控" },
    ],
  },
  {
    anchor: "mod-task",
    title: "三、任务管理",
    pages: [
      { anchor: "page-cronjob", title: "调度器监控" },
      { anchor: "page-cronnode", title: "节点管理" },
      { anchor: "page-workflow", title: "流程编排" },
      { anchor: "page-nodetype", title: "节点类型" },
    ],
  },
  {
    anchor: "mod-ai",
    title: "四、AI 模块",
    pages: [
      { anchor: "page-ai-chat", title: "AI智能助手" },
      { anchor: "page-ai-fachat", title: "会话聊天" },
      { anchor: "page-ai-memory", title: "会话记忆" },
    ],
  },
  {
    anchor: "mod-generator",
    title: "五、代码生成器",
    pages: [{ anchor: "page-gencode", title: "代码生成" }],
  },
  {
    anchor: "mod-app",
    title: "六、应用管理",
    pages: [{ anchor: "page-portal", title: "插件市场" }],
  },
  {
    anchor: "mod-example",
    title: "七、示例模块",
    pages: [{ anchor: "page-demo", title: "示例管理" }],
  },
  {
    anchor: "mod-dashboard",
    title: "八、仪表盘",
    pages: [
      { anchor: "page-home", title: "首页" },
      { anchor: "page-profile", title: "个人中心" },
      { anchor: "page-changelog", title: "更新日志" },
      { anchor: "page-db-workplace", title: "工作台" },
      { anchor: "page-db-console", title: "控制台" },
      { anchor: "page-db-analysis", title: "分析页" },
      { anchor: "page-db-ecommerce", title: "电子商务" },
      { anchor: "page-db-map", title: "地图" },
      { anchor: "page-db-pricing", title: "定价" },
      { anchor: "page-db-article", title: "文章管理" },
      { anchor: "page-db-tutorial", title: "教程" },
    ],
  },
  {
    anchor: "mod-layout",
    title: "九、布局与通用功能",
    pages: [
      { anchor: "layout-main", title: "主布局" },
      { anchor: "layout-sidebar", title: "侧栏菜单" },
      { anchor: "layout-header", title: "顶栏" },
      { anchor: "layout-worktab", title: "标签页" },
      { anchor: "layout-settings", title: "设置面板" },
      { anchor: "layout-notification", title: "通知" },
      { anchor: "layout-search", title: "全局搜索" },
      { anchor: "layout-lock", title: "锁屏" },
      { anchor: "layout-user", title: "用户菜单" },
      { anchor: "layout-theme", title: "主题切换" },
      { anchor: "layout-lang", title: "语言切换" },
    ],
  },
  {
    anchor: "mod-exception",
    title: "十、异常页",
    pages: [
      { anchor: "page-401", title: "401" },
      { anchor: "page-403", title: "403" },
      { anchor: "page-404", title: "404" },
      { anchor: "page-500", title: "500" },
    ],
  },
  {
    anchor: "mod-swagger",
    title: "十一、接口文档（API）",
    pages: [
      { anchor: "page-swagger", title: "Swagger文档" },
      { anchor: "page-redoc", title: "Redoc文档" },
      { anchor: "page-ljdoc", title: "LangJin文档" },
    ],
  },
];

/** 视频资源配置 */
const VIDEO_CONFIG = {
  /** 默认视频地址（建议上线后改为自有 OSS / 静态资源） */
  DEFAULT_URL:
    "//lf3-static.bytednsdoc.com/obj/eden-cn/nupenuvpxnuvo/xgplayer_doc/xgplayer-demo.mp4",
  /** 播放器 ID */
  PLAYER_ID: "dashboard-tutorial-player",
} as const;

const { DEFAULT_URL, PLAYER_ID } = VIDEO_CONFIG;

// ============ 状态管理 ============

const activeTab = ref<"video" | "manual" | "widgets">("video");
const videoUrl = ref(DEFAULT_URL);
const posterUrl = ref(lockImg);
const scrollbarRef = ref<{ $el?: HTMLElement } | null>(null);
const tocFilter = ref("");

// ============ 计算属性 ============

/** 过滤后的目录（标题 + manualTocSearch 别名，兼容改版前后检索词） */
const filteredToc = computed((): ManualModule[] => {
  const q = tocFilter.value.trim();
  if (!q) return MANUAL_TOC;

  return MANUAL_TOC.filter((mod) => {
    if (manualModuleMatchesQuery(mod.title, mod.anchor, q)) return true;
    return mod.pages.some((p) => manualPageMatchesQuery(p.title, p.anchor, q));
  }).map((mod) => {
    if (manualModuleMatchesQuery(mod.title, mod.anchor, q)) return mod;
    return {
      ...mod,
      pages: mod.pages.filter((p) => manualPageMatchesQuery(p.title, p.anchor, q)),
    };
  });
});

// ============ 方法 ============

/** 获取滚动容器元素 */
function getScrollWrap(): HTMLElement | null {
  const root = scrollbarRef.value?.$el;
  if (!root) return null;
  return root.querySelector<HTMLElement>(".el-scrollbar__wrap");
}

/** 滚动到指定锚点 */
function scrollToAnchor(anchorId: string) {
  const el = document.getElementById(anchorId);
  const wrap = getScrollWrap();
  if (!el) return;

  if (!wrap) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }

  const wrapRect = wrap.getBoundingClientRect();
  const elRect = el.getBoundingClientRect();
  const nextTop = elRect.top - wrapRect.top + wrap.scrollTop - 12;
  wrap.scrollTo({ top: Math.max(0, nextTop), behavior: "smooth" });
}

/** 处理文档内锚点点击 */
function handleAnchorClick(ev: MouseEvent) {
  const a = (ev.target as HTMLElement | null)?.closest("a");
  const href = a?.getAttribute("href");
  if (!href?.startsWith("#")) return;
  ev.preventDefault();
  scrollToAnchor(href.slice(1));
}

const fullEditorRef = ref();
const simpleEditorRef = ref();
const fullActiveTab = ref("preview");
const simpleActiveTab = ref("preview");
const activeCollapse = ref(["basic"]);

/**
 * 简化工具栏配置
 * 只包含基础的编辑功能
 */
const simpleToolbarKeys = [
  "bold",
  "italic",
  "underline",
  "|",
  "bulletedList",
  "numberedList",
  "|",
  "insertLink",
  "insertImage",
  "|",
  "undo",
  "redo",
];

// 完整编辑器内容
const fullEditorHtml = ref(`<h1>🎨 完整工具栏编辑器示例</h1>
<p>这个编辑器包含所有功能，您可以体验丰富的格式编辑功能。</p>

<h2>✨ 文本样式</h2>
<p><strong>这是加粗的文字</strong></p>
<p><em>这是斜体文字</em></p>
<p><u>这是下划线文字</u></p>
<p><span style="color: rgb(194, 79, 74);">这是彩色文字</span></p>

<h2>📝 列表和待办</h2>
<ul>
  <li>无序列表项 1</li>
  <li>无序列表项 2</li>
</ul>

<ol>
  <li>有序列表项 1</li>
  <li>有序列表项 2</li>
</ol>

<ul class="w-e-todo">
  <li class="w-e-todo-item"><input type="checkbox" checked="true" readonly="true" disabled="disabled"><span>已完成的任务</span></li>
  <li class="w-e-todo-item"><input type="checkbox" readonly="true" disabled="disabled"><span>待完成的任务</span></li>
</ul>

<h2>💬 引用和表格</h2>
<blockquote>
  这是一段引用文字，展示引用格式的效果。
</blockquote>

<table style="border-collapse: collapse; width: 100%;" border="1">
  <thead>
    <tr><th>功能</th><th>描述</th></tr>
  </thead>
  <tbody>
    <tr><td>完整工具栏</td><td>包含所有编辑功能</td></tr>
    <tr><td>自定义配置</td><td>支持灵活的工具栏配置</td></tr>
  </tbody>
</table>

<h2>💻 代码块</h2>
<pre><code class="language-javascript">// 完整编辑器支持代码高亮
function createEditor() {
  return new WangEditor({
    container: '#editor',
    toolbar: 'full' // 完整工具栏
  });
}</code></pre>

<p>🔗 <a href="https://www.wangeditor.com/" target="_blank">访问官网了解更多</a></p>`);

// 简化编辑器内容
const simpleEditorHtml = ref(`<h1>✨ 简化工具栏编辑器示例</h1>
<p>这个编辑器只包含基础的编辑功能，界面更加简洁。</p>

<h2>基础文本格式</h2>
<p><strong>加粗文字</strong></p>
<p><em>斜体文字</em></p>
<p><u>下划线文字</u></p>

<h2>列表功能</h2>
<ul>
  <li>无序列表项 1</li>
  <li>无序列表项 2</li>
</ul>

<ol>
  <li>有序列表项 1</li>
  <li>有序列表项 2</li>
</ol>

<h2>链接和图片</h2>
<p>支持插入 <a href="https://www.wangeditor.com/" target="_blank">链接</a> 和图片。</p>

<p>简化版编辑器专注于基础功能，适合简单的内容编辑需求。</p>`);

/**
 * 清空完整编辑器内容
 */
const clearFullEditor = () => {
  fullEditorRef.value?.clear();
  ElMessage.success("完整编辑器已清空");
};

/**
 * 获取完整编辑器内容
 */
const getFullEditorContent = () => {
  const content = fullEditorRef.value?.getHtml();
  console.log("完整编辑器内容:", content);
  ElMessage.success("完整编辑器内容已输出到控制台");
};

/**
 * 设置完整编辑器演示内容
 */
const setFullEditorDemo = () => {
  const demoContent = `<h2>🎉 完整编辑器演示内容</h2>
<p>这是通过方法设置的演示内容，展示完整编辑器的强大功能。</p>
<ul>
  <li>支持丰富的文本格式</li>
  <li>包含表格、代码块等高级功能</li>
  <li>提供完整的编辑体验</li>
</ul>
<table style="border-collapse: collapse; width: 100%;" border="1">
  <tr><th>特性</th><th>状态</th></tr>
  <tr><td>完整工具栏</td><td>✅ 已启用</td></tr>
  <tr><td>高级功能</td><td>✅ 已启用</td></tr>
</table>`;

  fullEditorRef.value?.setHtml(demoContent);
  ElMessage.success("已设置完整编辑器演示内容");
};

/**
 * 清空简化编辑器内容
 */
const clearSimpleEditor = () => {
  simpleEditorRef.value?.clear();
  ElMessage.success("简化编辑器已清空");
};

/**
 * 获取简化编辑器内容
 */
const getSimpleEditorContent = () => {
  const content = simpleEditorRef.value?.getHtml();
  console.log("简化编辑器内容:", content);
  ElMessage.success("简化编辑器内容已输出到控制台");
};

/**
 * 设置简化编辑器演示内容
 */
const setSimpleEditorDemo = () => {
  const demoContent = `<h2>⚡ 简化编辑器演示内容</h2>
<p>这是通过方法设置的演示内容，展示简化编辑器的核心功能。</p>
<ul>
  <li><strong>基础格式</strong>：加粗、斜体、下划线</li>
  <li><em>列表支持</em>：有序和无序列表</li>
  <li><u>媒体插入</u>：链接和图片</li>
</ul>
<ol>
  <li>界面简洁清爽</li>
  <li>功能专注实用</li>
  <li>适合快速编辑</li>
</ol>
<p>🔗 <a href="https://example.com" target="_blank">这是一个链接示例</a></p>`;

  simpleEditorRef.value?.setHtml(demoContent);
  ElMessage.success("已设置简化编辑器演示内容");
};
</script>

<style scoped lang="scss">
.manual-page {
  &__player {
    width: 100%;
  }

  /* Tab 内容区占满宽度，避免内部双栏网格被压窄 */
  &__tabs {
    width: 100%;

    :deep(.el-tab-pane) {
      box-sizing: border-box;
    }
  }
}

.manual-feature-body {
  &__toolbar {
    margin-bottom: 12px;
  }

  &__filter {
    max-width: 320px;
  }

  &__aside {
    height: 100%;
  }

  &__scrollbar {
    min-width: 0;
  }
}

// 侧边导航样式
.manual-nav {
  box-sizing: border-box;
  width: 100%;
  max-height: min(78vh, 880px);
  padding: 10px 12px;
  overflow: auto;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: var(--el-border-radius-base);

  &--empty {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 120px;
  }

  &__module + &__module {
    padding-top: 12px;
    margin-top: 12px;
    border-top: 1px solid var(--el-border-color-lighter);
  }

  &__mod-title {
    display: block;
    width: 100%;
    padding: 4px 0;
    margin: 0;
    font-size: 13px;
    font-weight: 600;
    line-height: 1.4;
    color: var(--el-color-primary);
    text-align: left;
    cursor: pointer;
    background: transparent;
    border: none;

    &:hover {
      text-decoration: underline;
    }
  }

  &__pages {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding-left: 4px;
    margin-top: 6px;
  }

  &__page {
    display: block;
    width: 100%;
    padding: 3px 6px;
    margin: 0;
    font-size: 12px;
    line-height: 1.35;
    color: var(--el-text-color-regular);
    text-align: left;
    cursor: pointer;
    background: transparent;
    border: none;
    border-radius: 4px;

    &:hover {
      color: var(--el-color-primary);
      background: var(--el-fill-color-light);
    }
  }
}

/* 手册正文（避免使用全局类名 container；补齐排版与表格样式） */
.manual-html {
  padding: 16px 18px 28px;
  font-size: 14px;
  line-height: 1.65;
  color: var(--el-text-color-primary);

  &__inner {
    max-width: 100%;
  }

  h1 {
    margin: 0 0 1rem;
    font-size: 1.375rem;
    font-weight: 600;

    small {
      display: block;
      margin-top: 0.4rem;
      font-size: 0.8125rem;
      font-weight: normal;
      line-height: 1.5;
      color: var(--el-text-color-secondary);
    }
  }

  .toc ul {
    padding: 0;
    margin: 0;
    list-style: none;
  }

  .toc li {
    margin-bottom: 0.85rem;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .toc-l2 {
    margin-top: 0.4rem;
    line-height: 1.85;
    overflow-wrap: break-word;
  }

  .module {
    padding-top: 1.5rem;
    margin-top: 2rem;
    border-top: 1px solid var(--el-border-color-lighter);
  }

  /* 紧跟目录卡片后的首个业务模块（前面还有 h1 + ElCard，不能用 :first-of-type） */
  .toc + .module {
    padding-top: 0;
    margin-top: 1.25rem;
    border-top: none;
  }

  .module h2 {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    margin: 0 0 1rem;
    font-size: 1.125rem;
    font-weight: 600;
  }

  .page {
    padding-bottom: 1.25rem;
    margin-bottom: 1.5rem;
    border-bottom: 1px dashed var(--el-border-color-light);

    &:last-child {
      padding-bottom: 0;
      margin-bottom: 0;
      border-bottom: none;
    }
  }

  .page h3 {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: baseline;
    margin: 0 0 0.75rem;
    font-size: 1.0625rem;
    font-weight: 600;

    .path {
      font-weight: normal;
    }
  }

  .section {
    margin-bottom: 0.65rem;
  }

  .feature-list {
    padding-left: 1.2rem;
    margin: 0.35rem 0 0;

    li {
      margin-bottom: 0.4rem;
    }
  }

  .manual-doc-table {
    th,
    td {
      padding: 6px 10px;
      border: 1px solid var(--el-border-color-lighter);
    }

    th {
      font-weight: 500;
      text-align: left;
      background: var(--el-fill-color-light);
    }
  }

  /* 文档内按钮仅为示意，避免误点触发业务样式反馈 */
  .manual-doc-btn {
    pointer-events: none;
  }

  .tag {
    display: inline-block;
    padding: 2px 8px;
    font-size: 12px;
    line-height: 1.4;
    border-radius: 4px;

    &.tag-success {
      color: var(--el-color-success);
      background: var(--el-color-success-light-9);
    }

    &.tag-danger {
      color: var(--el-color-danger);
      background: var(--el-color-danger-light-9);
    }

    &.tag-warning {
      color: var(--el-color-warning);
      background: var(--el-color-warning-light-9);
    }

    &.tag-info {
      color: var(--el-color-info);
      background: var(--el-color-info-light-9);
    }
  }

  .manual-footer-note {
    clear: both;
  }
}

// 响应式适配
@media (width <= 960px) {
  .manual-feature-body__aside {
    width: 100%;
  }

  .manual-nav {
    max-height: 40vh;
  }

  .manual-html {
    padding: 12px 12px 24px;
  }
}

.page-content {
  padding: 20px;
}

.editor-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-buttons {
  display: flex;
  gap: 8px;
}

.preview-card {
  margin-bottom: 24px;
}

.preview-card h3 {
  margin: 0 0 16px;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.content-preview {
  min-height: 200px;
  max-height: 300px;
  padding: 16px;
  overflow-y: auto;
  background-color: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
}

.content-preview :deep(h1),
.content-preview :deep(h2),
.content-preview :deep(h3) {
  margin: 16px 0 8px;
}

.content-preview :deep(p) {
  margin: 8px 0;
  line-height: 1.6;
}

.content-preview :deep(table) {
  margin: 16px 0;
}

.content-preview :deep(table th),
.content-preview :deep(table td) {
  padding: 8px 12px;
}

.content-preview :deep(pre) {
  padding: 12px;
  margin: 16px 0;
  overflow-x: auto;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
}

.content-preview :deep(blockquote) {
  padding-left: 16px;
  margin: 16px 0;
  color: var(--el-text-color-regular);
  border-left: 4px solid var(--el-color-primary);
}

.usage-card :deep(.el-collapse-item__content) {
  padding-bottom: 16px;
}

.usage-card pre {
  padding: 16px;
  margin: 0;
  overflow-x: auto;
  background-color: var(--el-fill-color-light);
  border-radius: 6px;
}

.usage-card pre code {
  font-family: Consolas, Monaco, "Courier New", monospace;
  font-size: 14px;
  line-height: 1.5;
}

.toolbar-explanation h4 {
  margin: 0 0 16px;
  color: var(--el-text-color-primary);
}

.toolbar-explanation h5 {
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.toolbar-explanation ul {
  padding-left: 20px;
  margin: 8px 0 16px;
}

.toolbar-explanation ul li {
  margin: 4px 0;
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.toolbar-explanation .note {
  margin: 8px 0 0;
  font-size: 12px;
  font-style: italic;
  color: var(--el-text-color-placeholder);
}

@media (width <= 768px) {
  .page-content {
    padding: 12px;
  }

  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch !important;
  }

  .header-buttons {
    justify-content: center;
  }

  .preview-card :deep(.el-col) {
    margin-bottom: 16px;
  }
}
</style>
