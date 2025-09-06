import request from "@/utils/request";

export const ResourceAPI = {
  /**
   * 获取目录列表
   * @param query 查询参数
   */
  getResourceList(query: ResourceListQuery) {
    return request<ApiResponse<ResourceItem[]>>({
      url: `/resource/resource/list`,
      method: "get",
      params: query,
    });
  },

  /**
   * 搜索资源
   * @param body 搜索条件
   */
  searchResource(body: ResourceSearchQuery) {
    return request<ApiResponse<ResourceItem[]>>({
      url: `/resource/resource/search`,
      method: "post",
      data: body,
    });
  },

  /**
   * 上传文件
   * @param formData 文件数据
   */
  uploadFile(formData: FormData) {
    return request<ApiResponse<UploadFilePath>>({
      url: `/resource/resource/upload`,
      method: "post",
      data: formData,
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  /**
   * 下载文件
   * @param path 文件路径
   */
  downloadFile(path: string) {
    return request<Blob>({
      url: `/resource/resource/download`,
      method: "get",
      params: { path },
      responseType: "blob",
    });
  },

  /**
   * 删除文件或目录
   * @param body 文件路径数组
   */
  deleteResource(body: string[]) {
    return request<ApiResponse>({
      url: `/resource/resource/delete`,
      method: "delete",
      data: body,
    });
  },

  /**
   * 移动文件或目录
   * @param body 移动参数
   */
  moveResource(body: ResourceMoveQuery) {
    return request<ApiResponse>({
      url: `/resource/resource/move`,
      method: "post",
      data: body,
    });
  },

  /**
   * 复制文件或目录
   * @param body 复制参数
   */
  copyResource(body: ResourceCopyQuery) {
    return request<ApiResponse>({
      url: `/resource/resource/copy`,
      method: "post",
      data: body,
    });
  },

  /**
   * 重命名文件或目录
   * @param body 重命名参数
   */
  renameResource(body: ResourceRenameQuery) {
    return request<ApiResponse>({
      url: `/resource/resource/rename`,
      method: "post",
      data: body,
    });
  },

  /**
   * 创建目录
   * @param body 创建目录参数
   */
  createDirectory(body: ResourceCreateDirQuery) {
    return request<ApiResponse>({
      url: `/resource/resource/create-dir`,
      method: "post",
      data: body,
    });
  },

  /**
   * 获取资源统计信息
   */
  getResourceStats() {
    return request<ApiResponse<ResourceStats>>({
      url: `/resource/resource/stats`,
      method: "get",
    });
  },

  /**
   * 导出资源列表
   * @param body 导出条件
   */
  exportResource(body: ResourceSearchQuery) {
    return request<Blob>({
      url: `/resource/resource/export`,
      method: "post",
      data: body,
      responseType: "blob",
    });
  },
};

export default ResourceAPI;

/**
 * 资源列表查询参数
 */
export interface ResourceListQuery {
  /** 目录路径 */
  path: string;
  /** 递归获取 */
  recursive?: boolean;
  /** 包含隐藏文件 */
  include_hidden?: boolean;
}

/**
 * 资源搜索查询参数
 */
export interface ResourceSearchQuery {
  /** 关键词 */
  keyword?: string;
  /** 文件类型 */
  file_type?: string;
  /** 资源类型 */
  resource_type?: string;
  /** 最小文件大小 */
  min_size?: number;
  /** 最大文件大小 */
  max_size?: number;
  /** 开始时间 */
  start_date?: string;
  /** 结束时间 */
  end_date?: string;
  /** 文件扩展名 */
  extensions?: string[];
  /** 包含隐藏文件 */
  include_hidden?: boolean;
  /** 最大深度 */
  max_depth?: number;
}

/**
 * 资源项信息
 */
export interface ResourceItem {
  /** 文件/目录名称 */
  name: string;
  /** 完整路径 */
  path: string;
  /** 是否为目录 */
  is_directory: boolean;
  /** 文件大小（字节） */
  size?: number;
  /** 文件扩展名 */
  extension?: string;
  /** 修改时间 */
  modified_time: string;
  /** 创建时间 */
  created_time: string;
  /** 是否为隐藏文件 */
  is_hidden: boolean;
  /** 文件类型 */
  file_type?: string;
  /** 资源类型 */
  resource_type?: string;
  /** 文件URL（如果是图片等可预览文件） */
  file_url?: string;
  /** 缩略图URL */
  thumbnail_url?: string;
}

/**
 * 资源移动参数
 */
export interface ResourceMoveQuery {
  /** 源路径 */
  source_path: string;
  /** 目标路径 */
  target_path: string;
  /** 是否覆盖 */
  overwrite?: boolean;
}

/**
 * 资源复制参数
 */
export interface ResourceCopyQuery {
  /** 源路径 */
  source_path: string;
  /** 目标路径 */
  target_path: string;
  /** 是否覆盖 */
  overwrite?: boolean;
}

/**
 * 资源重命名参数
 */
export interface ResourceRenameQuery {
  /** 原路径 */
  old_path: string;
  /** 新名称 */
  new_name: string;
}

/**
 * 创建目录参数
 */
export interface ResourceCreateDirQuery {
  /** 父目录路径 */
  parent_path: string;
  /** 目录名称 */
  dir_name: string;
}

/**
 * 资源统计信息
 */
export interface ResourceStats {
  /** 总文件数 */
  total_files: number;
  /** 总目录数 */
  total_directories: number;
  /** 总大小（字节） */
  total_size: number;
  /** 按文件类型统计 */
  file_type_stats: Array<{
    file_type: string;
    count: number;
    size: number;
  }>;
  /** 按资源类型统计 */
  resource_type_stats: Array<{
    resource_type: string;
    count: number;
    size: number;
  }>;
  /** 最近修改的文件 */
  recent_files: ResourceItem[];
}
