<template>
  <div class="flex flex-col h-full">
    <div
      class="flex items-center justify-between px-4 py-3 font-semibold border-b border-(--el-border-color-lighter)"
    >
      <span>节点信息</span>
      <ElButton type="text" class="p-1" @click="handleClose">
        <ElIcon><Close /></ElIcon>
      </ElButton>
    </div>

    <ElScrollbar class="flex-1" view-class="p-4">
      <div
        class="mb-3 flex items-center gap-2.5 rounded-lg border border-(--el-border-color-lighter) bg-(--el-fill-color-light) px-3 py-2.5"
      >
        <ElIcon :size="20" :color="color"><Folder /></ElIcon>
        <div class="flex flex-col min-w-0 leading-tight">
          <span class="truncate text-xs font-semibold text-(--el-text-color-primary)">{{
            node?.data?.label || "存储节点"
          }}</span>
          <span class="mt-0.5 text-[11px] text-(--el-text-color-secondary)">{{
            protocolText
          }}</span>
        </div>
      </div>

      <ElDescriptions :column="1" size="small" border label-width="88px" class="node-info-desc">
        <ElDescriptionsItem label="存储源ID">{{ node?.data?.source_id ?? "—" }}</ElDescriptionsItem>
        <ElDescriptionsItem label="协议">{{ protocolLabel }}</ElDescriptionsItem>
        <ElDescriptionsItem label="地址">
          <span class="break-all">{{ hostText }}</span>
        </ElDescriptionsItem>
      </ElDescriptions>

      <div class="mt-4">
        <div class="mb-1.5 text-xs font-medium text-(--el-text-color-primary)">默认源目录</div>
        <div class="flex items-center gap-1">
          <ElInput
            v-model="sourcePath"
            size="small"
            clearable
            class="flex-1"
            :placeholder="pathHint"
            @keyup.enter="handleSave"
          />
          <ElButton :icon="FolderOpened" size="small" title="选择目录" @click="openPicker" />
        </div>
        <p class="mt-1.5 text-[11px] leading-relaxed text-(--el-text-color-secondary)">
          执行流程时自动回显，可修改；留空则执行时手动选择源文件 / 目录。
        </p>
      </div>

      <div class="mt-3 text-xs leading-relaxed text-(--el-text-color-secondary)">
        <p>· 拖拽连线可定义「从哪里传输到哪里」</p>
        <p>· 点击连线配置目标路径与传输方式</p>
        <p>· 双击节点或点击下方按钮可浏览该存储源文件</p>
      </div>

      <div class="flex gap-2 pt-4 border-t border-(--el-border-color-lighter)">
        <ElButton type="primary" plain size="small" class="flex-1" @click="handleViewFiles">
          <ElIcon class="mr-1"><FolderOpened /></ElIcon>
          查看文件
        </ElButton>
        <ElButton type="primary" size="small" class="flex-1" @click="handleSave">保存</ElButton>
        <ElButton type="danger" size="small" class="flex-1" @click="handleDelete"
          >删除节点</ElButton
        >
      </div>
    </ElScrollbar>

    <FaFileBrowserDialog
      v-model:visible="browserVisible"
      :source-id="browserSourceId"
      :source-name="browserSourceName"
      :init-path="browserInitPath"
      :bucket="browserBucket"
      :root-path="browserRootPath"
      selectable
      @select="onSourceSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { ElMessage } from "element-plus";
import { Close, Folder, FolderOpened } from "@element-plus/icons-vue";
import NodeAPI from "@/api/module_task/workflow/node";
import {
  protocolColor,
  protocolLabel as getProtocolLabel,
  protocolText as getProtocolText,
} from "./protocol";
import FaFileBrowserDialog from "./FaFileBrowserDialog.vue";

interface Props {
  node?: Record<string, any>;
}

const props = withDefaults(defineProps<Props>(), {
  node: () => ({}),
});

const emit = defineEmits(["close", "delete", "view-files", "save"]);

const color = computed(() => protocolColor(props.node?.data?.protocol as string | undefined));

const protocol = computed(() => (props.node?.data?.protocol || "").toLowerCase());

const objectStorage = ["s3", "obs", "oss", "cos"];

// 地址：对象存储取接入点 endpoint，文件系统协议取主机地址 host
const address = computed(() => {
  const v = objectStorage.includes(protocol.value)
    ? props.node?.data?.endpoint
    : props.node?.data?.host;
  return (v as string | undefined) || "";
});

const protocolLabel = computed(() => getProtocolLabel(protocol.value));

const protocolText = computed(() =>
  getProtocolText(props.node?.data?.protocol as string | undefined, address.value || undefined)
);

const hostText = computed(() => address.value || "—");

const sourcePath = ref((props.node?.data?.source_path as string) || "");

watch(
  () => props.node,
  (n) => {
    sourcePath.value = (n?.data?.source_path as string) || "";
  },
  { deep: true }
);

const pathHint = computed(() => {
  if (objectStorage.includes(protocol.value)) return "Key 前缀，如 dir/sub（目录以 / 结尾）";
  if (protocol.value === "local") return "本地目录，如 /data/source";
  return "目录，如 /source";
});

// ── 默认源目录选择 ────────────────────────────────────────────────
const browserVisible = ref(false);
const browserSourceId = ref<number | null>(null);
const browserSourceName = ref("");
const browserInitPath = ref("");
const browserBucket = ref("");
const browserRootPath = ref("");

async function openPicker() {
  const sid = props.node?.data?.source_id as number | undefined;
  if (sid == null) {
    ElMessage.warning("节点未关联存储源，无法选择目录");
    return;
  }
  const current = (sourcePath.value || "").trim().replace(/^\/+|\/+$/g, "");
  const { data } = await NodeAPI.detailNode(sid);
  const src = data.data;
  const nodeRoot = (src?.path_prefix || "").replace(/^\/+|\/+$/g, "");
  const bucket = src?.bucket || "";
  const rootPath = bucket ? "" : nodeRoot;
  const init = current || nodeRoot;
  browserSourceId.value = sid;
  browserSourceName.value = props.node?.data?.label || "";
  browserInitPath.value = init;
  browserBucket.value = bucket;
  browserRootPath.value = rootPath;
  browserVisible.value = true;
}

function onSourceSelected(path: string) {
  const p = path || "";
  sourcePath.value = p ? (p.endsWith("/") ? p : `${p}/`) : "";
}

function handleSave() {
  emit("save", { source_path: sourcePath.value.trim() });
}

function handleClose() {
  emit("close");
}

function handleDelete() {
  emit("delete");
}

function handleViewFiles() {
  emit("view-files");
}
</script>
