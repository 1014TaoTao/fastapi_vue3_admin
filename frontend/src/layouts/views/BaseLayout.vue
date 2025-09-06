<template>
  <div class="layout" :class="layoutClass">
    <!-- 移动端遮罩层 -->
    <div v-if="isMobile && isSidebarOpen" class="layout__overlay" @click="closeSidebar" />

    <!-- 布局内容插槽 -->
    <slot></slot>

    <!-- 返回顶部按钮 -->
    <el-backtop target=".app-main">
      <div class="i-svg:backtop w-6 h-6" />
    </el-backtop>

    <!-- 新增：悬浮的系统设置按钮 -->
    <el-button
      v-if="settingStore.showSettings"
      class="floating-settings-button"
      type="primary"
      @click="handleSettingsClick"
    >
      <el-icon>
        <Setting />
      </el-icon>
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { useLayout } from "../composables/useLayout";
import { useLayoutResponsive } from "../composables/useLayoutResponsive";
import { defaultSettings } from "@/settings";
import { useSettingsStore } from "@/store";

const settingStore = useSettingsStore();

/**
 * 打开系统设置页面
 */
function handleSettingsClick() {
  settingStore.settingsVisible = true;
}

// 布局相关
const { layoutClass, isSidebarOpen, closeSidebar } = useLayout();

// 响应式处理
const { isMobile } = useLayoutResponsive();
</script>

<style lang="scss" scoped>
.layout {
  width: 100%;
  height: 100%;

  &__overlay {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 999;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.3);
  }

  // 新增：悬浮按钮样式
  .floating-settings-button {
    position: fixed; // 固定在页面上
    top: 50%; // 距离顶部20px
    right: 0px; // 距离右侧8px
    z-index: 999; // 层叠顺序
    width: 40px;
    height: 40px;
    border-top-right-radius: 0; // 右侧顶部无圆角
    border-bottom-right-radius: 0; // 右侧底部无圆角
  }
}
</style>
