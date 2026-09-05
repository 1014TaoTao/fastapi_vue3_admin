import type { BatchSetStatus } from './user'
import { http } from '@/http'

const SYSTEM_BASE = '/system'

/**
 * 公告管理 API
 * 与 web 端 module_system/notice.ts 对齐（完整字段定义）
 */
export const NoticeAPI = {
  getPage(params?: Record<string, any>) {
    return http.Get<PageResult<NoticeItem>>(`${SYSTEM_BASE}/notice/list`, params)
  },
  getDetail(id: number): Promise<NoticeItem> {
    return http.Get(`${SYSTEM_BASE}/notice/detail/${id}`)
  },
  create(data: NoticeForm): Promise<NoticeItem> {
    return http.Post(`${SYSTEM_BASE}/notice/create`, data)
  },
  update(id: number, data: NoticeForm): Promise<NoticeItem> {
    return http.Put(`${SYSTEM_BASE}/notice/update/${id}`, data)
  },
  remove(ids: number[]): Promise<void> {
    return http.Delete(`${SYSTEM_BASE}/notice/delete`, ids)
  },
  batchStatus(data: BatchSetStatus): Promise<void> {
    return http.Patch(`${SYSTEM_BASE}/notice/status/batch`, data)
  },
  getAvailable(): Promise<NoticeItem[]> {
    return http.Get(`${SYSTEM_BASE}/notice/available`)
  },
}

export interface NoticeForm extends BaseFormType {
  notice_title?: string
  notice_type?: string
  notice_content?: string
  status?: number
  description?: string
}

export interface NoticeItem extends BaseType, NoticeForm {}
