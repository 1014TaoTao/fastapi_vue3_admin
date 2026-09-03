/**
 * 聊天状态管理模块
 *
 * ## 主要功能
 *
 * - 全局未读数统计（顶部角标）
 * - 聊天 WebSocket 生命周期管理
 * - 在线状态缓存
 * - 当前会话消息实时分发
 *
 * @module store/modules/chat.store
 */
import { store } from "@stores";
import ChatAPI, { ChatMessageItem, ChatPushMessage, ChatSocket } from "@/api/module_system/chat";
import { defineStore } from "pinia";
import { ref } from "vue";

export const useChatStore = defineStore("chatStore", () => {
  /** 全局未读数 */
  const unreadTotal = ref(0);
  /** WebSocket 连接状态 */
  const wsConnected = ref(false);
  /** 在线用户缓存 */
  const onlineUsers = ref<Record<number, boolean>>({});

  let socket: ChatSocket | null = null;
  /** 当前打开的会话（用于实时消息分发） */
  const activeConversation = ref<{ type: 1 | 2; id: number } | null>(null);
  let onNewMessage: ((msg: ChatMessageItem) => void) | null = null;

  /** 初始化聊天 WebSocket（登录后调用一次） */
  function initChat() {
    if (socket) {
      // 已断开（如令牌失效后）时重新建立连接
      if (!socket.connected && !wsConnected.value) {
        socket.connect();
      }
      return;
    }
    socket = new ChatSocket({
      onMessage: handlePush,
      onStatus: (connected) => {
        wsConnected.value = connected;
      },
    });
    socket.connect();
  }

  /** 断开聊天 WebSocket（登出时调用） */
  function disconnectChat() {
    socket?.disconnect();
    socket = null;
    wsConnected.value = false;
  }

  /** 拉取会话并刷新全局未读数 */
  async function refreshUnread() {
    try {
      const response = await ChatAPI.listConversations();
      const items = Array.isArray(response.data?.data) ? response.data.data : [];
      unreadTotal.value = items.reduce((sum, item) => sum + (item.unread || 0), 0);
    } catch {
      /* 忽略网络错误 */
    }
  }

  /** 设置当前会话（页面进入会话时） */
  function setActiveConversation(
    conv: { type: 1 | 2; id: number },
    handler: (msg: ChatMessageItem) => void
  ) {
    activeConversation.value = conv;
    onNewMessage = handler;
  }

  /** 清除当前会话 */
  function clearActiveConversation() {
    activeConversation.value = null;
    onNewMessage = null;
  }

  /** 服务端推送分发 */
  function handlePush(msg: ChatPushMessage) {
    if (msg.type === "message") {
      const m = msg.data;
      const active = activeConversation.value;
      const inActive =
        active !== null && m.conversation_type === active.type && m.receiver_id === active.id;
      if (inActive) {
        onNewMessage?.(m);
      } else {
        unreadTotal.value += 1;
      }
    } else if (msg.type === "presence") {
      if (onlineUsers.value[msg.user_id] !== msg.online) {
        onlineUsers.value = { ...onlineUsers.value, [msg.user_id]: msg.online };
      }
    }
  }

  /** 标记会话已读并通知服务端 */
  async function markRead(conv: { type: 1 | 2; id: number }) {
    await ChatAPI.markRead({ conversation_type: conv.type, receiver_id: conv.id }).catch(() => {
      /* 忽略 */
    });
    await refreshUnread();
  }

  /** 清空聊天状态（登出） */
  function clearUserInfo() {
    disconnectChat();
    unreadTotal.value = 0;
    onlineUsers.value = {};
    activeConversation.value = null;
    onNewMessage = null;
  }

  return {
    unreadTotal,
    wsConnected,
    onlineUsers,
    initChat,
    disconnectChat,
    refreshUnread,
    setActiveConversation,
    clearActiveConversation,
    markRead,
    clearUserInfo,
  };
});

export function useChatStoreHook() {
  return useChatStore(store);
}
