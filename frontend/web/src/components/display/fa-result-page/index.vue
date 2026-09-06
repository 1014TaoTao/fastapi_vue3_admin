<template>
  <div class="page-content box-border px-20! py-3.5 text-center max-md:px-5!">
    <ElResult :icon="resultIcon" :title="title" :sub-title="message">
      <template #icon>
        <FaSvgIcon class="size-14!" :icon="iconCode" />
      </template>
      <template #extra>
        <slot name="buttons"></slot>
      </template>
    </ElResult>
    <div
      class="res mt-7.5 rounded bg-g-200/80 dark:bg-g-300/40 px-7.5 py-5.5 text-left max-md:px-7.5 max-md:py-2.5 [&_p]:flex [&_p]:items-center [&_p]:py-2 [&_p]:text-sm [&_p]:text-[#808695] [&_p_i]:mr-1.5"
    >
      <slot name="content"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

defineOptions({ name: "FaResultPage" });

defineSlots<{
  default?: () => void;
  content?: () => void;
  buttons?: () => void;
}>();

interface Props {
  /** 成功/失败 */
  type: "success" | "fail";
  /** 标题 */
  title: string;
  /** 消息 */
  message: string;
  /** 图标 */
  iconCode: string;
}

const props = withDefaults(defineProps<Props>(), {
  type: "success",
  title: "",
  message: "",
  iconCode: "",
});

const resultIcon = computed(() => (props.type === "success" ? "success" : "error"));
</script>
