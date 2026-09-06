<template>
  <div class="fa-full-height">
    <ElSplitter :style="'height: 100%'">
      <ElSplitterPanel :size="isSidebarCollapsed ? 64 : 200" :min="64" :max="400">
        <div class="sidebar-container h-full" :class="{ collapsed: isSidebarCollapsed }">
          <FaSidebar
            ref="sidebarRef"
            :current-session-id="currentSessionId"
            :is-collapsed="isSidebarCollapsed"
            @select-session="handleSelectSession"
            @new-session="handleNewSession"
            @open-config="configDrawerVisible = true"
          />
        </div>
      </ElSplitterPanel>
      <ElSplitterPanel :min="300">
        <div class="chat-container flex flex-col h-full overflow-hidden">
          <div class="chat-header">
            <FaChatNavbar
              :connection-status="connectionStatus"
              :is-connected="isConnected"
              :message-count="messages.length"
              :is-sidebar-collapsed="isSidebarCollapsed"
              @clear-chat="handleClearChat"
              @toggle-connection="toggleConnection"
              @toggle-sidebar="toggleSidebar"
            />
          </div>
          <div class="chat-main flex-1 overflow-hidden">
            <FaChatMessages
              ref="chatMessagesRef"
              :messages="messages"
              :error="error"
              @prompt-click="handleSendMessage"
              @error-close="error = ''"
            />
          </div>
          <div class="chat-footer">
            <FaChatInput
              :disabled="!isConnected"
              :sending="sending"
              :is-connected="isConnected"
              @send="handleSendMessage"
              @stop="handleStopMessage"
            />
          </div>
        </div>
      </ElSplitterPanel>
    </ElSplitter>

    <FaAiModelConfigPanel v-model="configDrawerVisible" />
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: "Chat",
  inheritAttrs: false,
});

import { ElMessage, ElMessageBox } from "element-plus";
import AiChatAPI, { type ChatSession } from "@/api/module_ai/chat";
import { Auth } from "@utils/auth";
import type { ChatMessage, UploadedFile } from "./types";
import FaSidebar from "./components/FaSidebar.vue";
import FaChatNavbar from "./components/FaChatNavbar.vue";
import FaChatMessages from "./components/FaChatMessages.vue";
import FaChatInput from "./components/FaChatInput.vue";
import FaAiModelConfigPanel from "./components/FaAiModelConfigPanel.vue";

// 状态
const messages = ref<ChatMessage[]>([]);
const sending = ref(false);
const isConnected = ref(false);
const connectionStatus = ref<"connected" | "connecting" | "disconnected">("disconnected");
const error = ref("");
const currentSessionId = ref<string | null>(null);
const isSidebarCollapsed = ref(false);
const configDrawerVisible = ref(false);

// Refs
const chatMessagesRef = ref<{ scrollToBottom: () => void }>();
const sidebarRef = ref<{ loadSessions: () => void }>();

// WebSocket
let ws: WebSocket | null = null;
const WS_URL = import.meta.env.VITE_APP_WS_ENDPOINT;

// ============ WebSocket 操作 ============
const connectWebSocket = () => {
  if (ws?.readyState === WebSocket.OPEN) return;

  connectionStatus.value = "connecting";
  error.value = "";

  try {
    const url = new URL("/api/v1/ai/chat/ws", WS_URL);
    const token = Auth.getAccessToken();
    // 令牌经 Sec-WebSocket-Protocol 传递，避免出现在 URL 与服务端 access log 中
    ws = token
      ? new WebSocket(url.toString(), ["access_token", `access_token.${token}`])
      : new WebSocket(url.toString());

    ws.onopen = () => {
      isConnected.value = true;
      connectionStatus.value = "connected";
      ElMessage.success("连接成功");
    };

    ws.onmessage = (event) => handleWebSocketMessage(event.data);

    ws.onclose = () => {
      isConnected.value = false;
      connectionStatus.value = "disconnected";
      finishLoadingMessages();
    };

    ws.onerror = () => {
      isConnected.value = false;
      connectionStatus.value = "disconnected";
      ElMessage.error("连接失败，请检查服务器状态");
      finishLoadingMessages();
    };
  } catch {
    connectionStatus.value = "disconnected";
    error.value = "无法创建连接";
  }
};

const disconnectWebSocket = () => {
  if (ws) {
    ws.close(1000, "用户主动断开");
    ws = null;
  }
  isConnected.value = false;
  connectionStatus.value = "disconnected";
  finishLoadingMessages();
};

const toggleConnection = () => {
  if (isConnected.value) {
    disconnectWebSocket();
    ElMessage.info("已断开连接");
  } else {
    connectWebSocket();
  }
};

// ============ 消息处理 ============
const handleWebSocketMessage = (data: string) => {
  const text = data || "";

  // 服务端结束标记
  if (text === "[DONE]") {
    finishLoadingMessages();
    sending.value = false;
    return;
  }

  // 服务端停止确认标记
  if (text === "[STOPPED]") {
    finishLoadingMessages();
    sending.value = false;
    ElMessage.info("已停止生成");
    return;
  }

  const lastMessage = messages.value[messages.value.length - 1];

  if (lastMessage?.type === "assistant" && lastMessage.loading) {
    lastMessage.content += text;
  } else {
    addMessage("assistant", text);
  }

  chatMessagesRef.value?.scrollToBottom();
};

const addMessage = (type: "user" | "assistant", content: string, files?: UploadedFile[]) => {
  messages.value.push({
    id: generateId(),
    type,
    content,
    timestamp: Date.now(),
    collapsed: content.length > 200,
    files,
    loading: type === "assistant" ? true : false,
  });
};

const finishLoadingMessages = () => {
  messages.value.forEach((msg) => {
    if (msg.type === "assistant" && msg.loading) {
      msg.loading = false;
      msg.collapsed = msg.content.length > 200;
    }
  });
};

const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).slice(2);
};

// ============ 发送消息 ============
const handleSendMessage = async (message: string, files?: UploadedFile[]) => {
  if ((!message && !files) || !isConnected.value || sending.value) return;

  // 结束上一个加载中的消息
  finishLoadingMessages();

  // 创建新会话（如果没有）
  if (!currentSessionId.value) {
    const success = await createNewSession(message);
    if (!success) return;
  }

  // 添加用户消息
  addMessage("user", message, files);

  // 添加加载中的助手消息
  messages.value.push({
    id: generateId(),
    type: "assistant",
    content: "",
    timestamp: Date.now(),
    loading: true,
  });

  sending.value = true;
  chatMessagesRef.value?.scrollToBottom();

  try {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(
        JSON.stringify({
          message,
          session_id: currentSessionId.value,
          files: files?.map((f) => ({ name: f.name, type: f.type, size: f.size })),
        })
      );
      // 注意：sending 状态保持为 true，等待 [DONE] / [STOPPED] 标记清除
    } else {
      throw new Error("WebSocket 连接未建立");
    }
  } catch {
    messages.value.pop();
    error.value = "发送消息失败，请检查连接状态";
    sending.value = false;
  }
};

// 停止当前生成
const handleStopMessage = () => {
  if (ws?.readyState !== WebSocket.OPEN) return;
  try {
    ws.send(
      JSON.stringify({
        action: "stop",
        session_id: currentSessionId.value,
      })
    );
  } catch {
    ElMessage.error("停止指令发送失败");
  }
};

const createNewSession = async (firstMessage: string): Promise<boolean> => {
  try {
    const title = firstMessage.slice(0, 20) + (firstMessage.length > 20 ? "..." : "");
    const res = await AiChatAPI.createSession({ title });

    if (res.data?.code === 0 || res.data?.success) {
      currentSessionId.value = res.data.data?.id ?? null;
      sidebarRef.value?.loadSessions();
      return true;
    }
    throw new Error("创建会话失败");
  } catch {
    return false;
  }
};

// ============ 会话操作 ============
const handleSelectSession = async (session: ChatSession) => {
  currentSessionId.value = session.id;
  messages.value = [];

  try {
    const response = await AiChatAPI.getSessionDetail(session.id);
    if (response.data?.code !== 0) {
      return;
    }

    const sessionData = response.data.data || {};
    const runs = sessionData.runs || [];

    runs.forEach((run: { messages?: { role: string; content: string }[] }) => {
      const runMessages = run.messages || [];
      runMessages.forEach((msg: { role: string; content: string }) => {
        if (msg.role === "user" || msg.role === "assistant") {
          addMessage(msg.role, msg.content);
        }
      });
    });

    ElMessage.success(`已切换到会话：${session.title}`);
  } catch {
    ElMessage.error("获取会话详情失败");
  }
};

const handleNewSession = () => {
  currentSessionId.value = null;
  messages.value = [];
  ElMessage.success("已开启新对话");
};

const handleClearChat = async () => {
  try {
    await ElMessageBox.confirm("确定要清空当前对话吗？此操作不可恢复。", "确认清空", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    messages.value = [];
    ElMessage.success("对话已清空");
  } catch {
    ElMessage.info("已取消清空对话");
  }
};

const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
};

// ============ 生命周期 ============
onMounted(connectWebSocket);
onUnmounted(disconnectWebSocket);
</script>

<style lang="scss" scoped>
/* 拆分条容器样式 */
:deep(.el-splitter) {
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  box-shadow: var(--el-box-shadow-light);
}

:deep(.el-splitter-panel) {
  overflow: hidden;
}

.sidebar-container {
  background: transparent;
  transition: width 0.3s ease;
}

.chat-header {
  height: auto;
  padding: 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.chat-main {
  flex: 1;
  overflow: hidden;
}

.chat-footer {
  height: auto;
  min-height: 80px;
  padding: 0;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
