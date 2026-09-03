<template>
  <ElSubMenu v-if="hasChildren" :index="item.path || item.meta.title" class="p-0!">
    <template #title>
      <FaMenuRouteIcon :icon="item.meta.icon" :color="theme?.iconColor" class="mr-1 text-lg" />
      <span class="text-md">{{ formatMenuTitle(item.meta.title) }}</span>
      <div
        v-if="item.meta.showBadge && !item.meta.showTextBadge"
        class="fa-badge fa-badge-horizontal"
      />
      <div v-if="item.meta.showBadge && item.meta.showTextBadge" class="fa-text-badge">
        {{ item.meta.showTextBadge }}
      </div>
    </template>

    <!-- 递归调用自身处理子菜单 -->
    <FaHorizontalSubmenu
      v-for="child in filteredChildren"
      :key="child.path"
      :item="child"
      :theme="theme"
      :level="level + 1"
      @close="closeMenu"
    />
  </ElSubMenu>

  <ElMenuItem
    v-else-if="isNavigableRoute"
    :index="item.path || item.meta.title"
    @click="goPage(item)"
  >
    <FaMenuRouteIcon
      :icon="item.meta.icon"
      :color="theme?.iconColor"
      class="mr-1 text-lg"
      :style="{ color: theme.iconColor }"
    />
    <span class="text-md">{{ formatMenuTitle(item.meta.title) }}</span>
    <div
      v-if="item.meta.showBadge && !item.meta.showTextBadge"
      class="fa-badge"
      :style="{ right: level === 0 ? '10px' : '20px' }"
    />
    <div v-if="item.meta.showBadge && item.meta.showTextBadge && level !== 0" class="fa-text-badge">
      {{ item.meta.showTextBadge }}
    </div>
  </ElMenuItem>
</template>

<script lang="ts" setup>
import { computed } from "vue";
import { handleMenuJump, formatMenuTitle } from "@utils";
import type { AppRouteRecord } from "@/types/router";

defineOptions({ name: "FaHorizontalSubmenu" });

interface Props {
  item: AppRouteRecord;
  theme?: Record<string, any>;
  level?: number;
}

const props = withDefaults(defineProps<Props>(), {
  theme: () => ({}),
  level: 0,
});

interface Emits {
  close: [];
}

const emit = defineEmits<Emits>();

// 过滤后的子菜单项（不包含隐藏的）
const filteredChildren = computed(() => {
  return props.item.children?.filter((child) => !child.meta.isHide) || [];
});

// 父菜单如果本身就是页面，则即使没有可见子菜单也应该保留为菜单项。
const isNavigableRoute = computed(() => {
  if (props.item.meta?.isHide) {
    return false;
  }
  if (props.item.meta?.shellRoute && props.item.path?.trim()) {
    return true;
  }
  return !!(
    ((props.item.path && props.item.path.trim()) ||
      props.item.meta.link ||
      props.item.meta.isIframe === true) &&
    (props.item.component || props.item.meta.link || props.item.meta.isIframe === true)
  );
});

// 计算当前项是否有可见的子菜单
const hasChildren = computed(() => {
  return filteredChildren.value.length > 0;
});

const goPage = (item: AppRouteRecord) => {
  closeMenu();
  handleMenuJump(item);
};

const closeMenu = () => {
  emit("close");
};
</script>

<style scoped>
:deep(.el-sub-menu__title .el-sub-menu__icon-arrow) {
  right: 10px !important;
}
</style>
