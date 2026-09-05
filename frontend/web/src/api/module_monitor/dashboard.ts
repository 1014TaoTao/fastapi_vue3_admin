import { request } from "@utils";
import { createSSEClient, httpEndpoint, type SSEClient } from "@utils/sse";
import type { HealthItem } from "@/mock/dashboard";

const API_PATH = "/monitor/online";

export interface RecentLoginItem {
  username: string;
  status: number; // 1:成功 2:失败
  login_time: string;
  login_ip?: string;
  login_location?: string;
}

export interface DashboardStats {
  online_users: number;
  total_users: number;
  today_login_count: number;
  today_unique_users: number;
  week_user_created: number;
  recent_logins: RecentLoginItem[];
}

const DashboardAPI = {
  getStats() {
    return request<ApiResponse<DashboardStats>>({
      url: `${API_PATH}/stats`,
      method: "get",
    });
  },

  /**
   * 订阅系统健康实时流（SSE，30s 一拍，免认证）
   * 返回取消订阅函数；连接断开后客户端内部自动重连
   */
  subscribeHealthStream(onItems: (items: HealthItem[]) => void): () => void {
    const client = createSSEClient({
      url: new URL(
        "/api/v1/monitor/health/stream",
        httpEndpoint(import.meta.env.VITE_APP_WS_ENDPOINT)
      ).toString(),
      getToken: () => null, // 健康端点免认证，与 /check 一致
      onEvent: (_event, data) => {
        try {
          onItems(mapReadinessToHealthItems(JSON.parse(data)));
        } catch {
          /* ignore */
        }
      },
    });
    return () => client.disconnect();
  },
};

export default DashboardAPI;

/** 健康 SSE 载荷（对应后端 ServiceInfoOut：进程 + DB / Redis 连通状态） */
interface ServiceInfoPayload {
  db_status: number;
  redis_status: number;
}

const OK_ITEM_CLASS = "bg-success/12 text-success";
const ERROR_ITEM_CLASS = "bg-error/12 text-error";

function dependencyItem(title: string, icon: string, status: number): HealthItem {
  const ok = status === 1;
  return {
    icon,
    class: ok ? OK_ITEM_CLASS : ERROR_ITEM_CLASS,
    title,
    status: ok ? "正常" : "异常",
    time: "",
  };
}

/** 健康载荷 → 健康卡片列表（数据库 / Redis） */
function mapReadinessToHealthItems(payload: ServiceInfoPayload): HealthItem[] {
  return [
    dependencyItem("数据库", "ri:database-2-line", payload.db_status),
    dependencyItem("Redis", "ri:server-line", payload.redis_status),
  ];
}

export type { SSEClient };
