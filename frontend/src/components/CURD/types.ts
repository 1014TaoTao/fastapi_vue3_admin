import type { DialogProps, DrawerProps, FormItemRule, PaginationProps } from "element-plus";
import type { FormProps, TableProps, ColProps, ButtonProps, CardProps } from "element-plus";
import type PageContent from "./PageContent.vue";
import type PageModal from "./PageModal.vue";
import type PageSearch from "./PageSearch.vue";
import type { CSSProperties } from "vue";

export type PageSearchInstance = InstanceType<typeof PageSearch>;
export type PageContentInstance = InstanceType<typeof PageContent>;
export type PageModalInstance = InstanceType<typeof PageModal>;

/**
 * 通用对象类型
 */
export type IObject = Record<string, any>;

/**
 * 组件类型定义
 */
type DateComponent = "date-picker" | "time-picker" | "time-select" | "custom-tag" | "input-tag";
type InputComponent = "input" | "select" | "input-number" | "cascader" | "tree-select";
type OtherComponent = "text" | "radio" | "checkbox" | "switch" | "icon-select" | "custom";
export type ISearchComponent = DateComponent | InputComponent;
export type IComponentType = DateComponent | InputComponent | OtherComponent;

/**
 * 工具按钮类型定义
 */
type ToolbarLeft = "add" | "delete" | "import" | "export";
type ToolbarRight = "refresh" | "filter" | "imports" | "exports" | "search";
type ToolbarTable = "edit" | "view" | "delete";

/**
 * 工具按钮接口
 */
export type IToolsButton = {
  /** 按钮名称 */
  name: string;
  /** 按钮文本 */
  text?: string;
  /** 权限标识(可以是完整权限字符串如'sys:user:add'或操作权限如'add') */
  perm?: Array<string> | string;
  /** 按钮属性 */
  attrs?: Partial<ButtonProps> & { style?: CSSProperties };
  /** 条件渲染 */
  render?: (row: IObject) => boolean;
  /** 按钮提示（支持字符串或Tooltip属性对象） */
  tooltip?: string | IObject;
};

/**
 * 工具按钮默认类型
 */
export type IToolsDefault = ToolbarLeft | ToolbarRight | ToolbarTable | IToolsButton;

/**
 * 操作数据接口
 */
export interface IOperateData {
  /** 操作名称 */
  name: string;
  /** 行数据 */
  row: IObject;
  /** 列数据 */
  column: IObject;
  /** 行索引 */
  $index: number;
}

/**
 * 搜索配置接口
 */
export interface ISearchConfig {
  /** 权限前缀(如sys:user，用于组成权限标识)，不提供则不进行权限校验 */
  permPrefix?: string;
  /** 标签冒号(默认：false) */
  colon?: boolean;
  /** 表单项(默认：[]) */
  formItems?: IFormItems<ISearchComponent>;
  /** 是否开启展开和收缩(默认：true) */
  isExpandable?: boolean;
  /** 默认展示的表单项数量(默认：3) */
  showNumber?: number;
  /** 卡片属性 */
  cardAttrs?: Partial<CardProps> & { style?: CSSProperties };
  /** form组件属性 */
  form?: IForm;
  /** 自适应网格布局(使用时表单不要添加 style: { width: "200px" }) */
  grid?: boolean | "left" | "right";
}

/**
 * 内容配置接口
 */
export interface IContentConfig<T = any> {
  /** 权限前缀(如sys:user，用于组成权限标识)，不提供则不进行权限校验 */
  permPrefix?: string;
  /** table组件属性 */
  table?: Omit<TableProps<any>, "data">;
  /** 页面标题与提示（用于卡片头部显示） */
  title?: string;
  /** 提示信息 */
  tooltip?: string | IObject;
  /** 分页组件位置(默认：left) */
  pagePosition?: "left" | "right";
  /** pagination组件属性 */
  pagination?:
  | boolean
  | Partial<
    Omit<
      PaginationProps,
      "v-model:page-size" | "v-model:current-page" | "total" | "currentPage"
    >
  >;
  /** 列表的网络请求函数(需返回promise) */
  indexAction: (queryParams: T) => Promise<any>;
  /** 默认的分页相关的请求参数 */
  request?: {
    page_no: string;
    page_size: string;
  };
  /** 数据格式解析的回调函数 */
  parseData?: (res: any) => {
    total: number;
    list: IObject[];
    [key: string]: any;
  };
  /** 修改属性的网络请求函数(需返回promise) */
  modifyAction?: (data: {
    [key: string]: any;
    field: string;
    value: boolean | string | number;
  }) => Promise<any>;
  /** 删除的网络请求函数(需返回promise) */
  deleteAction?: (ids: string) => Promise<any>;
  /** 后端导出的网络请求函数(需返回promise) */
  exportAction?: (queryParams: T) => Promise<any>;
  /** 前端全量导出的网络请求函数(需返回promise) */
  exportsAction?: (queryParams: T) => Promise<IObject[]>;
  /** 导入模板 */
  importTemplate?: string | (() => Promise<any>);
  /** 后端导入的网络请求函数(需返回promise) */
  importAction?: (file: File) => Promise<any>;
  /** 前端导入的网络请求函数(需返回promise) */
  importsAction?: (data: IObject[]) => Promise<any>;
  /** 主键名(默认为id) */
  pk?: string;
  /** 表格工具栏(默认:add,delete,export,也可自定义) */
  toolbar?: Array<ToolbarLeft | IToolsButton>;
  /** 表格工具栏右侧图标(默认:refresh,filter,imports,exports,search) */
  defaultToolbar?: Array<ToolbarRight | IToolsButton>;
  /** 更多操作按钮配置 */
  moreButtons?: Array<IToolsButton>;
  /** table组件列属性(额外的属性templet,operat,slotName) */
  cols: Array<{
    /** 列类型 */
    type?: "default" | "selection" | "index" | "expand";
    /** 列标签 */
    label?: string;
    /** 列属性 */
    prop?: string;
    /** 列宽度 */
    width?: string | number;
    /** 最小列宽度 */
    minWidth?: string | number;
    /** 对齐方式 */
    align?: "left" | "center" | "right";
    /** 列键名 */
    columnKey?: string;
    /** 是否保留选择 */
    reserveSelection?: boolean;
    /** 列是否显示 */
    show?: boolean;
    /** 模板类型 */
    templet?:
    | "image"
    | "list"
    | "url"
    | "switch"
    | "input"
    | "price"
    | "percent"
    | "icon"
    | "date"
    | "tool"
    | "custom";
    /** image模板相关参数 */
    imageWidth?: number;
    /** image模板相关参数 */
    imageHeight?: number;
    /** list模板相关参数 */
    selectList?: IObject;
    /** switch模板相关参数 */
    activeValue?: boolean | string | number;
    /** switch模板相关参数 */
    inactiveValue?: boolean | string | number;
    /** switch模板相关参数 */
    activeText?: string;
    /** switch模板相关参数 */
    inactiveText?: string;
    /** input模板相关参数 */
    inputType?: string;
    /** price模板相关参数 */
    priceFormat?: string;
    /** date模板相关参数 */
    dateFormat?: string;
    /** tool模板相关参数 */
    operat?: Array<ToolbarTable | IToolsButton>;
    /** filter值拼接符 */
    filterJoin?: string;
    /** 初始化数据函数 */
    initFn?: (item: IObject) => void;
    /** 是否禁用 */
    disabled?: boolean;
    /** 固定列 */
    fixed?: boolean | "left" | "right";
    /** 权限 */
    perm?: string;
    [key: string]: any;
  }>;
}

/**
 * 模态框配置接口
 */
export interface IModalConfig<T = any> {
  /** 权限前缀(如sys:user，用于组成权限标识)，不提供则不进行权限校验 */
  permPrefix?: string;
  /** 标签冒号(默认：false) */
  colon?: boolean;
  /** 主键名(主要用于编辑数据,默认为id) */
  pk?: string;
  /** 组件类型(默认：dialog) */
  component?: "dialog" | "drawer";
  /** dialog组件属性 */
  dialog?: Partial<Omit<DialogProps, "modelValue">>;
  /** drawer组件属性 */
  drawer?: Partial<Omit<DrawerProps, "modelValue">>;
  /** 查看模式渲染方式(默认：form；可选：descriptions) */
  viewMode?: "form" | "descriptions";
  /** descriptions组件属性（当 viewMode 为 descriptions 时生效） */
  descriptions?: IObject;
  /** form组件属性 */
  form?: IForm;
  /** 表单项 */
  formItems: IFormItems<IComponentType>;
  /** 提交之前处理 */
  beforeSubmit?: (data: T) => void;
  /** 提交的网络请求函数(需返回promise) */
  formAction?: (data: T) => Promise<any>;
}

/**
 * 表单属性类型
 */
export type IForm = Partial<Omit<FormProps, "model" | "rules">>;

/**
 * 表单项类型
 */
export type IFormItems<T = IComponentType> = Array<{
  /** 组件类型(如input,select,radio,custom等) */
  type: T;
  /** 标签提示 */
  tips?: string | IObject;
  /** 标签 */
  label: string;
  /** 属性名 */
  prop: string;
  /** 属性 */
  attrs?: IObject;
  /** 选项 */
  options?: Array<{ label: string; value: any;[key: string]: any }> | Ref<any[]>;
  /** 规则 */
  rules?: FormItemRule[];
  /** 初始值 */
  initialValue?: any;
  /** 插槽名称 */
  slotName?: string;
  /** 是否隐藏 */
  hidden?: boolean;
  /** 列属性 */
  col?: Partial<ColProps>;
  /** 事件 */
  events?: Record<string, (...args: any) => void>;
  /** 初始化函数 */
  initFn?: (item: IObject) => void;
}>;

/**
 * 页面表单接口
 */
export interface IPageForm {
  /** 主键 */
  pk?: string;
  /** 表单属性 */
  form?: IForm;
  /** 表单项 */
  formItems: IFormItems<IComponentType>;
}
