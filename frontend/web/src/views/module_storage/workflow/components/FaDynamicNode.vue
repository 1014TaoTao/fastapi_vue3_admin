<template>
  <div
    class="wf-node"
    :class="{ 'is-selected': selected }"
    @mouseenter="showHandles = true"
    @mouseleave="showHandles = false"
  >
    <div class="node-body" :style="{ '--node-color': color }">
      <span class="node-flag" :style="{ background: color }" />
      <ElIcon :size="16" :color="color"><Folder /></ElIcon>
      <div class="node-text">
        <span
          ref="labelRef"
          class="node-label"
          :title="isLabelOverflow ? nodeData.label || '未命名存储' : ''"
          >{{ nodeData.label || "未命名存储" }}</span
        >
        <span class="node-category">{{ categoryLabel }}</span>
        <span v-if="endpoint" class="node-endpoint" :title="endpoint">{{ endpoint }}</span>
        <span v-if="sourcePath" class="node-path" :title="`默认源目录：${sourcePath}`">{{
          sourcePath
        }}</span>
      </div>
      <span
        v-if="totalConnections > 0"
        class="node-connections"
        :title="`入站连接 ${incomingCount} 条，出站连接 ${outgoingCount} 条`"
        >入 {{ incomingCount }} · 出 {{ outgoingCount }}</span
      >
      <ElTooltip content="双击查看该存储源文件" placement="top" :show-after="300">
        <span class="node-files" :style="{ color }"><FolderOpened :size="13" /></span>
      </ElTooltip>
    </div>
    <Handle
      id="target-top"
      type="target"
      :position="Position.Top"
      :class="{ 'handle-visible': showHandles }"
      :style="{ background: color }"
    />
    <Handle
      id="target-left"
      type="target"
      :position="Position.Left"
      :class="{ 'handle-visible': showHandles }"
      :style="{ background: color }"
    />
    <Handle
      id="source-right"
      type="source"
      :position="Position.Right"
      :class="{ 'handle-visible': showHandles }"
      :style="{ background: color }"
    />
    <Handle
      id="source-bottom"
      type="source"
      :position="Position.Bottom"
      :class="{ 'handle-visible': showHandles }"
      :style="{ background: color }"
    />
  </div>
</template>

<script lang="ts" setup>
import { Handle, Position, useNodeConnections } from "@vue-flow/core";
import { ElIcon, ElTooltip } from "element-plus";
import { Folder, FolderOpened } from "@element-plus/icons-vue";
import { protocolColor, protocolLabel } from "./protocol";

interface Props {
  id?: string;
  data?: Record<string, any>;
  selected?: boolean;
}

const props = withDefaults(defineProps<Props>(), {});

const showHandles = ref(false);

const nodeData = computed(() => props.data ?? {});

const color = computed(() => protocolColor(nodeData.value.protocol as string | undefined));

const isObjectStorage = computed(() =>
  ["s3", "oss", "obs", "cos"].includes((nodeData.value.protocol || "").toLowerCase())
);

// 协议 · 主机/桶：对象存储显示桶名，其余协议显示主机地址
const categoryLabel = computed(() => {
  const label = protocolLabel(nodeData.value.protocol);
  const sub = isObjectStorage.value
    ? nodeData.value.bucket || nodeData.value.host
    : nodeData.value.host;
  return sub ? `${label} · ${sub}` : label;
});

// 对象存储地址（endpoint），供节点回显
const endpoint = computed(() => nodeData.value.endpoint || "");

// 默认源目录：流程节点上配置的优先，未配置则回退存储源的路径前缀
const sourcePath = computed(() => nodeData.value.source_path || nodeData.value.path_prefix || "");

// 节点连接数：入站（目标）与出站（源）分别统计，供画布上快速了解拓扑
const incomingConnections = useNodeConnections({
  nodeId: () => props.id ?? "",
  handleType: "target",
});
const outgoingConnections = useNodeConnections({
  nodeId: () => props.id ?? "",
  handleType: "source",
});
const incomingCount = computed(() => incomingConnections.value.length);
const outgoingCount = computed(() => outgoingConnections.value.length);
const totalConnections = computed(() => incomingCount.value + outgoingCount.value);

// 节点名称超长省略时显示悬停提示全名
const labelRef = ref<HTMLElement | null>(null);
const isLabelOverflow = ref(false);
let labelObserver: ResizeObserver | null = null;

function checkLabelOverflow() {
  const el = labelRef.value;
  isLabelOverflow.value = !!el && el.scrollWidth > el.clientWidth;
}

onMounted(() => {
  checkLabelOverflow();
  if (labelRef.value) {
    labelObserver = new ResizeObserver(checkLabelOverflow);
    labelObserver.observe(labelRef.value);
  }
});

onUnmounted(() => {
  labelObserver?.disconnect();
  labelObserver = null;
});
</script>

<style scoped lang="scss">
.wf-node {
  position: relative;
  cursor: pointer;

  .node-body {
    position: relative;
    display: flex;
    gap: 8px;
    align-items: center;
    min-width: 168px;
    padding: 10px 14px;
    overflow: hidden;
    background: var(--el-bg-color);
    border: 1.5px solid color-mix(in srgb, var(--node-color) 45%, #d1d5db);
    border-radius: 10px;
    box-shadow: 0 1px 4px rgb(0 0 0 / 6%);
    transition:
      box-shadow 0.2s ease,
      transform 0.2s ease,
      border-color 0.2s ease;

    &:hover {
      box-shadow: 0 6px 16px rgb(0 0 0 / 14%);
      transform: translateY(-1px);
    }
  }

  .node-flag {
    position: absolute;
    top: 50%;
    left: 0;
    width: 4px;
    height: 70%;
    border-radius: 0 4px 4px 0;
    transform: translateY(-50%);
  }

  .node-text {
    display: flex;
    flex-direction: column;
    min-width: 0;
    line-height: 1.3;

    .node-label {
      display: inline-block;
      max-width: 150px;
      overflow: hidden;
      text-overflow: ellipsis;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.3px;
      white-space: nowrap;
    }

    .node-category {
      max-width: 130px;
      overflow: hidden;
      text-overflow: ellipsis;
      font-size: 10px;
      color: var(--el-text-color-secondary);
      white-space: nowrap;
    }

    .node-path {
      display: inline-block;
      max-width: 140px;
      overflow: hidden;
      text-overflow: ellipsis;
      font-size: 10px;
      line-height: 1.3;
      color: var(--el-color-primary);
      white-space: nowrap;
    }

    .node-endpoint {
      display: inline-block;
      max-width: 140px;
      overflow: hidden;
      text-overflow: ellipsis;
      font-size: 10px;
      line-height: 1.3;
      color: var(--el-text-color-secondary);
      white-space: nowrap;
    }
  }

  .node-connections {
    display: inline-flex;
    flex-shrink: 0;
    align-items: center;
    padding: 1px 6px;
    margin-left: 6px;
    font-size: 10px;
    line-height: 1.4;
    color: var(--el-text-color-secondary);
    white-space: nowrap;
    background: var(--el-fill-color-light);
    border-radius: 999px;
  }

  .node-files {
    display: inline-flex;
    align-items: center;
    padding: 2px;
    margin-left: auto;
    border-radius: 4px;
    transition: background 0.2s ease;

    &:hover {
      background: color-mix(in srgb, var(--node-color) 12%, transparent);
    }
  }

  &.is-selected .node-body {
    border-color: var(--node-color);
    box-shadow:
      0 0 0 2px color-mix(in srgb, var(--node-color) 22%, transparent),
      0 6px 18px rgb(0 0 0 / 14%);
  }
}

.vue-flow__handle {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.vue-flow__handle.handle-visible,
.vue-flow__handle.vue-flow__handle-connecting,
.vue-flow__handle.vue-flow__handle-valid {
  opacity: 1;
}
</style>
