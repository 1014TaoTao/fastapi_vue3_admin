import { request } from "@utils";
import { Auth } from "@utils/auth";

const API_PATH = "/system/chat";

const ChatAPI = {
  /** 会话列表 */
  listConversations() {
    return request<ApiResponse<ConversationItem[]>>({
      url: `${API_PATH}/conversations`,
      method: "get",
    });
  },

  /** 历史消息（before_id 为分页游标，取该 ID 之前更早的消息） */
  listMessages(params: ChatMessageQuery) {
    return request<ApiResponse<{ items: ChatMessageItem[]; has_more: boolean }>>({
      url: `${API_PATH}/messages`,
      method: "get",
      params,
    });
  },

  /** 发送消息 */
  sendMessage(body: { conversation_type: number; receiver_id: number; content: string }) {
    return request<ApiResponse<ChatMessageItem>>({
      url: `${API_PATH}/messages`,
      method: "post",
      data: body,
    });
  },

  /** 标记已读 */
  markRead(body: { conversation_type: number; receiver_id: number }) {
    return request<ApiResponse>({
      url: `${API_PATH}/read`,
      method: "post",
      data: body,
    });
  },

  /** 用户选择器 */
  listUsers(keyword?: string) {
    return request<ApiResponse<ChatUserItem[]>>({
      url: `${API_PATH}/users`,
      method: "get",
      params: { keyword },
    });
  },

  /** 创建群组 */
  createGroup(body: { name: string; member_ids: number[] }) {
    return request<ApiResponse<ChatGroupDetail>>({
      url: `${API_PATH}/groups`,
      method: "post",
      data: body,
    });
  },

  /** 群组详情 */
  getGroupDetail(groupId: number) {
    return request<ApiResponse<ChatGroupDetail>>({
      url: `${API_PATH}/groups/${groupId}`,
      method: "get",
    });
  },

  /** 修改群组 */
  updateGroup(groupId: number, body: { name?: string; announcement?: string }) {
    return request<ApiResponse>({
      url: `${API_PATH}/groups/${groupId}`,
      method: "put",
      data: body,
    });
  },

  /** 解散群组 */
  deleteGroup(groupId: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/groups/${groupId}`,
      method: "delete",
    });
  },

  /** 添加群成员 */
  addGroupMembers(groupId: number, memberIds: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/groups/${groupId}/members`,
      method: "post",
      data: { member_ids: memberIds },
    });
  },

  /** 移除群成员 */
  removeGroupMembers(groupId: number, memberIds: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/groups/${groupId}/members`,
      method: "delete",
      data: memberIds,
    });
  },

  /** 退出群组 */
  quitGroup(groupId: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/groups/${groupId}/quit`,
      method: "post",
    });
  },
};

export default ChatAPI;

/** 会话项 */
export interface ConversationItem {
  id: number | null;
  conversation_type: 1 | 2;
  name: string;
  avatar?: string | null;
  online: boolean;
  member_count: number;
  last_message?: string | null;
  last_time?: string | null;
  unread: number;
}

/** 消息项 */
export interface ChatMessageItem {
  id: number;
  conversation_type: 1 | 2;
  sender_id: number;
  sender_name?: string;
  sender_avatar?: string | null;
  receiver_id: number;
  content: string;
  status: 0 | 1;
  created_time: string;
}

/** 历史消息查询 */
export interface ChatMessageQuery {
  conversation_type: 1 | 2;
  receiver_id: number;
  before_id?: number;
  page_size?: number;
}

/** 用户项 */
export interface ChatUserItem {
  id: number;
  name: string;
  username: string;
  avatar?: string | null;
}

/** 群组详情 */
export interface ChatGroupDetail {
  id: number;
  name: string;
  avatar?: string | null;
  announcement?: string | null;
  owner_id: number;
  member_count: number;
  members: ChatUserItem[];
}

/** 服务端推送消息 */
export type ChatPushMessage =
  | { type: "message"; data: ChatMessageItem }
  | { type: "read"; conversation_type: 1; peer_id: number; target_id: number }
  | { type: "presence"; user_id: number; online: boolean };

/** 聊天 WebSocket 客户端（轻量封装：自动重连 + 心跳） */
export class ChatSocket {
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private heartbeatTimer: ReturnType<typeof setTimeout> | null = null;
  private attempt = 0;
  private stopped = false;
  private handlers: {
    onMessage: (msg: ChatPushMessage) => void;
    onStatus: (connected: boolean) => void;
  };

  constructor(handlers: {
    onMessage: (msg: ChatPushMessage) => void;
    onStatus: (connected: boolean) => void;
  }) {
    this.handlers = handlers;
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN || this.ws?.readyState === WebSocket.CONNECTING)
      return;
    this.stopped = false;
    try {
      const url = new URL("/api/v1/system/chat/ws", import.meta.env.VITE_APP_WS_ENDPOINT);
      const token = Auth.getAccessToken();
      // 令牌经 Sec-WebSocket-Protocol 传递，避免出现在 URL 与服务端 access log 中
      this.ws = token
        ? new WebSocket(url.toString(), ["access_token", `access_token.${token}`])
        : new WebSocket(url.toString());
      this.ws.onopen = () => this.handleOpen();
      this.ws.onmessage = (event) => this.handleMessage(event);
      this.ws.onclose = (event) => this.handleClose(event);
      this.ws.onerror = () => this.ws?.close();
    } catch {
      this.scheduleReconnect();
    }
  }

  disconnect() {
    this.stopped = true;
    this.clearTimers();
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close(1000, "close");
      this.ws = null;
    }
  }

  private handleOpen() {
    this.attempt = 0;
    this.handlers.onStatus(true);
    this.heartbeatTimer = setTimeout(() => {
      try {
        this.ws?.send("ping");
      } catch {
        /* ignore */
      }
    }, 30000);
    this.pingTimer = setInterval(() => {
      try {
        this.ws?.send("ping");
      } catch {
        /* ignore */
      }
    }, 60000);
  }

  private handleMessage(event: MessageEvent) {
    if (event.data === "pong") return;
    try {
      this.handlers.onMessage(JSON.parse(event.data));
    } catch {
      /* ignore */
    }
  }

  private handleClose(event?: CloseEvent) {
    this.ws = null;
    this.clearTimers();
    this.handlers.onStatus(false);
    // 4001 = 令牌无效（登出/失效），不再自动重连
    if (event?.code === 4001) {
      this.stopped = true;
      return;
    }
    if (!this.stopped) this.scheduleReconnect();
  }

  private scheduleReconnect() {
    if (this.stopped || this.reconnectTimer) return;
    const delay = Math.min(2000 * Math.pow(1.5, this.attempt), 30000);
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.attempt += 1;
      this.connect();
    }, delay);
  }

  private clearTimers() {
    if (this.pingTimer) clearInterval(this.pingTimer);
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.heartbeatTimer) clearTimeout(this.heartbeatTimer);
    this.pingTimer = null;
    this.heartbeatTimer = null;
  }

  get connected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
