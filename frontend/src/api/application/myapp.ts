import request from "@/utils/request";

export const ApplicationAPI = {
  /**
   * 获取应用详情
   * @param id 应用ID
   */
  getApplicationDetail(id: number) {
    return request<ApiResponse<ApplicationInfo>>({
      url: `/application/application/detail/${id}`,
      method: "get",
    });
  },

  /**
   * 查询应用列表
   * @param query 查询参数
   */
  getApplicationList(query: ApplicationPageQuery) {
    return request<ApiResponse<PageResult<ApplicationInfo[]>>>({
      url: `/application/application/list`,
      method: "get",
      params: query,
    });
  },

  /**
   * 创建应用
   * @param body 应用信息
   */
  createApplication(body: ApplicationForm) {
    return request<ApiResponse>({
      url: `/application/application/create`,
      method: "post",
      data: body,
    });
  },

  /**
   * 修改应用
   * @param id 应用ID
   * @param body 应用信息
   */
  updateApplication(id: number, body: ApplicationForm) {
    return request<ApiResponse>({
      url: `/application/application/update/${id}`,
      method: "put",
      data: body,
    });
  },

  /**
   * 删除应用
   * @param body 应用ID数组
   */
  deleteApplication(body: number[]) {
    return request<ApiResponse>({
      url: `/application/application/delete`,
      method: "delete",
      data: body,
    });
  },

  /**
   * 批量修改应用状态
   * @param body 批量操作参数
   */
  batchAvailableApplication(body: BatchType) {
    return request<ApiResponse>({
      url: `/application/application/available/setting`,
      method: "patch",
      data: body,
    });
  },
};

export default ApplicationAPI;

/**
 * 应用分页查询参数
 */
export interface ApplicationPageQuery extends PageQuery {
  /** 应用名称 */
  name?: string;
  /** 是否启用 */
  status?: boolean;
  /** 创建人 */
  creator?: number;
  /** 开始时间 */
  start_time?: string;
  /** 结束时间 */
  end_time?: string;
  /** 排序字段,格式:[{'field':'asc/desc'}] */
  order_by?: string;
}

/**
 * 应用信息
 */
export interface ApplicationInfo {
  /** 应用ID */
  id?: number;
  /** 应用名称 */
  name?: string;
  /** 访问地址 */
  access_url?: string;
  /** 图标地址 */
  icon_url?: string;
  /** 是否启用 */
  status?: boolean;
  /** 应用描述 */
  description?: string;
  /** 创建时间 */
  created_at?: string;
  /** 更新时间 */
  updated_at?: string;
  /** 创建人 */
  creator?: creatorType;
}

/**
 * 应用表单
 */
export interface ApplicationForm {
  /** 应用ID */
  id?: number;
  /** 应用名称 */
  name: string;
  /** 访问地址 */
  access_url: string;
  /** 图标地址 */
  icon_url: string;
  /** 是否启用 */
  status: boolean;
  /** 应用描述 */
  description?: string;
}
