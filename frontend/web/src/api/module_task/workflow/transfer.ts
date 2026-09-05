import { request } from "@utils";
import { createSSEClient, httpEndpoint, type SSEClient } from "@utils/sse";

const API_PATH = "/workflow/transfer";

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

/** 服务端 SSE 推送消息 */
export type TransferPushMessage = { type: "task_update"; data: TransferTaskItem };

/** 传输任务 SSE 客户端（自动重连；令牌走 Authorization 头；连接生命周期由视图层按"是否存在进行中任务"控制） */
export class TransferStream {
  private client: SSEClient | null = null;
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

  /** 建立连接（幂等：已存在连接实例时直接返回，重连由客户端内部负责） */
  connect() {
    if (this.client) return;
    const url = new URL(
      "/api/v1/task/workflow/transfer/stream",
      httpEndpoint(import.meta.env.VITE_APP_WS_ENDPOINT)
    );
    this.client = createSSEClient({
      url: url.toString(),
      onEvent: (event, data) => {
        if (event !== "task_update") return;
        try {
          this.handlers.onMessage(JSON.parse(data));
        } catch {
          /* ignore */
        }
      },
      onStatus: (connected) => this.handlers.onStatus(connected),
      // 令牌失效：释放实例，视图层下次 sync 时以新令牌重建
      onFatal: () => {
        this.client = null;
      },
    });
  }

  disconnect() {
    this.client?.disconnect();
    this.client = null;
  }

  get connected() {
    return this.client?.connected ?? false;
  }
}
