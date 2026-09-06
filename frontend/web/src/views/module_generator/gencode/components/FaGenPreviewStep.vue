<template>
  <ElRow v-loading="previewLoading" element-loading-text="正在加载预览…">
    <ElCol v-if="!previewLoading && isTreeEmpty" :span="24">
      <ElEmpty>
        <template #description>
          <p class="mb-1 font-medium">暂无预览文件</p>
          <p class="m-0 mb-2 text-xs leading-normal text-(--el-text-color-secondary)">
            若刚保存过仍为空，可将「预览范围」改为「全部」；或返回上一步检查字段与主子表后重新进入。
          </p>
        </template>
      </ElEmpty>
    </ElCol>
    <template v-else>
      <ElCol :span="24" class="mb-2">
        <div class="flex items-center gap-3">
          <span class="text-sm text-[#909399]">预览范围</span>
          <ElRadioGroup v-model="previewScope" size="small">
            <ElRadioButton value="all">全部</ElRadioButton>
            <ElRadioButton value="frontend">前端</ElRadioButton>
            <ElRadioButton value="backend">后端</ElRadioButton>
          </ElRadioGroup>
          <span class="ml-3 text-sm text-[#909399]">类型</span>
          <ElCheckboxGroup v-model="previewTypes" size="small">
            <ElCheckboxButton v-for="t in previewTypeOptions" :key="t" :value="t">
              {{ t }}
            </ElCheckboxButton>
          </ElCheckboxGroup>
        </div>
      </ElCol>
      <ElCol :span="6">
        <ElScrollbar max-height="72vh">
          <ElTree
            :data="filteredTreeData"
            default-expand-all
            highlight-current
            @node-click="onTreeNodeClick"
          >
            <template #default="{ data }">
              <!-- 优先使用 resolveLocalIconUrl（@utils/icons），无对应 svg 时再走 Iconify -->
              <img
                v-if="previewIconAssetUrl(data.label)"
                :src="previewIconAssetUrl(data.label)"
                class="inline-block h-[1em] w-[1em] shrink-0 align-middle object-contain"
                alt=""
                aria-hidden="true"
              />
              <FaSvgIcon
                v-else
                :icon="resolveIconForFaSvgIcon(getFileTreeNodeIcon(data.label))"
                class="inline shrink-0 text-base"
              />
              <span class="ml-1" :title="data.full_path || data.label">
                {{ data.label }}
              </span>
            </template>
          </ElTree>
        </ElScrollbar>
      </ElCol>
      <ElCol :span="18">
        <ElScrollbar max-height="72vh">
          <div class="absolute z-36 right-5 top-2">
            <ElLink type="primary" @click="emit('copy-code')">
              <ElIcon>
                <CopyDocument />
              </ElIcon>
              复制代码
            </ElLink>
          </div>

          <Codemirror
            ref="cmRef"
            v-model:value="code"
            :options="cmOptions"
            border
            :readonly="true"
            height="100%"
            width="100%"
          />
        </ElScrollbar>
      </ElCol>
    </template>
  </ElRow>
</template>

<script setup lang="ts">
import "codemirror/mode/javascript/javascript.js";
import "codemirror/mode/python/python.js";
import "codemirror/mode/htmlmixed/htmlmixed.js";
import "codemirror/theme/dracula.css";
import Codemirror from "codemirror-editor-vue3";
import type { EditorConfiguration } from "codemirror";
import type { CmComponentRef } from "codemirror-editor-vue3";
import { resolveLocalIconUrl, resolveIconForFaSvgIcon } from "@utils";
import { CopyDocument } from "@element-plus/icons-vue";
import { GENCODE_CM_KEY } from "../gencodeInjectionKeys";
import type { TreeNode } from "../types";

defineOptions({ name: "GenPreviewStep" });

const previewScope = defineModel<"all" | "frontend" | "backend">("previewScope", {
  required: true,
});
const previewTypes = defineModel<string[]>("previewTypes", { required: true });

const props = defineProps<{
  previewLoading: boolean;
  previewTypeOptions: string[];
  filteredTreeData: TreeNode[];
  cmOptions: EditorConfiguration;
}>();

const isTreeEmpty = computed(() => !props.filteredTreeData || props.filteredTreeData.length === 0);

const code = defineModel<string>("code", { required: true });

interface Emits {
  "file-click": [data: TreeNode];
  "copy-code": [];
}

const emit = defineEmits<Emits>();

const cmRef = ref<CmComponentRef>();
const injected = inject(GENCODE_CM_KEY, undefined);

watch(
  cmRef,
  (v) => {
    if (injected) injected.value = v;
  },
  { immediate: true }
);

onUnmounted(() => {
  if (injected) injected.value = undefined;
});

function onTreeNodeClick(data: TreeNode) {
  emit("file-click", data);
}

/** 与 `src/assets/images/svg/*.svg` 基名对齐，供本地文件优先展示 */
function getFileTreeNodeIcon(label: string): string {
  const baseName = label.split(/[/\\]/).pop() ?? label;
  const lower = baseName.toLowerCase();
  if (lower.endsWith(".py")) return "python";
  if (lower.endsWith(".vue")) return "vue";
  if (lower.endsWith(".tsx") || lower.endsWith(".ts")) return "typescript";
  if (
    lower.endsWith(".jsx") ||
    lower.endsWith(".js") ||
    lower.endsWith(".mjs") ||
    lower.endsWith(".cjs")
  )
    return "item-js";
  if (lower.endsWith(".json")) return "file-json";
  if (lower.endsWith(".html") || lower.endsWith(".htm")) return "file-html";
  if (
    lower.endsWith(".css") ||
    lower.endsWith(".scss") ||
    lower.endsWith(".sass") ||
    lower.endsWith(".less")
  )
    return "file-css";
  if (lower.endsWith(".sql")) return "sql";
  if (lower.endsWith(".java")) return "java";
  if (lower.endsWith(".xml")) return "xml";
  if (lower.endsWith(".md")) return "document";
  if (lower.endsWith(".yaml") || lower.endsWith(".yml")) return "file-json";
  if (/\.(png|jpe?g|gif|webp|svg|ico)$/i.test(lower)) return "file-image";
  if (/\.(zip|rar|7z)$/i.test(lower)) return "file-zip";
  if (/\.(pdf)$/i.test(lower)) return "file-pdf";
  return "file";
}

/** 若 assets/images/svg 存在对应 svg 则返回 Vite 资源 URL，否则 undefined → 回退 Iconify */
function previewIconAssetUrl(label: string): string | undefined {
  return resolveLocalIconUrl(getFileTreeNodeIcon(label));
}
</script>
