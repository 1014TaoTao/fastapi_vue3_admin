<template>
  <div class="flex flex-col relative last:mb-0">
    <FaDashboardSkeleton v-if="loading" />
    <template v-else>
      <!-- 左列：主内容区 | 右列：侧边栏 -->
      <ElRow :gutter="20">
        <ElCol :xs="24" :md="18">
          <Banner class="mb-5" />

          <ElRow :gutter="20">
            <ElCol :xs="24" :md="16">
              <ElRow :gutter="20">
                <ElCol :xs="24" :sm="24" :md="24">
                  <CardList />
                </ElCol>
              </ElRow>
              <ElRow :gutter="20">
                <ElCol :xs="24" :sm="8" :md="8" class="mb-5">
                  <FaStatsCard
                    :icon="'ri:money-cny-box-line'"
                    :iconStyle="'bg-theme'"
                    :boxStyle="'bg-theme/10!'"
                    :title="'总收入'"
                    :description="'月收入超过¥350,000+'"
                    :count="35000"
                    :textColor="'var(--theme-color)'"
                    :decimals="0"
                    :showArrow="false"
                    separator=","
                    customIconStyle="'text-theme! text-3xl!''"
                  />
                </ElCol>
                <ElCol :xs="24" :sm="8" :md="8" class="mb-5">
                  <FaProgressCard
                    :percentage="65"
                    :title="'任务进度'"
                    :color="'var(--theme-color)'"
                  />
                </ElCol>
                <ElCol :xs="24" :sm="8" :md="8" class="mb-5">
                  <FaProgressCard
                    :percentage="80"
                    :title="'任务进度'"
                    :color="'var(--theme-color)'"
                    :icon="'ri:twitch-line'"
                    :iconStyle="'bg-theme/12 text-theme'"
                  />
                </ElCol>
              </ElRow>
              <ElRow :gutter="20">
                <ElCol :xs="24" :sm="8" :md="8" class="mb-5">
                  <FaBarChartCard
                    :isMiniChart="true"
                    :value="15480"
                    label="浏览量"
                    date="过去14天"
                    :percentage="-4.15"
                    :height="9.5"
                    barWidth="45%"
                    :chartData="[120, 100, 150, 140, 90, 120, 130]"
                  />
                </ElCol>
                <ElCol :xs="24" :sm="8" :md="8" class="mb-5">
                  <FaLineChartCard
                    :isMiniChart="true"
                    :value="2545"
                    label="粉丝数"
                    date="过去30天"
                    :percentage="1.2"
                    :height="9.5"
                    :showAreaColor="true"
                    :chartData="[150, 180, 160, 200, 180, 220, 240]"
                  />
                </ElCol>
                <ElCol :xs="24" :sm="8" :md="8" class="mb-5">
                  <FaDonutChartCard
                    :value="36358"
                    title="粉丝量"
                    :percentage="18"
                    percentageLabel="较去年"
                    :data="[50, 40]"
                    :height="9.5"
                    currentValue="2022"
                    previousValue="2021"
                    :radius="['50%', '70%']"
                  />
                </ElCol>
              </ElRow>
            </ElCol>
            <ElCol :xs="24" :md="8" class="mb-5">
              <FaTimelineListCard :list="timelineData" title="最近交易" subtitle="2024年12月20日" />
            </ElCol>
          </ElRow>

          <ElRow :gutter="20">
            <ElCol :xs="24" :sm="12" :md="12" class="mb-5">
              <ElCard
                shadow="hover"
                class="fa-card overflow-hidden border border-(--el-border-color-lighter) rounded-xl flex flex-col h-138"
              >
                <template #header>
                  <div class="flex flex-wrap gap-3 items-start justify-between w-full">
                    <div>
                      <span
                        class="text-base font-semibold tracking-[0.02em]"
                        style="color: var(--el-text-color-primary)"
                        >日程日历</span
                      >
                      <p
                        class="mt-0.5 text-xs font-normal leading-[1.45]"
                        style="color: var(--el-text-color-secondary)"
                      >
                        点击日期添加或编辑（本地演示）
                      </p>
                    </div>
                  </div>
                </template>
                <div>
                  <FaCalendar />
                </div>
              </ElCard>
            </ElCol>
            <ElCol :xs="24" :sm="12" :md="12" class="mb-5">
              <NewUser />
            </ElCol>
          </ElRow>
        </ElCol>

        <ElCol :xs="24" :md="6" class="flex flex-col gap-5">
          <QuickLinks class="mb-5" />
          <FaDataListCard
            class="mb-5"
            :maxCount="4"
            :list="healthList"
            title="系统健康"
            subtitle="实时 · 30s"
            :showMoreButton="true"
            @more="handleMore"
          />
          <TodoList class="mb-5" />
        </ElCol>
      </ElRow>

      <ElRow :gutter="20">
        <ElCol :xs="24" :sm="6" :md="6" class="mb-5">
          <ImageCards />
        </ElCol>
        <ElCol :xs="24" :sm="6" :md="6" class="mb-5">
          <ItBanners />
        </ElCol>
        <ElCol :xs="24" :sm="12" :md="12" class="mb-5">
          <AboutProject />
        </ElCol>
      </ElRow>
    </template>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: "Home", inheritAttrs: false });

import { ref, onMounted, onUnmounted, defineAsyncComponent } from "vue";
import { ElMessage } from "element-plus";
import DashboardAPI from "@/api/module_monitor/dashboard";
import { getDashboardMock, type HealthItem } from "@/mock/dashboard";
import ImageCards from "./modules/image_cards.vue";
import ItBanners from "./modules/it_banners.vue";
import Banner from "./modules/banner.vue";
import NewUser from "./modules/new-user.vue";
import TodoList from "./modules/todo-list.vue";
import CardList from "./modules/card-list.vue";
import AboutProject from "./modules/about-project.vue";
import QuickLinks from "./modules/quick-links.vue";

const mock = getDashboardMock();
const loading = ref(false);
const healthList = ref<HealthItem[]>(mock.health); // 初值 mock 兜底，健康流首帧到达即覆盖
const timelineData = ref(mock.timeline);

let unsubscribeHealth: (() => void) | null = null;

onMounted(() => {
  // 后续替换为真实接口:
  // const { data } = await DashboardAPI.getStats();
  // 并删除 getDashboardMock() 调用
  unsubscribeHealth = DashboardAPI.subscribeHealthStream((items) => {
    healthList.value = items;
  });
});

onUnmounted(() => {
  unsubscribeHealth?.();
  unsubscribeHealth = null;
});

// 图表组件异步导入，减少首屏 echarts 加载
const FaLineChartCard = defineAsyncComponent(
  () => import("@/components/cards/fa-line-chart-card/index.vue")
);
const FaBarChartCard = defineAsyncComponent(
  () => import("@/components/cards/fa-bar-chart-card/index.vue")
);
const FaDonutChartCard = defineAsyncComponent(
  () => import("@/components/cards/fa-donut-chart-card/index.vue")
);

const FaTimelineListCard = defineAsyncComponent(
  () => import("@/components/cards/fa-timeline-list-card/index.vue")
);

function handleMore() {
  ElMessage.info("查看更多");
}
</script>
