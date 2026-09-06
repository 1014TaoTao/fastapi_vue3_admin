import { request } from "@utils";

const API_PATH = "/example/demo";

const DemoAPI = {
  listDemo(query: DemoPageQuery) {
    return request<ApiResponse<PageResult<DemoTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailDemo(query: number) {
    return request<ApiResponse<DemoTable>>({
      url: `${API_PATH}/detail/${query}`,
      method: "get",
    });
  },

  createDemo(body: DemoForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateDemo(id: number, body: DemoForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteDemo(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: body,
    });
  },

  batchDemo(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/status/batch`,
      method: "patch",
      data: body,
    });
  },

  exportDemo(body: DemoPageQuery) {
    return request<Blob>({
      url: `${API_PATH}/export`,
      method: "post",
      data: body,
      responseType: "blob",
    });
  },

  downloadTemplateDemo() {
    return request<Blob>({
      url: `${API_PATH}/download/template`,
      method: "post",
      responseType: "blob",
    });
  },

  importDemo(body: FormData) {
    return request<ApiResponse>({
      url: `${API_PATH}/import`,
      method: "post",
      data: body,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
};

export default DemoAPI;

export interface DemoPageQuery extends PageQuery, UserByQueryParams {
  name?: string;
  status?: number;
}

export interface DemoTable extends BaseType {
  name?: string;
  status?: number;
  description?: string;
  int_val?: number;
  bigint_val?: number;
  float_val?: number;
  bool_val?: boolean;
  date_val?: string;
  time_val?: string;
  datetime_val?: string;
  text_val?: string;
  json_val?: Record<string, any>;
}

export interface DemoForm extends BaseFormType {
  name?: string;
  status?: number;
  description?: string;
  int_val?: number;
  bigint_val?: number;
  float_val?: number;
  bool_val?: boolean;
  date_val?: string;
  time_val?: Date | string;
  datetime_val?: Date | string;
  text_val?: string;
  json_val?: Record<string, any>;
}
