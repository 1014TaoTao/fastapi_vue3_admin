<template>
  <div class="fa-transfer">
    <ElTransfer
      v-model="selected"
      :data="transferData"
      :titles="titles"
      :filterable="filterable"
      :filter-placeholder="filterPlaceholder"
      :props="transferProps"
      v-bind="$attrs"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

defineOptions({ name: "FaTransfer" });

interface Props {
  modelValue?: any[];
  data?: any[];
  titles?: [string, string];
  filterable?: boolean;
  filterPlaceholder?: string;
  keyProp?: string;
  labelProp?: string;
  disabledProp?: string;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => [],
  data: () => [],
  titles: () => ["待选择", "已选择"],
  filterable: true,
  keyProp: "value",
  labelProp: "label",
  disabledProp: "disabled",
});

const emit = defineEmits<{
  "update:modelValue": [value: any[]];
  change: [value: any[], direction: "left" | "right", movedKeys: any[]];
  "left-check-change": [keys: any[], checkedKeys: any[]];
  "right-check-change": [keys: any[], checkedKeys: any[]];
}>();

const transferProps = computed(() => ({
  key: props.keyProp,
  label: props.labelProp,
  disabled: props.disabledProp,
}));

const selected = computed({
  get: () => props.modelValue,
  set: (val: any[]) => {
    emit("update:modelValue", val);
  },
});

const transferData = computed(() => {
  return props.data.map((item: any) => ({
    key: item[props.keyProp],
    label: item[props.labelProp],
    disabled: item[props.disabledProp],
  }));
});
</script>
