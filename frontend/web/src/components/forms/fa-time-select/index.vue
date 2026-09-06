<template>
  <div class="fa-time-select">
    <ElTimeSelect
      v-model="timeValue"
      :start="start"
      :end="end"
      :step="step"
      :min-time="minTime"
      :max-time="maxTime"
      :placeholder="placeholder"
      :clearable="clearable"
      :disabled="disabled"
      v-bind="$attrs"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

defineOptions({
  name: "FaTimeSelect",
});

interface FaTimeSelectProps {
  modelValue?: string;
  start?: string;
  end?: string;
  step?: string;
  minTime?: string;
  maxTime?: string;
  placeholder?: string;
  clearable?: boolean;
  disabled?: boolean;
}

const props = withDefaults(defineProps<FaTimeSelectProps>(), {
  modelValue: "",
  start: "09:00",
  end: "18:00",
  step: "00:30",
  placeholder: "请选择时间",
  clearable: true,
  disabled: false,
});

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
  (e: "change", value: string): void;
}>();

const timeValue = computed({
  get: () => props.modelValue,
  set: (value: string) => {
    emit("update:modelValue", value);
    emit("change", value);
  },
});
</script>
