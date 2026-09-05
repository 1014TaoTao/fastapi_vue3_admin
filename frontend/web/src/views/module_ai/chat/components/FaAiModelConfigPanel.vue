<template>
  <FaDrawer v-model="drawerVisible" title="配置中心" size="60%" destroy-on-close>
    <div class="ai-model-config">
      <div v-if="loading" class="loading-tip">
        <ElIcon class="is-loading"><Loading /></ElIcon>
        <span>加载中...</span>
      </div>
      <template v-else>
        <!-- 顶部状态栏 -->
        <div class="status-bar">
          <div class="status-info">
            <span class="status-title">当前使用</span>
            <ElTag :type="activeId ? 'primary' : 'info'" effect="dark" size="small">
              <ElIcon class="tag-icon"><CircleCheck v-if="activeId" /><Cpu v-else /></ElIcon>
              <span>{{ activeModelName }}</span>
            </ElTag>
          </div>
          <ElButton
            v-if="items.length > 0"
            :disabled="!activeId"
            size="small"
            plain
            @click="handleUseDefault"
          >
            <ElIcon><RefreshLeft /></ElIcon>
            <span>恢复系统默认</span>
          </ElButton>
        </div>

        <!-- 配置列表 -->
        <div class="config-section">
          <div class="section-header">
            <div class="header-left">
              <span class="section-title">已配置的模型</span>
              <ElTag v-if="items.length > 0" size="small" effect="plain" type="info">
                {{ items.length }} 个
              </ElTag>
            </div>
          </div>

          <!-- 空状态 - 直接显示添加按钮作为唯一行动 -->
          <ElEmpty v-if="items.length === 0">
            <template #image>
              <div class="empty-illust">
                <ElIcon :size="56"><Cpu /></ElIcon>
                <ElIcon class="empty-icon-bg" :size="100"><ChatLineSquare /></ElIcon>
              </div>
            </template>
            <template #description>
              <div class="empty-title">添加你的第一个 AI 模型</div>
              <div class="empty-desc">
                支持 OpenAI、DeepSeek、Ollama 等任何 OpenAI 兼容服务<br />
                配置后即可在 AI 助手页一键切换
              </div>
            </template>
            <ElButton type="primary" size="large" :icon="Plus" @click="openCreate">
              立即添加
            </ElButton>
          </ElEmpty>

          <!-- 列表 -->
          <div v-else class="config-list">
            <TransitionGroup name="list" tag="div" class="list-inner">
              <div
                v-for="item in items"
                :key="item.id"
                class="config-item"
                :class="{
                  active: item.id === activeId,
                  expanded: expandedId === item.id,
                  flash: flashId === item.id,
                }"
                @click="handleItemClick(item)"
              >
                <div class="config-item-main">
                  <div class="item-icon-wrap">
                    <ElIcon class="item-icon" :size="18">
                      <CircleCheck v-if="item.id === activeId" />
                      <ChatLineSquare v-else />
                    </ElIcon>
                  </div>
                  <div class="item-content">
                    <div class="item-row1">
                      <span class="item-name">{{ item.name }}</span>
                      <ElTag v-if="item.id === activeId" type="success" size="small" effect="light">
                        使用中
                      </ElTag>
                    </div>
                    <div class="item-model">{{ item.model_id }}</div>
                  </div>
                  <div class="item-actions" @click.stop>
                    <ElTooltip content="展开详情" placement="top" :show-after="200">
                      <ElButton text circle size="small" @click="toggleExpand(item.id)">
                        <ElIcon :class="{ rotated: expandedId === item.id }">
                          <ArrowDown />
                        </ElIcon>
                      </ElButton>
                    </ElTooltip>
                    <ElTooltip content="编辑" placement="top" :show-after="200">
                      <ElButton text circle size="small" :icon="Edit" @click="openEdit(item)" />
                    </ElTooltip>
                    <ElTooltip content="删除" placement="top" :show-after="200">
                      <ElButton
                        text
                        circle
                        size="small"
                        :icon="Delete"
                        @click="handleDelete(item)"
                      />
                    </ElTooltip>
                  </div>
                </div>
                <!-- 展开详情 -->
                <div v-show="expandedId === item.id" class="item-detail">
                  <div class="detail-row">
                    <span class="detail-label">Base URL</span>
                    <span class="detail-value">{{ item.base_url }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">API Key</span>
                    <div class="api-key-wrap">
                      <span class="detail-value api-key">
                        {{ showKeyId === item.id ? item.api_key : `****${maskKey(item.api_key)}` }}
                      </span>
                      <ElButton
                        text
                        size="small"
                        @click="showKeyId = showKeyId === item.id ? null : item.id"
                      >
                        <ElIcon><View v-if="showKeyId !== item.id" /><Hide v-else /></ElIcon>
                      </ElButton>
                      <ElButton
                        text
                        size="small"
                        :disabled="!item.api_key"
                        @click="copyKey(item.api_key)"
                      >
                        <ElIcon><CopyDocument /></ElIcon>
                      </ElButton>
                    </div>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">Temperature</span>
                    <span class="detail-value">{{ item.temperature.toFixed(1) }}</span>
                  </div>
                  <div v-if="item.created_time" class="detail-row">
                    <span class="detail-label">添加于</span>
                    <span class="detail-value">{{ item.created_time }}</span>
                  </div>
                </div>
              </div>
            </TransitionGroup>
          </div>
        </div>

        <!-- 底部固定添加按钮 - 始终可见 -->
        <div v-if="items.length > 0" class="footer-add">
          <ElButton type="primary" plain :icon="Plus" class="add-btn" @click="openCreate">
            添加新模型
          </ElButton>
        </div>
      </template>

      <!-- 新增/编辑弹窗 -->
      <FaDialog
        v-model="dialogVisible"
        :title="form.id ? '编辑模型' : '新增模型'"
        width="520px"
        :close-on-click-modal="false"
      >
        <ElForm
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="100px"
          label-position="right"
          @submit.prevent="handleSave"
        >
          <ElFormItem label="配置名称" prop="name">
            <ElInput
              v-model="form.name"
              placeholder="如：日常对话 / 代码助手"
              maxlength="50"
              show-word-limit
              clearable
              autofocus
            />
          </ElFormItem>
          <ElFormItem label="Base URL" prop="base_url">
            <ElInput v-model="form.base_url" placeholder="https://api.openai.com/v1" clearable>
              <template #append>
                <ElDropdown trigger="click" @command="(v: string) => (form.base_url = v)">
                  <ElButton text size="small">
                    预设
                    <ElIcon><ArrowDown /></ElIcon>
                  </ElButton>
                  <template #dropdown>
                    <ElDropdownMenu>
                      <ElDropdownItem
                        v-for="preset in baseUrlPresets"
                        :key="preset.label"
                        :command="preset.url"
                      >
                        <div class="preset-item">
                          <span class="preset-label">{{ preset.label }}</span>
                          <span class="preset-url">{{ preset.url }}</span>
                        </div>
                      </ElDropdownItem>
                    </ElDropdownMenu>
                  </template>
                </ElDropdown>
              </template>
            </ElInput>
          </ElFormItem>
          <ElFormItem label="API Key" prop="api_key">
            <ElInput
              v-model="form.api_key"
              type="password"
              placeholder="sk-..."
              show-password
              clearable
            />
          </ElFormItem>
          <ElFormItem label="模型 ID" prop="model_id">
            <ElInput
              v-model="form.model_id"
              placeholder="如：gpt-4o-mini / deepseek-chat"
              clearable
            />
          </ElFormItem>
          <ElFormItem label="Temperature" prop="temperature">
            <ElSlider
              v-model="form.temperature"
              :min="0"
              :max="2"
              :step="0.1"
              show-input
              :show-input-controls="false"
            />
            <div class="form-tip">越高越有创造性，0 更确定</div>
          </ElFormItem>
        </ElForm>
        <template #footer>
          <ElButton @click="dialogVisible = false">取消</ElButton>
          <ElButton type="primary" :loading="saving" @click="handleSave">
            <ElIcon><Check /></ElIcon>
            <span>{{ form.id ? "保存" : "新增并使用" }}</span>
          </ElButton>
        </template>
      </FaDialog>
    </div>
  </FaDrawer>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import {
  Plus,
  Edit,
  Delete,
  Cpu,
  ChatLineSquare,
  CircleCheck,
  ArrowDown,
  RefreshLeft,
  Loading,
  Check,
  View,
  Hide,
  CopyDocument,
} from "@element-plus/icons-vue";
import AiChatAPI, {
  type AiModelConfigInput,
  type AiModelConfigItem,
  type AiModelConfigList,
} from "@/api/module_ai/chat";
import FaDialog from "@/components/modal/fa-dialog/index.vue";

const emit = defineEmits<{
  (e: "changed"): void;
  (e: "update:modelValue", value: boolean): void;
}>();

interface Props {
  modelValue?: boolean;
}

const props = withDefaults(defineProps<Props>(), { modelValue: false });
const drawerVisible = computed({
  get: () => props.modelValue,
  set: (val: boolean) => emit("update:modelValue", val),
});

const loading = ref(false);
const saving = ref(false);
const items = ref<AiModelConfigItem[]>([]);
const activeId = ref<string | null>(null);
const expandedId = ref<string | null>(null);
const showKeyId = ref<string | null>(null);
const flashId = ref<string | null>(null);
const dialogVisible = ref(false);

const formRef = ref<FormInstance>();
const form = reactive<AiModelConfigItem>({
  id: "",
  name: "",
  base_url: "",
  api_key: "",
  model_id: "",
  temperature: 0.7,
  created_time: null,
});

// 常用 Base URL 预设 - 提升用户输入效率
const baseUrlPresets = [
  { label: "OpenAI 官方", url: "https://api.openai.com/v1" },
  { label: "DeepSeek", url: "https://api.deepseek.com/v1" },
  { label: "通义千问", url: "https://dashscope.aliyuncs.com/compatible-mode/v1" },
  { label: "月之暗面 Moonshot", url: "https://api.moonshot.cn/v1" },
  { label: "智谱 GLM", url: "https://open.bigmodel.cn/api/paas/v4" },
  { label: "Ollama (本地)", url: "http://localhost:11434/v1" },
];

const rules: FormRules<AiModelConfigInput> = {
  name: [{ required: true, message: "请输入配置名称", trigger: "blur" }],
  base_url: [
    { required: true, message: "请输入 Base URL", trigger: "blur" },
    {
      validator: (_rule, value: string, callback) => {
        if (!value) return callback();
        if (!/^https?:\/\//.test(value)) {
          callback(new Error("必须以 http:// 或 https:// 开头"));
        } else {
          callback();
        }
      },
      trigger: "blur",
    },
  ],
  api_key: [{ required: true, message: "请输入 API Key", trigger: "blur" }],
  model_id: [{ required: true, message: "请输入模型 ID", trigger: "blur" }],
  temperature: [{ required: true, message: "请设置温度", trigger: "change" }],
};

const activeModelName = computed(() => {
  if (!activeId.value) return "系统默认";
  const item = items.value.find((i) => i.id === activeId.value);
  return item?.name || "系统默认";
});

const loadList = async () => {
  loading.value = true;
  try {
    const res = await AiChatAPI.getModelConfig();
    if (res.data?.code === 0 && res.data.data) {
      const data: AiModelConfigList = res.data.data;
      items.value = data.items || [];
      activeId.value = data.active_id;
    }
  } catch {
    ElMessage.error("加载模型配置失败");
  } finally {
    loading.value = false;
  }
};

const resetForm = () => {
  form.id = "";
  form.name = "";
  form.base_url = "";
  form.api_key = "";
  form.model_id = "";
  form.temperature = 0.7;
  form.created_time = null;
  formRef.value?.clearValidate();
};

const openCreate = () => {
  resetForm();
  dialogVisible.value = true;
};

const openEdit = (item: AiModelConfigItem) => {
  form.id = item.id;
  form.name = item.name;
  form.base_url = item.base_url;
  form.api_key = item.api_key;
  form.model_id = item.model_id;
  form.temperature = item.temperature;
  form.created_time = item.created_time;
  formRef.value?.clearValidate();
  dialogVisible.value = true;
};

const handleSave = async () => {
  if (!formRef.value || saving.value) return;
  try {
    await formRef.value.validate();
  } catch {
    return;
  }
  saving.value = true;
  try {
    const payload: AiModelConfigInput = {
      name: form.name,
      base_url: form.base_url,
      api_key: form.api_key,
      model_id: form.model_id,
      temperature: form.temperature,
    };
    let res;
    if (form.id) {
      res = await AiChatAPI.updateModelConfig(form.id, payload);
    } else {
      res = await AiChatAPI.createModelConfig(payload);
    }
    if (res.data?.code === 0) {
      const newId = form.id || res.data.data?.id;
      dialogVisible.value = false;
      if (!form.id && newId) {
        await AiChatAPI.activateModelConfig(newId);
      }
      resetForm();
      emit("changed");
      await loadList();
      if (newId) flashHighlight(newId);
      ElMessage.success(form.id ? "已保存" : "已添加并启用");
    } else {
      ElMessage.error(res.data?.msg || "保存失败");
    }
  } catch {
    ElMessage.error("保存失败");
  } finally {
    saving.value = false;
  }
};

const flashHighlight = (id: string) => {
  flashId.value = id;
  setTimeout(() => {
    flashId.value = null;
  }, 1500);
};

const handleItemClick = async (item: AiModelConfigItem) => {
  if (item.id === activeId.value) {
    toggleExpand(item.id);
    return;
  }
  try {
    const res = await AiChatAPI.activateModelConfig(item.id);
    if (res.data?.code === 0) {
      activeId.value = item.id;
      emit("changed");
    } else {
      ElMessage.error(res.data?.msg || "切换失败");
    }
  } catch {
    ElMessage.error("切换失败");
  }
};

const handleUseDefault = async () => {
  try {
    const res = await AiChatAPI.activateModelConfig("");
    if (res.data?.code === 0) {
      activeId.value = null;
      emit("changed");
    } else {
      ElMessage.error(res.data?.msg || "操作失败");
    }
  } catch {
    ElMessage.error("操作失败");
  }
};

const handleDelete = async (item: AiModelConfigItem) => {
  try {
    await confirmDelete(`确认删除模型「${item.name}」？此操作不可恢复`);
  } catch {
    return;
  }
  try {
    const res = await AiChatAPI.deleteModelConfig(item.id);
    if (res.data?.code === 0) {
      ElMessage.success("已删除");
      if (form.id === item.id) dialogVisible.value = false;
      if (expandedId.value === item.id) expandedId.value = null;
      emit("changed");
      await loadList();
    } else {
      ElMessage.error(res.data?.msg || "删除失败");
    }
  } catch {
    ElMessage.error("删除失败");
  }
};

const toggleExpand = (id: string) => {
  expandedId.value = expandedId.value === id ? null : id;
  if (expandedId.value !== id) showKeyId.value = null;
};

const copyKey = async (key: string) => {
  if (!key) return;
  try {
    await navigator.clipboard.writeText(key);
    ElMessage.success("已复制到剪贴板");
  } catch {
    ElMessage.error("复制失败");
  }
};

const maskKey = (key: string): string => {
  if (!key) return "";
  return key.length <= 4 ? key : key.slice(-4);
};

defineExpose({ refresh: loadList });
onMounted(loadList);
</script>

<style lang="scss" scoped>
.ai-model-config {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.loading-tip {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

/* 顶部状态栏 */
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
}

.status-info {
  display: flex;
  gap: 8px;
  align-items: center;
}

.status-title {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.tag-icon {
  margin-right: 2px;
}

.config-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  gap: 8px;
  align-items: center;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.empty-illust {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
}

.empty-icon-bg {
  position: absolute;
  color: var(--el-color-primary-light-7);
  opacity: 0.4;
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.empty-desc {
  font-size: 13px;
  line-height: 1.6;
  color: var(--el-text-color-secondary);
}

/* 列表 */
.config-list {
  width: 100%;
}

.list-inner {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-item {
  padding: 10px 12px;
  cursor: pointer;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  transition: all 0.2s;

  &.active {
    background: var(--el-color-primary-light-9);
    border-color: var(--el-color-primary);

    .item-icon {
      color: var(--el-color-primary);
    }

    .item-icon-wrap {
      background: var(--el-color-primary-light-7);
    }
  }

  &.expanded {
    background: var(--el-color-primary-light-9);
  }

  &:hover {
    border-color: var(--el-color-primary-light-5);

    .item-actions {
      opacity: 1;
    }
  }

  &.flash {
    animation: flash 1.5s ease;
  }
}

@keyframes flash {
  0% {
    box-shadow: 0 0 0 0 var(--el-color-primary-light-5);
  }

  30% {
    box-shadow: 0 0 0 6px var(--el-color-primary-light-7);
  }

  100% {
    box-shadow: 0 0 0 0 transparent;
  }
}

.config-item-main {
  display: flex;
  gap: 12px;
  align-items: center;
}

.item-icon-wrap {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  transition: background 0.2s;
}

.item-icon {
  color: var(--el-text-color-secondary);
  transition: color 0.2s;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-row1 {
  display: flex;
  gap: 8px;
  align-items: center;
}

.item-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.item-model {
  margin-top: 2px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.item-actions {
  display: flex;
  flex-shrink: 0;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.2s;
}

.config-item.expanded .item-actions {
  opacity: 1;
}

.item-detail {
  padding: 12px 0 0 44px;
  margin-top: 10px;
  border-top: 1px dashed var(--el-border-color-light);
}

.detail-row {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 4px 0;
  font-size: 12px;
}

.detail-label {
  flex-shrink: 0;
  width: 80px;
  color: var(--el-text-color-secondary);
}

.detail-value {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--el-text-color-regular);
  white-space: nowrap;

  &.api-key {
    font-family: var(--el-font-family-monospace, monospace);
  }
}

.api-key-wrap {
  display: flex;
  flex: 1;
  gap: 4px;
  align-items: center;
}

/* 底部添加 */
.footer-add {
  display: flex;
  justify-content: center;
  padding: 8px 0 0;
}

.add-btn {
  width: 100%;
  border-style: dashed;
}

/* 表单提示 */
.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

/* 预设选项 */
.preset-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 2px 0;
}

.preset-label {
  font-size: 13px;
  font-weight: 500;
}

.preset-url {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

/* 列表过渡 */
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.list-move {
  transition: transform 0.3s ease;
}
</style>
