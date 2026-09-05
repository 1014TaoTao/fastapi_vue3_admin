import type { SystemThemeEnum, MenuTypeEnum } from "@/enums/appEnum";
import type { MenuThemeType } from "@/types/store";

/** 主题设置 */
export interface ThemeSetting {
  name: string;
  theme: SystemThemeEnum;
  color: string[];
  leftLineColor: string;
  rightLineColor: string;
  img: string;
}

/** 菜单布局 */
export interface MenuLayout {
  name: string;
  value: MenuTypeEnum;
  img: string;
  description?: string;
}

/** 节日配置 */
export interface FestivalConfig {
  date: string;
  endDate?: string;
  name: string;
  image: string;
  scrollText: string;
  isActive?: boolean;
  count?: number;
  fireworkInterval?: number;
  skipFireworks?: boolean;
  isResidentBanner?: boolean;
}

/** 系统基础配置 */
export interface SystemBasicConfig {
  name: string;
  description?: string;
  logo?: string;
  favicon?: string;
  copyright?: string;
}

/** 快速入口基础项 */
export interface FastEnterBaseItem {
  name: string;
  enabled?: boolean;
  order?: number;
  routeName?: string;
  routeQuery?: Record<string, string>;
  link?: string;
  isDialog?: boolean;
}

/** 快速入口应用项 */
export interface FastEnterApplication extends FastEnterBaseItem {
  description: string;
  icon: string;
  iconColor: string;
}

/** 快速链接项 */
export type FastEnterQuickLink = FastEnterBaseItem;

/** 快速入口配置 */
export interface FastEnterConfig {
  applications: FastEnterApplication[];
  quickLinks: FastEnterQuickLink[];
  minWidth?: number;
}

/** 系统配置 */
export interface SystemConfig {
  systemInfo: SystemBasicConfig;
  systemThemeStyles: Record<"dark" | "light", { className: string }>;
  settingThemeList: ThemeSetting[];
  menuLayoutList: MenuLayout[];
  themeList: MenuThemeType[];
  darkMenuStyles: MenuThemeType[];
  systemMainColor: readonly string[];
  fastEnter?: FastEnterConfig;
  headerBar?: HeaderBarFeatureConfig;
}

/** 环境配置 */
export interface EnvConfig {
  NODE_ENV: string;
  VITE_VERSION: string;
  VITE_PORT: string;
  VITE_BASE_URL: string;
  VITE_API_URL: string;
  VITE_USE_MOCK?: string;
  VITE_USE_GZIP?: string;
  VITE_USE_CDN?: string;
}

/** 应用配置 */
export interface AppConfig extends SystemConfig {
  env: EnvConfig;
  isDev: boolean;
  isProd: boolean;
  isTest: boolean;
}

/** 功能配置项基础接口 */
export interface FeatureConfigItem {
  enabled: boolean;
  description: string;
}

/** 顶部栏功能配置接口 */
export interface HeaderBarFeatureConfig {
  menuButton: FeatureConfigItem;
  refreshButton: FeatureConfigItem;
  fastEnter: FeatureConfigItem;
  breadcrumb: FeatureConfigItem;
  globalSearch: FeatureConfigItem;
  fullscreen: FeatureConfigItem;
  notification: FeatureConfigItem;
  language: FeatureConfigItem;
  settings: FeatureConfigItem;
  themeToggle: FeatureConfigItem;
  sizeSelect: FeatureConfigItem;
}
