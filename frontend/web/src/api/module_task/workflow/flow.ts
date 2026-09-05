import { request } from "@utils";

const API_PATH = "/workflow/flow";

const FlowAPI = {
  pageFlow(query?: FlowPageQuery) {
    return request<ApiResponse<PageResult<FlowTable>>>({
      url: `${API_PATH}/page`,
      method: "get",
      params: query,
    });
  },

  listFlow(query?: Omit<FlowPageQuery, "page_no" | "page_size">) {
    return request<ApiResponse<FlowTable[]>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailFlow(id: number) {
    return request<ApiResponse<FlowTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  createFlow(body: FlowForm) {
    return request<ApiResponse<FlowTable>>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateFlow(id: number, body: FlowForm) {
    return request<ApiResponse<FlowTable>>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteFlow(ids: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: ids,
    });
  },

  /** 执行传输流程：遍历画布连线生成传输任务，返回任务ID列表；source_paths 为执行时选择的源文件/目录映射 {source_id: 路径} */
  executeFlow(id: number, body?: { source_paths?: Record<string, string> }) {
    return request<ApiResponse<number[]>>({
      url: `${API_PATH}/execute/${id}`,
      method: "post",
      data: body,
    });
  },
};

export default FlowAPI;

/** 流程目标节点配置 */
export interface FlowTarget {
  target_id: number;
  target_path: string;
}

/** 流程源节点配置（由画布启用连线实时派生） */
export interface FlowSource {
  source_id: number;
  source_name?: string | null;
}

/** 表单中的目标行（提交前会清理空项） */
export interface FlowTargetInput {
  target_id?: number | null;
  target_path?: string;
}

export interface FlowForm extends BaseFormType {
  name?: string;
  task_type?: "parallel" | "chain";
  targets?: FlowTargetInput[];
  /** VueFlow 画布数据 {nodes, edges}（后端按 graph 派生 sources/targets） */
  graph?: { nodes?: Record<string, any>[]; edges?: Record<string, any>[] } | null;
  status?: number;
  description?: string;
}

export interface FlowTable extends BaseType {
  name?: string;
  sources?: FlowSource[];
  task_type?: "parallel" | "chain";
  targets?: FlowTarget[];
  /** VueFlow 画布数据 {nodes, edges}（列表接口不返回，仅详情返回） */
  graph?: { nodes?: Record<string, any>[]; edges?: Record<string, any>[] } | null;
  /** 画布节点/连线统计（列表接口返回） */
  graph_stats?: { node_count?: number; edge_count?: number } | null;
  status?: number;
  description?: string;
}

export interface FlowPageQuery extends PageQuery {
  name?: string;
  task_type?: "parallel" | "chain";
  status?: number;
}
