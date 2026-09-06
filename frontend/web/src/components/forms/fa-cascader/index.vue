<template>
  <div class="fa-cascader">
    <ElCascader
      v-model="selectedValue"
      :options="options"
      :props="cascaderProps"
      :placeholder="placeholder"
      :clearable="clearable"
      :filterable="filterable"
      v-bind="$attrs"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

defineOptions({
  name: "FaCascader",
});

interface FaCascaderProps {
  modelValue?: any;
  options?: any[];
  placeholder?: string;
  clearable?: boolean;
  filterable?: boolean;
  showAllLevels?: boolean;
  separator?: string;
  checkStrictly?: boolean;
  multiple?: boolean;
}

const props = withDefaults(defineProps<FaCascaderProps>(), {
  modelValue: () => [],
  options: () => [],
  placeholder: "请选择",
  clearable: true,
  filterable: true,
  showAllLevels: true,
  separator: "/",
  checkStrictly: false,
  multiple: false,
});

const emit = defineEmits<{
  (e: "update:modelValue", value: any): void;
  (e: "change", value: any): void;
}>();

const cascaderProps = computed(() => ({
  checkStrictly: props.checkStrictly,
  multiple: props.multiple,
  emitPath: false,
}));

const selectedValue = computed({
  get: () => props.modelValue,
  set: (value: any) => {
    emit("update:modelValue", value);
    emit("change", value);
  },
});
</script>
