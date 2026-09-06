<template>
  <ElCarousel height="400px">
    <ElCarouselItem>
      <FaCardBanner
        title="系统运行正常"
        description="所有核心服务运行稳定，响应时间在正常范围内。"
      />
    </ElCarouselItem>

    <ElCarouselItem>
      <FaCardBanner
        :image="icon2"
        title="重要消息通知"
        description="您有 3 条待处理的重要消息，请及时查看。"
        :button="{
          show: true,
          text: '查看详情',
          color: 'var(--fa-warning)',
          textColor: '#fff',
        }"
      />
    </ElCarouselItem>

    <ElCarouselItem>
      <FaCardBanner
        :image="icon3"
        title="数据分析报告"
        description="本周业务数据分析报告已完成，请查看关键指标。"
        :button="{
          show: true,
          text: '下载报告',
          color: 'var(--fa-error)',
          textColor: '#fff',
        }"
      />
    </ElCarouselItem>

    <ElCarouselItem>
      <FaCardBanner
        :image="icon4"
        title="版本更新提醒"
        description="FastapiAdmin v3.1.0 已发布，包含优化和新功能。"
        :button="{
          show: true,
          text: '立即更新',
          color: 'var(--theme-color)',
          textColor: '#fff',
        }"
        :cancelButton="{
          show: true,
          text: '稍后提醒',
          color: '#eee',
          textColor: '#333',
        }"
        @click="handleConfirm"
        @cancel="handleCancel"
      />
    </ElCarouselItem>
  </ElCarousel>
</template>

<script setup lang="ts">
// 非关键组件异步导入（延迟加载，提升首屏速度）
import FaCardBanner from "@/components/banners/fa-card-banner/index.vue";
import icon2 from "@imgs/3d/icon2.webp";
import icon3 from "@imgs/3d/icon3.webp";
import icon4 from "@imgs/3d/icon4.webp";

defineOptions({ name: "ItBanners" });

/**
 * 处理确认按钮点击事件
 */
const handleConfirm = () => {
  // TODO: 接入真实操作
  console.log("confirm clicked");
};

/**
 * 处理取消按钮点击事件
 */
const handleCancel = () => {
  // TODO: 接入真实操作
  console.log("cancel clicked");
};
</script>
