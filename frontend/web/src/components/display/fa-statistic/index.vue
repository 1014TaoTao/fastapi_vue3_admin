<template>
  <ElStatistic
    :value="displayValue"
    :title="title"
    :precision="precision"
    :value-style="valueStyle"
  >
    <template #title>
      <slot name="title">{{ title }}</slot>
    </template>
    <template #prefix>
      <slot name="prefix">{{ prefix }}</slot>
    </template>
    <template #suffix>
      <slot name="suffix">{{ suffix }}</slot>
    </template>
    <template v-if="$slots.default" #default>
      <slot />
    </template>
  </ElStatistic>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";

defineOptions({ name: "FaStatistic" });

interface Props {
  /** 数值 */
  value: number;
  /** 标题 */
  title?: string;
  /** 数值前缀 */
  prefix?: string;
  /** 数值后缀 */
  suffix?: string;
  /** 小数位数 */
  precision?: number;
  /** 字体颜色 */
  color?: string;
  /** 是否启用数字滚动动画 */
  animated?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  title: "",
  prefix: "",
  suffix: "",
  precision: 0,
  color: "",
  animated: false,
});

const displayValue = ref(props.animated ? 0 : props.value);

const valueStyle = computed(() => {
  const style: Record<string, any> = {};
  if (props.color) {
    style.color = props.color;
  }
  return style;
});

watch(
  () => props.value,
  (newVal) => {
    if (!props.animated) {
      displayValue.value = newVal;
      return;
    }
    const start = displayValue.value;
    const duration = 800;
    const startTime = performance.now();

    function step(currentTime: number) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      displayValue.value = start + (newVal - start) * progress;

      if (progress < 1) {
        requestAnimationFrame(step);
      }
    }

    requestAnimationFrame(step);
  }
);
</script>
