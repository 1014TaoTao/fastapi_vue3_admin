<!-- 重置密码 / 忘记密码 -->
<template>
  <div>
    <ElForm
      ref="formRef"
      :model="forgetForm"
      :rules="forgetRules"
      :key="formKey"
      class="login-page-form mt-4"
      @keyup.enter="$emit('submit')"
    >
      <ElFormItem prop="username">
        <ElInput
          v-model.trim="forgetForm.username"
          class="custom-height"
          clearable
          :placeholder="$t('login.placeholder.username')"
          @keyup.enter="$emit('submit')"
        >
          <template #prefix>
            <ElIcon><User /></ElIcon>
          </template>
        </ElInput>
      </ElFormItem>
      <div class="mt-6">
        <ElButton
          class="h-11 w-full min-w-0 rounded-lg! text-base font-medium"
          type="primary"
          :loading="forgetLoading"
          v-ripple
          @click="$emit('submit')"
        >
          {{ $t("common.confirm") }}
        </ElButton>
      </div>
    </ElForm>

    <FaLoginAuthLinkRow
      :hint="$t('login.thinkOfPasswd')"
      :link-text="$t('login.backLoginBtnText')"
      @link="$emit('toLogin')"
    />
  </div>
</template>

<script setup lang="ts">
import { User } from "@element-plus/icons-vue";
import type { ForgetPasswordForm } from "@/api/module_system/user";
import type { FormRules } from "element-plus";

const forgetForm = defineModel<ForgetPasswordForm>("forgetForm", { required: true });

defineOptions({ name: "FaLoginForgetPanel" });

interface Props {
  forgetRules: FormRules<ForgetPasswordForm>;
  formKey: number | string;
  forgetLoading: boolean;
}

withDefaults(defineProps<Props>(), {});

interface Emits {
  submit: [];
  toLogin: [];
}

defineEmits<Emits>();

const formRef = ref();

defineExpose({
  validate: () => formRef.value?.validate?.(),
  clearValidate: () => formRef.value?.clearValidate?.(),
});
</script>
