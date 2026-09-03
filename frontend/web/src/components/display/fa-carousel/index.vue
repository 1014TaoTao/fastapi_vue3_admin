<template>
  <div class="fa-carousel">
    <ElCarousel
      v-bind="$attrs"
      :height="height"
      :indicator-position="indicatorPosition"
      :autoplay="autoplay"
      :interval="interval"
      :type="type"
    >
      <ElCarouselItem v-for="item in items" :key="item.value">
        <div
          class="fa-carousel__item h-full flex items-center justify-center"
          :style="{ backgroundColor: item.color || '#f0f0f0' }"
        >
          <template v-if="item.image">
            <img :src="item.image" :alt="item.label" class="max-h-full max-w-full object-contain" />
          </template>
          <template v-else>
            <div class="fa-carousel__content text-center px-4">
              <h3 class="text-lg font-medium mb-2">{{ item.label }}</h3>
              <p v-if="item.description" class="text-sm text-gray-500">
                {{ item.description }}
              </p>
            </div>
          </template>
        </div>
      </ElCarouselItem>
      <slot name="default" />
    </ElCarousel>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: "FaCarousel" });

interface CarouselItem {
  value: string;
  label: string;
  description?: string;
  image?: string;
  color?: string;
}

interface Props {
  items: CarouselItem[];
  height?: string;
  indicatorPosition?: "none" | "outside";
  autoplay?: boolean;
  interval?: number;
  type?: "card";
}

withDefaults(defineProps<Props>(), {
  height: "300px",
  indicatorPosition: undefined,
  autoplay: true,
  interval: 4000,
  type: undefined,
});
</script>
