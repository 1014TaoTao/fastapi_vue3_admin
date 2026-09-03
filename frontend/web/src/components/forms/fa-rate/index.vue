<template>
  <div class="fa-rate">
    <ElRate
      v-model="rateValue"
      :max="max"
      :disabled="disabled"
      :allow-half="allowHalf"
      :show-text="showText"
      :show-score="showScore"
      :texts="texts"
      :colors="colors"
      :low-threshold="lowThreshold"
      :high-threshold="highThreshold"
      v-bind="$attrs"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

defineOptions({
  name: "FaRate",
});

interface Props {
  modelValue?: number;
  max?: number;
  disabled?: boolean;
  allowHalf?: boolean;
  showText?: boolean;
  showScore?: boolean;
  texts?: string[];
  colors?: string[];
  lowThreshold?: number;
  highThreshold?: number;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: 0,
  max: 5,
  disabled: false,
  allowHalf: false,
  showText: false,
  showScore: false,
  texts: () => [],
  colors: () => [],
  lowThreshold: 2,
  highThreshold: 4,
});

const emit = defineEmits<{
  "update:modelValue": [value: number];
  change: [value: number];
}>();

const rateValue = computed({
  get: () => props.modelValue,
  set: (val: number) => {
    emit("update:modelValue", val);
    emit("change", val);
  },
});
</script>
