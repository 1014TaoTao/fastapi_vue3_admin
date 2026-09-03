<!-- 个人中心（Art 模版布局 + 当前用户接口） -->
<template>
  <div class="w-full h-full p-0 bg-transparent border-none shadow-none">
    <div class="relative flex justify-between mt-2.5 max-md:block max-md:mt-1">
      <!-- 左侧卡片 -->
      <div class="w-md mr-5 max-md:w-full max-md:mr-0">
        <div class="fa-card-sm relative p-9 pb-6 overflow-hidden text-center">
          <img
            class="absolute top-0 left-0 w-full h-50 object-cover"
            src="@imgs/user/bg.webp"
            alt=""
          />

          <div class="relative z-10 mt-30 mx-auto">
            <div class="relative inline-block">
              <img
                v-if="infoFormState.avatar"
                class="w-20 h-20 object-cover border-2 border-white rounded-full"
                :src="infoFormState.avatar"
                alt=""
              />
              <img
                v-else
                class="w-20 h-20 object-cover border-2 border-white rounded-full"
                src="@imgs/user/avatar.webp"
                alt=""
              />
              <ElUpload
                ref="uploadRef"
                v-model:file-list="fileList"
                class="profile-avatar-upload"
                name="file"
                :show-file-list="false"
                :before-upload="handleBeforeUpload"
                :http-request="handleUpload"
                :limit="1"
                :auto-upload="false"
                @change="handleAvatarFileChange"
              >
                <template #trigger>
                  <ElButton
                    type="primary"
                    :icon="Camera"
                    circle
                    size="small"
                    class="upload-trigger"
                  />
                </template>
              </ElUpload>
            </div>
          </div>

          <p class="relative z-10 mt-3 text-sm text-g-600">{{ greeting }}</p>
          <h2 class="relative z-10 mt-1 text-xl font-normal">{{ infoFormState.name || "—" }}</h2>
          <p class="relative z-10 mt-2 text-sm text-g-500">
            {{ infoFormState.roles?.map((r) => r.name).join("、") || " " }}
          </p>

          <div class="relative z-10 w-75 mx-auto mt-7.5 text-left">
            <div class="mt-2.5 flex items-start">
              <FaSvgIcon icon="ri:user-3-line" class="text-g-700 shrink-0 mt-0.5" />
              <span class="ml-2 text-sm">{{ infoFormState.username || "—" }}</span>
            </div>
            <div class="mt-2.5 flex items-start">
              <FaSvgIcon icon="ri:checkbox-circle-line" class="text-g-700 shrink-0 mt-0.5" />
              <ElTag :type="infoFormState.status === 0 ? 'success' : 'danger'" size="small">
                {{ infoFormState.status === 0 ? "启用" : "停用" }}
              </ElTag>
            </div>
            <div class="mt-2.5 flex items-start">
              <FaSvgIcon icon="ri:mail-line" class="text-g-700 shrink-0 mt-0.5" />
              <span class="ml-2 text-sm break-all">{{ infoFormState.email || "—" }}</span>
            </div>
            <div class="mt-2.5 flex items-start">
              <FaSvgIcon icon="ri:map-pin-line" class="text-g-700 shrink-0 mt-0.5" />
              <span class="ml-2 text-sm">{{ infoFormState.dept?.name || "—" }}</span>
            </div>
            <div class="mt-2.5 flex items-start">
              <FaSvgIcon icon="ri:briefcase-line" class="text-g-700 shrink-0 mt-0.5" />
              <span class="ml-2 text-sm">
                {{ infoFormState.positions?.map((p) => p.name).join("、") || "—" }}
              </span>
            </div>
            <div class="mt-2.5 flex items-start">
              <FaSvgIcon icon="ri:calendar-line" class="text-g-700 shrink-0 mt-0.5" />
              <span class="ml-2 text-sm">
                注册:
                {{ infoFormState.created_time ? formatDate(infoFormState.created_time) : "—" }}
              </span>
            </div>
            <div class="mt-2.5 flex items-start">
              <FaSvgIcon icon="ri:time-line" class="text-g-700 shrink-0 mt-0.5" />
              <span class="ml-2 text-sm">
                更新:
                {{ infoFormState.updated_time ? formatDate(infoFormState.updated_time) : "—" }}
              </span>
            </div>
          </div>
          <div v-if="roleTagList.length" class="relative z-10 mt-10">
            <h3 class="text-sm font-medium">角色</h3>
            <div class="flex flex-wrap justify-center mt-3.5">
              <div
                v-for="item in roleTagList"
                :key="item"
                class="py-1 px-1.5 mr-2.5 mb-2.5 text-xs border border-g-300 rounded"
              >
                {{ item }}
              </div>
            </div>
          </div>

          <div v-if="hasThirdPartyBindings" class="relative z-10 mt-10">
            <h3 class="text-sm font-medium">第三方账号</h3>
            <div class="flex flex-wrap justify-center mt-3.5 gap-3">
              <div v-if="infoFormState.github_login" class="flex items-center text-xs text-g-600">
                <FaSvgIcon icon="ri:github-fill" class="mr-1" />
                {{ infoFormState.github_login }}
              </div>
              <div v-if="infoFormState.gitee_login" class="flex items-center text-xs text-g-600">
                <FaSvgIcon icon="ri:gitee-fill" class="mr-1" />
                {{ infoFormState.gitee_login }}
              </div>
              <div v-if="infoFormState.wx_login" class="flex items-center text-xs text-g-600">
                <FaSvgIcon icon="ri:wechat-fill" class="mr-1" />
                {{ infoFormState.wx_login }}
              </div>
              <div v-if="infoFormState.qq_login" class="flex items-center text-xs text-g-600">
                <FaSvgIcon icon="ri:qq-fill" class="mr-1" />
                {{ infoFormState.qq_login }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <FaDialog
        v-model="avatarCropVisible"
        title="裁剪头像"
        width="960px"
        :draggable="false"
        @closed="onAvatarCropDialogClosed"
      >
        <FaCutterImg
          v-if="avatarCropVisible && avatarCropSrc"
          :key="avatarCropSrc"
          v-model:imgUrl="avatarCropSrc"
          :boxWidth="530"
          :boxHeight="300"
          :cutWidth="360"
          :cutHeight="200"
          :quality="1"
          :tool="true"
          :showPreview="true"
          :originalGraph="false"
          title="调整头像"
          previewTitle="预览"
          @update:img-url="onAvatarCropConfirm"
          @error="onAvatarCropImgError"
        />
      </FaDialog>

      <!-- 右侧表单 -->
      <div class="flex-1 overflow-hidden max-md:w-full max-md:mt-3.5">
        <div class="fa-card-sm">
          <h1 class="p-4 text-xl font-normal border-b border-g-300">基本设置</h1>

          <ElForm
            ref="infoFormRef"
            :model="infoFormState"
            class="box-border p-5 [&>.el-row_.el-form-item]:w-[calc(50%-10px)] [&>.el-row_.el-input]:w-full [&>.el-row_.el-select]:w-full"
            :rules="rules"
            label-width="86px"
            label-position="top"
          >
            <ElRow>
              <ElFormItem label="姓名" prop="name">
                <ElInput
                  v-model="infoFormState.name"
                  :disabled="!isEdit"
                  placeholder="请输入姓名"
                />
              </ElFormItem>
              <ElFormItem label="性别" prop="gender" class="ml-5">
                <ElSelect
                  v-model="infoFormState.gender"
                  placeholder="请选择"
                  :disabled="!isEdit"
                  class="w-full"
                >
                  <ElOption
                    v-for="item in dictDataStore['sys_user_sex']"
                    :key="String(item.dict_value)"
                    :label="item.dict_label"
                    :value="normalizeGenderValue(item.dict_value)"
                  />
                </ElSelect>
              </ElFormItem>
            </ElRow>

            <ElRow>
              <ElFormItem label="邮箱" prop="email">
                <ElInput
                  v-model="infoFormState.email"
                  :disabled="!isEdit"
                  placeholder="请输入邮箱"
                />
              </ElFormItem>
              <ElFormItem label="手机" prop="mobile" class="ml-5">
                <ElInput
                  v-model="infoFormState.mobile"
                  :disabled="!isEdit"
                  placeholder="请输入手机号码"
                />
              </ElFormItem>
            </ElRow>

            <ElRow class="mb-4">
              <ElFormItem label="描述" prop="description" class="w-full!">
                <ElInput
                  v-model="infoFormState.description"
                  :disabled="!isEdit"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入描述"
                />
              </ElFormItem>
            </ElRow>

            <div class="flex items-center justify-end [&_.el-button]:w-27.5!">
              <ElButton
                type="primary"
                class="w-22.5"
                :loading="infoSubmitting"
                v-ripple
                @click="onBasicToggleSave"
              >
                {{ isEdit ? "保存" : "编辑" }}
              </ElButton>
            </div>
          </ElForm>
        </div>

        <div class="fa-card-sm my-5">
          <h1 class="p-4 text-xl font-normal border-b border-g-300">登录会话</h1>

          <div v-if="loadingSessions" class="flex justify-center py-6">
            <ElIcon class="is-loading" :size="20">
              <Loading />
            </ElIcon>
          </div>

          <div v-else-if="currentSessions.length === 0" class="p-5 text-sm text-g-400 text-center">
            暂无活跃会话
          </div>

          <ElTable v-else :data="currentSessions" stripe class="p-4" size="small">
            <ElTableColumn type="index" label="#" width="50" />
            <ElTableColumn label="浏览器" min-width="110">
              <template #default="{ row }">
                <FaSvgIcon :icon="getBrowserIcon(row.browser)" class="mr-1" />{{
                  row.browser || "—"
                }}
              </template>
            </ElTableColumn>
            <ElTableColumn label="操作系统" min-width="110">
              <template #default="{ row }">
                <FaSvgIcon :icon="getOsIcon(row.os)" class="mr-1" />{{ row.os || "—" }}
              </template>
            </ElTableColumn>
            <ElTableColumn prop="ipaddr" label="IP 地址" min-width="130" />
            <ElTableColumn prop="login_location" label="登录位置" min-width="120" />
            <ElTableColumn label="登录时间" min-width="160">
              <template #default="{ row }">
                {{ row.login_time ? formatDate(row.login_time) : "—" }}
              </template>
            </ElTableColumn>
          </ElTable>
        </div>

        <div class="fa-card-sm my-5">
          <h1 class="p-4 text-xl font-normal border-b border-g-300">更改密码</h1>

          <ElForm
            ref="passwordFormRef"
            :model="passwordFormState"
            class="box-border p-5"
            :rules="resetPasswordRules"
            label-width="86px"
            label-position="top"
          >
            <ElFormItem label="当前密码" prop="old_password">
              <ElInput
                v-model="passwordFormState.old_password"
                type="password"
                :disabled="!isEditPwd"
                show-password
              />
            </ElFormItem>

            <ElFormItem label="新密码" prop="new_password">
              <ElInput
                v-model="passwordFormState.new_password"
                type="password"
                :disabled="!isEditPwd"
                show-password
              />
            </ElFormItem>

            <ElFormItem label="确认新密码" prop="confirm_password">
              <ElInput
                v-model="passwordFormState.confirm_password"
                type="password"
                :disabled="!isEditPwd"
                show-password
              />
            </ElFormItem>

            <div class="flex items-center justify-end [&_.el-button]:w-27.5!">
              <ElButton
                type="primary"
                class="w-22.5"
                :loading="passwordChanging"
                v-ripple
                @click="onPasswordToggleSave"
              >
                {{ isEditPwd ? "保存" : "编辑" }}
              </ElButton>
            </div>
          </ElForm>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { FormInstance, UploadRequestOptions, UploadFile } from "element-plus";
import type { ElUpload } from "element-plus";
import UserAPI, { type InfoFormState, type PasswordFormState } from "@/api/module_system/user";
import OnlineAPI from "@/api/module_monitor/online";
import type { OnlineUserTable } from "@/api/module_monitor/online";
import { useUserStore, useDictStore } from "@stores";
import { Camera, Loading } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { useI18n } from "vue-i18n";
import { redirectToLogin, dataURLToFile } from "@utils";

defineOptions({ name: "UserProfile" });

const { t } = useI18n();
const userStore = useUserStore();
const dictStore = useDictStore();
const infoFormRef = ref<FormInstance>();
const passwordFormRef = ref<FormInstance>();

const infoSubmitting = ref(false);
const passwordChanging = ref(false);

const isEdit = ref(false);
const isEditPwd = ref(false);

const dictDataStore = computed(() => dictStore.dictData);

const greeting = ref("");

const roleTagList = computed(() =>
  (infoFormState.roles ?? [])
    .map((r) => r.name)
    .filter((n): n is string => !!n && n.trim().length > 0)
);

const currentSessions = ref<OnlineUserTable[]>([]);
const loadingSessions = ref(false);

function getBrowserIcon(browser?: string): string {
  if (!browser) return "ri:question-line";
  const lower = browser.toLowerCase();
  if (lower.includes("chrome")) return "ri:chrome-fill";
  if (lower.includes("firefox") || lower.includes("mozilla")) return "ri:firefox-fill";
  if (lower.includes("safari")) return "ri:safari-fill";
  if (lower.includes("edge")) return "ri:edge-fill";
  if (lower.includes("opera")) return "ri:opera-fill";
  return "ri:earth-line";
}

function getOsIcon(os?: string): string {
  if (!os) return "ri:question-line";
  const lower = os.toLowerCase();
  if (lower.includes("windows")) return "ri:windows-fill";
  if (lower.includes("mac") || lower.includes("darwin")) return "ri:apple-fill";
  if (lower.includes("linux")) return "ri:linux-fill";
  if (lower.includes("android")) return "ri:android-fill";
  if (lower.includes("ios")) return "ri:apple-fill";
  return "ri:computer-line";
}

async function fetchCurrentSessions() {
  loadingSessions.value = true;
  try {
    const response = await OnlineAPI.listCurrentOnline();
    if (response.data.code === 0) {
      currentSessions.value = response.data.data ?? [];
    }
  } catch {
    // ignore
  } finally {
    loadingSessions.value = false;
  }
}

const hasThirdPartyBindings = computed(
  () =>
    !!(
      infoFormState.github_login ||
      infoFormState.gitee_login ||
      infoFormState.wx_login ||
      infoFormState.qq_login
    )
);

function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return "—";
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return dateStr;
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const infoFormState = reactive<InfoFormState>({
  name: undefined,
  gender: undefined,
  mobile: undefined,
  email: undefined,
  username: undefined,
  dept_name: undefined,
  dept: {},
  positions: [],
  roles: [],
  avatar: undefined,
  created_time: undefined,
  updated_time: undefined,
  description: undefined,
  status: undefined,
  github_login: undefined,
  gitee_login: undefined,
  wx_login: undefined,
  qq_login: undefined,
});

const passwordFormState = reactive<PasswordFormState>({
  old_password: "",
  new_password: "",
  confirm_password: "",
});

const fileList = ref<any[]>([]);
const uploadRef = ref<InstanceType<typeof ElUpload>>();

const avatarCropVisible = ref(false);
const avatarCropSrc = ref("");
const avatarCropName = ref("");

function revokeAvatarCropSrc() {
  if (avatarCropSrc.value.startsWith("blob:")) {
    URL.revokeObjectURL(avatarCropSrc.value);
  }
  avatarCropSrc.value = "";
}

function onAvatarCropDialogClosed() {
  revokeAvatarCropSrc();
}

function onAvatarCropImgError() {
  ElMessage.error("图片加载失败，请换一张图重试");
}

async function onAvatarCropConfirm(dataURL: string) {
  try {
    const file = dataURLToFile(dataURL, avatarCropName.value);
    const formData = new FormData();
    formData.append("file", file);
    const response = await UserAPI.uploadCurrentUserAvatar(formData);

    if (response.data.code === 0 && response.data.data) {
      const fileUrl = response.data.data.file_url;
      updateAvatar(fileUrl);
      uploadRef.value?.clearFiles();
      fileList.value = [];
      ElMessage.success("头像已更新，请保存基本设置以同步资料（如需）");
      avatarCropVisible.value = false;
    } else {
      ElMessage.error(response.data.msg || "上传失败");
    }
  } catch {
    ElMessage.error("头像上传失败，请重试");
  }
}

/** 性别统一为字符串，与后端 CurrentUserUpdateSchema(gender: str) 对齐 */
function normalizeGenderValue(v: string | number | undefined): string {
  if (v === undefined || v === null || v === "") return "1";
  const n = typeof v === "string" ? Number(v) : v;
  return Number.isFinite(n) ? String(n) : "1";
}

const initInfoForm = () => {
  const basicInfo = userStore.basicInfo;
  Object.assign(infoFormState, {
    ...basicInfo,
    gender: normalizeGenderValue(basicInfo.gender),
    avatar: basicInfo.avatar?.trim(),
  });
};

const getOptions = async () => {
  await dictStore.getDict(["sys_user_sex"]);
};

const rules = {
  name: [{ required: true, message: "请输入姓名", trigger: "blur" }],
  mobile: [
    {
      validator: (_: unknown, v: string, cb: (e?: Error) => void) => {
        const s = v != null ? String(v).trim() : "";
        if (!s) return cb();
        if (!/^1[3-9]\d{9}$/.test(s)) {
          cb(new Error("请输入有效的手机号格式"));
          return;
        }
        cb();
      },
      trigger: "blur",
    },
  ],
  email: [
    {
      validator: (_: unknown, v: string, cb: (e?: Error) => void) => {
        const s = v != null ? String(v).trim() : "";
        if (!s) return cb();
        if (!/\w[-\w.+]*@([A-Za-z0-9][-A-Za-z0-9]+\.)+[A-Za-z]{2,14}/.test(s)) {
          cb(new Error("请输入有效的邮箱格式"));
          return;
        }
        cb();
      },
      trigger: "blur",
    },
  ],
};

const resetPasswordRules = {
  old_password: [
    {
      required: true,
      trigger: "blur",
      message: t("login.message.password.currentRequired"),
    },
  ],
  new_password: [
    {
      required: true,
      trigger: "blur",
      message: t("login.message.password.required"),
    },
    {
      min: 6,
      message: t("login.message.password.min"),
      trigger: "blur",
    },
  ],
  confirm_password: [
    {
      required: true,
      trigger: "blur",
      message: t("login.message.password.required"),
    },
    {
      min: 6,
      message: t("login.message.password.min"),
      trigger: "blur",
    },
    {
      validator: (_: unknown, value: string) => {
        return value === passwordFormState.new_password;
      },
      trigger: "blur",
      message: t("login.message.password.inconformity"),
    },
  ],
};

function refreshGreeting() {
  const h = new Date().getHours();
  if (h >= 6 && h < 9) greeting.value = "早上好";
  else if (h >= 9 && h < 11) greeting.value = "上午好";
  else if (h >= 11 && h < 13) greeting.value = "中午好";
  else if (h >= 13 && h < 18) greeting.value = "下午好";
  else if (h >= 18 && h < 24) greeting.value = "晚上好";
  else greeting.value = "很晚了，早点休息";
}

const handleBeforeUpload = (file: File) => {
  const isImage = file.type.startsWith("image/");
  const isLt2M = file.size / 1024 / 1024 < 2;

  if (!isImage) {
    ElMessage.error("只能上传图片文件");
    return false;
  }
  if (!isLt2M) {
    ElMessage.error("上传图片大小不能超过 2MB!");
    return false;
  }
  return true;
};

const handleUpload = async (options: UploadRequestOptions) => {
  try {
    const file = options.file;
    const formData = new FormData();
    formData.append("file", file);

    const response = await UserAPI.uploadCurrentUserAvatar(formData);

    if (response.data.code === 0 && response.data.data) {
      const fileUrl = response.data.data.file_url;
      updateAvatar(fileUrl);
      options.onSuccess(response);
      uploadRef.value?.clearFiles();
      fileList.value = [];
      ElMessage.success("头像已更新，请保存基本设置以同步资料（如需）");
    } else {
      const errorMsg = response.data.msg || "上传失败";
      ElMessage.error(errorMsg);
      options.onError({
        ...new Error(errorMsg),
        status: response.status || 500,
        method: "POST",
        url: "/system/user/current/avatar/upload",
      });
    }
  } catch (error) {
    ElMessage.error("头像上传失败，请重试");
    const errorObj = error instanceof Error ? error : new Error(String(error));
    options.onError({
      ...errorObj,
      status: 500,
      method: "POST",
      url: "/system/user/current/avatar/upload",
    });
  }
};

const handleAvatarFileChange = (file: UploadFile) => {
  if (!file.raw) {
    return;
  }
  if (!handleBeforeUpload(file.raw)) {
    uploadRef.value?.clearFiles();
    fileList.value = [];
    return;
  }

  const raw = file.raw;
  avatarCropName.value = raw.name;

  // 非 canvas 兼容格式（如 svg），跳过裁剪直接上传原文件
  if (raw.type !== "image/png" && raw.type !== "image/jpeg" && raw.type !== "image/webp") {
    uploadRef.value?.submit();
    return;
  }

  revokeAvatarCropSrc();
  avatarCropSrc.value = URL.createObjectURL(raw);
  avatarCropVisible.value = true;
  uploadRef.value?.clearFiles();
  fileList.value = [];
};

const updateAvatar = (fileUrl: string) => {
  if (fileUrl) {
    infoFormState.avatar = fileUrl.trim();
  } else {
    ElMessage.error("无效的头像URL");
  }
};

const initPasswordForm = () => {
  Object.assign(passwordFormState, {
    old_password: "",
    new_password: "",
    confirm_password: "",
  });
};

const handleSave = async () => {
  try {
    infoSubmitting.value = true;
    const valid = await infoFormRef.value?.validate().catch(() => false);
    if (!valid) {
      return false;
    }
    // 只提交后端可编辑字段，避免携带 dept/roles/positions 等冗余信息
    const response = await UserAPI.updateCurrentUserInfo({
      name: infoFormState.name,
      gender: infoFormState.gender,
      mobile: infoFormState.mobile,
      email: infoFormState.email,
      avatar: infoFormState.avatar,
      description: infoFormState.description,
    });
    await userStore.setUserInfo(response.data.data);
    initInfoForm();
    ElMessage.success("个人资料已保存");
    return true;
  } catch (e) {
    console.error(e);
    return false;
  } finally {
    infoSubmitting.value = false;
  }
};

const handlePasswordChange = async () => {
  try {
    passwordChanging.value = true;
    const valid = await passwordFormRef.value?.validate().catch(() => false);
    if (!valid) {
      return false;
    }
    const response = await UserAPI.changeCurrentUserPassword(passwordFormState);
    initPasswordForm();
    await redirectToLogin(response.data.msg);
    return true;
  } catch (error) {
    console.error(error);
    return false;
  } finally {
    passwordChanging.value = false;
  }
};

async function onBasicToggleSave() {
  if (!isEdit.value) {
    isEdit.value = true;
    return;
  }
  const ok = await handleSave();
  if (ok) {
    isEdit.value = false;
  }
}

async function onPasswordToggleSave() {
  if (!isEditPwd.value) {
    isEditPwd.value = true;
    initPasswordForm();
    return;
  }
  await handlePasswordChange();
}

onMounted(async () => {
  refreshGreeting();
  await getOptions();
  initInfoForm();
  await fetchCurrentSessions();
});
</script>

<style lang="scss" scoped>
.profile-avatar-upload {
  position: absolute;
  right: 0;
  bottom: 0;
  z-index: 2;

  :deep(.el-upload) {
    display: inline-flex;
  }

  .upload-trigger {
    box-shadow: 0 1px 4px rgb(0 0 0 / 15%);
  }
}
</style>
