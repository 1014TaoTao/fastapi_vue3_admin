import { http } from '@/http'

const USER_BASE_URL = '/system/user'

/**
 * 用户管理 API
 * 与 web 端 module_system/user.ts 对齐（完整字段定义）
 */
const UserAPI = {
  /**
   * 个人中心用户信息
   *
   * @returns 登录用户昵称、头像信息，包括角色和权限
   */
  getCurrentUserInfo(): Promise<UserInfo> {
    return http.Get(`${USER_BASE_URL}/current/info`)
  },

  /**
   * 当前用户头像上传
   *
   * @param body 上传参数
   * @param body.filePath 本地临时文件路径（uni.chooseImage 选择结果）
   * @param body.name 上传字段名，后端约定为 file
   * @returns uni.uploadFile 成功回调（statusCode + data 响应体字符串，需调用方解析）
   */
  uploadCurrentUserAvatar(body: { filePath: string, name?: string }): Promise<{ statusCode: number, data: string }> {
    return http.Post('/file/upload?upload_type=avatar', body, { requestType: 'upload' })
  },

  /**
   * 修改个人中心用户信息
   *
   * @param body
   * @returns 修改后的用户信息
   */
  updateCurrentUserInfo(body: UserProfileForm): Promise<UserInfo> {
    return http.Put(`${USER_BASE_URL}/current/info/update`, body)
  },

  /**
   * 修改个人中心用户密码
   *
   * @param body
   * @returns 修改后的用户信息
   */
  changeCurrentUserPassword(body: PasswordChangeForm): Promise<void> {
    return http.Put(`${USER_BASE_URL}/password/change`, body)
  },

  /**
   * 注册用户（公开接口）
   *
   * @param body 注册参数
   * @param body.username 用户名（字母开头，3-32 位）
   * @param body.password 密码（6-128 位）
   * @param body.name 昵称（可选）
   * @returns 注册结果
   */
  registerUser(body: RegisterForm): Promise<void> {
    return http.Post(`${USER_BASE_URL}/register`, body, { meta: { ignoreAuth: true } })
  },

  /**
   * 忘记密码（公开接口）
   *
   * @param body 重置参数
   * @param body.username 用户名（字母开头，3-32 位）
   * @param body.new_password 新密码（6-128 位）
   * @returns 重置结果
   */
  forgetPassword(body: ForgetPasswordForm): Promise<void> {
    return http.Post(`${USER_BASE_URL}/password/forget`, body, { meta: { ignoreAuth: true } })
  },

  /**
   * 重置用户密码
   *
   * @param id 用户ID
   * @param body 新密码
   * @param body.password 新密码
   */
  resetPassword(id: number, body: { password: string }): Promise<void> {
    return http.Put(`${USER_BASE_URL}/password/reset/${id}`, body)
  },

  /**
   * 批量修改用户状态
   *
   * @param body 批量操作参数
   * @param body.ids 用户ID列表
   * @param body.status 目标状态
   */
  batchStatus(body: BatchSetStatus): Promise<void> {
    return http.Patch(`${USER_BASE_URL}/status/batch`, body)
  },

  /**
   * 导出用户
   *
   * @param params 导出参数
   */
  exportUsers(params?: Record<string, any>): Promise<unknown> {
    return http.Post(`${USER_BASE_URL}/export`, params)
  },

  /**
   * 获取用户导入模板
   */
  getImportTemplate(): Promise<unknown> {
    return http.Get(`${USER_BASE_URL}/import/template`)
  },

  /**
   * 导入用户数据
   *
   * @param body 导入数据
   */
  importData(body: Record<string, any>): Promise<void> {
    return http.Post(`${USER_BASE_URL}/import/data`, body)
  },

  /**
   * 获取用户分页列表
   *
   * @param queryParams 查询参数
   */
  getUserPage(queryParams: UserPageQuery): Promise<PageResult<UserInfo>> {
    return http.Get(`${USER_BASE_URL}/list`, queryParams)
  },

  /**
   * 获取用户表单详情
   *
   * @param userId 用户ID
   * @returns 用户表单详情
   */
  getUserDetail(userId: number): Promise<UserForm> {
    return http.Get(`${USER_BASE_URL}/detail/${userId}`)
  },

  /**
   * 添加用户
   *
   * @param body 用户表单数据
   */
  addUser(body: UserForm): Promise<void> {
    return http.Post(`${USER_BASE_URL}/create`, body)
  },

  /**
   * 修改用户
   *
   * @param body 用户表单数据
   */
  updateUser(body: UserForm): Promise<void> {
    return http.Put(`${USER_BASE_URL}/update/${body.id}`, body)
  },

  /**
   * 删除用户
   *
   * @param ids 用户ID数组
   */
  deleteUser(ids: number[]): Promise<void> {
    return http.Delete(`${USER_BASE_URL}/delete`, ids)
  },
}

export default UserAPI

/* 忘记密码申请（与后端 UserForgetPasswordSchema 一致：仅用户名，后端不会直接改密） */
export interface ForgetPasswordForm {
  username: string
}

/* 注册表单 */
export interface RegisterForm {
  username: string
  password: string
  name?: string
}

/* 分页查询表单 */
export interface UserPageQuery extends PageQuery {
  username?: string
  name?: string
  mobile?: string
  email?: string
  dept_id?: number
  status?: number
  start_time?: string
  end_time?: string
}

/* 搜索选择器数据类型 */
export interface searchSelectDataType {
  name?: string
  status?: number
}

/* 用户表单 */
export interface UserForm extends BaseFormType {
  username?: string
  name?: string
  dept_id?: number
  dept_name?: string
  role_ids?: number[]
  role_names?: string[]
  position_ids?: number[]
  position_names?: string[]
  password?: string
  gender?: number
  email?: string
  mobile?: string
  avatar?: string
  is_superuser?: boolean
  status?: number
  description?: string
}

/* 登录用户信息 */
export interface UserInfo extends BaseType {
  username?: string
  name?: string
  avatar?: string
  email?: string
  mobile?: string
  gender?: string
  password?: string
  menus?: MenuTable[]
  dept?: deptTreeType
  dept_id?: deptTreeType['id']
  dept_name?: deptTreeType['name']
  roles?: roleSelectorType[]
  role_names?: roleSelectorType['name'][]
  role_ids?: roleSelectorType['id'][]
  positions?: positionSelectorType[]
  position_names?: positionSelectorType['name'][]
  position_ids?: positionSelectorType['id'][]
  is_superuser?: boolean
  last_login?: string
  gitee_login?: string
  github_login?: string
  wx_login?: string
  qq_login?: string
  status?: number
  description?: string
}

/* 菜单表 */
export interface MenuTable extends BaseType {
  name?: string
  type?: number
  icon?: string
  order?: number
  permission?: string
  route_name?: string
  route_path?: string
  component_path?: string
  redirect?: string
  parent_id?: number
  parent_name?: string
  keep_alive?: boolean
  hidden?: boolean
  always_show?: boolean
  title?: string
  params?: { key: string, value: string }[]
  affix?: boolean
  status?: number
  description?: string
  children?: MenuTable[]
}

/* 部门树 */
export interface deptTreeType {
  id?: number
  name?: string
  parent_id?: number
  children?: deptTreeType[]
}

/* 角色选择器 */
export interface roleSelectorType {
  id?: number
  name?: string
  status?: number
  description?: string
}

/* 职位选择器 */
export interface positionSelectorType {
  id?: number
  name?: string
  status?: number
  description?: string
}

/* 个人中心用户信息表单 */
export interface UserProfileForm extends BaseFormType {
  name?: string
  gender?: string
  mobile?: string
  email?: string
  username?: string
  dept_name?: string
  positions?: positionSelectorType[]
  roles?: roleSelectorType[]
  avatar?: string
  created_time?: string
}

/* 修改密码表单 */
export interface PasswordChangeForm {
  old_password: string
  new_password: string
  confirm_password: string
}

/* 重置密码表单 */
export interface ResetPasswordForm {
  id: number
  password: string
}

/* 批量设置状态 */
export interface BatchSetStatus {
  ids: number[]
  status: number
}
