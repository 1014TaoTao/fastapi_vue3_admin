<template>
  <ElCarousel height="220px" :interval="6000">
    <ElCarouselItem>
      <FaBasicBanner
        height="100%"
        :title="bannerTitle"
        :subtitle="bannerSubtitle"
        boxStyle="bg-theme/10!"
        titleColor="var(--fa-gray-900)"
        subtitleColor="var(--fa-gray-500)"
        :decoration="false"
        :meteorConfig="{
          enabled: true,
          count: 10,
        }"
        :buttonConfig="{
          show: false,
          text: '开始探索',
          color: 'var(--fa-success)',
          textColor: '#fff',
          radius: '6px',
        }"
        :imageConfig="{
          src: bannerCover,
          width: '18rem',
          bottom: '-7.5rem',
        }"
        @click="handleBannerClick"
      >
        <div class="flex items-center gap-3 mt-2">
          <ElAvatar
            v-if="currentUser.avatar"
            :size="44"
            :src="currentUser.avatar"
            style="background-color: transparent"
          />
          <ElIcon v-else :size="40" class="text-g-500"><UserFilled /></ElIcon>
          <div>
            <div class="text-base font-semibold text-g-800">{{ currentUser.name }}</div>
            <div class="text-xs text-g-600">
              {{ currentUser.dept_name }} · {{ currentUser.description }} ·
              {{ currentUser.last_login }}
            </div>
          </div>
        </div>
      </FaBasicBanner>
    </ElCarouselItem>

    <ElCarouselItem>
      <FaBasicBanner
        height="100%"
        title="数据中心运行状态"
        subtitle="系统访问量同比增长 23%，所有服务运行稳定，数据监控正常。"
      />
    </ElCarouselItem>

    <ElCarouselItem>
      <FaBasicBanner
        height="100%"
        title="欢迎使用 FastapiAdmin"
        subtitle="基于 Vue 3 + TypeScript + Element Plus 构建的现代化管理系统。"
        titleColor="#333"
        subtitleColor="#666"
        boxStyle="!bg-[#D4F1F7]"
        :buttonConfig="{
          show: true,
          text: '开始探索',
          color: 'var(--fa-success)',
          textColor: '#fff',
          radius: '6px',
        }"
        @buttonClick="handleBannerClick"
      />
    </ElCarouselItem>

    <ElCarouselItem>
      <FaBasicBanner
        height="100%"
        title="探索星空计划"
        subtitle="加入我们的天文观测活动，发现宇宙的奥秘"
        boxStyle="!bg-[#FF8AAB]"
        :buttonConfig="{
          show: true,
          text: '立即参与',
          color: '#FF5A89',
          textColor: '#fff',
        }"
        :imageConfig="{
          src: icon3,
        }"
      />
    </ElCarouselItem>

    <ElCarouselItem>
      <FaBasicBanner
        height="100%"
        boxStyle="!bg-[#70B1FF]"
        :imageConfig="{
          src: icon5,
        }"
      >
        <template #title>
          <h2 style="margin: 0; font-size: 1.6rem; color: #fff !important">智能组件系统</h2>
        </template>

        <template #subtitle>
          <div style="margin-top: 12px">
            <p style="position: relative; z-index: 10; font-style: italic">
              灵活配置，强大扩展，支持自定义插槽内容
            </p>
          </div>
        </template>

        <template #button>
          <div style="margin-top: 12px">
            <ElButton type="primary" color="#04A1FF"> 查看文档 </ElButton>
          </div>
        </template>
      </FaBasicBanner>
    </ElCarouselItem>

    <ElCarouselItem>
      <FaBasicBanner v-bind="PresetBanners.marketing" height="100%" />
    </ElCarouselItem>

    <ElCarouselItem>
      <FaBasicBanner v-bind="PresetBanners.info" height="100%" />
    </ElCarouselItem>
  </ElCarousel>
</template>

<script setup lang="ts">
import { computed } from "vue";
import bannerCover from "@imgs/login/lf_icon2.webp";
import { useUserStore } from "@stores";
import { greetings } from "@utils";
import { UserFilled } from "@element-plus/icons-vue";
import icon3 from "@imgs/3d/icon3.webp";
import icon5 from "@imgs/3d/icon7.webp";

const userStore = useUserStore();

const userInfo = computed(() => userStore.basicInfo);

const handleBannerClick = (): void => {
  // TODO: 接入真实跳转或路由
  console.log("banner clicked");
};

const timefix = greetings();
const welcome = "祝你开心每一天！";
const currentUser = {
  avatar: userStore.basicInfo.avatar || "",
  name: userInfo.value.name || "吴彦祖",
  username: userInfo.value.username || "账号信息",
  description: userInfo.value.description || "用户说明",
  dept_name: userInfo.value.dept_name || "软件专业部",
  last_login: userInfo.value.last_login || "2023-01-01 00:00:00",
};

const bannerTitle = `欢迎回来 ～ ${currentUser.name}（${currentUser.username}） ${timefix} ${welcome}`;

const bannerSubtitle = `基于 FastAPI + Vue3 + TypeScript 构建的企业级中后台解决方案，支持多端开发。`;

/**
 * 预设横幅配置
 * 提供常用的横幅样式配置，可直接通过 v-bind 使用
 */
const PresetBanners = {
  marketing: {
    title: "限时优惠活动",
    subtitle: "精选商品 48 小时闪购，最高享受 7 折优惠，数量有限！",
    titleColor: "var(--fa-gray-900)",
    subtitleColor: "var(--fa-gray-900)",
    boxStyle: "!bg-success/15",
    meteorConfig: { enabled: true, count: 15 },
    buttonConfig: {
      show: true,
      text: "立即抢购",
      color: "var(--fa-success)",
      textColor: "#fff",
    },
  },
  info: {
    title: "服务到期提醒",
    subtitle: "您的高级服务将在 7 天后到期，请及时续费以继续享受完整功能。",
    titleColor: "var(--fa-gray-900)",
    subtitleColor: "var(--fa-gray-900)",
    boxStyle: "!bg-theme/15",
    meteorConfig: { enabled: true, count: 15 },
    buttonConfig: {
      show: true,
      text: "立即续费",
      color: "var(--fa-secondary)",
      textColor: "#fff",
    },
  },
} as const;
</script>
