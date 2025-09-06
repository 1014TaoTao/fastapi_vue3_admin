<template>
  <el-drawer
    v-model="drawerVisible"
    :size="drawerSize"
    :title="t('settings.project')"
    :before-close="handleCloseDrawer"
    class="settings-drawer"
  >
    <div class="settings-content">
      <!-- 主题设置 -->
      <section class="config-section">
        <el-divider>{{ t("settings.theme") }}</el-divider>

        <div class="flex-center">
          <el-switch
            v-model="isDark"
            active-action-icon="Moon"
            inactive-action-icon="Sunny"
            @change="handleThemeChange"
          />
        </div>
      </section>

      <!-- 布局设置 -->
      <section class="config-section">
        <el-divider>{{ t("settings.layoutSetting") }}</el-divider>

        <!-- 整合的布局选择器 -->
        <div class="layout-select">
          <div class="layout-grid">
            <el-tooltip
              v-for="item in layoutOptions"
              :key="item.value"
              :content="item.label"
              placement="bottom"
            >
              <div
                role="button"
                tabindex="0"
                :class="[
                  'layout-item',
                  item.className,
                  {
                    'is-active': settingsStore.layout === item.value,
                  },
                ]"
                @click="handleLayoutChange(item.value)"
                @keydown.enter.space="handleLayoutChange(item.value)"
              >
                <!-- 布局预览图标 -->
                <div class="layout-preview">
                  <div v-if="item.value !== LayoutMode.LEFT" class="layout-header"></div>
                  <div v-if="item.value !== LayoutMode.TOP" class="layout-sidebar"></div>
                  <div class="layout-main"></div>
                </div>
                <!-- 布局名称 -->
                <div class="layout-name">{{ item.label }}</div>
                <!-- 选中状态指示器 -->
                <div v-if="settingsStore.layout === item.value" class="layout-check">
                  <el-icon><Check /></el-icon>
                </div>
              </div>
            </el-tooltip>
          </div>
        </div>
      </section>

      <!-- 系统主题 -->
      <section class="config-section">
        <el-divider>{{ t("settings.systemTheme") }}</el-divider>
        <div class="config-item">
          <!-- <div class="flex-x-between mb-3">
            <span class="text-xs">{{ t("settings.themeColor") }}</span>
          </div> -->
          <!-- 自定义主题颜色选择器 -->
          <div class="theme-color-selector">
            <div class="color-options">
              <!-- 预设颜色选项 -->
              <div
                v-for="(color, index) in displayColorPresets"
                :key="color"
                :class="[
                  'color-option',
                  { 'is-active': selectedThemeColor === color }
                ]"
                :style="{ backgroundColor: color }"
                @click="handleColorSelect(color)"
              >
                <div v-if="selectedThemeColor === color" class="color-check">
                  <el-icon><Check /></el-icon>
                </div>
              </div>
              <!-- 自定义颜色选择器 -->
              <div class="color-picker-wrapper">
                <el-color-picker
                  v-model="selectedThemeColor"
                  :predefine="allColorPresets"
                  show-alpha
                  size="small"
                  class="custom-color-picker"
                />
              </div>
            </div>
          </div>
        </div>
      </section>


      <!-- 导航主题 -->
      <section v-if="!isDark" class="config-section ">
        <el-divider>{{ t("settings.navigation") }}</el-divider>
        <div class="config-item flex-x-between">
          <span class="text-xs">{{ t("settings.sidebarColorScheme") }}</span>
          <el-radio-group v-model="sidebarColor" @change="changeSidebarColor">
            <el-radio :value="SidebarColor.CLASSIC_BLUE">
              {{ t("settings.classicBlue") }}
            </el-radio>
            <el-radio :value="SidebarColor.MINIMAL_WHITE">
              {{ t("settings.minimalWhite") }}
            </el-radio>
          </el-radio-group>
        </div>
      </section>

      <!-- 界面设置 -->
      <section class="config-section">
        <el-divider>{{ t("settings.interface") }}</el-divider>

        <div class="flex-x-between">
          <span class="text-xs">{{ t("settings.showTagsView") }}</span>
          <el-switch v-model="settingsStore.showTagsView" />
        </div>

        <div class="flex-x-between">
          <span class="text-xs">{{ t("settings.showAppLogo") }}</span>
          <el-switch v-model="settingsStore.showAppLogo" />
        </div>

        <div class="flex-x-between">
          <span class="text-xs">{{ t("settings.showWatermark") }}</span>
          <el-switch v-model="settingsStore.showWatermark" />
        </div>
        
      </section>
    </div>

    <!-- 操作按钮区域 - 固定到底部 -->
    <div class="action-footer">
      <div class="action-divider"></div>
      <div class="action-card">
        <div class="action-buttons">
          <el-tooltip
            content="复制配置将生成当前设置的代码，覆盖 src/settings.ts 下的 defaultSettings 变量"
            placement="top"
          >
            <el-button
              type="primary"
              size="default"
              :icon="copyIcon"
              :loading="copyLoading"
              class="action-btn"
              @click="handleCopySettings"
            >
              {{ copyLoading ? "复制中..." : t("settings.copyConfig") }}
            </el-button>
          </el-tooltip>
          <el-tooltip content="重置将恢复所有设置为默认值" placement="top">
            <el-button
              type="warning"
              size="default"
              :icon="resetIcon"
              :loading="resetLoading"
              class="action-btn"
              @click="handleResetSettings"
            >
              {{ resetLoading ? "重置中..." : t("settings.resetConfig") }}
            </el-button>
          </el-tooltip>
        </div>
      </div>
    </div>
  </el-drawer>

  
</template>

<script setup lang="ts">
import { DocumentCopy, RefreshLeft, Check, Plus } from "@element-plus/icons-vue";

const { t } = useI18n();
import { LayoutMode, SidebarColor, ThemeMode } from "@/enums";
import { useSettingsStore } from "@/store";
import { themeColorPresets } from "@/settings";
import { useAppStore } from "@/store/modules/app.store";
import { DeviceEnum } from "@/enums/settings/device.enum";

const appStore = useAppStore();
const drawerSize = computed(() => (appStore.device === DeviceEnum.DESKTOP ? "400px" : "90%"));

// 按钮图标
const copyIcon = markRaw(DocumentCopy);
const resetIcon = markRaw(RefreshLeft);

// 加载状态
const copyLoading = ref(false);
const resetLoading = ref(false);

// 布局选项配置
interface LayoutOption {
  value: LayoutMode;
  label: string;
  className: string;
}

const layoutOptions: LayoutOption[] = [
  { value: LayoutMode.LEFT, label: t("settings.leftLayout"), className: "left" },
  { value: LayoutMode.TOP, label: t("settings.topLayout"), className: "top" },
  { value: LayoutMode.MIX, label: t("settings.mixLayout"), className: "mix" },
];

// 使用统一的颜色预设配置
const colorPresets = themeColorPresets;
const settingsStore = useSettingsStore();

// 主题颜色选择器相关
const displayColorPresets = computed(() => themeColorPresets.slice(0, 9)); // 只显示前9个预设颜色
const allColorPresets = themeColorPresets; // 所有颜色预设，用于自定义颜色选择器

// 判断当前颜色是否为自定义颜色（不在前7个预设中）
const isCustomColor = computed(() => {
  return !displayColorPresets.value.includes(selectedThemeColor.value);
});

const isDark = ref<boolean>(settingsStore.theme === ThemeMode.DARK);
const sidebarColor = ref(settingsStore.sidebarColorScheme);

const selectedThemeColor = computed({
  get: () => settingsStore.themeColor,
  set: (value) => settingsStore.updateThemeColor(value),
});

const drawerVisible = computed({
  get: () => settingsStore.settingsVisible,
  set: (value) => (settingsStore.settingsVisible = value),
});

/**
 * 处理主题切换
 *
 * @param isDark 是否启用暗黑模式
 */
const handleThemeChange = (isDark: string | number | boolean) => {
  settingsStore.updateTheme(isDark ? ThemeMode.DARK : ThemeMode.LIGHT);
};

/**
 * 更改侧边栏颜色
 *
 * @param val 颜色方案名称
 */
const changeSidebarColor = (val: any) => {
  settingsStore.updateSidebarColorScheme(val);
};

/**
 * 切换布局
 *
 * @param layout - 布局模式
 */
const handleLayoutChange = (layout: LayoutMode) => {
  if (settingsStore.layout === layout) return;

  settingsStore.updateLayout(layout);
};

/**
 * 处理颜色选择
 *
 * @param color - 选中的颜色
 */
const handleColorSelect = (color: string) => {
  selectedThemeColor.value = color;
};


/**
 * 复制当前配置
 */
const handleCopySettings = async () => {
  try {
    copyLoading.value = true;

    // 生成配置代码
    const configCode = generateSettingsCode();

    // 复制到剪贴板
    await navigator.clipboard.writeText(configCode);

    // 显示成功消息
    ElMessage.success({
      message: t("settings.copySuccess"),
      duration: 3000,
    });
  } catch {
    ElMessage.error("复制配置失败");
  } finally {
    copyLoading.value = false;
  }
};

/**
 * 重置为默认配置
 */
const handleResetSettings = async () => {
  resetLoading.value = true;

  try {
    settingsStore.resetSettings();

    // 同步更新本地状态
    isDark.value = settingsStore.theme === ThemeMode.DARK;
    sidebarColor.value = settingsStore.sidebarColorScheme;

    ElMessage.success(t("settings.resetSuccess"));
  } catch {
    ElMessage.error("重置配置失败");
  } finally {
    resetLoading.value = false;
  }
};

/**
 * 生成配置代码字符串
 */
const generateSettingsCode = (): string => {
  const settings = {
    title: "pkg.name",
    version: "pkg.version",
    showSettings: true,
    showTagsView: settingsStore.showTagsView,
    showAppLogo: settingsStore.showAppLogo,
    layout: `LayoutMode.${settingsStore.layout.toUpperCase()}`,
    theme: `ThemeMode.${settingsStore.theme.toUpperCase()}`,
    size: "ComponentSize.DEFAULT",
    language: "LanguageEnum.ZH_CN",
    themeColor: `"${settingsStore.themeColor}"`,
    showWatermark: settingsStore.showWatermark,
    watermarkContent: "pkg.name",
    sidebarColorScheme: `SidebarColor.${settingsStore.sidebarColorScheme.toUpperCase().replace("-", "_")}`,
  };

  return `const defaultSettings: AppSettings = {
  title: ${settings.title},
  version: ${settings.version},
  showSettings: ${settings.showSettings},
  showTagsView: ${settings.showTagsView},
  showAppLogo: ${settings.showAppLogo},
  layout: ${settings.layout},
  theme: ${settings.theme},
  size: ${settings.size},
  language: ${settings.language},
  themeColor: ${settings.themeColor},
  showWatermark: ${settings.showWatermark},
  watermarkContent: ${settings.watermarkContent},
  sidebarColorScheme: ${settings.sidebarColorScheme},
};`;
};

/**
 * 关闭抽屉前的回调
 */
const handleCloseDrawer = () => {
  settingsStore.settingsVisible = false;
};
</script>

<style lang="scss" scoped>
/* 设置抽屉样式 */
.settings-drawer {
  :deep(.el-drawer__body) {
    position: relative;
    height: 100%;
    padding: 0;
    overflow: hidden;
  }
}

/* 设置内容区域 */
.settings-content {
  height: calc(100vh - 120px); /* 减去头部和底部按钮的高度 */
  padding: 20px;
  padding-bottom: 20px;
  overflow-y: auto;
}

/* 底部操作区域样式 */
.action-footer {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 10;
  padding: 0;
  background: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-light);

  .action-divider {
    display: none; /* 移除重复的分割线 */
  }

  .action-card {
    padding: 16px 20px;
    margin: 0;
    background: var(--el-fill-color-extra-light);
    border: none;
    border-radius: 0;

    .action-buttons {
      display: flex;
      gap: 12px;

      .action-btn {
        flex: 1;
        font-size: 14px;
        border-radius: 8px;
        transition: all 0.3s ease;

        &:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          transform: translateY(-2px);
        }
      }
    }
  }
}

/* 主题切换器优化 */
.theme-switch {
  transform: scale(1.2);
  transition: all 0.3s ease;

  &:hover {
    transform: scale(1.25);
  }
}

.config-section {
  margin-bottom: 24px;

  .config-item {
    padding: 12px 0;
    border-bottom: 1px solid var(--el-border-color-light);
    transition: all 0.3s ease;

    &:last-child {
      border-bottom: none;
    }

    &:hover {
      padding-right: 8px;
      padding-left: 8px;
      margin: 0 -8px;
      background-color: var(--el-fill-color-light);
      border-radius: 6px;
    }
  }
}

/* 布局选择器样式优化 */
.layout-select {
  padding: 16px 8px;

  .layout-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    justify-items: center;
  }
}

.layout-item {
  position: relative;
  width: 70px;
  height: 80px;
  overflow: hidden;
  cursor: pointer;
  background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
  border: 2px solid var(--el-border-color-light);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    background: linear-gradient(145deg, #ffffff 0%, var(--el-color-primary-light-9) 100%);
    border-color: var(--el-color-primary-light-3);
    transform: translateY(-4px) scale(1.05);
  }

  &:active {
    transform: translateY(-2px) scale(1.02);
  }

  .layout-preview {
    position: relative;
    width: 100%;
    height: 50px;
    margin: 8px 0 4px 0;
  }

  .layout-header {
    position: absolute;
    top: 0;
    right: 4px;
    left: 4px;
    height: 8px;
    background: linear-gradient(
      90deg,
      var(--el-color-primary) 0%,
      var(--el-color-primary-light-3) 100%
    );
    border-radius: 2px;
  }

  .layout-sidebar {
    position: absolute;
    left: 4px;
    width: 12px;
    background: linear-gradient(
      180deg,
      var(--el-color-primary-dark-2) 0%,
      var(--el-color-primary) 100%
    );
    border-radius: 2px;
  }

  .layout-main {
    position: absolute;
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 2px;
  }

  .layout-name {
    position: absolute;
    right: 0;
    bottom: 6px;
    left: 0;
    font-size: 10px;
    font-weight: 500;
    color: var(--el-text-color-regular);
    text-align: center;
    transition: color 0.3s ease;
  }

  .layout-check {
    position: absolute;
    top: 4px;
    right: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    font-size: 10px;
    color: white;
    background: var(--el-color-success);
    border-radius: 50%;
  }

  // 左侧布局
  &.left {
    .layout-sidebar {
      top: 4px;
      bottom: 4px;
    }
    .layout-main {
      top: 4px;
      right: 4px;
      bottom: 4px;
      left: 20px;
    }
  }

  // 顶部布局
  &.top {
    .layout-header {
      height: 12px;
    }
    .layout-main {
      top: 16px;
      right: 4px;
      bottom: 4px;
      left: 4px;
    }
  }

  // 混合布局
  &.mix {
    .layout-header {
      height: 10px;
    }
    .layout-sidebar {
      top: 14px;
      bottom: 4px;
    }
    .layout-main {
      top: 14px;
      right: 4px;
      bottom: 4px;
      left: 20px;
    }
  }

  &.is-active {
    background: linear-gradient(
      145deg,
      var(--el-color-primary-light-9) 0%,
      var(--el-color-primary-light-8) 100%
    );
    border-color: var(--el-color-primary);
    transform: translateY(-2px) scale(1.08);

    .layout-name {
      font-weight: 600;
      color: var(--el-color-primary);
    }
  }
}

/* 深色模式适配 */
.dark {
  .action-footer {
    background: var(--el-bg-color);
    border-top-color: var(--el-border-color);
  }

  .action-card {
    background: var(--el-fill-color-extra-light);
  }

  .layout-item {
    background: linear-gradient(145deg, var(--el-bg-color) 0%, var(--el-bg-color-page) 100%);
    border-color: var(--el-border-color);

    &:hover {
      background: linear-gradient(
        145deg,
        var(--el-bg-color-page) 0%,
        var(--el-color-primary-light-9) 100%
      );
    }

    &.is-active {
      background: linear-gradient(
        145deg,
        var(--el-color-primary-light-9) 0%,
        var(--el-color-primary-light-8) 100%
      );
    }

    .layout-main {
      background: linear-gradient(135deg, var(--el-fill-color) 0%, var(--el-fill-color-light) 100%);
    }
  }
}

/* 主题颜色选择器样式 */
.theme-color-selector {
  .color-options {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
  }

  .color-option {
    position: relative;
    width: 22px;
    height: 22px;
    cursor: pointer;
    border: 2px solid var(--el-border-color-light);
    border-radius: 6px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

    &:hover {
      transform: translateY(-2px) scale(1.05);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      border-color: var(--el-color-primary-light-3);
    }

    &.is-active {
      border-color: var(--el-color-primary);
      transform: translateY(-1px) scale(1.08);
      box-shadow: 0 4px 16px rgba(64, 128, 255, 0.3);
    }

    .color-check {
      position: absolute;
      top: 50%;
      left: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 16px;
      height: 16px;
      color: white;
      background: rgba(0, 0, 0, 0.6);
      border-radius: 50%;
      transform: translate(-50%, -50%);
      font-size: 10px;
      backdrop-filter: blur(2px);
    }
  }

  .color-picker-wrapper {
    .custom-color-picker {
      :deep(.el-color-picker__trigger) {
        width: 22px !important;
        height: 22px !important;
        border: 2px solid var(--el-border-color-light) !important;
        border-radius: 6px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;

        &:hover {
          transform: translateY(-2px) scale(1.05) !important;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
          border-color: var(--el-color-primary-light-3) !important;
        }
      }

      :deep(.el-color-picker__color) {
        border: none !important;
        border-radius: 3px !important;
      }

      :deep(.el-color-picker__color-inner) {
        border-radius: 3px !important;
      }

      :deep(.el-color-picker__icon) {
        font-size: 10px !important;
      }
    }
  }
}


/* 深色模式适配 */
.dark {
  .theme-color-selector {
    .color-option {
      border-color: var(--el-border-color);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);

      &:hover {
        border-color: var(--el-color-primary-light-3);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
      }
    }

    .color-picker-wrapper {
      .custom-color-picker {
        :deep(.el-color-picker__trigger) {
          border-color: var(--el-border-color) !important;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;

          &:hover {
            border-color: var(--el-color-primary-light-3) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
          }
        }
      }
    }
  }
}

/* 复制配置对话框样式 */
:deep(.copy-config-dialog) {
  .el-message-box__content {
    max-height: 400px;
    overflow-y: auto;
  }
}
</style>

