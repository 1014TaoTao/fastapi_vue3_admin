<template>
  <BaseEdge
    :id="props.id"
    :path="path"
    :marker-end="props.markerEnd"
    :style="props.style"
    :interaction-width="props.interactionWidth ?? 20"
  />
  <EdgeLabelRenderer>
    <div
      class="wf-edge-label nodrag nopan"
      :class="{ 'is-disabled': isDisabled }"
      :style="labelStyle"
      @click.stop="onChipClick"
    >
      <span class="wf-edge-label-text">{{ props.label }}</span>
    </div>
  </EdgeLabelRenderer>
</template>

<script setup lang="ts">
import { computed, type CSSProperties } from "vue";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
  useEdge,
  useVueFlow,
} from "@vue-flow/core";
import type { EdgeProps } from "@vue-flow/core";
import { protocolColor } from "./protocol";

const props = defineProps<EdgeProps>();

const { edge } = useEdge();
const { emits, addSelectedEdges, nodesSelectionActive } = useVueFlow();

// 与官网内置 SmoothStepEdge 一致的路径计算，节点拖动时随坐标变化重算
const smoothPath = computed(() =>
  getSmoothStepPath({
    sourceX: props.sourceX,
    sourceY: props.sourceY,
    sourcePosition: props.sourcePosition,
    targetX: props.targetX,
    targetY: props.targetY,
    targetPosition: props.targetPosition,
  })
);
const path = computed(() => smoothPath.value[0]);
const labelX = computed(() => smoothPath.value[1]);
const labelY = computed(() => smoothPath.value[2]);

const edgeData = computed(() => (props.data ?? {}) as Record<string, any>);
// 禁用的连线标签整体置灰，路径描边已在保存时置灰
const isDisabled = computed(() => edgeData.value.enabled === false);
// 标签配色跟随源节点协议色
const chipColor = computed(() =>
  isDisabled.value ? "#c0c4cc" : protocolColor(edgeData.value.source_protocol as string | undefined)
);

// EdgeLabelRenderer 渲染在画布 HTML 层，标签需内联定位到路径中心并允许点击
const labelStyle = computed<CSSProperties>(() => ({
  position: "absolute",
  transform: `translate(-50%, -50%) translate(${labelX.value}px, ${labelY.value}px)`,
  pointerEvents: "all",
  color: chipColor.value,
  borderColor: chipColor.value,
}));

// 点击标签等价于点击连线：选中连线并触发 edgeClick（与官网内置 EdgeWrapper 行为一致），由画布打开连线配置面板
function onChipClick(event: MouseEvent) {
  nodesSelectionActive.value = false;
  addSelectedEdges([edge]);
  emits.edgeClick({ event, edge });
}
</script>

<style scoped lang="scss">
.wf-edge-label {
  position: absolute;
  display: inline-flex;
  align-items: center;
  max-width: 220px;
  padding: 3px 10px;
  font-size: 11px;
  line-height: 1.2;
  white-space: nowrap;
  cursor: pointer;
  background: var(--el-bg-color);
  border: 1px solid;
  border-radius: 999px;
  box-shadow: 0 1px 4px rgb(0 0 0 / 8%);
  transition:
    box-shadow 0.2s ease,
    background 0.2s ease;

  .wf-edge-label-text {
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &:hover {
    background: var(--el-fill-color-light);
    box-shadow: 0 2px 10px rgb(0 0 0 / 16%);
  }

  &.is-disabled {
    background: var(--el-fill-color-light);
  }
}
</style>
