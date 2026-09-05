<!-- 登录、注册、忘记密码左侧背景 -->
<template>
  <div class="login-left-view">
    <div v-if="!hideTopBranding" class="logo">
      <FaLogo class="icon" size="46" :src="webLogoSrc" />
      <div class="logo-title-wrap">
        <div class="logo-title-inline">
          <h1 class="title">{{ siteTitle }}</h1>
          <ElTooltip :content="displayVersion" placement="bottom">
            <div class="logo-version-badge">
              <span class="logo-version-pill">{{ displayVersion }}</span>
            </div>
          </ElTooltip>
        </div>
      </div>
    </div>

    <div class="left-img">
      <FaThemeSvg :src="loginIcon" size="100%" />
    </div>

    <div class="text-wrap">
      <h1>{{ configStore.configData?.login_title?.config_value || $t("login.leftView.title") }}</h1>
      <p>
        {{ configStore.configData?.login_subtitle?.config_value || $t("login.leftView.subTitle") }}
      </p>
    </div>

    <!-- 几何装饰元素 -->
    <div class="geometric-decorations">
      <!-- 基础几何形状 -->
      <div
        class="geo-element circle-outline animate-fade-in-up"
        :style="'animation-delay: 0s'"
      ></div>
      <div
        class="geo-element square-rotated animate-fade-in-left"
        :style="'animation-delay: 0s'"
      ></div>
      <div
        class="geo-element circle-small animate-fade-in-up"
        :style="'animation-delay: 0.3s'"
      ></div>

      <div
        class="geo-element square-bottom-right animate-fade-in-right"
        :style="'animation-delay: 0s'"
      ></div>

      <!-- 背景泡泡 -->
      <div class="geo-element bg-bubble animate-scale-in" :style="'animation-delay: 0.5'"></div>

      <!-- 太阳/月亮 -->
      <div
        class="geo-element circle-top-right animate-fade-in-down"
        :style="'animation-delay: 0.5'"
        @click="themeAnimation"
      ></div>

      <!-- 装饰点 -->
      <div
        class="geo-element dot dot-top-left animate-bounce-in"
        :style="'animation-delay: 0s'"
      ></div>
      <div
        class="geo-element dot dot-top-right animate-bounce-in"
        :style="'animation-delay: 0s'"
      ></div>
      <div
        class="geo-element dot dot-center-right animate-bounce-in"
        :style="'animation-delay: 0s'"
      ></div>

      <!-- 叠加方块组 -->
      <div class="squares-group">
        <i
          class="geo-element square square-blue animate-fade-in-left-rotated-blue"
          :style="'animation-delay: 0.2s'"
        ></i>
        <i
          class="geo-element square square-pink animate-fade-in-left-rotated-pink"
          :style="'animation-delay: 0.4s'"
        ></i>
        <i
          class="geo-element square square-purple animate-fade-in-left-no-rotation"
          :style="'animation-delay: 0.6s'"
        ></i>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import AppConfig from "@/config";
import loginIcon from "@fa_imgs/background.svg";
import { useConfigStore } from "@stores";
import { themeAnimation } from "@utils";

defineOptions({ name: "FaLoginLeftView" });

interface Props {
  hideContent?: boolean;
  /** 顶栏已展示 Logo/标题/版本时隐藏左侧重复顶栏 */
  hideTopBranding?: boolean;
}

withDefaults(defineProps<Props>(), {
  hideContent: false,
  hideTopBranding: false,
});

const configStore = useConfigStore();

/** 接口 logo_url，空则 FaLogo 内置默认图 */
const webLogoSrc = computed(
  () => configStore.configData.logo_url?.config_value?.trim() || undefined
);

const siteTitle = computed(
  () => configStore.configData.sys_name?.config_value?.trim() || AppConfig.systemInfo.name
);

const DEFAULT_APP_VERSION = "3.0.0";
const displayVersion = computed(() => {
  const raw = configStore.configData.version?.config_value?.trim();
  const ver = raw || DEFAULT_APP_VERSION;
  return ver.startsWith("v") || ver.startsWith("V") ? ver : `v${ver}`;
});
</script>

<style lang="scss" scoped>
// 颜色变量定义
$primary-light-7: var(--el-color-primary-light-7);
$primary-light-8: var(--el-color-primary-light-8);
$primary-light-9: var(--el-color-primary-light-9);
$primary-base: var(--el-color-primary);
$main-bg: var(--default-box-color);

// 混合颜色函数
$bg-mix-light-9: color-mix(in srgb, $primary-light-9 100%, $main-bg);
$bg-mix-light-8: color-mix(in srgb, $primary-light-8 80%, $main-bg);
$bg-mix-light-7: color-mix(in srgb, $primary-light-7 80%, $main-bg);

.login-left-view {
  position: relative;
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  padding: 15px;
  overflow: hidden;
  background-color: $bg-mix-light-9;

  .logo {
    position: relative;
    z-index: 100;
    display: flex;
    align-items: center;

    .logo-title-wrap {
      flex: 1;
      min-width: 0;
      margin-left: 10px;
    }

    /** 标题与版本：垂直居中对齐（上下在同一水平中线），长标题可自然换行 */
    .logo-title-inline {
      display: flex;
      flex-flow: row wrap;
      gap: 0.45rem;
      align-items: center;
      min-width: 0;
      max-width: 100%;
    }

    .title {
      flex: 0 1 auto;
      min-width: 0;
      max-width: 100%;
      margin: 0;
      font-size: clamp(1.05rem, 1.6vw, 1.25rem);
      font-weight: 600;
      line-height: 1.35;
      color: var(--el-text-color-primary);
      letter-spacing: -0.02em;
    }

    .logo-version-badge {
      flex-shrink: 0;
    }

    .logo-version-pill {
      display: inline-block;
      padding: 0.28rem 0.6rem;
      font-size: 11px;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
      line-height: 1.15;
      color: var(--el-color-primary);
      letter-spacing: 0.02em;
      background: color-mix(in srgb, var(--el-color-primary) 11%, transparent);
      border: 1px solid color-mix(in srgb, var(--el-color-primary) 28%, transparent);
      border-radius: 999px;
      box-shadow: 0 1px 2px rgb(0 0 0 / 4%);
      transition:
        border-color 0.2s ease,
        background 0.2s ease;
    }
  }

  .left-img {
    position: absolute;
    inset: 0 0 10.5%;
    z-index: 10;
    width: 40%;
    margin: auto;
    animation: slideInLeft 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
  }

  .text-wrap {
    position: absolute;
    bottom: 80px;
    width: 100%;
    text-align: center;
    animation: slideInLeft 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;

    h1 {
      font-size: 24px;
      font-weight: 400;
      color: var(--fa-gray-900) !important;
    }

    p {
      margin-top: 10px;
      font-size: 14px;
      color: var(--fa-gray-600) !important;
    }
  }

  .geometric-decorations {
    .geo-element {
      position: absolute;
      opacity: 0;
      animation-duration: 0.8s;
      animation-timing-function: cubic-bezier(0.25, 0.46, 0.45, 0.94);
      animation-fill-mode: forwards;
    }

    // 动画 mixin
    @mixin fadeAnimation($direction: "", $rotation: 0deg) {
      from {
        opacity: 0;

        @if $direction == "up" {
          transform: translateY(30px) rotate($rotation);
        } @else if $direction == "down" {
          transform: translateY(-30px) rotate($rotation);
        } @else if $direction == "left" {
          transform: translateX(-30px) rotate($rotation);
        } @else if $direction == "right" {
          transform: translateX(30px) rotate($rotation);
        }
      }

      to {
        opacity: 1;

        @if $direction == "up" or $direction == "down" {
          transform: translateY(0) rotate($rotation);
        } @else {
          transform: translateX(0) rotate($rotation);
        }
      }
    }

    // 动画定义
    @keyframes fadeInUp {
      @include fadeAnimation("up");
    }

    @keyframes fadeInDown {
      @include fadeAnimation("down");
    }

    @keyframes fadeInLeft {
      @include fadeAnimation("left");
    }

    @keyframes fadeInLeftRotated {
      @include fadeAnimation("left", -25deg);
    }

    @keyframes fadeInRight {
      @include fadeAnimation("right");
    }

    @keyframes fadeInRightRotated {
      @include fadeAnimation("right", 45deg);
    }

    @keyframes fadeInLeftRotatedBlue {
      @include fadeAnimation("left", -10deg);
    }

    @keyframes fadeInLeftRotatedPink {
      @include fadeAnimation("left", 10deg);
    }

    @keyframes fadeInLeftNoRotation {
      @include fadeAnimation("left");
    }

    @keyframes scaleIn {
      from {
        opacity: 0;
        transform: scale(0.8);
      }

      to {
        opacity: 1;
        transform: scale(1);
      }
    }

    @keyframes bounceIn {
      0% {
        opacity: 0;
        transform: scale(0.3);
      }

      50% {
        opacity: 1;
        transform: scale(1.05);
      }

      70% {
        transform: scale(0.9);
      }

      100% {
        opacity: 1;
        transform: scale(1);
      }
    }

    @keyframes lineGrow {
      from {
        opacity: 0;
      }

      to {
        opacity: 1;
      }
    }

    @keyframes slideInLeft {
      from {
        opacity: 0;
        transform: translateX(-30px);
      }

      to {
        opacity: 1;
        transform: translateX(0);
      }
    }

    // 动画类
    .animate-fade-in-up {
      animation-name: fadeInUp;
    }

    .animate-fade-in-down {
      animation-name: fadeInDown;
    }

    .animate-fade-in-left {
      animation-name: fadeInLeft;
    }

    .animate-fade-in-right {
      animation-name: fadeInRight;
    }

    .animate-scale-in {
      animation-name: scaleIn;
      animation-duration: 1.2s;
    }

    .animate-bounce-in {
      animation-name: bounceIn;
      animation-duration: 0.6s;
    }

    .animate-fade-in-left-rotated-blue {
      animation-name: fadeInLeftRotatedBlue;
    }

    .animate-fade-in-left-rotated-pink {
      animation-name: fadeInLeftRotatedPink;
    }

    .animate-fade-in-left-no-rotation {
      animation-name: fadeInLeftNoRotation;
    }

    // 基础几何形状
    .circle-outline {
      top: 10%;
      left: 25%;
      width: 42px;
      height: 42px;
      border: 2px solid $primary-light-8;
      border-radius: 50%;
    }

    .square-rotated {
      top: 50%;
      left: 16%;
      width: 60px;
      height: 60px;
      background-color: $bg-mix-light-8;

      &.animate-fade-in-left {
        animation-name: fadeInLeftRotated;
      }
    }

    .circle-small {
      bottom: 26%;
      left: 30%;
      width: 18px;
      height: 18px;
      background-color: $primary-light-8;
      border-radius: 50%;
    }

    // 太阳/月亮效果
    .circle-top-right {
      top: 3%;
      right: 3%;
      z-index: 100;
      width: 50px;
      height: 50px;
      cursor: pointer;
      background: $bg-mix-light-7;
      border-radius: 50%;
      box-shadow: 0 0 20px rgba(#fffc00, 0.5);
      transition: all 0.3s;

      &::after {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 100%;
        height: 100%;
        content: "";
        background: linear-gradient(to right, #fcbb04, #fffc00);
        border-radius: 50%;
        opacity: 1;
        transform: translate(-50%, -50%);
        transition: all 0.5s;
      }

      &:hover {
        box-shadow: 0 0 36px #fffc00;
        transform: scale(1.08);
      }
    }

    .square-bottom-right {
      right: 10%;
      bottom: 10%;
      width: 50px;
      height: 50px;
      background-color: $primary-light-8;

      &.animate-fade-in-right {
        animation-name: fadeInRightRotated;
      }
    }

    // 背景泡泡
    .bg-bubble {
      top: -120px;
      right: -120px;
      width: 360px;
      height: 360px;
      background-color: $bg-mix-light-8;
      border-radius: 50%;
    }

    // 装饰点
    .dot {
      width: 14px;
      height: 14px;
      background-color: $primary-light-7;
      border-radius: 50%;

      &.dot-top-left {
        top: 140px;
        left: 100px;
      }

      &.dot-top-right {
        top: 140px;
        right: 120px;
      }

      &.dot-center-right {
        top: 46%;
        right: 22%;
        background-color: $primary-light-8;
      }
    }

    // 叠加方块组
    .squares-group {
      position: absolute;
      bottom: 18px;
      left: 20px;
      width: 140px;
      height: 140px;
      pointer-events: none;

      .square {
        position: absolute;
        display: block;
        border-radius: 8px;
        box-shadow: 0 8px 24px rgb(64 87 167 / 12%);

        &.square-blue {
          top: 12px;
          left: 30px;
          z-index: 2;
          width: 50px;
          height: 50px;
          background-color: rgb(from $primary-base r g b / 30%);
        }

        &.square-pink {
          top: 30px;
          left: 48px;
          z-index: 1;
          width: 70px;
          height: 70px;
          background-color: rgb(from $primary-base r g b / 15%);
        }

        &.square-purple {
          top: 66px;
          left: 86px;
          z-index: 3;
          width: 32px;
          height: 32px;
          background-color: rgb(from $primary-base r g b / 45%);
        }
      }

      // 装饰线条
      &::after {
        position: absolute;
        top: 86px;
        left: 72px;
        width: 80px;
        height: 1px;
        content: "";
        background: linear-gradient(90deg, var(--el-color-primary-light-6), transparent);
        opacity: 0;
        transform: rotate(50deg);
        animation: lineGrow 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
        animation-delay: 1.2s;
      }
    }
  }

  @media only screen and (width <= 1600px) {
    .text-wrap {
      bottom: 40px;
    }
  }

  @media only screen and (width <= 1180px) {
    width: auto;
    height: auto;
    padding: 0;
    // 隐藏背景和其他内容，只保留 logo
    background: transparent;

    .left-img,
    .text-wrap,
    .geometric-decorations {
      display: none;
    }

    .logo {
      display: none;
    }
  }
}

// 暗色主题
.dark .login-left-view {
  background-color: color-mix(in srgb, $primary-light-9 60%, #070707);

  @media only screen and (width <= 1180px) {
    background: transparent;
  }

  .geometric-decorations {
    // 月亮效果
    .circle-top-right {
      background-color: #f5f3d0;
      box-shadow: 0 0 30px rgba(#fffc00, 0.35);
      rotate: -48deg;
      transition: all 0.3s ease-in-out 0.1s;

      &::after {
        opacity: 0;
      }

      &::before {
        position: absolute;
        top: 0;
        left: 15px;
        width: 50px;
        height: 50px;
        content: "";
        background-color: color-mix(in srgb, $primary-light-9 60%, #070707);
        border-radius: 50%;
        transition: all 0.3s ease-in-out;
      }

      &:hover {
        background-color: #fffc00;
        box-shadow: 0 0 45px rgba(#fffc00, 0.6);

        &::before {
          left: 22px;
        }

        &::after {
          opacity: 0;
        }
      }
    }

    .bg-bubble {
      background-color: $bg-mix-light-9;
    }

    // 其他元素颜色调整
    .square-rotated {
      background-color: $bg-mix-light-9;
    }

    .circle-small,
    .dot {
      background-color: $primary-light-8;
    }

    .square-bottom-right {
      background-color: $primary-light-9;
    }

    .dot.dot-top-right {
      background-color: $primary-light-8;
    }
  }

  // 方块组暗色调整
  .squares-group {
    .square {
      box-shadow: none;

      &.square-blue {
        background-color: rgb(from $primary-base r g b / 18%);
      }

      &.square-pink {
        background-color: rgb(from $primary-base r g b / 10%);
      }

      &.square-purple {
        background-color: rgb(from $primary-base r g b / 20%);
      }
    }

    &::after {
      background: linear-gradient(90deg, $primary-light-8, transparent);
    }
  }
}
</style>
