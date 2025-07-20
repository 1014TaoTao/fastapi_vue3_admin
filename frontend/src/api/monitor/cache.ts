import request from "@/utils/request";

const CacheAPI = {
  getCacheInfo() {
    return request<ApiResponse>({
      url: `/monitor/cache/info`,
      method: "get",
    });
  },

  getCacheNames() {
    return request<ApiResponse>({
      url: `/monitor/cache/get/names`,
      method: "get",
    });
  },

  getCacheKeys(cacheName: string) {
    return request<ApiResponse>({
      url: `/monitor/cache/get/keys/${cacheName}`,
      method: "get",
    });
  },

  getCacheValue(cacheName: string, cacheKey: string) {
    return request<ApiResponse>({
      url: `/monitor/cache/get/value/${cacheName}/${cacheKey}`,
      method: "get",
    });
  },

  deleteCacheName(cacheName: string) {
    return request<ApiResponse>({
      url: `/monitor/cache/delete/name/${cacheName}`,
      method: "delete",
    });
  },

  deleteCacheKey(cacheKey: string) {
    return request<ApiResponse>({
      url: `/monitor/cache/delete/key/${cacheKey}`,
      method: "delete",
    });
  },

  deleteCacheAll() {
    return request<ApiResponse>({
      url: "/monitor/cache/delete/all",
      method: "delete",
    });
  },
};

export default CacheAPI;

export interface CacheForm {
  cache_name: string;
  cache_key: string;
  cache_value: string;
}

export interface CacheInfo {
  cache_key: string;
  cache_name: string;
  cache_value: string;
  remark: string;
}

export interface CommandStats {
  name: string;
  value: string;
}

export interface RedisInfo {
  redis_version: string;
  redis_mode: string;
  tcp_port: number;
  connected_clients: number;
  uptime_in_days: number;
  used_memory_human: string;
  used_cpu_user_children: string;
  maxmemory_human: string;
  aof_enabled: string;
  rdb_last_bgsave_status: string;
  instantaneous_input_kbps: number;
  instantaneous_output_kbps: number;
}

export interface CacheMonitor {
  command_stats: CommandStats[];
  db_size: number;
  info: RedisInfo;
}
