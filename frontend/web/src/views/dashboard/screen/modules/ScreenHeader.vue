<template>
  <header class="screen-header">
    <div class="header-left">
      <span class="dot" :class="{ pulse: online }" />
      <span class="text-xs">SYSTEM ONLINE</span>
    </div>
    <h1 class="screen-title">
      <span class="deco-line" />
      FastapiAdmin · 智能运营数据监控平台
      <span class="deco-line" />
    </h1>
    <div class="header-right">
      <ElTooltip :content="isFs ? '退出全屏' : '进入全屏'" placement="bottom">
        <button class="fullscreen-btn" @click="handleToggle">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            class="fs-icon"
          >
            <path
              v-if="isFs"
              d="M4 14h2v2h2v2H4v-4zm12 0h2v2h2v2h-4v-4zM4 4h4v2H6v2H4V4zm14 0h4v4h-2V6h-2V4z"
            />
            <path
              v-else
              d="M4 4h4v2H6v2H4V4zm14 0h4v4h-2V6h-2V4zM4 20h4v-2H6v-2H4v4zm14 0h4v-4h-2v2h-2v2z"
            />
          </svg>
        </button>
      </ElTooltip>
      <span class="header-time font-mono text-sm">{{ currentTime }}</span>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, inject, onMounted, onUnmounted } from "vue";

defineOptions({ name: "ScreenHeader" });

const toggleFullscreen = inject<() => void>("toggleFullscreen", () => {});
const isFs = inject("isFullscreen", ref(false));

const online = ref(true);
const currentTime = ref("");

let timer = 0;
onMounted(() => {
  const tick = () => {
    currentTime.value = new Date().toLocaleString("zh-CN", { hour12: false });
  };
  tick();
  timer = window.setInterval(tick, 1000);
});
onUnmounted(() => clearInterval(timer));

function handleToggle() {
  toggleFullscreen();
}
</script>

<style scoped>
.screen-header {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 32px 14px;
  margin-bottom: 12px;
  border-bottom: 1px solid rgb(26 40 80 / 60%);
}

.header-left {
  display: flex;
  gap: 8px;
  align-items: center;
  width: 140px;
  font-size: 12px;
  opacity: 0.7;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: flex-end;
  width: 200px;
}

.header-time {
  font-variant-numeric: tabular-nums;
  opacity: 0.7;
}

.dot {
  display: inline-block;
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  background: #00d4ff;
  border-radius: 50%;
}

.pulse {
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%,
  100% {
    box-shadow: 0 0 8px #00d4ff;
    opacity: 1;
  }

  50% {
    opacity: 0.3;
  }
}

.screen-title {
  flex: 1;
  font-size: 20px;
  font-weight: 700;
  text-align: center;
  letter-spacing: 4px;
  text-shadow: 0 0 30px rgb(0 212 255 / 50%);
}

.deco-line {
  display: inline-block;
  width: 40px;
  height: 1px;
  margin: 0 12px;
  vertical-align: middle;
  background: linear-gradient(90deg, transparent, #00d4ff, transparent);
}

.fullscreen-btn {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  color: var(--accent, #00d4ff);
  cursor: pointer;
  background: rgb(0 212 255 / 10%);
  border: 1px solid rgb(0 212 255 / 30%);
  border-radius: 6px;
  transition: background 0.2s;
}

.fullscreen-btn:hover {
  background: rgb(0 212 255 / 20%);
}

.fs-icon {
  width: 16px;
  height: 16px;
}
</style>
