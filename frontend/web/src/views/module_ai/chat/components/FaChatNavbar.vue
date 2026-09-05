<template>
  <div class="chat-navbar">
    <div class="navbar-left">
      <button class="collapse-btn" @click="toggleSidebar">
        <FaSvgIcon
          v-if="!props.isSidebarCollapsed"
          :icon="resolveIconForFaSvgIcon('layout_leftbar_close_line')"
          class="size-6"
        />
        <FaSvgIcon
          v-else
          :icon="resolveIconForFaSvgIcon('layout_leftbar_open_line')"
          class="size-6"
        />
      </button>
      <span class="navbar-title">FA 助手</span>
    </div>

    <div class="navbar-right">
      <ElTag
        class="connection-status"
        effect="plain"
        :type="connectionStatus === 'connected' ? 'success' : 'danger'"
      >
        <ElIcon :class="['status-icon', connectionStatus]">
          <Connection v-if="connectionStatus === 'connected'" />
          <Loading v-else-if="connectionStatus === 'connecting'" />
          <Warning v-else />
        </ElIcon>
        <span class="status-text">{{ connectionStatusText }}</span>
      </ElTag>
      <ElButton text :icon="Setting" @click="handleToggleConnection">
        {{ isConnected ? "断开连接" : "重新连接" }}
      </ElButton>
      <ElButton v-if="hasMessages" text :icon="Delete" @click="handleClearChat">
        清空对话
      </ElButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Connection, Loading, Warning, Delete, Setting } from "@element-plus/icons-vue";
import { resolveIconForFaSvgIcon } from "@utils";

interface Props {
  connectionStatus: "connected" | "connecting" | "disconnected";
  isConnected: boolean;
  messageCount: number;
  isSidebarCollapsed?: boolean;
}

interface Emits {
  (e: "clear-chat"): void;
  (e: "toggle-connection"): void;
  (e: "toggle-sidebar"): void;
}

const props = withDefaults(defineProps<Props>(), {
  isSidebarCollapsed: false,
});
const emit = defineEmits<Emits>();

const connectionStatusText = computed(() => {
  switch (props.connectionStatus) {
    case "connected":
      return "已连接";
    case "connecting":
      return "连接中...";
    case "disconnected":
      return "未连接";
    default:
      return "未知状态";
  }
});

const hasMessages = computed(() => props.messageCount > 0);

const handleClearChat = () => emit("clear-chat");
const handleToggleConnection = () => emit("toggle-connection");
const toggleSidebar = () => emit("toggle-sidebar");
</script>

<style lang="scss" scoped>
.chat-navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;

  .navbar-left {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .navbar-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  .navbar-right {
    display: flex;
    flex-wrap: nowrap;
    gap: 12px;
    align-items: center;

    :deep(.el-button) {
      margin: 0;
    }
  }
}

.collapse-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  color: var(--el-text-color-regular);
  cursor: pointer;
  background: transparent;
  border: none;
  border-radius: 4px;
  transition:
    background-color 0.2s,
    color 0.2s;

  &:hover {
    color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
  }

  &:focus-visible {
    outline: 2px solid var(--el-color-primary);
    outline-offset: 2px;
  }

  & > div {
    color: inherit;
  }
}

.connection-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 32px;
  padding: 0 12px;
  margin: 0;
  font-size: 14px;
  line-height: 1;

  :deep(.el-tag__content) {
    display: inline-flex;
    gap: 6px;
    align-items: center;
  }

  .status-icon {
    &.connected {
      color: var(--el-color-success);
    }

    &.connecting {
      color: var(--el-color-warning);
    }

    &.disconnected {
      color: var(--el-color-danger);
    }
  }

  .status-text {
    color: var(--el-text-color-secondary);
  }
}
</style>
