import { request } from "@utils";
import { MenuTable, MenuForm } from "@/api/module_system/menu";

const API_PATH = "/system/user";

export const UserAPI = {
  getCurrentUserInfo(checkDataScope?: boolean) {
    return request<ApiResponse<UserInfo>>({
      url: `${API_PATH}/current/info`,
      method: "get",
      params: checkDataScope === false ? { check_data_scope: false } : undefined,
    });
  },

  uploadCurrentUserAvatar(body: FormData) {
    return request<ApiResponse<UploadFilePath>>({
      url: `/common/file/upload?upload_type=avatar`,
      method: "post",
      data: body,
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  updateCurrentUserInfo(body: InfoFormState) {
    return request<ApiResponse<UserInfo>>({
      url: `${API_PATH}/current/info/update`,
      method: "put",
      data: body,
    });
  },

  changeCurrentUserPassword(body: PasswordFormState) {
    return request<ApiResponse>({
      url: `${API_PATH}/password/change`,
      method: "put",
      data: body,
    });
  },

  resetUserPassword(id: number, body: ResetPasswordForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/password/reset/${id}`,
      method: "put",
      data: body,
    });
  },

  forgetPassword(body: ForgetPasswordForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/password/forget`,
      method: "post",
      data: body,
    });
  },

  register(body: RegisterForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/register`,
      method: "post",
      data: body,
    });
  },

  listUser(query: UserPageQuery) {
    return request<ApiResponse<PageResult<UserInfo>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailUser(id: number) {
    return request<ApiResponse<UserInfo>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  createUser(body: UserForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateUser(id: number, body: UserForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteUser(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: body,
    });
  },

  batchUser(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/status/batch`,
      method: "patch",
      data: body,
    });
  },

  exportUser(query: UserPageQuery) {
    return request<Blob>({
      url: `${API_PATH}/export`,
      method: "post",
      data: query,
      responseType: "blob",
    });
  },

  downloadTemplateUser() {
    return request<Blob>({
      url: `${API_PATH}/import/template`,
      method: "get",
      responseType: "blob",
    });
  },

  importUser(body: FormData) {
    return request<ApiResponse>({
      url: `${API_PATH}/import/data`,
      method: "post",
      data: body,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
};

export default UserAPI;

export interface ForgetPasswordForm {
  username: string;
}

export interface RegisterForm {
  username: string;
  password: string;
  confirmPassword: string;
  name?: string;
}

export interface UserPageQuery extends PageQuery, UserByQueryParams {
  username?: string;
  name?: string;
  mobile?: string;
  email?: string;
  dept_id?: number;
  status?: number;
}

export interface searchSelectDataType {
  name?: string;
  status?: number;
}

export interface UserInfo extends BaseType {
  username?: string;
  name?: string;
  avatar?: string;
  email?: string;
  mobile?: string;
  gender?: string;
  password?: string;
  menus?: MenuTable[];
  dept?: deptTreeType;
  dept_id?: deptTreeType["id"];
  dept_name?: deptTreeType["name"];
  roles?: roleSelectorType[];
  role_names?: roleSelectorType["name"][];
  role_ids?: roleSelectorType["id"][];
  positions?: positionSelectorType[];
  position_names?: positionSelectorType["name"][];
  position_ids?: positionSelectorType["id"][];
  is_superuser?: boolean;

  last_login?: string;
  created_by?: CommonType;
  updated_by?: CommonType;
  deleted_by?: CommonType;
  gitee_login?: string;
  github_login?: string;
  wx_login?: string;
  qq_login?: string;
  status?: number;
  description?: string;
}

export interface deptTreeType {
  id?: number;
  name?: string;
  parent_id?: number;
  children?: deptTreeType[];
}

export interface roleSelectorType {
  id?: number;
  name?: string;
  code?: string;
  status?: number;
  description?: string;
  menus?: MenuForm[];
}

export interface positionSelectorType {
  id?: number;
  name?: string;
  status?: number;
  description?: string;
}

export interface InfoFormState {
  id?: number;
  name?: string;
  gender?: string;
  mobile?: string;
  email?: string;
  username?: string;
  dept_name?: string;
  dept?: deptTreeType;
  positions?: positionSelectorType[];
  roles?: roleSelectorType[];
  avatar?: string;
  created_time?: string;
  updated_time?: string;
  status?: number;
  description?: string;
  gitee_login?: string;
  github_login?: string;
  wx_login?: string;
  qq_login?: string;
}

export interface PasswordFormState {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export interface ResetPasswordForm {
  password: string;
}

export interface UserForm extends BaseFormType {
  username?: string;
  name?: string;
  dept_id?: number;
  dept_name?: string;
  role_ids?: number[];
  role_names?: string[];
  position_ids?: number[];
  position_names?: string[];
  password?: string;
  gender?: string;
  email?: string;
  mobile?: string;
  is_superuser?: boolean;
  avatar?: string;
  status?: number;
  description?: string;
}

export interface CurrentUserFormState {
  name?: string;
  gender?: string;
  mobile?: string;
  email?: string;
  avatar?: string;
}
