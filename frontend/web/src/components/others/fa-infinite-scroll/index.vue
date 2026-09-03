<template>
  <div
    v-infinite-scroll="handleScroll"
    :infinite-scroll-disabled="disabled"
    :infinite-scroll-distance="distance"
    :infinite-scroll-immediate="immediate"
    class="fa-infinite-scroll"
    :style="{ height: height, overflow: 'auto' }"
  >
    <template v-if="loading && !$slots.loading">
      <div class="flex justify-center py-4">
        <ElIcon class="is-loading"><Loading /></ElIcon>
      </div>
    </template>
    <slot />
    <div
      v-if="noMore && showNoMore"
      class="fa-infinite-scroll__empty text-center py-4 text-sm text-gray-400"
    >
      {{ noMoreText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { Loading } from "@element-plus/icons-vue";

defineOptions({ name: "FaInfiniteScroll" });

interface Props {
  /** 容器高度 */
  height?: string;
  /** 是否禁用 */
  disabled?: boolean;
  /** 触发加载的距离阈值 */
  distance?: number;
  /** 是否立即触发加载 */
  immediate?: boolean;
  /** 是否正在加载 */
  loading?: boolean;
  /** 是否没有更多数据 */
  noMore?: boolean;
  /** 是否显示"没有更多了"提示 */
  showNoMore?: boolean;
  /** 没有更多数据时的提示文本 */
  noMoreText?: string;
}

withDefaults(defineProps<Props>(), {
  height: "300px",
  disabled: false,
  distance: 100,
  immediate: true,
  loading: false,
  noMore: false,
  showNoMore: true,
  noMoreText: "没有更多了",
});

interface Emits {
  load: [];
}

const emit = defineEmits<Emits>();

const handleScroll = () => {
  emit("load");
};
</script>
