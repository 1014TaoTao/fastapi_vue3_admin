<!-- 表单组件 -->
<!-- 支持常用表单组件、自定义组件、插槽、校验、隐藏表单项 -->
<!-- 写法同 ElementPlus 官方文档组件，把属性写在 props 里面就可以了 -->
<template>
  <section class="px-4 pb-0 pt-4 md:px-4 md:pt-4">
    <ElScrollbar v-if="scrollbar" :max-height="maxHeight" :view-style="{ overflowX: 'hidden' }">
      <ElForm
        ref="formRef"
        :model="modelValue"
        :label-position="labelPosition"
        v-bind="{ ...$attrs }"
      >
        <ElRow class="flex flex-wrap" :gutter="gutter">
          <ElCol
            v-for="item in visibleFormItems"
            :key="item.key"
            :xs="getColSpan(item.span, 'xs')"
            :sm="getColSpan(item.span, 'sm')"
            :md="getColSpan(item.span, 'md')"
            :lg="getColSpan(item.span, 'lg')"
            :xl="getColSpan(item.span, 'xl')"
          >
            <ElFormItem
              :prop="item.key"
              :label="typeof item.label === 'string' ? item.label : undefined"
              :label-width="item.label ? item.labelWidth || labelWidth : undefined"
            >
              <!-- 字符串 label 走 ElFormItem 默认渲染使 label-suffix 生效；组件 label 保留插槽 -->
              <template v-if="item.label && typeof item.label !== 'string'" #label>
                <component :is="item.label" />
              </template>
              <slot :name="item.key" :item="item" :modelValue="modelValue">
                <component
                  :is="getComponent(item)"
                  :model-value="getFieldValue(item.key)"
                  @update:model-value="setFieldValue(item.key, $event)"
                  v-bind="getProps(item)"
                >
                  <!-- 下拉选择 -->
                  <template v-if="item.type === 'select' && getProps(item)?.options">
                    <ElOption
                      v-for="option in getProps(item).options"
                      v-bind="option"
                      :key="option.value"
                    />
                  </template>

                  <!-- 复选框组 -->
                  <template v-if="item.type === 'checkboxgroup' && getProps(item)?.options">
                    <ElCheckbox
                      v-for="option in getProps(item).options"
                      v-bind="option"
                      :key="option.value"
                    />
                  </template>

                  <!-- 单选框组 -->
                  <template v-if="item.type === 'radiogroup' && getProps(item)?.options">
                    <ElRadio
                      v-for="option in getProps(item).options"
                      v-bind="option"
                      :key="option.value"
                    />
                  </template>

                  <!-- 动态插槽支持 -->
                  <template
                    v-for="(slotFn, slotName) in getSlots(item)"
                    :key="slotName"
                    #[slotName]
                  >
                    <component :is="slotFn" />
                  </template>
                </component>
              </slot>
            </ElFormItem>
          </ElCol>
          <ElCol :xs="24" :sm="24" :md="span" :lg="span" :xl="span" class="max-w-full flex-1">
            <div
              class="mb-3 flex items-center flex-wrap justify-end md:flex-row md:items-stretch md:gap-2"
              :style="actionButtonsStyle"
            >
              <div class="flex gap-2 md:justify-center">
                <ElButton v-if="showReset" class="reset-button" @click="handleReset" v-ripple>
                  {{ t("table.form.reset") }}
                </ElButton>
                <ElButton
                  v-if="showSubmit"
                  type="primary"
                  class="submit-button"
                  @click="handleSubmit"
                  v-ripple
                  :disabled="disabledSubmit"
                  :loading="loading"
                >
                  {{ t("table.form.submit") }}
                </ElButton>
              </div>
            </div>
          </ElCol>
        </ElRow>
      </ElForm>
    </ElScrollbar>
    <ElForm
      v-else
      ref="formRef"
      :model="modelValue"
      :label-position="labelPosition"
      v-bind="{ ...$attrs }"
    >
      <ElRow class="flex flex-wrap" :gutter="gutter">
        <ElCol
          v-for="item in visibleFormItems"
          :key="item.key"
          :xs="getColSpan(item.span, 'xs')"
          :sm="getColSpan(item.span, 'sm')"
          :md="getColSpan(item.span, 'md')"
          :lg="getColSpan(item.span, 'lg')"
          :xl="getColSpan(item.span, 'xl')"
        >
          <ElFormItem
            :prop="item.key"
            :label="typeof item.label === 'string' ? item.label : undefined"
            :label-width="item.label ? item.labelWidth || labelWidth : undefined"
          >
            <!-- 字符串 label 走 ElFormItem 默认渲染使 label-suffix 生效；组件 label 保留插槽 -->
            <template v-if="item.label && typeof item.label !== 'string'" #label>
              <component :is="item.label" />
            </template>
            <slot :name="item.key" :item="item" :modelValue="modelValue">
              <component
                :is="getComponent(item)"
                :model-value="getFieldValue(item.key)"
                @update:model-value="setFieldValue(item.key, $event)"
                v-bind="getProps(item)"
              >
                <template v-if="item.type === 'select' && getProps(item)?.options">
                  <ElOption
                    v-for="option in getProps(item).options"
                    v-bind="option"
                    :key="option.value"
                  />
                </template>
                <template v-if="item.type === 'checkboxgroup' && getProps(item)?.options">
                  <ElCheckbox
                    v-for="option in getProps(item).options"
                    v-bind="option"
                    :key="option.value"
                  />
                </template>
                <template v-if="item.type === 'radiogroup' && getProps(item)?.options">
                  <ElRadio
                    v-for="option in getProps(item).options"
                    v-bind="option"
                    :key="option.value"
                  />
                </template>
                <template v-for="(slotFn, slotName) in getSlots(item)" :key="slotName" #[slotName]>
                  <component :is="slotFn" />
                </template>
              </component>
            </slot>
          </ElFormItem>
        </ElCol>
        <ElCol :xs="24" :sm="24" :md="span" :lg="span" :xl="span" class="max-w-full flex-1">
          <div
            class="mb-3 flex items-center flex-wrap justify-end md:flex-row md:items-stretch md:gap-2"
            :style="actionButtonsStyle"
          >
            <div class="flex gap-2 md:justify-center">
              <ElButton v-if="showReset" class="reset-button" @click="handleReset" v-ripple>
                {{ t("table.form.reset") }}
              </ElButton>
              <ElButton
                v-if="showSubmit"
                type="primary"
                class="submit-button"
                @click="handleSubmit"
                v-ripple
                :disabled="disabledSubmit"
                :loading="loading"
              >
                {{ t("table.form.submit") }}
              </ElButton>
            </div>
          </div>
        </ElCol>
      </ElRow>
    </ElForm>
  </section>
</template>

<script setup lang="ts">
/**
 * FaForm —— 动态表单组件。
 *
 * 渲染策略：items 配置项数组 → componentMap[type] 映射组件 → 动态 :is 渲染。
 * 支持所有 Element Plus 表单组件类型、自定义 render、插槽插写。
 *
 * @see SearchFormItem 接口定义
 */
import { useI18n } from "vue-i18n";
import { type Component } from "vue";
import FaDatePicker from "@/components/forms/fa-search-bar/FaDatePicker.vue";
import {
  ElCascader,
  ElCheckbox,
  ElCheckboxGroup,
  ElInput,
  ElInputTag,
  ElInputNumber,
  ElRadioGroup,
  ElRate,
  ElSelect,
  ElSlider,
  ElSwitch,
  ElTimePicker,
  ElTimeSelect,
  ElTreeSelect,
  type FormInstance,
} from "element-plus";
import {
  cloneModelValue as cloneModelValueShared,
  sanitizeOutputValue as sanitizeOutputValueShared,
  getProps as getPropsShared,
  getSlots as getSlotsShared,
  getColSpan as getColSpanShared,
  useSanitizeOutputOptions,
  type SanitizeOutputOptions,
} from "../composables/useFormBase";
import FaFileUpload from "@/components/forms/fa-file-upload/index.vue";
import FaUpload from "@/components/actions/fa-upload/index.vue";
import FaWangEditor from "@/components/forms/fa-wang-editor/index.vue";

defineOptions({ name: "FaForm" });

defineSlots<{
  [slotName: string]: (props: { item: FormItem; modelValue: Record<string, any> }) => any;
}>();

const componentMap = {
  input: ElInput, // 输入框
  inputtag: ElInputTag, // 标签输入框
  number: ElInputNumber, // 数字输入框
  select: ElSelect, // 选择器
  switch: ElSwitch, // 开关
  checkbox: ElCheckbox, // 复选框
  checkboxgroup: ElCheckboxGroup, // 复选框组
  radiogroup: ElRadioGroup, // 单选框组
  date: FaDatePicker, // 日期选择器
  daterange: FaDatePicker, // 日期范围选择器
  datetime: FaDatePicker, // 日期时间选择器
  datetimerange: FaDatePicker, // 日期时间范围选择器
  rate: ElRate, // 评分
  slider: ElSlider, // 滑块
  cascader: ElCascader, // 级联选择器
  timepicker: ElTimePicker, // 时间选择器
  timeselect: ElTimeSelect, // 时间选择
  treeselect: ElTreeSelect, // 树选择器
  editor: FaWangEditor, // 富文本编辑器
  imageupload: FaUpload, // 单图上传
  fileupload: FaFileUpload, // 单文件上传
};

const { t } = useI18n();
const formInstance = useTemplateRef<FormInstance>("formRef");

// 表单项配置
export interface FormItem {
  /** 表单项的唯一标识 */
  key: string;
  /** 表单项的标签文本或自定义渲染函数 */
  label: string | (() => VNode) | Component;
  /** 表单项标签的宽度，会覆盖 Form 的 labelWidth */
  labelWidth?: string | number;
  /** 表单项类型，支持预定义的组件类型 */
  type?: keyof typeof componentMap | string;
  /** 自定义渲染函数或组件，用于渲染自定义组件（优先级高于 type） */
  render?: (() => VNode) | Component;
  /** 是否隐藏该表单项 */
  hidden?: boolean;
  /** 表单项占据的列宽，基于24格栅格系统 */
  span?: number;
  /** 选项数据，用于 select、checkbox-group、radio-group 等 */
  options?: Record<string, any>;
  /** 传递给表单项组件的属性 */
  props?: Record<string, any>;
  /** 表单项的插槽配置 */
  slots?: Record<string, (() => any) | undefined>;
  /** 表单项的占位符文本 */
  placeholder?: string;
  /** 更多属性配置请参考 ElementPlus 官方文档 */
}

// 表单配置
interface Props {
  /** 表单数据 */
  items?: FormItem[];
  /** 每列的宽度（基于 24 格布局） */
  span?: number;
  /** 表单控件间隙 */
  gutter?: number;
  /** 表单域标签的位置 */
  labelPosition?: "left" | "right" | "top";
  /** 文字宽度 */
  labelWidth?: string | number;
  /** 可见表单项少时按钮左对齐，该值控制对齐方式切换阈值 */
  buttonLeftLimit?: number;
  /** 是否显示重置按钮 */
  showReset?: boolean;
  /** 是否显示提交按钮 */
  showSubmit?: boolean;
  /** 是否禁用提交按钮 */
  disabledSubmit?: boolean;
  /** 提交按钮 loading（防止重复提交） */
  loading?: boolean;
  /** 提交时是否清洗空值 */
  sanitizeOutput?: Partial<SanitizeOutputOptions>;
  /** 是否需要内置 ElScrollbar 包裹 */
  scrollbar?: boolean;
  /** ElScrollbar 最大高度 */
  maxHeight?: string;
  /** 表单校验规则（通过 $attrs 透传至 ElForm） */
}

const props = withDefaults(defineProps<Props>(), {
  items: () => [],
  span: 6,
  gutter: 12,
  labelPosition: "right",
  labelWidth: "70px",
  buttonLeftLimit: 2,
  showReset: false,
  showSubmit: false,
  disabledSubmit: false,
  loading: false,
  sanitizeOutput: () => ({}),
  scrollbar: false,
  maxHeight: "75vh",
});

interface Emits {
  reset: [];
  submit: [Record<string, any>];
}

const emit = defineEmits<Emits>();

const modelValue = defineModel<Record<string, any>>({ default: {} });
const initialModelValue = ref<Record<string, any>>({});

// 保存组件初始化时的表单快照，用于 reset 时恢复默认值。
initialModelValue.value = cloneModelValueShared(modelValue.value);

const sanitizeOutputOptions = useSanitizeOutputOptions(props.sanitizeOutput);

// 模板引用的函数（从公共 composable 重新导出，使模板可访问）
// 注：getColSpan 保持 2 参数签名（span 从组件内部读取）
const getColSpan = (itemSpan: number | undefined, breakpoint: any) =>
  getColSpanShared(itemSpan, span.value, breakpoint);
const getProps = getPropsShared;
const getSlots = getSlotsShared;

const PATH_NUMBER_RE = /^\d+$/;

// 兼容 a.b、a.0.b 这类路径写法，数字段会被当作数组索引处理。
const parsePath = (path: string) => {
  return path
    .split(".")
    .filter(Boolean)
    .map((segment) => (PATH_NUMBER_RE.test(segment) ? Number(segment) : segment));
};

const getFieldValue = (path: string) => {
  return parsePath(path).reduce<any>((currentValue, segment) => {
    if (currentValue == null) return undefined;
    return currentValue[segment];
  }, modelValue.value);
};

// 清空字段时只删除路径的最后一段，避免误删同级数据。
const deleteFieldValue = (path: string) => {
  const segments = parsePath(path);
  if (!segments.length) return;

  const lastSegment = segments.pop();
  const parent = segments.reduce<any>((currentValue, segment) => {
    if (currentValue == null) return undefined;
    return currentValue[segment];
  }, modelValue.value);

  if (parent != null && lastSegment !== undefined) {
    delete parent[lastSegment];
  }
};

// 表单清空输入时不保留空字符串，同时按路径自动补齐中间对象或数组。
const setFieldValue = (path: string, value: unknown) => {
  const normalizedValue = value === "" ? undefined : value;
  const segments = parsePath(path);

  if (!segments.length) return;

  if (normalizedValue === undefined) {
    deleteFieldValue(path);
    return;
  }

  let currentValue: any = modelValue.value;

  segments.forEach((segment, index) => {
    const isLast = index === segments.length - 1;

    if (isLast) {
      currentValue[segment] = normalizedValue;
      return;
    }

    const nextSegment = segments[index + 1];
    const nextContainer = typeof nextSegment === "number" ? [] : {};

    if (
      currentValue[segment] === null ||
      currentValue[segment] === undefined ||
      typeof currentValue[segment] !== "object"
    ) {
      currentValue[segment] = nextContainer;
    }

    currentValue = currentValue[segment];
  });
};

const getSanitizedOutput = () => {
  return (sanitizeOutputValueShared(
    cloneModelValueShared(modelValue.value),
    sanitizeOutputOptions.value
  ) || {}) as Record<string, any>;
};

// 组件
const getComponent = (item: FormItem) => {
  // 优先使用 render 函数或组件渲染自定义组件
  if (item.render) {
    return item.render;
  }
  // 使用 type 获取预定义组件
  const { type } = item;
  const comp = componentMap[type as keyof typeof componentMap];
  if (!comp) {
    console.warn(`[FaForm] 未知表单类型 "${type}"，回退到 input`, item);
    return componentMap["input"];
  }
  return comp;
};

/**
 * 可见的表单项
 */
const visibleFormItems = computed(() => {
  return props.items.filter((item) => !item.hidden);
});

/**
 * 操作按钮样式
 */
const actionButtonsStyle = computed(() => {
  if (visibleFormItems.value.length <= props.buttonLeftLimit) {
    return { justifyContent: "flex-start" as const };
  }
  return undefined;
});

/**
 * 处理重置事件
 */
const handleReset = () => {
  // 重置表单字段（UI 层）
  formInstance.value?.resetFields();

  // 恢复初始表单值，保留默认值而不是简单清空。
  Object.keys(modelValue.value).forEach((key) => {
    delete modelValue.value[key];
  });
  Object.assign(modelValue.value, cloneModelValueShared(initialModelValue.value));

  // 触发 reset 事件
  emit("reset");
};

/**
 * 处理提交事件
 */
const handleSubmit = () => {
  // 对外只抛出清洗后的结果，避免业务层重复过滤空值。
  emit("submit", getSanitizedOutput());
};

defineExpose({
  ref: formInstance,
  validate: (...args: any[]) => formInstance.value?.validate(...args),
  /** 代理 ElForm.resetFields */
  resetFields: (...args: any[]) => formInstance.value?.resetFields(...args),
  /** 代理 ElForm.clearValidate */
  clearValidate: (...args: any[]) => formInstance.value?.clearValidate(...args),
  /** 代理 ElForm.validateField */
  validateField: (...args: any[]) => formInstance.value?.validateField(...args),
  reset: handleReset,
  // 允许外部在不触发提交事件时主动获取清洗后的输出。
  getOutput: getSanitizedOutput,
});

// 解构 props 以便在模板中直接使用
const { span, gutter, labelPosition, labelWidth } = toRefs(props);
</script>
