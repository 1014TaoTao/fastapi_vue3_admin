import { request } from "@utils";

const API_PATH = "/task/storage/node";

const NodeAPI = {
  pageNode(query?: TablePageQuery) {
    return request<ApiResponse<PageResult<SourceTable>>>({
      url: `${API_PATH}/page`,
      method: "get",
      params: query,
    });
  },

  listNode(query?: Omit<TablePageQuery, "page_no" | "page_size">) {
    return request<ApiResponse<SourceTable[]>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailNode(id: number) {
    return request<ApiResponse<SourceTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  createNode(body: SourceForm) {
    return request<ApiResponse<SourceTable>>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateNode(id: number, body: SourceForm) {
    return request<ApiResponse<SourceTable>>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteNode(ids: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: ids,
    });
  },

  testNode(id: number) {
    return request<ApiResponse<boolean>>({
      url: `${API_PATH}/test/${id}`,
      method: "post",
    });
  },

  testNodeConfig(body: SourceForm & { source_id?: number }) {
    return request<ApiResponse<boolean>>({
      url: `${API_PATH}/test`,
      method: "post",
      data: body,
    });
  },

  /** 支持的存储协议列表（协议枚举 + 默认端口） */
  getProtocols() {
    return request<ApiResponse<ProtocolItem[]>>({
      url: `${API_PATH}/protocols`,
      method: "get",
    });
  },

  /** 存储 SDK 高级配置字段定义（按协议分组） */
  getAdvancedFields() {
    return request<ApiResponse<Record<string, AdvancedFieldDef[]>>>({
      url: `${API_PATH}/advanced-fields`,
      method: "get",
    });
  },
};

export default NodeAPI;

/** 存储协议项 */
export interface ProtocolItem {
  protocol: string;
  name: string;
  default_port: number;
}

/** SDK 高级配置字段定义（后端按协议模型自动生成） */
export interface AdvancedFieldDef {
  key: string;
  label: string;
  default: string | number | boolean | null;
  /** 组件类型：text | number | boolean | select */
  type: "text" | "number" | "boolean" | "select";
  options?: string[];
}

export interface SourceForm extends BaseFormType {
  name?: string;
  protocol?: string;
  host?: string;
  port?: number;
  username?: string;
  password?: string;
  bucket?: string;
  endpoint?: string;
  region?: string;
  path_prefix?: string;
  scheme?: string;
  encrypt_type?: number;
  connection_mode?: number;
  encoding?: string;
  is_secure?: boolean;
  implicit_tls?: boolean;
  /** 分片大小(MB，对象存储分片上传，每个端点独立配置) */
  multipart_part_size?: number;
  /** 分片上传并发路数 */
  multipart_concurrency?: number;
  /** 分片上传内存预算(MB) */
  multipart_memory_budget?: number;
  /** SDK 高级配置(JSON，按协议解析；留空使用 SDK 默认值) */
  advanced_config?: Record<string, string | number | boolean> | null;
  is_default?: boolean;
  status?: number;
  description?: string;
}

export interface SourceTable extends BaseType {
  name?: string;
  protocol?: string;
  host?: string;
  port?: number;
  username?: string;
  has_password?: boolean;
  bucket?: string;
  endpoint?: string;
  region?: string;
  path_prefix?: string;
  scheme?: string;
  encrypt_type?: number;
  connection_mode?: number;
  encoding?: string;
  is_secure?: boolean;
  implicit_tls?: boolean;
  multipart_part_size?: number;
  multipart_concurrency?: number;
  multipart_memory_budget?: number;
  advanced_config?: Record<string, string | number | boolean> | null;
  is_default?: boolean;
  status?: number;
  description?: string;
}

export interface TablePageQuery extends PageQuery {
  name?: string;
  protocol?: string;
  status?: number;
}
