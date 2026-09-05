/**
 * AI 聊天 API 模块（对应后端 module_ai 插件）
 */
import { http } from '@/http'

const AI_BASE = '/ai/chat'

export const ChatAPI = {
  /** 获取会话列表 */
  getSessions(params?: Record<string, any>): Promise<PageResult<ChatSession>> {
    return http.Get(`${AI_BASE}/list`, params)
  },
  /** 创建会话 */
  createSession(title?: string): Promise<ChatSession> {
    return http.Post(`${AI_BASE}/create`, { title: title || '新对话' })
  },
  /** 获取会话详情（含消息列表） */
  getDetail(sessionId: number): Promise<{ messages: ChatMessage[] }> {
    return http.Get(`${AI_BASE}/detail/${sessionId}`)
  },
  /** 更新会话标题 */
  updateSession(sessionId: number, data: Record<string, any>): Promise<void> {
    return http.Put(`${AI_BASE}/update/${sessionId}`, data)
  },
  /** 删除会话 */
  removeSession(ids: number[]): Promise<void> {
    return http.Delete(`${AI_BASE}/delete`, ids)
  },
  /** 发送消息 (非流式) */
  sendMessage(sessionId: number, content: string): Promise<ChatMessage> {
    // silent：聊天页将错误内联展示为 AI 消息，避免与全局 toast 重复提示
    return http.Post(`${AI_BASE}/ai-chat`, { session_id: sessionId, content }, { meta: { silent: true } })
  },
  /** 获取 AI 模型配置列表 */
  getModels(): Promise<AIModelList> {
    return http.Get(`${AI_BASE}/model`)
  },
  /** 新增 AI 模型配置 */
  createModel(data: AIModelForm): Promise<AIModelConfig> {
    return http.Post(`${AI_BASE}/model`, data)
  },
  /** 更新 AI 模型配置 */
  updateModel(configId: number, data: AIModelForm): Promise<AIModelConfig> {
    return http.Put(`${AI_BASE}/model/${configId}`, data)
  },
  /** 删除 AI 模型配置 */
  deleteModel(configId: number): Promise<void> {
    return http.Delete(`${AI_BASE}/model/${configId}`)
  },
  /** 切换激活的 AI 模型配置 */
  activateModel(configId: number): Promise<void> {
    return http.Post(`${AI_BASE}/model/${configId}/activate`)
  },
}

/* ==================== 类型定义 ==================== */

export interface ChatSession {
  id: number
  session_name?: string
  title?: string
  created_at?: number
}

export interface ChatMessage {
  id?: string
  role: string
  content: string
  created_at?: number
  time?: string
}

export interface AIModelForm {
  name: string
  base_url: string
  api_key: string
  model_id: string
  temperature?: number
}

export interface AIModelConfig extends AIModelForm {
  config_id: number
  is_active?: boolean
  created_time?: string
  updated_time?: string
}

/** 模型配置列表响应：items 为配置数组，active_id 为当前激活的配置 id */
export interface AIModelList {
  items: AIModelConfig[]
  active_id: number | null
}
