import { request } from "@utils";

const API_PATH = "/task/cronjob/node";

const NodeAPI = {
  getNodeTypeOptions() {
    return request<ApiResponse<NodeType[]>>({
      url: `${API_PATH}/options`,
      method: "get",
    });
  },

  listNode(query: NodePageQuery) {
    return request<ApiResponse<PageResult<NodeTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailNode(query: number) {
    return request<ApiResponse<NodeTable>>({
      url: `${API_PATH}/detail/${query}`,
      method: "get",
    });
  },

  createNode(body: NodeForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateNode(id: number, body: NodeForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteNode(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: body,
    });
  },

  clearNode() {
    return request<ApiResponse>({
      url: `${API_PATH}/clear`,
      method: "delete",
    });
  },

  batchNode(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/status/batch`,
      method: "patch",
      data: body,
    });
  },

  executeNode(id: number) {
    return request<ApiResponse<ExecuteNodeResult>>({
      url: `${API_PATH}/execute/${id}`,
      method: "post",
    });
  },
};

export default NodeAPI;

export interface NodePageQuery extends PageQuery, UserByQueryParams {
  name?: string;
  code?: string;
  status?: number;
}

/** 正式排程的触发器类型（空 = 不排程，仅手动执行一次） */
export type TriggerType = "cron" | "interval" | "date";

export interface ExecuteNodeResult {
  job_id: string;
  status: string;
  trigger: string;
}

export interface NodeTable extends BaseType {
  name: string;
  code: string;
  jobstore?: string;
  executor?: string;
  trigger?: TriggerType;
  trigger_args?: string;
  func?: string;
  args?: string;
  kwargs?: string;
  coalesce?: boolean;
  max_instances?: number;
  start_date?: string;
  end_date?: string;
  status?: number;
  description?: string;
  next_run_time?: string;
  last_run_time?: string;
  last_run_status?: number;
}

export interface NodeForm extends BaseFormType {
  name: string;
  code?: string;
  jobstore?: string;
  executor?: string;
  func?: string;
  args?: string;
  kwargs?: string;
  coalesce?: boolean;
  max_instances?: number;
  trigger?: TriggerType | "";
  trigger_args?: string;
  start_date?: string;
  end_date?: string;
  description?: string;
}

export interface NodeType {
  id: number;
  name: string;
  code: string;
  func?: string;
  args?: string;
  kwargs?: string;
}
