<!--
  FaCardGrid：ElRow/ElCol + ElCard 卡片网格 + 分页。
  - 提供 header/body/footer 三个插槽，透传 item、index。
  - 分页配置与 FaTable 一致：pagination { current, size, total } + paginationOptions 合并默认值。
-->
<template>
  <div class="fa-card-grid">
    <ElScrollbar class="fa-card-grid__main">
      <!-- 加载骨架 -->
      <div v-if="loading && isEmpty" class="fa-card-grid__skeleton">
        <ElSkeleton animated>
          <template #template>
            <div
              :style="{ gridTemplateColumns: `repeat(auto-fill, minmax(${cardMinWidth}, 1fr))` }"
              class="grid gap-4"
            >
              <div v-for="i in skeletonCount" :key="i" :style="{ height: skeletonHeight }">
                <ElSkeletonItem
                  variant="rect"
                  class="w-full h-full"
                  style="border-radius: var(--custom-radius)"
                />
              </div>
            </div>
          </template>
        </ElSkeleton>
      </div>

      <!-- 卡片网格 -->
      <div v-else-if="!isEmpty" :style="{ padding: `0 ${gutter / 2}px` }">
        <ElRow :gutter="gutter">
          <ElCol
            v-for="(item, index) in items"
            :key="item[keyField] ?? index"
            :xs="xs"
            :sm="sm"
            :md="md"
            :lg="lg"
            :xl="xl"
            class="mb-4"
          >
            <ElCard
              class="fa-card"
              :class="cardClass"
              shadow="hover"
              :header-class="headerClass"
              :body-class="bodyClass"
              :footer-class="footerClass"
              @click="(e: MouseEvent) => emit('itemClick', item, e)"
            >
              <template v-if="$slots.header" #header>
                <slot name="header" :item="item" :index="index" />
              </template>

              <slot :item="item" :index="index" />

              <template v-if="$slots.footer" #footer>
                <slot name="footer" :item="item" :index="index" />
              </template>
            </ElCard>
          </ElCol>
        </ElRow>
      </div>

      <!-- 空状态 -->
      <ElEmpty v-else :description="emptyText">
        <template v-if="$slots.empty" #default>
          <slot name="empty" />
        </template>
      </ElEmpty>
    </ElScrollbar>

    <!-- 分页 -->
    <div v-if="showPagination" class="fa-card-grid__pagination">
      <FaPagination
        :page="pagination!.current"
        :limit="pagination!.size"
        :total="pagination!.total"
        :page-sizes="mergedPaginationOptions.pageSizes"
        :disabled="!!loading"
        @pagination="handlePaginationEvent"
      />
    </div>
  </div>
</template>

<script setup lang="ts" generic="T extends Record<string, any>">
import { computed } from "vue";
import {
  ElCard,
  ElRow,
  ElCol,
  ElEmpty,
  ElSkeleton,
  ElSkeletonItem,
  ElScrollbar,
} from "element-plus";
import FaPagination from "@/components/tables/fa-pagination/index.vue";

defineOptions({ name: "FaCardGrid" });

/** 分页状态 */
interface FaPaginationConfig {
  current: number;
  size: number;
  total: number;
}

/** 分页配置选项 */
interface PaginationOptions {
  pageSizes?: number[];
  hideOnSinglePage?: boolean;
}

interface Props {
  items: T[];
  loading?: boolean;
  emptyText?: string;
  /** 分页状态（传入后显示分页器） */
  pagination?: FaPaginationConfig;
  /** 分页配置覆盖 */
  paginationOptions?: PaginationOptions;
  gutter?: number;
  keyField?: string;
  xs?: number;
  sm?: number;
  md?: number;
  lg?: number;
  xl?: number;
  cardClass?: string;
  headerClass?: string;
  bodyClass?: string;
  footerClass?: string;
  skeletonMinWidth?: number;
  skeletonCount?: number;
  skeletonHeight?: string;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  emptyText: "暂无数据",
  pagination: undefined,
  paginationOptions: () => ({}),
  gutter: 16,
  keyField: "id",
  xs: 24,
  sm: 12,
  md: 8,
  lg: 6,
  xl: undefined,
  cardClass: "",
  headerClass: "",
  bodyClass: "",
  footerClass: "",
  skeletonMinWidth: 320,
  skeletonCount: 6,
  skeletonHeight: "340px",
});

interface Emits {
  (e: "itemClick", item: T, event: MouseEvent): void;
  (e: "pagination:size-change", val: number): void;
  (e: "pagination:current-change", val: number): void;
}

const emit = defineEmits<Emits>();

const DEFAULT_PAGINATION_OPTIONS: PaginationOptions = {
  pageSizes: [12, 24, 48],
  hideOnSinglePage: false,
};

const mergedPaginationOptions = computed(() => ({
  ...DEFAULT_PAGINATION_OPTIONS,
  ...props.paginationOptions,
}));

const isEmpty = computed(() => !props.items?.length);
const showPagination = computed(() => !!props.pagination);
const cardMinWidth = computed(() => `${props.skeletonMinWidth}px`);

function handlePaginationEvent(payload: { page: number; limit: number }) {
  const p = props.pagination;
  if (!p) return;
  if (payload.limit !== p.size) {
    emit("pagination:size-change", payload.limit);
    return;
  }
  if (payload.page !== p.current) {
    emit("pagination:current-change", payload.page);
  }
}
</script>

<style scoped>
.fa-card-grid {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
}

.fa-card-grid__main {
  flex: 1;
  min-height: 0;
  padding-top: 10px;
}

.fa-card-grid__skeleton {
  padding: 6px 0;
}

.fa-card-grid__pagination {
  display: flex;
  flex-shrink: 0;
  justify-content: center;
  padding-top: 13px;
  border-top: 1px solid var(--el-border-color-lighter);
}

/* 卡片紧凑布局 */
.fa-card :deep(.el-card__header) {
  padding: 8px 16px;
}

.fa-card :deep(.el-card__body) {
  padding: 8px 16px;
}

.fa-card :deep(.el-card__footer) {
  padding: 8px 16px;
}
</style>
