import { request } from "@utils";
import { Auth } from "@utils/auth";

const API_PATH = "/task/workflow/transfer";

const TransferAPI = {
  /** 创建传输任务（远端源，JSON） */
  createTask(body: TransferTaskCreate) {
    return request<ApiResponse<{ id: number }>>({
      url: `${API_PATH}/task`,
      method: "post",
      data: body,
    });
  },

  /** 创建传输任务（本地上传源，multipart：file + name + task_type + targets） */
  createLocalTask(formData: FormData) {
    return request<ApiResponse<{ id: number }>>({
      url: `${API_PATH}/task/upload`,
      method: "post",
      data: formData,
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  /** 分页查询传输任务 */
  pageTask(query?: TransferTaskQuery) {
    return request<ApiResponse<PageResult<TransferTaskItem>>>({
      url: `${API_PATH}/task/page`,
      method: "get",
      params: query,
    });
  },

  /** 任务详情（含步骤） */
  detailTask(id: number) {
    return request<ApiResponse<TransferTaskItem>>({
      url: `${API_PATH}/task/${id}`,
      method: "get",
    });
  },

  /** 取消任务 */
  cancelTask(id: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/task/${id}/cancel`,
      method: "post",
    });
  },

  /** 删除任务 */
  deleteTask(ids: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/task`,
      method: "delete",
      data: ids,
    });
  },
};

export default TransferAPI;

export type TransferStatus = "pending" | "running" | "success" | "failed" | "canceled";
export type TransferTaskType = "parallel" | "chain";
export type TransferSourceType = "local" | "remote";

/** 传输目标配置 */
export interface TransferTarget {
  target_id: number;
  target_path: string;
}

/** 创建传输任务参数 */
export interface TransferTaskCreate {
  name: string;
  task_type: TransferTaskType;
  source_type?: TransferSourceType;
  source_id?: number | null;
  source_path?: string | null;
  targets: TransferTarget[];
  /** 传输方式：stream 流式 / multipart 分片；不传用存储源默认 */
  transfer_mode?: "stream" | "multipart" | null;
  multipart_part_size?: number | null;
  multipart_concurrency?: number | null;
}

/** 传输步骤 */
export interface TransferStepItem {
  id: number;
  task_id: number;
  step_order: number;
  source_id?: number | null;
  source_path?: string | null;
  target_id: number;
  target_path: string;
  status: TransferStatus;
  progress: number;
  speed: number;
  total_size: number;
  transferred_size: number;
  error_msg?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
}

/** 传输任务（列表/详情/WS 推送） */
export interface TransferTaskItem extends BaseType {
  name: string;
  task_type: TransferTaskType;
  source_type: TransferSourceType;
  source_id?: number | null;
  source_path?: string | null;
  source_name?: string | null;
  source_size?: number | null;
  status: TransferStatus;
  total_size: number;
  transferred_size: number;
  progress: number;
  speed: number;
  error_msg?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  steps?: TransferStepItem[];
}

/** 传输任务分页查询 */
export interface TransferTaskQuery extends PageQuery {
  name?: string;
  task_type?: TransferTaskType;
  status?: TransferStatus;
}

/** 服务端 WS 推送消息 */
export type TransferPushMessage = { type: "task_update"; data: TransferTaskItem };

/** 传输任务 WebSocket 客户端（自动重连 + 心跳，参照 ChatSocket） */
export class TransferSocket {
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private heartbeatTimer: ReturnType<typeof setTimeout> | null = null;
  private attempt = 0;
  private stopped = false;
  private handlers: {
    onMessage: (msg: TransferPushMessage) => void;
    onStatus: (connected: boolean) => void;
  };

  constructor(handlers: {
    onMessage: (msg: TransferPushMessage) => void;
    onStatus: (connected: boolean) => void;
  }) {
    this.handlers = handlers;
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN || this.ws?.readyState === WebSocket.CONNECTING)
      return;
    this.stopped = false;
    try {
      const url = new URL(
        "/api/v1/task/workflow/transfer/ws",
        import.meta.env.VITE_APP_WS_ENDPOINT
      );
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
