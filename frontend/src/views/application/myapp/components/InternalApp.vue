<!-- 内部应用展示页面 -->
<template>
  <div class="internal-app-container">
    <div class="internal-app-content">
      <iframe 
        ref="iframeRef"
        :src="appUrl" 
        class="internal-app-iframe"
        frameborder="0"
        allowfullscreen
        @load="handleIframeLoad"
      ></iframe>
      <div v-if="loading" class="loading-overlay">
        <el-icon class="loading-icon">
          <Loading />
        </el-icon>
        <span>加载中...</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';
import { Loading } from '@element-plus/icons-vue';
import { useTagsViewStore } from '@/store';

defineOptions({
  name: "InternalApp",
  inheritAttrs: false,
});

const route = useRoute();
const tagsViewStore = useTagsViewStore();
const iframeRef = ref<HTMLIFrameElement>();
const loading = ref(true);

// 从路由参数获取应用信息
const appUrl = computed(() => route.query.url as string);
const appId = computed(() => route.query.appId as string);
const appName = computed(() => route.query.appName as string);

// iframe加载完成
function handleIframeLoad() {
  loading.value = false;
}

// 监听路由变化，更新iframe
watch(() => route.query.url, (newUrl) => {
  if (newUrl && iframeRef.value) {
    loading.value = true;
    iframeRef.value.src = newUrl as string;
  }
});

// 在组件挂载时设置标签标题
onMounted(() => {
  if (appName.value) {
    // 查找当前标签并更新标题
    nextTick(() => {
      const currentTag = tagsViewStore.visitedViews.find(tag => tag.path === route.path);
      if (currentTag && currentTag.title !== appName.value) {
        tagsViewStore.updateVisitedView({
          ...currentTag,
          title: appName.value,
          fullPath: route.fullPath,
          query: route.query,
        });
      }
    });
  }
});

// 监听应用名称变化，更新标签标题
watch(() => appName.value, (newAppName) => {
  if (newAppName) {
    const currentTag = tagsViewStore.visitedViews.find(tag => tag.path === route.path);
    if (currentTag) {
      tagsViewStore.updateVisitedView({
        ...currentTag,
        title: newAppName,
        fullPath: route.fullPath,
        query: route.query,
      });
    }
  }
});
</script>

<style lang="scss" scoped>
.internal-app-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color);
}

.internal-app-content {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.internal-app-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: var(--el-bg-color);
  gap: 12px;
  
  .loading-icon {
    font-size: 24px;
    color: var(--el-color-primary);
    animation: rotate 2s linear infinite;
  }
  
  span {
    color: var(--el-text-color-regular);
    font-size: 14px;
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
