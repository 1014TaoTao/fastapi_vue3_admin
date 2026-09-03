import { request } from "@utils";

const API_PATH = "/task/workflow/storage";

const StorageAPI = {
  /** 查询文件/目录列表。传 page_no/page_size 时分页返回（PageResult），否则返回全量数组。 */
  listFiles(params?: FileListParams) {
    return request<ApiResponse<StorageObject[] | StoragePageResult>>({
      url: `${API_PATH}/list`,
      method: "get",
      params,
    });
  },

  /** 查询存储源账号下全部存储桶（对象存储） */
  listBuckets(params?: { source_id?: number | null }) {
    return request<ApiResponse<string[]>>({
      url: `${API_PATH}/buckets`,
      method: "get",
      params,
    });
  },

  /** 上传文件（可传 onProgress 回调获取 0-100 进度百分比） */
  uploadFile(formData: FormData, onProgress?: (percent: number) => void) {
    return request<ApiResponse<Record<string, unknown>>>({
      url: `${API_PATH}/upload`,
      method: "post",
      data: formData,
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: onProgress
        ? (e) => {
            if (e.total) onProgress(Math.min(99, Math.round((e.loaded / e.total) * 100)));
          }
        : undefined,
    });
  },

  /** 下载目录：后端递归拉取并打包 ZIP 返回 */
  downloadDir(body: FilePathBody) {
    return request<Blob>({
      url: `${API_PATH}/download_dir`,
      method: "post",
      data: body,
      responseType: "blob",
    });
  },

  downloadFile(body: FilePathBody) {
    return request<Blob>({
      url: `${API_PATH}/download`,
      method: "post",
      data: body,
      responseType: "blob",
    });
  },

  deleteFile(body: FilePathBody) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: body,
    });
  },

  /** 重命名/移动（同存储源内） */
  renameFile(body: FileRenameBody) {
    return request<ApiResponse<Record<string, unknown>>>({
      url: `${API_PATH}/rename`,
      method: "put",
      data: body,
    });
  },

  /** 新建目录 */
  mkdir(body: { source_id?: number | null; remote_dir: string; bucket?: string }) {
    return request<ApiResponse<Record<string, unknown>>>({
      url: `${API_PATH}/mkdir`,
      method: "post",
      data: body,
    });
  },

  /** 生成分享链接（对象存储为预签名 URL） */
  shareFile(body: {
    source_id?: number | null;
    remote_path: string;
    expire?: number;
    bucket?: string;
  }) {
    return request<ApiResponse<string | null>>({
      url: `${API_PATH}/share`,
      method: "post",
      data: body,
    });
  },

  /** 复制/移动文件（move=true 为移动，同源移动即重命名） */
  copyFile(body: FileCopyBody) {
    return request<ApiResponse<Record<string, unknown>>>({
      url: `${API_PATH}/copy`,
      method: "post",
      data: body,
    });
  },
};

export default StorageAPI;

export interface FileListParams {
  source_id?: number | null;
  prefix?: string;
  bucket?: string;
  /** 每页数量（传了才走游标分页，不传返回全量） */
  page_size?: number;
  /** 下一页游标（上一页返回的 next_cursor） */
  cursor?: string;
}

/** 游标分页结果（与后端 StoragePage 对齐：无总条数，只能顺序翻页） */
export interface StoragePageResult {
  items: StorageObject[];
  has_next: boolean;
  next_cursor: string | null;
}

export interface FilePathBody {
  remote_path: string;
  source_id?: number | null;
  bucket?: string;
}

export interface FileRenameBody {
  source_id?: number | null;
  source_path: string;
  target_path: string;
  bucket?: string;
}

export interface FileCopyBody {
  source_id?: number | null;
  source_path: string;
  target_id: number;
  target_path: string;
  move?: boolean;
  bucket?: string;
}

export interface StorageObject {
  name?: string;
  key?: string;
  is_dir?: boolean;
  size?: number;
  modified_time?: string;
}
