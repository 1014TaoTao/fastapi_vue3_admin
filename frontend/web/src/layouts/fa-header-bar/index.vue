<!-- 顶部栏 -->
<template>
  <div
    class="w-full bg-(--default-bg-color)"
    :class="[
      tabStyle === 'tab-card' || tabStyle === 'tab-google' || tabStyle === 'tab-default'
        ? 'max-sm:mb-3 bg-box!'
        : '',
    ]"
  >
    <div
      class="relative box-border flex justify-between h-15 leading-15 select-none"
      :class="[
        tabStyle === 'tab-card' || tabStyle === 'tab-google' || tabStyle === 'tab-default'
          ? 'border-b border-(--fa-card-border)'
          : '',
      ]"
    >
      <div class="flex items-center flex-1 min-w-0 leading-15" :style="{ display: 'flex' }">
        <!-- 系统信息：Logo + 标题一并受「显示应用 Logo」控制 -->
        <div
          class="flex items-center cursor-pointer"
          @click="toHome"
          v-if="isTopMenu && showAppLogo"
        >
          <FaLogo class="pl-4.5" :src="headerLogoSrc" />
          <p v-if="width >= 1400" class="my-0 mx-2 ml-2 text-lg">{{ headerSystemName }}</p>
        </div>

        <FaLogo
          v-if="showAppLogo"
          class="hidden! pl-3.5 overflow-hidden align-[-0.15em] fill-current"
          :src="headerLogoSrc"
          @click="toHome"
        />

        <!-- 菜单按钮 -->
        <FaIconButton
          v-if="isLeftMenu && shouldShowMenuButton"
          icon="ri:menu-2-fill"
          class="ml-3 max-sm:ml-1.75"
          @click="visibleMenu"
        />

        <!-- 刷新按钮 -->
        <FaIconButton
          v-if="shouldShowRefreshButton"
          icon="ri:refresh-line"
          class="ml-3! refresh-btn max-sm:hidden!"
          :style="{ marginLeft: !isLeftMenu ? '10px' : '0' }"
          @click="reload"
        />

        <!-- 快速入口 -->
        <FaFastEnter v-if="shouldShowFastEnter && width >= headerBarFastEnterMinWidth">
          <FaIconButton icon="ri:function-line" class="ml-3" />
        </FaFastEnter>

        <!-- 面包屑 -->
        <FaBreadcrumb
          v-if="(shouldShowBreadcrumb && isLeftMenu) || (shouldShowBreadcrumb && isDualMenu)"
        />

        <!-- 顶部菜单 -->
        <FaHorizontalMenu v-if="isTopMenu" :list="menuList" />

        <!-- 混合菜单-顶部 -->
        <FaMixedMenu v-if="isTopLeftMenu" :list="menuList" />
      </div>

      <div id="app-header-toolbar" class="flex items-center gap-2.5">
        <!-- 搜索 -->
        <div
          v-if="shouldShowGlobalSearch"
          class="search-bar-trigger flex items-center justify-between w-40 h-9 px-2.5 cursor-pointer border border-g-400 rounded-custom-sm max-md:hidden! transition duration-300 hover:-translate-y-0.5 hover:shadow-md"
          @click="openSearchDialog"
        >
          <div class="flex items-center">
            <FaSvgIcon icon="ri:search-line" class="text-sm text-g-500" />
            <span class="ml-1 text-xs font-normal text-g-500">{{ $t("topBar.search.title") }}</span>
          </div>
          <div class="flex items-center h-5 px-1.5 text-g-500/80 border rounded">
            <FaSvgIcon v-if="isWindows" icon="vaadin:ctrl-a" class="text-sm" />
            <FaSvgIcon v-else icon="ri:command-fill" class="text-xs" />
            <span class="ml-0.5 text-xs">k</span>
          </div>
        </div>

        <!-- 全屏按钮 -->
        <FaIconButton
          v-if="shouldShowFullscreen"
          :icon="isFullscreen ? 'ri:fullscreen-exit-line' : 'ri:fullscreen-fill'"
          :class="[!isFullscreen ? 'full-screen-btn' : 'exit-full-screen-btn', 'ml-3']"
          class="max-md:hidden!"
          @click="toggleFullScreen"
        />

        <!-- 组件尺寸 default/large/small（沿用旧版持久化开关 showSizeSelect） -->
        <div
          v-if="shouldShowSizeSelect"
          class="flex items-center justify-center ml-1 max-md:hidden!"
        >
          <FaSizeSelect />
        </div>

        <!-- 国际化按钮 -->
        <ElDropdown
          @command="changeLanguage"
          popper-class="langDropDownStyle"
          v-if="shouldShowLanguage"
        >
          <FaIconButton icon="ri:translate-2" class="language-btn text-[19px]" />
          <template #dropdown>
            <ElDropdownMenu>
              <div v-for="item in languageOptions" :key="item.value" class="lang-btn-item">
                <ElDropdownItem
                  :command="item.value"
                  :class="{ 'is-selected': locale === item.value }"
                >
                  <span class="menu-txt">{{ item.label }}</span>
                  <FaSvgIcon icon="ri:check-fill" v-if="locale === item.value" />
                </ElDropdownItem>
              </div>
            </ElDropdownMenu>
          </template>
        </ElDropdown>

        <!-- 通知按钮 -->
        <FaIconButton
          v-if="shouldShowNotification"
          icon="ri:notification-2-line"
          class="notice-button relative"
          @click="visibleNotice"
        >
          <ElBadge
            v-if="noticeStore.total > 0"
            :value="noticeStore.total > 99 ? '99+' : noticeStore.total"
            :max="99"
            class="absolute top-0 right-0"
          >
            <div class="size-1.5"></div>
          </ElBadge>
        </FaIconButton>

        <!-- 设置按钮 -->
        <div v-if="shouldShowSettings">
          <ElPopover :visible="showSettingGuide" placement="bottom-start" :width="190" :offset="0">
            <template #reference>
              <div class="flex items-center justify-center">
                <FaIconButton icon="ri:settings-line" class="setting-btn" @click="openSetting" />
              </div>
            </template>
            <template #default>
              <p>
                {{ $t("topBar.guide.title") }}
                <span :style="{ color: systemThemeColor }">{{ $t("topBar.guide.theme") }}</span>
                、
                <span :style="{ color: systemThemeColor }">{{ $t("topBar.guide.menu") }}</span>
                {{ $t("topBar.guide.description") }}
              </p>
            </template>
          </ElPopover>
        </div>

        <!-- 主题切换按钮 -->
        <FaIconButton
          v-if="shouldShowThemeToggle"
          @click="themeAnimation"
          :icon="isDark ? 'ri:sun-fill' : 'ri:moon-line'"
        />

        <!-- 用户头像、菜单 -->
        <FaUserMenu />
      </div>
    </div>

    <!-- 标签页 -->
    <FaWorkTab />

    <!-- 通知 -->
    <FaNotification v-model:value="showNotice" />
  </div>
</template>

<script setup lang="ts">
import { LanguageEnum, MenuTypeEnum } from "@/enums/appEnum";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { useFullscreen, useWindowSize } from "@vueuse/core";

import {
  useSettingsStore,
  useMenuStore,
  useUserStore,
  useNoticeStore,
  useConfigStore,
  refreshAppCaches,
} from "@stores";
import AppConfig from "@/config";
import { languageOptions } from "@/locales";
import { mittBus, themeAnimation } from "@utils";
import { useCommon } from "@/hooks/core/useCommon";
import { useHeaderBar } from "@/hooks/core/useHeaderBar";
import { ElMessage } from "element-plus";
import FaUserMenu from "./widgets/FaUserMenu.vue";

defineOptions({ name: "FaHeaderBar" });

// 检测操作系统类型
const isWindows = navigator.userAgent.includes("Windows");

const router = useRouter();
const { locale, t } = useI18n();
const { width } = useWindowSize();

const settingStore = useSettingsStore();
const userStore = useUserStore();
const menuStore = useMenuStore();
const configStore = useConfigStore();
const noticeStore = useNoticeStore();

/** 租户配置：logo_url / name */
const headerLogoSrc = computed(() => {
  const raw = configStore.configData.logo_url?.config_value;
  return typeof raw === "string" && raw.trim() ? raw.trim() : undefined;
});

const headerSystemName = computed(() => {
  const raw = configStore.configData.sys_name?.config_value;
  if (typeof raw === "string" && raw.trim()) return raw.trim();
  return AppConfig.systemInfo.name;
});

// 顶部栏功能配置
const {
  shouldShowMenuButton,
  shouldShowRefreshButton,
  shouldShowFastEnter,
  shouldShowBreadcrumb,
  shouldShowGlobalSearch,
  shouldShowFullscreen,
  shouldShowNotification,
  shouldShowLanguage,
  shouldShowSettings,
  shouldShowThemeToggle,
  shouldShowSizeSelect,
  fastEnterMinWidth: headerBarFastEnterMinWidth,
} = useHeaderBar();

const { menuOpen, systemThemeColor, showSettingGuide, menuType, isDark, tabStyle, showAppLogo } =
  storeToRefs(settingStore);

const { language } = storeToRefs(userStore);
const { visibleMenus: menuList } = storeToRefs(menuStore);

const showNotice = ref(false);

// 菜单类型判断
const isLeftMenu = computed(() => menuType.value === MenuTypeEnum.LEFT);
const isDualMenu = computed(() => menuType.value === MenuTypeEnum.DUAL_MENU);
const isTopMenu = computed(() => menuType.value === MenuTypeEnum.TOP);
const isTopLeftMenu = computed(() => menuType.value === MenuTypeEnum.TOP_LEFT);

const { isFullscreen, toggle: toggleFullscreen } = useFullscreen();

onMounted(() => {
  initLanguage();
  document.addEventListener("click", bodyCloseNotice);
  noticeStore.getNotice();
});

onUnmounted(() => {
  document.removeEventListener("click", bodyCloseNotice);
});

/**
 * 切换全屏状态
 */
const toggleFullScreen = (): void => {
  toggleFullscreen();
};

/**
 * 切换菜单显示/隐藏状态
 */
const visibleMenu = (): void => {
  settingStore.setMenuOpen(!menuOpen.value);
};

const { homePath } = useCommon();
const { refresh } = useCommon();

/**
 * 跳转到首页
 */
const toHome = (): void => {
  router.push(homePath.value);
};

/**
 * 刷新缓存并刷新页面
 */
const reload = async (): Promise<void> => {
  try {
    await refreshAppCaches();
    refresh();
    ElMessage.success({
      message: t("worktab.refreshCacheDone"),
      duration: 3000,
    });
  } catch (e) {
    console.error(e);
    ElMessage.error(t("worktab.refreshCacheFail"));
  }
};

/**
 * 初始化语言设置
 */
const initLanguage = (): void => {
  locale.value = language.value;
};

/**
 * 切换系统语言
 * @param {LanguageEnum} lang - 目标语言类型
 */
const changeLanguage = (lang: LanguageEnum): void => {
  if (locale.value === lang) return;
  locale.value = lang;
  userStore.setLanguage(lang);
  reload();
};

/**
 * 打开设置面板
 */
const openSetting = (): void => {
  mittBus.emit("openSetting");

  // 隐藏设置引导提示
  if (showSettingGuide.value) {
    settingStore.hideSettingGuide();
  }
};

/**
 * 打开全局搜索对话框
 */
const openSearchDialog = (): void => {
  mittBus.emit("openSearchDialog");
};

/**
 * 点击页面其他区域关闭通知面板
 * @param {Event} e - 点击事件对象
 */
const bodyCloseNotice = (e: any): void => {
  if (!showNotice.value) return;

  const target = e.target as HTMLElement;

  // 检查是否点击了通知按钮或通知面板内部
  const isNoticeButton = target.closest(".notice-button");
  const isNoticePanel = target.closest(".fa-notification-panel");

  if (!isNoticeButton && !isNoticePanel) {
    showNotice.value = false;
  }
};

/**
 * 切换通知面板显示状态
 */
const visibleNotice = (): void => {
  showNotice.value = !showNotice.value;
};
</script>

<style lang="scss" scoped>
/* Custom animations */
@keyframes rotate180 {
  0% {
    transform: rotate(0);
  }

  100% {
    transform: rotate(180deg);
  }
}

@keyframes shake {
  0% {
    transform: rotate(0);
  }

  25% {
    transform: rotate(-5deg);
  }

  50% {
    transform: rotate(5deg);
  }

  75% {
    transform: rotate(-5deg);
  }

  100% {
    transform: rotate(0);
  }
}

@keyframes expand {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.1);
  }

  100% {
    transform: scale(1);
  }
}

@keyframes shrink {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(0.9);
  }

  100% {
    transform: scale(1);
  }
}

@keyframes moveUp {
  0% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-3px);
  }

  100% {
    transform: translateY(0);
  }
}

@keyframes breathing {
  0% {
    opacity: 0.4;
    transform: scale(0.9);
  }

  50% {
    opacity: 1;
    transform: scale(1.1);
  }

  100% {
    opacity: 0.4;
    transform: scale(0.9);
  }
}

/* Hover animation classes */
.refresh-btn:hover :deep(.fa-svg-icon) {
  animation: rotate180 0.5s;
}

.language-btn:hover :deep(.fa-svg-icon) {
  animation: moveUp 0.4s;
}

.setting-btn:hover :deep(.fa-svg-icon) {
  animation: rotate180 0.5s;
}

.full-screen-btn:hover :deep(.fa-svg-icon) {
  animation: expand 0.6s forwards;
}

:deep(.size-select-btn:hover .fa-svg-icon) {
  animation: expand 0.6s forwards;
}

.exit-full-screen-btn:hover :deep(.fa-svg-icon) {
  animation: shrink 0.6s forwards;
}

/* 会话列表 hover 边框变主题色 */
.search-bar-trigger:hover {
  border-color: var(--el-color-primary) !important;
}

.notice-button:hover :deep(.fa-svg-icon) {
  animation: shake 0.5s ease-in-out;
}

/* iPad breakpoint adjustments */
@media screen and (width <= 768px) {
  .logo2 {
    display: block !important;
  }
}

@media screen and (width <= 640px) {
  .btn-box {
    width: 40px;
  }
}
</style>
