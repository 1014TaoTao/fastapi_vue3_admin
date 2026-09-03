<template>
  <div class="flex flex-col h-full">
    <div
      class="flex items-center justify-between px-4 py-3 font-semibold border-b border-(--el-border-color-lighter)"
    >
      <span>传输配置</span>
      <ElButton type="text" class="p-1" @click="handleClose">
        <ElIcon><Close /></ElIcon>
      </ElButton>
    </div>

    <ElScrollbar class="flex-1" view-class="p-4">
      <div
        class="mb-3 flex items-center gap-2 rounded-lg border border-(--el-border-color-lighter) bg-(--el-fill-color-light) px-3 py-2 text-xs text-(--el-text-color-regular)"
      >
        <ElIcon :size="14" :color="edgeColor"><Share /></ElIcon>
        <span class="min-w-0 truncate">{{ sourceLabel }} → {{ targetLabel }}</span>
      </div>

      <FaForm
        v-model="formData"
        :items="edgeFormItems"
        label-width="80px"
        size="small"
        label-position="right"
        :span="24"
        :gutter="12"
        :show-reset="false"
        :show-submit="false"
        class="panel-art-form"
      >
        <template #color>
          <ElColorPicker v-model="formData.color" />
        </template>
      </FaForm>

      <div
        class="mt-3 rounded-lg border border-dashed border-(--el-border-color) bg-(--el-fill-color-lighter) px-3 py-2 text-xs text-(--el-text-color-secondary)"
      >
        连线只定义传输方式；禁用后执行流程将跳过该连线。源文件 /
        目录在执行流程时选择（节点可配置默认源目录），目标目录由目标节点的默认源目录决定。
      </div>

      <div
        class="flex gap-2 pt-4 border-t border-(--el-border-color-lighter) [&_.el-button]:flex-1"
      >
        <ElButton type="primary" size="small" @click="handleSave">保存</ElButton>
        <ElButton type="danger" size="small" @click="handleDelete">删除连线</ElButton>
      </div>
    </ElScrollbar>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";

import { Close, Share } from "@element-plus/icons-vue";
import FaForm from "@/components/forms/fa-form/index.vue";

interface Props {
  edge?: Record<string, any>;
}

const props = withDefaults(defineProps<Props>(), {
  edge: () => ({}),
});

const emit = defineEmits(["close", "save", "delete"]);

const formData = ref({
  transfer_mode: (props.edge?.data?.transfer_mode as string) || "stream",
  multipart_part_size: (props.edge?.data?.multipart_part_size as number) ?? 50,
  multipart_concurrency: (props.edge?.data?.multipart_concurrency as number) ?? 6,
  enabled: props.edge?.data?.enabled !== false,
  color: props.edge?.style?.stroke || "#409eff",
  animated: props.edge?.animated !== false,
});

const edgeColor = computed(() => formData.value.color);

const sourceLabel = computed(() => props.edge?.data?.source_label || "源节点");
const targetLabel = computed(() => props.edge?.data?.target_label || "目标节点");

const edgeFormItems = computed(() => [
  {
    label: "启用连线",
    key: "enabled",
    type: "switch",
    span: 24,
    props: {
      activeText: "启用",
      inactiveText: "禁用",
      activeValue: true,
      inactiveValue: false,
    },
  },
  {
    label: "传输方式",
    key: "transfer_mode",
    type: "radiogroup",
    span: 24,
    props: {
      options: [
        { label: "流式传输", value: "stream" },
        { label: "分片传输", value: "multipart" },
      ],
    },
  },
  {
    label: "分片大小",
    key: "multipart_part_size",
    type: "number",
    span: 24,
    hidden: formData.value.transfer_mode !== "multipart",
    props: { min: 5, max: 5000, step: 1, placeholder: "MB，默认 50" },
  },
  {
    label: "并发线程",
    key: "multipart_concurrency",
    type: "number",
    span: 24,
    hidden: formData.value.transfer_mode !== "multipart",
    props: { min: 1, max: 64, step: 1, placeholder: "默认 6" },
  },
  {
    label: "连线颜色",
    key: "color",
    type: "input",
    span: 24,
    placeholder: "",
  },
  {
    label: "启用动画",
    key: "animated",
    type: "switch",
    span: 24,
  },
]);

watch(
  () => props.edge,
  (newEdge) => {
    if (newEdge) {
      formData.value = {
        transfer_mode: (newEdge.data?.transfer_mode as string) || "stream",
        multipart_part_size: (newEdge.data?.multipart_part_size as number) ?? 50,
        multipart_concurrency: (newEdge.data?.multipart_concurrency as number) ?? 6,
        enabled: newEdge.data?.enabled !== false,
        color: newEdge.style?.stroke || "#409eff",
        animated: newEdge.animated !== false,
      };
    }
  },
  { deep: true }
);

function handleClose() {
  emit("close");
}

function handleSave() {
  emit("save", {
    animated: formData.value.animated,
    style: { stroke: formData.value.color },
    data: {
      enabled: formData.value.enabled,
      transfer_mode: formData.value.transfer_mode,
      multipart_part_size:
        formData.value.transfer_mode === "multipart"
          ? formData.value.multipart_part_size
          : undefined,
      multipart_concurrency:
        formData.value.transfer_mode === "multipart"
          ? formData.value.multipart_concurrency
          : undefined,
    },
  });
}

function handleDelete() {
  emit("delete");
}
</script>

<style scoped lang="scss">
.panel-art-form :deep(.el-row > .el-col:last-child) {
  display: none;
}

.panel-art-form :deep(.el-form-item__content) {
  max-width: 100%;
}

.panel-art-form :deep(section) {
  padding: 0;
}
</style>
