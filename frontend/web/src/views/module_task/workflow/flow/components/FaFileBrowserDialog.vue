<template>
  <FaDialog
    :model-value="visible"
    :title="title || `文件浏览 · ${sourceName || '存储源'}`"
    width="720px"
    top="8vh"
    append-to-body
    @close="handleClose"
  >
    <div class="mb-3 flex items-center gap-2">
      <ElBreadcrumb separator="/" class="flex-1 min-w-0">
        <ElBreadcrumbItem>
          <a
            class="cursor-pointer text-(--el-color-primary)"
            @click="navTo('')"
            title="回到存储根目录（登录目录/桶根）"
            >根目录</a
          >
        </ElBreadcrumbItem>
        <ElBreadcrumbItem v-if="props.bucket">
          <a
            class="cursor-pointer text-(--el-text-color-secondary) hover:text-(--el-color-primary)"
            title="点击返回桶根"
            @click="dir !== '' && navTo('')"
            >{{ props.bucket }}</a
          >
        </ElBreadcrumbItem>
        <ElBreadcrumbItem v-for="(seg, i) in segments" :key="i">
          <a
            class="cursor-pointer text-(--el-color-primary)"
            @click="navTo(segments.slice(0, i + 1).join('/'))"
          >
            {{ seg }}
          </a>
        </ElBreadcrumbItem>
      </ElBreadcrumb>
      <ElButton :icon="Refresh" size="small" circle @click="load" />
    </div>

    <div
      v-loading="loading"
      class="file-browser-body border border-(--el-border-color-lighter) rounded-lg overflow-hidden"
      style="height: 380px"
    >
      <ElEmpty
        v-if="!loading && entries.length === 0"
        description="该目录下没有文件"
        :image-size="60"
      />
      <div v-else class="flex flex-col h-full">
        <div
          v-for="(item, idx) in entries"
          :key="idx"
          class="flex items-center gap-2 px-3 py-2 text-[13px] border-b border-(--el-border-color-lighter) last:border-0 cursor-pointer hover:bg-(--el-fill-color-light) transition-colors"
          :class="{ 'font-semibold': item.is_dir }"
          @dblclick="item.is_dir && navTo(joinPath(dir, item.name))"
        >
          <ElIcon :size="16" :color="item.is_dir ? '#e6a23c' : '#909399'">
            <Folder v-if="item.is_dir" />
            <Document v-else />
          </ElIcon>
          <span class="flex-1 min-w-0 truncate" :title="item.name">{{ item.name }}</span>
          <span v-if="!item.is_dir && item.size" class="text-xs text-(--el-text-color-secondary)">{{
            formatSize(item.size)
          }}</span>
          <span v-if="item.modified_time" class="text-xs text-(--el-text-color-secondary)">{{
            formatTime(item.modified_time)
          }}</span>
          <span v-if="item.is_dir" class="text-xs text-(--el-text-color-secondary)">目录</span>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="text-xs text-(--el-text-color-secondary) mr-auto">
        共 {{ entries.length }} 项 · 双击目录进入
      </div>
      <ElButton v-if="selectable" type="primary" @click="handleSelect">选择当前目录</ElButton>
      <ElButton @click="handleClose">关闭</ElButton>
    </template>
  </FaDialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";

import { Document, Folder, Refresh } from "@element-plus/icons-vue";
import StorageAPI, { type StorageObject } from "@/api/module_task/workflow/storage";

interface Props {
  visible?: boolean;
  sourceId?: number | null;
  sourceName?: string;
  /** 自定义标题（默认「文件浏览 · 存储源名」） */
  title?: string;
  /** 打开时默认定位的目录（节点配置的路径前缀），空为存储真根 */
  initPath?: string;
  /** 存储桶（对象存储）：面包屑中作为存储根标识展示，不参与路径导航 */
  bucket?: string;
  /** 工作根：文件系统协议为 path_prefix，对象存储为空（桶根）；点击"根目录"回到该位置 */
  rootPath?: string;
  /** 选择模式：显示"选择当前目录"按钮，点击后 emit select(当前目录) 并关闭 */
  selectable?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  sourceId: null,
  sourceName: "",
  title: "",
  initPath: "",
  bucket: "",
  rootPath: "",
  selectable: false,
});

const emit = defineEmits(["update:visible", "select"]);

const entries = ref<StorageObject[]>([]);
const dir = ref("");
const loading = ref(false);

const segments = computed(() => dir.value.split("/").filter(Boolean));

function joinPath(base: string, name?: string) {
  if (!name) return base;
  return base ? `${base}/${name}` : name;
}

async function load() {
  if (!props.sourceId) return;
  loading.value = true;
  try {
    const { data } = await StorageAPI.listFiles({
      source_id: props.sourceId,
      prefix: dir.value || undefined,
    });
    const r = data.data;
    entries.value = Array.isArray(r) ? r : r?.items || [];
  } finally {
    loading.value = false;
  }
}

function navTo(path: string) {
  dir.value = path;
  load();
}

function formatTime(mtime?: string) {
  if (!mtime) return "";
  const d = new Date(mtime);
  if (Number.isNaN(d.getTime())) return mtime;
  const pad = (x: number) => String(x).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function formatSize(size?: number) {
  if (size == null || size <= 0) return "";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let n = size;
  let i = 0;
  while (n >= 1024 && i < units.length - 1) {
    n /= 1024;
    i += 1;
  }
  return `${n.toFixed(n >= 100 || i === 0 ? 0 : 1)} ${units[i]}`;
}

function handleClose() {
  emit("update:visible", false);
}

function handleSelect() {
  emit("select", dir.value);
  emit("update:visible", false);
}

watch(
  () => props.visible,
  (val) => {
    if (val) {
      dir.value = props.initPath || "";
      load();
    }
  }
);

watch(
  () => props.sourceId,
  () => {
    if (props.visible) {
      dir.value = props.initPath || "";
      load();
    }
  }
);
</script>
