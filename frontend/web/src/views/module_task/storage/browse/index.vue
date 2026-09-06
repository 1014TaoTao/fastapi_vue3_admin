<!-- 文件浏览：多节点标签 + 上传/下载/新建目录/复制/移动/重命名/分享/删除（源项目风格，对接 /storage/browse） -->
<template>
  <div class="flex h-full">
    <el-card shadow="never" class="browse-card flex min-h-0 flex-1 flex-col">
      <!-- 多节点浏览：el-tabs 左侧标签（状态点+文字靠左、关闭按钮右端对齐，参考 data-transfer/web 已验证实现） -->
      <el-tabs
        v-if="tabs.length"
        v-model="activeId as number"
        tab-position="left"
        class="min-h-0 flex-1"
        :addable="true"
        :editable="true"
        @tab-change="onElTabChange"
        @tab-remove="(name) => closeTab(Number(name))"
        @tab-add="openAddDialog"
      >
        <el-tab-pane
          v-for="tab in orderedTabs"
          :key="tab.nodeId"
          :name="tab.nodeId"
          :closable="!tab.pinned"
          lazy
          class="h-full"
        >
          <template #label>
            <!-- flex-auto 占据弹性空间：状态点+文字靠左，EP 的关闭按钮被推到最右端 -->
            <span
              class="inline-flex min-w-0 flex-auto items-center gap-1.5"
              :title="`${tab.name}（${tab.protocol}${tab.host ? ' ' + tab.host : ''}）${tab.pinned ? '（默认节点，不可关闭）' : ''}`"
            >
              <span class="tab-status shrink-0" :class="`status-${tab.status || 'ok'}`" />
              <span class="truncate max-w-28">{{ tab.name }}</span>
            </span>
          </template>

          <div class="flex h-full flex-col px-4 py-3">
            <template v-if="activeTab">
              <!-- 行1：后退 / 前进 / 路径地址栏 / 刷新 -->
              <div class="mb-2 flex items-center gap-2">
                <el-tooltip content="后退" placement="top">
                  <el-button size="small" :disabled="!canBack" @click="goBack">
                    <el-icon><ArrowLeft /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="前进" placement="top">
                  <el-button size="small" :disabled="!canForward" @click="goForward">
                    <el-icon><ArrowRight /></el-icon>
                  </el-button>
                </el-tooltip>
                <div
                  class="flex h-7 min-w-0 flex-1 cursor-text items-center overflow-hidden rounded border border-(--el-border-color) text-xs text-(--el-text-color-regular) hover:border-(--el-color-primary-light-5)"
                  title="点击协议前缀回到最外层，点击路径段可跳转，点击「存储路径」回到存储根目录，点击空白处可编辑完整路径"
                  @click.self="startEdit"
                >
                  <!-- 前缀：协议（如 ftp://、oss://），点击回到最外层 -->
                  <span
                    class="shrink-0 cursor-pointer whitespace-nowrap bg-(--el-fill-color) px-2 py-1 text-[13px] text-(--el-color-primary) hover:bg-(--el-fill-color-light)"
                    title="点击回到最外层"
                    @click="goOuter"
                    >{{ pathPrefix }}</span
                  >
                  <!-- 中间：桶 + 路径段（非编辑态，el-breadcrumb）/ 输入框（编辑态） -->
                  <div
                    v-if="!editingPath"
                    class="flex min-w-0 flex-1 items-center"
                    @click.self="startEdit"
                  >
                    <el-breadcrumb
                      v-if="!activeTab?.browseBuckets"
                      separator="/"
                      class="path-breadcrumb min-w-0 flex-1 px-2.5"
                    >
                      <el-breadcrumb-item v-if="activeTab?.bucket">
                        <span
                          class="cursor-pointer text-(--el-text-color-secondary) hover:text-(--el-color-primary)"
                          :title="`存储桶：${activeTab.bucket}（点击返回桶根）`"
                          @click="goBucketRoot"
                          >{{ activeTab.bucket }}</span
                        >
                      </el-breadcrumb-item>
                      <!-- 所有路径段均可点击跳转（含最后一段：重新加载当前目录），与已验证实现一致 -->
                      <el-breadcrumb-item v-for="(seg, i) in segments" :key="i">
                        <span
                          class="cursor-pointer whitespace-nowrap"
                          :class="
                            i === segments.length - 1
                              ? 'text-[#909399] hover:text-(--el-color-primary)'
                              : 'text-(--el-text-color-primary) hover:text-(--el-color-primary)'
                          "
                          @click="goToSegment(i)"
                          >{{ seg }}</span
                        >
                      </el-breadcrumb-item>
                    </el-breadcrumb>
                  </div>
                  <el-input
                    v-else
                    ref="pathInputRef"
                    v-model="pathText"
                    size="small"
                    class="min-w-0 flex-1"
                    placeholder="输入完整路径（如 ftp://zhangtao/data），回车跳转"
                    @keyup.enter="commitPathEdit"
                    @keyup.esc="cancelPathEdit"
                    @blur="cancelPathEdit"
                  />
                  <!-- 后缀：存储路径按钮，点击回到存储根目录 -->
                  <span
                    class="shrink-0 cursor-pointer whitespace-nowrap bg-(--el-fill-color) px-2 py-1 text-[13px] text-(--el-color-primary) hover:bg-(--el-fill-color-light)"
                    title="点击回到存储根目录（FTP/SFTP 登录目录、对象存储桶根，不带路径前缀）"
                    @click="goRoot"
                    >存储路径</span
                  >
                </div>
                <el-tooltip content="刷新" placement="top">
                  <el-button size="small" :loading="activeTab.loading" @click="load">
                    <el-icon><Refresh /></el-icon>
                  </el-button>
                </el-tooltip>
              </div>

              <!-- 行2：文件操作 + 搜索（桶列表最外层时隐藏，无文件可操作） -->
              <div
                v-if="!activeTab?.browseBuckets"
                class="mb-2.5 flex items-center justify-between gap-2"
              >
                <div class="flex min-w-0 items-center gap-2">
                  <el-button size="small" type="primary" plain @click="triggerUpload">
                    <el-icon class="mr-1"><Upload /></el-icon>上传
                  </el-button>
                  <el-button size="small" @click="createDir">
                    <el-icon class="mr-1"><FolderAdd /></el-icon>新建目录
                  </el-button>
                  <el-divider direction="vertical" />
                  <el-button size="small" :disabled="!selectedRows.length" @click="batchDownload">
                    <el-icon class="mr-1"><Download /></el-icon>下载
                  </el-button>
                  <el-button
                    size="small"
                    type="primary"
                    :disabled="!selectedRows.length"
                    @click="openTransferDialog"
                  >
                    <el-icon class="mr-1"><Promotion /></el-icon>传输到
                  </el-button>
                  <el-dropdown
                    :disabled="!selectedRows.length"
                    trigger="click"
                    @command="onMoreCommand"
                  >
                    <el-button size="small" :disabled="!selectedRows.length">
                      更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item
                          command="copy"
                          :icon="CopyDocument"
                          :disabled="hasDirSelection"
                          >复制到</el-dropdown-item
                        >
                        <el-dropdown-item
                          command="move"
                          :icon="FolderOpened"
                          :disabled="hasDirSelection"
                          >移动到</el-dropdown-item
                        >
                        <el-dropdown-item command="rename" :icon="EditPen">重命名</el-dropdown-item>
                        <el-dropdown-item v-if="isObjectStorage" command="share" :icon="Share"
                          >分享</el-dropdown-item
                        >
                        <el-dropdown-item command="delete" divided>
                          <el-icon class="mr-1.5 text-(--el-color-danger)"><Delete /></el-icon>
                          <span class="text-(--el-color-danger)">删除</span>
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
                <div class="flex shrink-0 items-center gap-2">
                  <el-input
                    v-model="activeTab.keyword"
                    placeholder="文件名称搜索"
                    clearable
                    size="small"
                    class="w-55"
                    @keyup.enter="load"
                    @clear="load"
                  >
                    <template #prefix
                      ><el-icon><Search /></el-icon
                    ></template>
                  </el-input>
                </div>
              </div>

              <el-alert
                v-if="activeTab.error"
                :title="activeTab.error"
                type="error"
                show-icon
                :closable="false"
                class="mb-2.5"
              />

              <!-- 桶列表（对象存储最外层：账号下全部存储桶） -->
              <el-scrollbar
                v-if="activeTab?.browseBuckets"
                v-loading="activeTab.loading"
                class="min-h-0 flex-1"
              >
                <div class="mb-2 text-[13px] text-[#909399]">存储桶（账号下全部，点击进入）</div>
                <div
                  v-for="b in objectBuckets"
                  :key="b"
                  class="flex cursor-pointer items-center gap-2.5 rounded-lg border border-(--el-border-color) px-3.5 py-3 text-[13px] transition-colors hover:border-(--el-color-primary) hover:bg-(--el-fill-color-light)"
                  :title="`进入存储桶 ${b}`"
                  @click="enterBucket(b)"
                >
                  <el-icon :size="18" color="#e6a23c"><Folder /></el-icon>
                  <span class="min-w-0 truncate font-medium text-(--el-text-color-primary)">{{
                    b
                  }}</span>
                  <el-tag
                    v-if="b === activeTab?.bucket"
                    size="small"
                    type="primary"
                    effect="plain"
                    class="shrink-0"
                    >当前桶</el-tag
                  >
                  <span class="ml-auto shrink-0 text-xs text-[#909399]">点击进入</span>
                </div>
                <el-empty
                  v-if="!activeTab.loading && !objectBuckets.length"
                  description="账号下暂无存储桶"
                  :image-size="72"
                />
              </el-scrollbar>

              <!-- 文件/文件夹列表（支持拖拽上传） -->
              <div
                v-if="!activeTab?.browseBuckets"
                class="min-h-0 flex-1"
                @dragover.prevent
                @drop.prevent="onDrop"
              >
                <FaTable
                  :loading="activeTab.loading"
                  :data="entries"
                  :columns="browseColumns"
                  height="100%"
                  :empty-text="activeTab.error ? '加载失败' : '该目录下没有内容'"
                  @selection-change="onSelectionChange"
                  @sort-change="onSortChange"
                >
                  <template #name="{ row }">
                    <span class="inline-flex items-center gap-1">
                      <el-icon :size="16" :class="row.is_dir ? 'text-[#e6a23c]' : 'text-[#909399]'">
                        <Folder v-if="row.is_dir" />
                        <Document v-else />
                      </el-icon>
                      <span
                        :class="
                          row.is_dir
                            ? 'cursor-pointer font-medium text-[#409eff] hover:underline'
                            : ''
                        "
                        :title="row.name"
                        @click.stop="row.is_dir && enterDir(row.name || '')"
                        >{{ row.name }}</span
                      >
                      <el-icon
                        class="shrink-0 cursor-pointer text-[#c0c4cc] hover:text-(--el-color-primary)"
                        :size="14"
                        title="复制文件名"
                        @click.stop="copyName(row.name)"
                        ><CopyDocument
                      /></el-icon>
                    </span>
                  </template>
                  <template #size="{ row }">
                    <span class="text-xs text-[#909399]">{{
                      row.is_dir ? "—" : formatSize(row.size)
                    }}</span>
                  </template>
                  <template #modified_time="{ row }">
                    <span class="text-xs text-[#909399]">{{ formatTime(row.modified_time) }}</span>
                  </template>
                  <template #operation="{ row }">
                    <div class="inline-flex items-center justify-end gap-1">
                      <el-button
                        link
                        type="primary"
                        size="small"
                        :icon="Download"
                        :title="row.is_dir ? '下载目录（ZIP）' : '下载'"
                        @click.stop="downloadRow(row)"
                      />
                      <el-dropdown
                        size="small"
                        trigger="click"
                        @command="(cmd) => onRowMoreCommand(cmd as string, row)"
                      >
                        <el-button link type="primary" size="small" :icon="MoreFilled" />
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item
                              v-if="isObjectStorage"
                              command="share"
                              :icon="Share"
                              :disabled="row.is_dir"
                              >分享</el-dropdown-item
                            >
                            <el-dropdown-item
                              command="copy"
                              :icon="CopyDocument"
                              :disabled="row.is_dir"
                              >复制到</el-dropdown-item
                            >
                            <el-dropdown-item
                              command="move"
                              :icon="FolderOpened"
                              :disabled="row.is_dir"
                              >移动到</el-dropdown-item
                            >
                            <el-dropdown-item
                              command="rename"
                              :icon="EditPen"
                              :disabled="isObjectStorage && row.is_dir"
                              >重命名</el-dropdown-item
                            >
                            <el-dropdown-item command="delete" divided>
                              <span class="text-(--el-color-danger)">删除</span>
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                  </template>
                </FaTable>
              </div>

              <!-- 状态栏 + 游标分页（桶列表最外层不显示） -->
              <div
                v-if="!activeTab?.browseBuckets"
                class="mt-2.5 flex shrink-0 items-center gap-2 text-[13px] text-[#606266]"
              >
                <span>当前页 {{ entries.length }} 项 · 第 {{ pageNo }} 页</span>
                <span v-if="selectedRows.length" class="text-(--el-color-primary)"
                  >已选中 {{ selectedRows.length }} 项 · 共
                  {{ formatSize(selectedTotalSize) }}</span
                >
                <el-tag v-if="activeTab.keyword" size="small" type="warning" effect="plain"
                  >关键字：{{ activeTab.keyword }}</el-tag
                >
                <!-- 有关键字时本地过滤不分页（全量拉取）；否则游标分页：只拉当前页数据，上一页经游标栈恢复 -->
                <div class="ml-auto flex shrink-0 items-center gap-1.5">
                  <el-button size="small" :disabled="!activeTab.cursors.length" @click="prevPage"
                    >上一页</el-button
                  >
                  <el-button
                    size="small"
                    :disabled="!activeTab.hasNext || !activeTab.nextCursor"
                    @click="nextPage"
                    >下一页</el-button
                  >
                </div>
              </div>
            </template>
            <el-empty
              v-else
              :description="
                nodes.length
                  ? '从左侧打开一个节点开始浏览（可同时打开多个节点）'
                  : '暂无节点，请先在「存储源管理」中创建'
              "
              :image-size="100"
            >
              <el-button v-if="nodes.length" type="primary" @click="openAddDialog">
                <el-icon style="margin-right: 4px"><Plus /></el-icon>打开节点
              </el-button>
            </el-empty>
          </div>
        </el-tab-pane>
      </el-tabs>
      <div v-else class="flex min-h-0 flex-1 items-center justify-center">
        <el-empty
          :description="
            nodes.length
              ? '从左侧打开一个节点开始浏览（可同时打开多个节点）'
              : '暂无节点，请先在「存储源管理」中创建'
          "
          :image-size="120"
        >
          <el-button v-if="nodes.length" type="primary" @click="openAddDialog">
            <el-icon style="margin-right: 4px"><Plus /></el-icon>打开节点
          </el-button>
        </el-empty>
      </div>

      <!-- 打开节点对话框 -->
      <FaDialog
        v-model="addDialogVisible"
        title="打开节点"
        width="420px"
        form-mode="create"
        confirm-text="打开"
        @cancel="addDialogVisible = false"
        @confirm="confirmAdd"
      >
        <el-select v-model="newNodeId" placeholder="选择要打开的节点" filterable class="w-full">
          <el-option
            v-for="n in nodes"
            :key="n.id"
            :value="n.id!"
            :disabled="isTabOpen(n.id)"
            :label="`${n.name}（${n.protocol} ${n.host || '-'}）`"
          />
        </el-select>
      </FaDialog>

      <!-- 分享对话框：对象存储生成预签名链接并回显 -->
      <FaDialog
        v-model="shareDialog.visible"
        title="分享文件"
        width="480px"
        :close-on-click-modal="false"
        @close="shareDialog.visible = false"
      >
        <div class="inline-flex items-center gap-2">
          <span class="text-[13px] text-[#909399]">有效期</span>
          <el-radio-group v-model="shareDialog.expireSeconds">
            <el-radio v-for="opt in shareExpireOptions" :key="opt.value" :value="opt.value">{{
              opt.label
            }}</el-radio>
          </el-radio-group>
        </div>
        <div v-if="shareDialog.url" class="mt-3 inline-flex items-center gap-2">
          <el-input v-model="shareDialog.url" readonly class="min-w-0 flex-1" />
          <el-button type="primary" :icon="CopyDocument" @click="copyShareUrl">复制</el-button>
        </div>
        <p class="mt-2 text-xs text-[#909399]">
          {{
            shareDialog.url
              ? "链接已生成，有效期结束后自动失效"
              : "生成预签名链接，直接指向云存储，过期后链接自动失效"
          }}
        </p>
        <template #footer>
          <el-button @click="shareDialog.visible = false">关闭</el-button>
          <el-button type="primary" :loading="shareDialog.loading" @click="doShare"
            >生成链接</el-button
          >
        </template>
      </FaDialog>

      <!-- 复制/移动目标目录选择器：点击目录逐层进入，以当前目录为目标 -->
      <FaDialog
        v-model="dirPicker.visible"
        :title="dirPicker.mode === 'copy' ? '复制到' : '移动到'"
        width="480px"
        :close-on-click-modal="false"
        form-mode="create"
        :confirm-text="dirPicker.mode === 'copy' ? '复制' : '移动'"
        @cancel="dirPicker.visible = false"
        @confirm="confirmPickDir"
      >
        <div class="mb-2 inline-flex w-full items-center gap-2">
          <span class="text-[13px] text-[#909399]">目标目录</span>
          <div
            class="flex h-7 min-w-0 flex-1 items-center gap-2 rounded px-2 text-xs text-(--el-text-color-regular)"
            :title="dirPicker.dir || '（最外层）'"
          >
            <span class="text-xs text-[#909399]">/</span
            ><span class="truncate">{{ dirPicker.dir || "（最外层）" }}</span>
          </div>
          <el-button link type="primary" size="small" :disabled="!dirPicker.dir" @click="pickerBack"
            >上级</el-button
          >
          <el-button
            link
            size="small"
            :icon="Refresh"
            :disabled="dirPicker.loading"
            @click="loadPickerDirs"
          />
        </div>
        <div class="rounded border border-(--el-border-color)">
          <el-scrollbar max-height="320px">
            <div v-if="dirPicker.loading" class="py-6 text-center text-xs text-[#909399]">
              <el-icon class="is-loading"><Loading /></el-icon>
            </div>
            <template v-else>
              <div
                v-for="e in dirPicker.entries"
                :key="e.name"
                class="flex cursor-pointer items-center gap-2 px-3 py-2 text-[13px] hover:bg-(--el-color-primary-light-9)"
                :title="`进入 ${e.name}`"
                @click="pickerEnter(e.name || '')"
              >
                <el-icon class="shrink-0 text-[#e6a23c]"><Folder /></el-icon>
                <span class="min-w-0 flex-1 truncate">{{ e.name }}</span>
              </div>
              <el-empty
                v-if="!dirPicker.entries.length"
                description="没有子目录"
                :image-size="60"
              />
            </template>
          </el-scrollbar>
        </div>
        <p class="mt-2 text-xs text-[#909399]">
          文件将{{ dirPicker.mode === "copy" ? "复制" : "移动" }}到当前显示的目录
        </p>
      </FaDialog>

      <!-- 传输到：选中文件/目录 → 其他存储源 -->
      <FaDialog v-model="transferVisible" title="传输到其他存储" width="480px" top="12vh">
        <FaForm v-model="transferForm" :items="transferFormItems" label-width="88px" :span="24" />
        <p class="mt-2 text-xs leading-relaxed text-(--el-text-color-secondary)">
          将创建 {{ selectedRows.length }} 个传输任务：选中的文件 /
          目录依次传输到目标存储源的指定目录。
        </p>
        <template #footer>
          <el-button @click="transferVisible = false">取消</el-button>
          <el-button type="primary" :loading="transferSubmitting" @click="confirmTransfer"
            >创建任务</el-button
          >
        </template>
      </FaDialog>

      <!-- 隐藏文件输入框：上传触发 -->
      <input ref="fileInputRef" type="file" class="hidden" multiple @change="onFileChange" />
    </el-card>

    <!-- 上传队列：底部浮动进度卡片（多选/拖拽上传时展示） -->
    <el-card
      v-if="uploadingList.length"
      shadow="always"
      class="upload-queue fixed bottom-5 right-5 z-50 w-80"
      :body-style="{ padding: '8px 12px 12px' }"
    >
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-[13px] font-medium text-(--el-text-color-primary)"
            >上传队列（{{ uploadingCount }}）</span
          >
          <el-button link type="primary" size="small" @click="uploadingList = []">清空</el-button>
        </div>
      </template>
      <el-scrollbar max-height="240px">
        <div v-for="u in uploadingList" :key="u.id" class="mb-2.5 last:mb-0">
          <div class="mb-0.5 flex items-center justify-between gap-2 text-xs">
            <span class="min-w-0 truncate text-(--el-text-color-primary)" :title="u.name">{{
              u.name
            }}</span>
            <el-tag
              size="small"
              effect="plain"
              class="shrink-0"
              :type="u.status === 'failed' ? 'danger' : u.status === 'success' ? 'success' : 'info'"
            >
              {{
                u.status === "uploading"
                  ? `${u.progress}%`
                  : u.status === "success"
                    ? "完成"
                    : "失败"
              }}
            </el-tag>
          </div>
          <el-progress
            :percentage="u.progress"
            :status="u.status === 'failed' ? 'exception' : undefined"
            :stroke-width="4"
          />
        </div>
      </el-scrollbar>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router";
import { saveAs } from "file-saver";
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  CopyDocument,
  Delete,
  Document,
  Download,
  EditPen,
  Folder,
  FolderAdd,
  FolderOpened,
  Loading,
  MoreFilled,
  Plus,
  Promotion,
  Refresh,
  Search,
  Share,
  Upload,
} from "@element-plus/icons-vue";
import StorageAPI, { type StorageObject } from "@/api/module_storage/browse";
import NodeAPI, { type SourceTable } from "@/api/module_storage/node";
import TransferAPI from "@/api/module_storage/transfer";
import type { ColumnOption } from "@/types/component";
import type { FormItem } from "@/components/forms/fa-form/index.vue";

defineOptions({
  name: "WorkflowBrowse",
  inheritAttrs: false,
});

const OBJECT_STORAGE_PROTOCOLS = ["s3", "oss", "obs", "cos"];

interface BrowseTab {
  nodeId: number;
  name: string;
  protocol: string;
  host?: string;
  port?: number;
  bucket?: string;
  base_path?: string;
  region?: string;
  dir: string;
  keyword: string;
  loading: boolean;
  status: "ok" | "error" | "loading" | "idle";
  error: string;
  entries: StorageObject[];
  history: string[];
  historyIndex: number;
  /** 与 history 平行的各目录所属桶（对象存储多桶浏览：后退/前进可跨桶恢复） */
  historyBucket: (string | undefined)[];
  /** 固定标签（本地存储默认节点）：不可关闭 */
  pinned?: boolean;
  /** 对象存储最外层（桶列表模式）：true 时显示账号下全部存储桶，不加载目录列表 */
  browseBuckets?: boolean;
  /** 账号下全部存储桶（对象存储，进入最外层时按需加载） */
  buckets: string[];
  /** 游标分页状态：cursors 为已访问页的起点游标栈（不含首页），翻页经游标只拉当前页数据 */
  pageSize: number;
  cursors: string[];
  nextCursor: string | null;
  hasNext: boolean;
}

const STORAGE_KEY = "workflow_storage_tabs";

// ─── 状态 ──────────────────────────────────────────────────────────
const tabs = ref<BrowseTab[]>([]);
const activeId = ref<number | null>(null);
const nodes = ref<SourceTable[]>([]);
const addDialogVisible = ref(false);
const newNodeId = ref<number | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);
const selectedRows = ref<StorageObject[]>([]);

const activeTab = computed(() => tabs.value.find((t) => t.nodeId === activeId.value) || null);

// 展示顺序：固定标签（本地存储默认节点）始终置顶，其余保持打开顺序
const orderedTabs = computed(() => {
  const arr = [...tabs.value];
  arr.sort((a, b) => Number(b.pinned ?? false) - Number(a.pinned ?? false));
  return arr;
});
// 工作根：文件系统协议（FTP/SFTP/LOCAL）为节点配置的路径前缀，对象存储为桶根。
// 用于复制/移动目标选择器的初始浏览位置（"根目录"点击则跳转存储真根，见 goRoot）。
const workRoot = computed(() => {
  const tab = activeTab.value;
  if (!tab) return "";
  if (tab.bucket) return ""; // 对象存储：桶根即根（面包屑显示"根目录 / {bucket}"）
  return (tab.base_path || "").replace(/^\/+|\/+$/g, ""); // 文件系统协议：path_prefix 为工作根
});
/** 地址栏路径段：按 "/" 拆分当前目录（不含 bucket，bucket 单独展示） */
const segments = computed(() => (activeTab.value?.dir || "").split("/").filter(Boolean));
const isObjectStorage = computed(() =>
  OBJECT_STORAGE_PROTOCOLS.includes((activeTab.value?.protocol || "").toLowerCase())
);
/** 当前页排序（客户端）：对象存储游标分页无全局排序能力，排序作用于当前页/搜索过滤结果 */
const sortKey = ref<"name" | "size" | "modified_time" | "">("");
const sortOrder = ref<"ascending" | "descending" | null>(null);

/** 文件浏览表格列配置：选择列 + 自定义排序，复杂单元格走具名插槽（FaTable） */
const browseColumns: ColumnOption[] = [
  { type: "selection", width: 45 },
  {
    prop: "name",
    label: "名称",
    minWidth: 240,
    showOverflowTooltip: true,
    sortable: "custom",
    useSlot: true,
  },
  { prop: "size", label: "大小", width: 120, sortable: "custom", useSlot: true },
  { prop: "modified_time", label: "修改时间", width: 180, sortable: "custom", useSlot: true },
  {
    prop: "operation",
    label: "操作",
    width: 110,
    fixed: "right",
    align: "center",
    useSlot: true,
  },
];

function onSortChange({ prop, order }: { prop: string | null; order: string | null }) {
  if (!order || !prop) {
    sortKey.value = "";
    sortOrder.value = null;
    return;
  }
  sortKey.value = prop as typeof sortKey.value;
  sortOrder.value = order as "ascending" | "descending";
}

const entries = computed(() => {
  const tab = activeTab.value;
  if (!tab) return [];
  const kw = (tab.keyword || "").trim().toLowerCase();
  let list = tab.entries;
  if (kw) list = list.filter((e) => (e.name || "").toLowerCase().includes(kw));
  if (sortKey.value && sortOrder.value) {
    const dir = sortOrder.value === "ascending" ? 1 : -1;
    const key = sortKey.value;
    list = [...list].sort((a, b) => {
      // 目录始终排在文件之前
      if (a.is_dir !== b.is_dir) return a.is_dir ? -1 : 1;
      if (key === "size") {
        const av = a.size || 0;
        const bv = b.size || 0;
        return (av - bv) * dir;
      }
      const av = (a[key] || "") as string;
      const bv = (b[key] || "") as string;
      return av.localeCompare(bv) * dir;
    });
  }
  return list;
});

/** 选中文件总大小（目录不计） */
const selectedTotalSize = computed(() =>
  selectedRows.value.reduce((sum, r) => sum + (r.is_dir ? 0 : r.size || 0), 0)
);

/** 对象存储最外层桶列表（账号下全部桶，进入最外层时按需加载） */
const objectBuckets = computed(() => activeTab.value?.buckets || []);

/** 选中项含目录：复制/移动接口为文件级实现，目录需走传输任务 */
const hasDirSelection = computed(() => selectedRows.value.some((r) => r.is_dir));

const canBack = computed(() => (activeTab.value?.historyIndex ?? 0) > 0);
const canForward = computed(() => {
  const t = activeTab.value;
  return !!t && t.historyIndex < t.history.length - 1;
});

// ─── 标签管理 ──────────────────────────────────────────────────────
const isTabOpen = (id?: number) => tabs.value.some((t) => t.nodeId === id);

function createTab(node: SourceTable) {
  if (isTabOpen(node.id)) {
    activeId.value = node.id!;
    return;
  }
  // 打开节点默认定位到节点配置的路径前缀（存储真根下的目录），地址栏即显示该路径；点"根目录"可回到真根
  const initialDir = (node.path_prefix || "").replace(/^\/+|\/+$/g, "");
  tabs.value.push({
    nodeId: node.id!,
    name: node.name || "",
    protocol: node.protocol || "",
    host: node.host,
    port: node.port,
    bucket: node.bucket,
    base_path: node.path_prefix,
    region: node.region,
    dir: initialDir,
    keyword: "",
    loading: false,
    status: "idle",
    error: "",
    entries: [],
    history: [initialDir],
    historyIndex: 0,
    historyBucket: [node.bucket],
    // 本地存储节点固定为默认标签，不可关闭
    pinned: node.protocol === "local",
    // 对象存储最外层（桶列表模式）初始关闭
    browseBuckets: false,
    // 账号下全部存储桶：进入最外层时按需加载
    buckets: [],
    pageSize: 20,
    cursors: [],
    nextCursor: null,
    hasNext: false,
  });
  activeId.value = node.id!;
  const rt = tabs.value.find((t) => t.nodeId === node.id)!;
  loadTab(rt);
}

function closeTab(id: number) {
  const t = tabs.value.find((x) => x.nodeId === id);
  if (!t || t.pinned) return; // 固定标签（本地存储默认节点）不可关闭
  const idx = tabs.value.findIndex((x) => x.nodeId === id);
  if (idx < 0) return;
  tabs.value.splice(idx, 1);
  if (activeId.value === id) {
    activeId.value = tabs.value[idx]?.nodeId ?? tabs.value[idx - 1]?.nodeId ?? null;
  }
}

function openAddDialog() {
  newNodeId.value = null;
  addDialogVisible.value = true;
}

function confirmAdd() {
  const node = nodes.value.find((n) => n.id === newNodeId.value);
  if (!node) {
    ElMessage.warning("请选择节点");
    return;
  }
  addDialogVisible.value = false;
  createTab(node);
}

// ─── 目录导航 ──────────────────────────────────────────────────────
/** 当前操作桶（对象存储多桶浏览：非对象存储或无桶不传，后端回退节点配置桶） */
function currentBucket() {
  const tab = activeTab.value;
  return tab?.bucket || undefined;
}

async function loadTab(tab: BrowseTab) {
  // 对象存储最外层（桶列表模式）：加载账号下全部存储桶
  if (tab.browseBuckets) {
    tab.loading = true;
    tab.status = "loading";
    try {
      const { data } = await StorageAPI.listBuckets({ source_id: tab.nodeId });
      tab.buckets = data.data || [];
      tab.status = "ok";
    } finally {
      tab.loading = false;
    }
    return;
  }
  tab.loading = true;
  tab.status = "loading";
  try {
    // 有关键字时本地过滤（全量拉取不传分页）；否则游标分页（只拉当前页）
    const keywordFiltered = (tab.keyword || "").trim().length > 0;
    const { data } = await StorageAPI.listFiles({
      source_id: tab.nodeId,
      prefix: tab.dir || undefined,
      bucket: tab.bucket || undefined,
      ...(keywordFiltered
        ? {}
        : {
            page_size: tab.pageSize,
            ...(tab.cursors.length ? { cursor: tab.cursors[tab.cursors.length - 1] } : {}),
          }),
    });
    const r = data.data;
    if (Array.isArray(r)) {
      tab.entries = r;
      tab.hasNext = false;
      tab.nextCursor = null;
    } else {
      tab.entries = r?.items || [];
      tab.hasNext = !!r?.has_next;
      tab.nextCursor = r?.next_cursor ?? null;
    }
    tab.status = "ok";
  } finally {
    tab.loading = false;
  }
}

function load() {
  const tab = activeTab.value;
  if (tab) loadTab(tab);
}

/** 下一页：当前页游标入栈后经新游标重新请求（只拉下一页数据） */
function nextPage() {
  const tab = activeTab.value;
  if (!tab || !tab.hasNext) return;
  if (tab.nextCursor) tab.cursors.push(tab.nextCursor);
  loadTab(tab);
}

/** 上一页：弹出当前页游标，用上一页起点游标重新请求（首页无游标） */
function prevPage() {
  const tab = activeTab.value;
  if (!tab || !tab.cursors.length) return;
  tab.cursors.pop();
  loadTab(tab);
}

/** 当前页码（cursors 栈长 + 1，首页为第 1 页） */
const pageNo = computed(() => (activeTab.value?.cursors.length || 0) + 1);

// el-tabs 切换：切到未加载的标签时按需加载（记住的目录会跳回原位置）
function onElTabChange() {
  const tab = activeTab.value;
  if (tab && tab.status === "idle" && !tab.loading) loadTab(tab);
}

function navTo(dir: string) {
  const tab = activeTab.value;
  if (!tab) return;
  tab.history = tab.history.slice(0, tab.historyIndex + 1);
  tab.historyBucket = tab.historyBucket.slice(0, tab.historyIndex + 1);
  tab.history.push(dir);
  tab.historyBucket.push(tab.bucket); // 记录该目录所属桶，后退/前进可跨桶恢复
  tab.historyIndex = tab.history.length - 1;
  tab.dir = dir;
  tab.cursors = []; // 进入新目录重置到第一页
  tab.nextCursor = null;
  tab.hasNext = false;
  loadTab(tab);
}

// 地址栏协议前缀（如 ftp://）：点击回到最外层（FTP 类=登录目录真根，对象存储=桶根）
const pathPrefix = computed(() => {
  const tab = activeTab.value;
  return tab ? `${(tab.protocol || "").toLowerCase()}://` : "";
});

// 地址栏完整路径（编辑态输入框默认值）：协议://桶/目录；桶列表模式下仅协议://
function pathDisplay() {
  const tab = activeTab.value;
  if (!tab) return "";
  if (isObjectStorage.value && tab.browseBuckets) return pathPrefix.value;
  const head = tab.bucket ? `${tab.bucket}/` : "";
  return pathPrefix.value + head + (tab.dir || "");
}

function goRoot() {
  const tab = activeTab.value;
  if (!tab) return;
  // 对象存储：先退出桶列表最外层，再回到存储真根（桶根）
  if (isObjectStorage.value) tab.browseBuckets = false;
  // 点击「存储路径」：回到存储真根（FTP/SFTP 登录目录、LOCAL host 根、对象存储桶根），不带 path_prefix
  navTo("");
}

/** 协议前缀点击：进入最外层（对象存储=桶列表模式，FTP 类=登录目录真根） */
function goOuter() {
  const tab = activeTab.value;
  if (!tab) return;
  if (isObjectStorage.value) {
    if (tab.browseBuckets) return; // 已在桶列表
    tab.browseBuckets = true;
    tab.dir = "";
    loadTab(tab);
    return;
  }
  navTo("");
}

/** 从桶列表（最外层）点击桶：切换当前操作桶并进入桶内根 */
function enterBucket(name: string) {
  const tab = activeTab.value;
  if (!tab || !name) return;
  tab.bucket = name;
  tab.browseBuckets = false;
  navTo("");
}

/** 点击存储桶返回桶根（对象存储：根即桶） */
function goBucketRoot() {
  if (activeTab.value?.bucket) navTo("");
}

function goToSegment(i: number) {
  navTo(segments.value.slice(0, i + 1).join("/"));
}

function enterDir(name: string) {
  const tab = activeTab.value;
  if (!tab) return;
  // 桶列表（最外层）点击桶：切换当前桶并进入桶内根
  if (tab.browseBuckets) {
    enterBucket(name);
    return;
  }
  const d = tab.dir || "";
  navTo(d ? `${d}/${name}` : name);
}

function goBack() {
  const t = activeTab.value;
  if (!t || !canBack.value) return;
  t.historyIndex -= 1;
  t.dir = t.history[t.historyIndex] ?? "";
  t.bucket = t.historyBucket[t.historyIndex]; // 恢复该目录所属桶
  loadTab(t);
}

function goForward() {
  const t = activeTab.value;
  if (!t || !canForward.value) return;
  t.historyIndex += 1;
  t.dir = t.history[t.historyIndex] ?? "";
  t.bucket = t.historyBucket[t.historyIndex]; // 恢复该目录所属桶
  loadTab(t);
}

// 地址栏编辑
const editingPath = ref(false);
const pathText = ref("");
const pathInputRef = ref<{ focus: () => void } | null>(null);

function startEdit() {
  editingPath.value = true;
  pathText.value = pathDisplay();
  nextTick(() => visibleRef(pathInputRef.value)?.focus());
}

function commitPathEdit() {
  editingPath.value = false;
  const tab = activeTab.value;
  if (!tab) return;
  // 去掉协议前缀与前导斜杠
  let p = String(pathText.value || "")
    .replace(/^[a-z0-9]+:\/\//i, "")
    .replace(/^\/+|\/+$/g, "");
  if (isObjectStorage.value) {
    const segs = p.split("/").filter(Boolean);
    if (segs.length) {
      const first = segs[0];
      // 第一段即桶名：与当前桶相同则剥除；是账号其他桶则切换当前桶
      if (first === tab.bucket) {
        segs.shift();
      } else if (first && objectBuckets.value.includes(first)) {
        tab.bucket = first;
        segs.shift();
      }
    }
    p = segs.join("/");
    // 提交非空路径即退出桶列表模式；仅输入协议:// 时保持桶列表（最外层）
    if (p) tab.browseBuckets = false;
  } else if (tab.bucket) {
    p = p.replace(new RegExp(`^${tab.bucket}/?`), "");
  }
  navTo(p.split("/").filter(Boolean).join("/"));
}

function cancelPathEdit() {
  editingPath.value = false;
}

// ─── 表格交互 ──────────────────────────────────────────────────────
function onSelectionChange(rows: StorageObject[]) {
  selectedRows.value = rows;
}

/**
 * el-tab-pane 处于 v-for 中，其内部模板引用（如 pathInputRef）会退化为数组：
 * 取其中可见（激活标签页）的实例，其余 display:none 的 pane 实例忽略。
 */
function visibleRef<T>(r: T | T[] | null): T | null {
  if (Array.isArray(r)) {
    return (
      ((r as unknown[]).find(
        (el) => el && (el as { $el?: HTMLElement }).$el?.offsetParent !== null
      ) as T | undefined) ?? null
    );
  }
  return r;
}

function remotePathOf(name: string): string {
  const dir = activeTab.value?.dir || "";
  return dir ? `${dir}/${name}` : name;
}

function pathOf(row: StorageObject): string {
  return row.key || remotePathOf(row.name || "");
}

// ─── 文件操作：上传（多选 + 队列进度 + 拖拽） ─────────────────────
interface UploadItem {
  id: number;
  name: string;
  progress: number;
  status: "uploading" | "success" | "failed";
}

const uploadingList = ref<UploadItem[]>([]);
let uploadSeq = 0;

const uploadingCount = computed(
  () => uploadingList.value.filter((u) => u.status === "uploading").length
);

function triggerUpload() {
  fileInputRef.value?.click();
}

/** 批量上传：逐个加入队列并发上传，底部浮动条展示进度 */
function uploadFiles(files: File[]) {
  const tab = activeTab.value;
  if (!tab) return;
  const valid = files.filter((f) => f.size > 0);
  if (!valid.length) {
    ElMessage.warning("请选择文件");
    return;
  }
  for (const file of valid) {
    const item: UploadItem = { id: ++uploadSeq, name: file.name, progress: 0, status: "uploading" };
    uploadingList.value.push(item);
    void doUpload(file, item, tab);
  }
}

async function doUpload(file: File, item: UploadItem, tab: BrowseTab) {
  const formData = new FormData();
  formData.append("file", file);
  if (tab.nodeId) formData.append("source_id", String(tab.nodeId));
  if (tab.dir) formData.append("remote_path", `${tab.dir}/`);
  if (tab.bucket) formData.append("bucket", tab.bucket);
  try {
    await StorageAPI.uploadFile(formData, (p) => {
      item.progress = p;
    });
    item.progress = 100;
    item.status = "success";
    ElMessage.success(`「${file.name}」上传成功`);
    load();
  } catch {
    item.status = "failed";
    // 失败原因由全局拦截器提示
  }
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement;
  const files = input.files ? Array.from(input.files) : [];
  input.value = "";
  uploadFiles(files);
}

function onDrop(e: DragEvent) {
  const files = e.dataTransfer?.files ? Array.from(e.dataTransfer.files) : [];
  if (files.length) uploadFiles(files);
}

// ─── 文件操作：新建目录 ────────────────────────────────────────────
async function createDir() {
  const tab = activeTab.value;
  if (!tab) return;
  const { value } = await ElMessageBox.prompt("请输入目录名称", "新建目录", {
    inputPattern: /\S+/,
    inputErrorMessage: "名称不能为空",
  }).catch(() => ({ value: undefined as string | undefined }));
  if (!value) return;
  await StorageAPI.mkdir({
    source_id: tab.nodeId,
    remote_dir: remotePathOf(value),
    bucket: currentBucket(),
  });
  ElMessage.success("创建成功");
  load();
}

// ─── 文件操作：下载 ────────────────────────────────────────────────
function filenameFromDisposition(header: string | undefined, fallback: string): string {
  if (!header) return fallback;
  const match =
    header.match(/filename\*=UTF-8''([^;]+)/i) || header.match(/filename="?([^";]+)"?/i);
  if (match && match[1]) {
    return decodeURIComponent(match[1]);
  }
  return fallback;
}

async function downloadRemote(row: StorageObject): Promise<boolean> {
  const tab = activeTab.value;
  if (!tab) return false;
  const isDir = !!row.is_dir;
  const res = isDir
    ? await StorageAPI.downloadDir({
        source_id: tab.nodeId,
        remote_path: pathOf(row),
        bucket: currentBucket(),
      })
    : await StorageAPI.downloadFile({
        source_id: tab.nodeId,
        remote_path: pathOf(row),
        bucket: currentBucket(),
      });
  const blob = res.data as Blob;
  const fallback = isDir ? `${row.name || "download"}.zip` : row.name || "download";
  const name = filenameFromDisposition(
    res.headers?.["content-disposition"] as string | undefined,
    fallback
  );
  saveAs(blob, name);
  return true;
}

async function downloadRow(row: StorageObject) {
  if (await downloadRemote(row)) ElMessage.success("已开始下载");
}

async function batchDownload() {
  if (!selectedRows.value.length) return;
  const rows = [...selectedRows.value];
  let ok = 0;
  for (const row of rows) {
    if (await downloadRemote(row)) ok += 1;
  }
  if (ok) ElMessage.success(`已下载 ${ok} 个文件/目录`);
}

// ─── 传输到：选中文件/目录 → 其他存储源建传输任务 ─────────────────
const transferVisible = ref(false);
const transferSubmitting = ref(false);

/** 目标存储源选项：排除当前浏览节点 */
const transferTargetNodes = computed(() =>
  nodes.value.filter((n) => n.id !== activeTab.value?.nodeId)
);

/** 传输到表单（FaForm v-model） */
const transferForm = ref({ target_id: null as number | null, target_path: "" });
const transferFormItems = computed<FormItem[]>(() => [
  {
    key: "target_id",
    label: "目标存储源",
    type: "select",
    props: {
      placeholder: "选择目标存储源",
      filterable: true,
      style: "width: 100%",
      options: transferTargetNodes.value.map((n) => ({
        label: `${n.name}（${n.protocol}${n.host ? " " + n.host : ""}）`,
        value: n.id!,
      })),
    },
  },
  {
    key: "target_path",
    label: "目标目录",
    type: "input",
    props: { placeholder: "如 /backup；留空传到目标根目录", clearable: true },
  },
]);

function openTransferDialog() {
  if (!selectedRows.value.length || !activeTab.value) return;
  transferForm.value = { target_id: null, target_path: "" };
  transferVisible.value = true;
}

async function confirmTransfer() {
  const tab = activeTab.value;
  const targetId = transferForm.value.target_id;
  if (!tab || !targetId) {
    ElMessage.warning("请选择目标存储源");
    return;
  }
  const targetDir = (transferForm.value.target_path || "").trim().replace(/^\/+|\/+$/g, "");
  const rows = [...selectedRows.value];
  transferSubmitting.value = true;
  try {
    let ok = 0;
    for (const row of rows) {
      const name = row.name || "传输任务";
      const tgtPath = targetDir ? `${targetDir}/${name}` : name;
      await TransferAPI.createTask({
        name,
        task_type: "parallel",
        source_type: "remote",
        source_id: tab.nodeId,
        source_path: pathOf(row),
        targets: [{ target_id: targetId, target_path: tgtPath }],
      });
      ok += 1;
    }
    ElMessage.success(`已创建 ${ok} 个传输任务`);
    transferVisible.value = false;
  } finally {
    transferSubmitting.value = false;
  }
}

// ─── 文件操作：重命名 ──────────────────────────────────────────────
async function renameRow(row: StorageObject) {
  const tab = activeTab.value;
  if (!tab) return;
  const { value } = await ElMessageBox.prompt("请输入新名称", "重命名", {
    inputValue: row.name,
    inputPattern: /\S+/,
    inputErrorMessage: "名称不能为空",
  }).catch(() => ({ value: undefined as string | undefined }));
  if (!value || value === row.name) return;
  await StorageAPI.renameFile({
    source_id: tab.nodeId,
    source_path: pathOf(row),
    target_path: remotePathOf(value),
    bucket: currentBucket(),
  });
  ElMessage.success("重命名成功");
  load();
}

// ─── 文件操作：删除 ────────────────────────────────────────────────
async function confirmAction(message: string): Promise<boolean> {
  try {
    await ElMessageBox.confirm(message, "提示", {
      type: "warning",
      confirmButtonText: "确定",
      cancelButtonText: "取消",
    });
    return true;
  } catch {
    return false;
  }
}

async function deleteRow(row: StorageObject) {
  const tab = activeTab.value;
  if (!tab) return;
  if (!(await confirmAction(`确定删除「${row.name}」吗？`))) return;
  await StorageAPI.deleteFile({
    source_id: tab.nodeId,
    remote_path: pathOf(row),
    bucket: currentBucket(),
  });
  ElMessage.success("删除成功");
  load();
}

async function batchDelete() {
  if (!selectedRows.value.length) return;
  const rows = [...selectedRows.value];
  if (!(await confirmAction(`确定删除选中的 ${rows.length} 项吗？`))) return;
  let ok = 0;
  for (const row of rows) {
    await StorageAPI.deleteFile({
      source_id: activeTab.value?.nodeId,
      remote_path: pathOf(row),
      bucket: currentBucket(),
    });
    ok += 1;
  }
  ElMessage.success(`已删除 ${ok} 项`);
  load();
}

// ─── 文件操作：复制 / 移动 ─────────────────────────────────────────
const dirPicker = reactive({
  visible: false,
  loading: false,
  mode: "copy" as "copy" | "move",
  rows: [] as StorageObject[],
  dir: "",
  entries: [] as StorageObject[],
});

function copyMove(rows: StorageObject[], mode: "copy" | "move") {
  const tab = activeTab.value;
  if (!tab || !rows.length) return;
  dirPicker.mode = mode;
  dirPicker.rows = [...rows];
  // 目标选择器从当前工作根开始浏览（与主地址栏语义一致），可回退到更上层
  dirPicker.dir = workRoot.value;
  dirPicker.visible = true;
  loadPickerDirs();
}

async function loadPickerDirs() {
  const tab = activeTab.value;
  if (!tab) return;
  dirPicker.loading = true;
  try {
    const { data } = await StorageAPI.listFiles({
      source_id: tab.nodeId,
      prefix: dirPicker.dir || undefined,
      bucket: currentBucket(),
    });
    const r = data.data;
    dirPicker.entries = (Array.isArray(r) ? r : r?.items || []).filter((e) => e.is_dir);
  } finally {
    dirPicker.loading = false;
  }
}

function pickerEnter(name: string) {
  const dir = dirPicker.dir;
  dirPicker.dir = dir ? `${dir}/${name}` : name;
  loadPickerDirs();
}

function pickerBack() {
  const dir = dirPicker.dir;
  if (!dir) return;
  const i = dir.lastIndexOf("/");
  dirPicker.dir = i >= 0 ? dir.slice(0, i) : "";
  loadPickerDirs();
}

async function confirmPickDir() {
  const tab = activeTab.value;
  if (!tab) return;
  const isCopy = dirPicker.mode === "copy";
  const targetDir = dirPicker.dir;
  if (tab.dir === targetDir) {
    ElMessage.warning("目标目录不能与当前目录相同");
    return;
  }
  const rows = [...dirPicker.rows];
  dirPicker.visible = false;
  let ok = 0;
  for (const row of rows) {
    await StorageAPI.copyFile({
      source_id: tab.nodeId,
      source_path: pathOf(row),
      target_id: tab.nodeId,
      target_path: targetDir ? `${targetDir}/${row.name || ""}` : row.name || "",
      move: !isCopy,
      bucket: currentBucket(),
    });
    ok += 1;
  }
  ElMessage.success(`${isCopy ? "复制" : "移动"}成功 ${ok} 项`);
  load();
}

function onMoreCommand(cmd: string) {
  if (!selectedRows.value.length) return;
  const rows = [...selectedRows.value];
  const row = rows[0];
  if (cmd === "copy") return copyMove(rows, "copy");
  if (cmd === "move") return copyMove(rows, "move");
  if (cmd === "rename") return row ? renameRow(row) : undefined;
  if (cmd === "share") return row ? shareRow(row) : undefined;
  if (cmd === "delete") return batchDelete();
}

function onRowMoreCommand(cmd: string, row: StorageObject) {
  if (cmd === "copy") return copyMove([row], "copy");
  if (cmd === "move") return copyMove([row], "move");
  if (cmd === "rename") return renameRow(row);
  if (cmd === "delete") return deleteRow(row);
}

// ─── 文件操作：分享（对象存储预签名链接） ───────────────────────────
const shareExpireOptions = [
  { label: "1小时", value: 3600 },
  { label: "1天", value: 86400 },
  { label: "3天", value: 259200 },
  { label: "7天", value: 604800 },
];
const shareDialog = reactive({
  visible: false,
  loading: false,
  expireSeconds: 86400,
  url: "",
  target: null as StorageObject | null,
});

function shareRow(row: StorageObject) {
  shareDialog.target = row;
  shareDialog.expireSeconds = 86400;
  shareDialog.url = "";
  shareDialog.visible = true;
}

async function doShare() {
  const tab = activeTab.value;
  if (!tab || !shareDialog.target) return;
  shareDialog.loading = true;
  try {
    const { data } = await StorageAPI.shareFile({
      source_id: tab.nodeId,
      remote_path: pathOf(shareDialog.target),
      expire: shareDialog.expireSeconds,
      bucket: currentBucket(),
    });
    shareDialog.url = data.data || "";
    if (!shareDialog.url) ElMessage.info("该存储源不支持分享链接");
  } finally {
    shareDialog.loading = false;
  }
}

// 复制分享链接 / 文件名
async function copyShareUrl() {
  try {
    await navigator.clipboard.writeText(shareDialog.url);
    ElMessage.success("已复制到剪贴板");
  } catch {
    ElMessage.error("复制失败，请手动选择复制");
  }
}

async function copyName(name: string) {
  try {
    await navigator.clipboard.writeText(name);
    ElMessage.success("已复制文件名");
  } catch {
    ElMessage.error("复制失败");
  }
}

// ─── 工具函数 ──────────────────────────────────────────────────────
function formatSize(size?: number | null) {
  if (size === null || size === undefined) return "—";
  const n = Number(size);
  if (!Number.isFinite(n) || n < 0) return "—";
  if (n === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  const i = Math.min(Math.floor(Math.log(n) / Math.log(1024)), units.length - 1);
  return (n / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1) + " " + units[i];
}

function formatTime(mtime?: string | null) {
  if (!mtime) return "—";
  const d = new Date(mtime);
  if (Number.isNaN(d.getTime())) return String(mtime);
  const pad = (x: number) => String(x).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

// ─── 节点加载与标签持久化 ───────────────────────────────────────────
const route = useRoute();

async function loadNodes() {
  const { data } = await NodeAPI.listNode({});
  nodes.value = data.data;
}

function persist() {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        activeId: activeId.value,
        tabs: tabs.value.map((t) => ({
          nodeId: t.nodeId,
          name: t.name,
          protocol: t.protocol,
          host: t.host,
          port: t.port,
          bucket: t.bucket,
          base_path: t.base_path,
          region: t.region,
          dir: t.dir,
          keyword: t.keyword,
          pinned: t.pinned,
          historyBucket: t.historyBucket,
        })),
      })
    );
  } catch {
    // 忽略持久化失败
  }
}

function restoreTabs() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    if (!Array.isArray(saved.tabs)) return;
    tabs.value = saved.tabs
      .filter((t: Partial<BrowseTab>) => t.nodeId)
      .map((t: Partial<BrowseTab>) => ({
        nodeId: t.nodeId!,
        name: t.name || "",
        protocol: t.protocol || "",
        host: t.host,
        port: t.port,
        bucket: t.bucket,
        base_path: t.base_path,
        region: t.region,
        dir: t.dir || "",
        keyword: t.keyword || "",
        loading: false,
        status: "idle" as const,
        error: "",
        entries: [],
        history: t.dir ? ["", t.dir] : [""],
        historyIndex: t.dir ? 1 : 0,
        historyBucket: (t.dir ? ["", t.dir] : [""]).map(() => t.bucket),
        pinned: t.pinned,
        buckets: t.buckets || [],
        pageSize: t.pageSize || 20,
        cursors: [],
        nextCursor: null,
        hasNext: false,
      }));
    if (saved.activeId && tabs.value.some((t) => t.nodeId === saved.activeId)) {
      activeId.value = saved.activeId;
    }
  } catch {
    // 忽略恢复失败
  }
}

// 丢弃已不存在的节点标签，并为旧缓存补齐节点信息
function filterMissing() {
  const ids = new Set(nodes.value.map((n) => n.id));
  tabs.value = tabs.value.filter((t) => ids.has(t.nodeId));
  if (activeId.value != null && !tabs.value.some((t) => t.nodeId === activeId.value)) {
    activeId.value = tabs.value[0]?.nodeId ?? null;
  }
  for (const t of tabs.value) {
    const n = nodes.value.find((x) => x.id === t.nodeId);
    if (!n) continue;
    if (t.port == null) t.port = n.port;
    if (!t.bucket) t.bucket = n.bucket;
    if (!t.base_path) t.base_path = n.path_prefix;
    if (!t.region) t.region = n.region;
    if (!t.pinned) t.pinned = n.protocol === "local";
    // 旧缓存根目录（未定位）：打开默认进入节点配置的路径前缀，地址栏显示该路径
    if (!t.dir && n.path_prefix) {
      const p = String(n.path_prefix).replace(/^\/+|\/+$/g, "");
      if (p) {
        t.dir = p;
        t.history = ["", p];
        t.historyIndex = 1;
        t.historyBucket = ["", p].map(() => t.bucket);
      }
    }
  }
}

// 从存储源管理「打开」跳转进入时，自动打开对应节点
async function openFromQuery() {
  const sid = Number(route.query.source_id);
  if (!sid) return;
  if (isTabOpen(sid)) {
    activeId.value = sid;
    return;
  }
  const node = nodes.value.find((n) => n.id === sid) || (await NodeAPI.detailNode(sid)).data.data;
  if (node) createTab(node);
}

watch([tabs, activeId], () => persist(), { deep: true });

onMounted(async () => {
  await loadNodes();
  restoreTabs();
  filterMissing();
  // 默认固定打开本地存储节点（不可关闭）：无任何标签时兜底
  const localNode = nodes.value.find((n) => n.protocol === "local") || nodes.value[0];
  if (localNode && localNode.id != null && !isTabOpen(localNode.id)) createTab(localNode);
  const active = activeTab.value;
  if (active && active.status === "idle") loadTab(active);
  await openFromQuery();
});
</script>

<style scoped>
/* 布局 hack：卡片 body 撑满剩余高度（其余布局均由 Tailwind 原子类承担） */
.browse-card :deep(.el-card__body) {
  display: flex;
  flex: 1;
  min-height: 0;
  padding: 0;
}

/* 路径地址栏面包屑：压缩字号/分隔符间距，与 h-7 地址栏垂直对齐 */
.path-breadcrumb {
  --el-breadcrumb-font-size: 12px;
  --el-breadcrumb-separator-margin: 0 2px;
}

.path-breadcrumb :deep(.el-breadcrumb__separator) {
  color: #c0c4cc;
}

.path-breadcrumb :deep(.el-breadcrumb__inner),
.path-breadcrumb :deep(.el-breadcrumb__inner a) {
  font-weight: 400;
  line-height: 24px;
}

/* 上传队列浮动卡片：压缩 header 内边距，保持紧凑 */
.upload-queue :deep(.el-card__header) {
  padding: 8px 12px;
}

/* 高度链闭合：左侧标签布局下内容区撑满，使表格独立滚动、状态栏/分页固定底部 */
.browse-card :deep(.el-tabs) {
  height: 100%;
}

.browse-card :deep(.el-tabs--left .el-tabs__content) {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.browse-card :deep(.el-tabs--left .el-tabs__content > .el-tab-pane) {
  height: 100%;
}

/* 节点状态点（颜色 + 闪烁动画，原子类无法表达） */
.tab-status {
  display: inline-block;
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  margin-right: 6px;
  border-radius: 50%;
}

.status-ok {
  background: var(--el-color-success);
}

.status-error {
  background: var(--el-color-danger);
}

.status-loading {
  background: var(--el-color-warning);
  animation: status-blink 1s infinite;
}

.status-idle {
  background: var(--el-color-info);
}
@keyframes status-blink {
  50% {
    opacity: 0.3;
  }
}
</style>
