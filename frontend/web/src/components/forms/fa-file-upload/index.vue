<!-- 单文件上传控件：绑定文件 URL，上传到 /file/upload（upload_type=file） -->
<template>
  <div class="fa-file-upload">
    <div v-if="modelValue" class="file-item">
      <el-icon class="file-item-icon"><Document /></el-icon>
      <el-link type="primary" :href="modelValue" target="_blank" :underline="false">
        {{ fileName }}
      </el-link>
      <el-icon class="file-item-action" title="移除" @click="handleRemove"><CircleCloseFilled /></el-icon>
    </div>
    <el-button v-else type="primary" plain :loading="uploading" @click="fileInputRef?.click()">
      <el-icon class="mr-1"><UploadFilled /></el-icon>
      <span>选择文件</span>
    </el-button>
    <input
      ref="fileInputRef"
      class="file-input"
      type="file"
      :accept="accept"
      @change="onFileChange"
    />
    <div v-if="tip" class="file-tip">{{ tip }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { CircleCloseFilled, Document, UploadFilled } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { request } from "@utils";
import type { AxiosResponse } from "axios";

defineOptions({ name: "FaFileUpload" });

interface Props {
  /** 允许的文件类型（accept 语法，默认不限） */
  accept?: string;
  /** 文件大小上限（MB） */
  maxSize?: number;
  /** 提示文案 */
  tip?: string;
}

const props = withDefaults(defineProps<Props>(), {
  accept: "",
  maxSize: 20,
  tip: "",
});

const modelValue = defineModel<string>({ default: "" });

const uploading = ref(false);
const fileInputRef = ref<HTMLInputElement>();

const fileName = computed(() => {
  const url = modelValue.value;
  if (!url) return "";
  try {
    const { pathname } = new URL(url, window.location.origin);
    return pathname.split("/").filter(Boolean).pop() || url;
  } catch {
    return url.split("/").pop() || url;
  }
});

const handleRemove = () => {
  modelValue.value = "";
};

const onFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;

  if (file.size > props.maxSize * 1024 * 1024) {
    ElMessage.warning(`文件大小不能超过 ${props.maxSize}MB`);
    return;
  }

  void doUpload(file);
};

const doUpload = async (file: File) => {
  uploading.value = true;
  try {
    const formData = new FormData();
    formData.append("file", file);
    const response = await request.post<
      ApiResponse<UploadFilePath>,
      AxiosResponse<ApiResponse<UploadFilePath>>
    >("/file/upload", formData, {
      params: { upload_type: "file" },
      headers: { "Content-Type": "multipart/form-data" },
    });
    const fileUrl = response.data.data?.file_url;
    if (!fileUrl) {
      throw new Error("上传失败，未返回文件地址");
    }
    modelValue.value = fileUrl;
    ElMessage.success("上传成功");
  } catch (error) {
    console.error("文件上传失败:", error);
    ElMessage.error("文件上传失败");
  } finally {
    uploading.value = false;
  }
};
</script>

<style scoped>
.fa-file-upload .file-input {
  display: none;
}

.fa-file-upload .file-item {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.fa-file-upload .file-item-icon {
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.fa-file-upload .file-item-action {
  cursor: pointer;
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.fa-file-upload .file-item-action:hover {
  color: var(--el-color-danger);
}

.fa-file-upload .file-tip {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}
</style>
