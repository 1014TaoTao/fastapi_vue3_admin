/**
 * 通用 SSE（Server-Sent Events）客户端
 * 基于 fetch 流式读取：支持 Authorization 头携带令牌（浏览器原生 EventSource
 * 无法自定义请求头）、命名事件分发、空闲注释行（心跳）忽略与指数退避自动重连。
 */
import { Auth } from "@utils/auth";

export interface SSEClient {
  /** 断开连接并停止重连（幂等） */
  disconnect: () => void;
  /** 当前是否处于连接打开状态 */
  readonly connected: boolean;
}

export interface SSEClientOptions {
  /** 完整 SSE 端点 URL（http/https） */
  url: string;
  /** 事件回调：event 为 SSE 事件名（缺省 "message"），data 为原始载荷 */
  onEvent: (event: string, data: string) => void;
  /** 连接状态变化回调 */
  onStatus?: (connected: boolean) => void;
  /** 不可恢复错误回调（如 401/403）：收到后停止自动重连 */
  onFatal?: (reason: string) => void;
  /** 访问令牌提供者；缺省取本地登录态令牌，返回空则不带 Authorization 头 */
  getToken?: () => string | null;
}

/** ws(s):// 基址转 http(s)://：SSE 走普通 HTTP，复用同一环境变量配置 */
export function httpEndpoint(endpoint: string): string {
  return endpoint.replace(/^ws/, "http");
}

const RECONNECT_BASE_DELAY = 2000;
const RECONNECT_MAX_DELAY = 30000;

export function createSSEClient(options: SSEClientOptions): SSEClient {
  let controller: AbortController | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let attempt = 0;
  let stopped = false;
  let open = false;

  const setConnected = (value: boolean) => {
    if (open !== value) {
      open = value;
      options.onStatus?.(value);
    }
  };

  async function connect() {
    if (stopped) return;
    controller = new AbortController();
    const token = (options.getToken ?? (() => Auth.getAccessToken()))();
    const headers: Record<string, string> = { Accept: "text/event-stream" };
    if (token) headers.Authorization = `Bearer ${token}`;
    try {
      const res = await fetch(options.url, { headers, signal: controller.signal });
      // 令牌无效/无权限：重连也不会成功，交由上层处理（对齐原 WS 4001 语义）
      if (res.status === 401 || res.status === 403) {
        setConnected(false);
        options.onFatal?.(`认证失败(${res.status})`);
        return;
      }
      if (!res.ok || !res.body) throw new Error(`SSE 连接失败(${res.status})`);
      attempt = 0;
      setConnected(true);
      await consume(res.body);
      setConnected(false);
      if (!stopped) scheduleReconnect(); // 服务端正常关流：继续重连
    } catch (err) {
      setConnected(false);
      if (stopped || (err instanceof DOMException && err.name === "AbortError")) return;
      scheduleReconnect();
    }
  }

  /** 消费响应流：按空行分帧交由 dispatch 解析 */
  async function consume(body: ReadableStream<Uint8Array>) {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let index: number;
      while ((index = buffer.indexOf("\n\n")) >= 0) {
        dispatch(buffer.slice(0, index));
        buffer = buffer.slice(index + 2);
      }
    }
  }

  /** 解析单帧：`:` 开头为注释行（服务端心跳保活）直接忽略 */
  function dispatch(frame: string) {
    let event = "message";
    const dataLines: string[] = [];
    for (const line of frame.split("\n")) {
      if (line.startsWith(":")) continue;
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).replace(/^ /, ""));
    }
    if (dataLines.length > 0) options.onEvent(event, dataLines.join("\n"));
  }

  function scheduleReconnect() {
    if (stopped || reconnectTimer) return;
    const delay = Math.min(RECONNECT_BASE_DELAY * Math.pow(1.5, attempt), RECONNECT_MAX_DELAY);
    attempt += 1;
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, delay);
  }

  connect();

  return {
    disconnect() {
      stopped = true;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      controller?.abort();
      controller = null;
      setConnected(false);
    },
    get connected() {
      return open;
    },
  };
}
