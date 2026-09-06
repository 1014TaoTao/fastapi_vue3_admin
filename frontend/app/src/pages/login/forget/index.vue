<script setup lang="ts">
import type { FormSchema } from '@wot-ui/ui/components/wd-form/types'
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import UserAPI from '@/api/module_system/user'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'
import { REMEMBER_ME_KEY } from '@/constants'
import { Storage } from '@/utils/storage'

definePage({ name: 'forget', style: { navigationBarTitleText: '忘记密码' } })
useI18nNavTitle('forget.navTitle')

const { t } = useI18n()
const toast = useToast()

const submitting = ref(false)
const forgetFormRef = ref()
const forgetForm = reactive({
  username: '',
})

/** 与后端 UserForgetPasswordSchema 一致：字母开头，3-32 位，仅允许字母、数字、_ . - */
const USERNAME_REG = /^[a-z][\w.-]{2,31}$/i

/** 表单验证 schema — 字段级错误提示（与登录页 wd-form 一致） */
const forgetSchema: FormSchema = {
  validate: (model) => {
    const errors: Array<{ path: Array<string | number>, message: string }> = []
    const username = String(model.username ?? '').trim()
    if (!username)
      errors.push({ path: ['username'], message: t('common.form.usernameRequired') })
    else if (!USERNAME_REG.test(username))
      errors.push({ path: ['username'], message: t('common.form.usernameFormat') })
    return errors
  },
}

/** 提交忘记密码申请：后端不会直接改密，成功后提示联系管理员 */
async function handleSubmit() {
  if (submitting.value)
    return
  const { valid } = await forgetFormRef.value.validate()
  if (!valid)
    return

  const username = forgetForm.username.trim()
  submitting.value = true
  try {
    await UserAPI.forgetPassword({ username })
    Storage.set(REMEMBER_ME_KEY, { username, remember: true })
    toast.success(t('forget.success'))
    uni.reLaunch({ url: '/pages/login/index' })
  }
  catch {
    // http 层已统一错误提示
  }
  finally {
    submitting.value = false
  }
}

function goLogin() {
  uni.reLaunch({ url: '/pages/login/index' })
}
</script>

<template>
  <view class="forget-page">
    <view class="forget-card">
      <text class="forget-card__title">
        {{ t('forget.title') }}
      </text>

      <view class="forget-form">
        <wd-form ref="forgetFormRef" :model="forgetForm" :schema="forgetSchema">
          <wd-form-item prop="username" custom-style="margin-bottom: 14rpx; padding-left: 0; padding-right: 0;">
            <wd-input
              v-model="forgetForm.username"
              :placeholder="t('common.form.usernamePlaceholder')"
              clearable
              :compact="false"
              prefix-icon="user"
            />
          </wd-form-item>
        </wd-form>
        <wd-button type="primary" round block :loading="submitting" @click="handleSubmit">
          {{ submitting ? t('forget.submitting') : t('forget.submit') }}
        </wd-button>
      </view>

      <view class="forget-footer">
        <wd-text class="forget-footer__link" :text="t('forget.toLogin')" type="primary" @click="goLogin" />
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.forget-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  /* H5 下 100vh 包含导航栏，使用uni-app的可用视口高度变量避免溢出 */
  /* #ifdef H5 */
  height: calc(100vh - 44px);
  /* #endif */
  /* #ifndef H5 */
  height: 100vh;
  /* #endif */
  padding: 0 64rpx;
  padding-bottom: calc(48rpx + env(safe-area-inset-bottom));
  /* 接入全局水滴渐变（--drop-bg 由 App.vue 按主题色定义，暗色回退纯色由下方规则接管） */
  background: var(--drop-bg, #F9F9F9);
  overflow: hidden;
  box-sizing: border-box;
}

/* 暗黑模式下整页背景变深，消除白色断层（wot 根类为 wot-theme-dark） */
.wot-theme-dark .forget-page {
  @apply wot-bg-filled-bottom;
}

.forget-card {
  width: 100%;
  margin-top: 120rpx;
  /* 亮色下默认带主题色最浅阶，避免一片纯白；--card-bg-color 可被外部覆盖 */
  background: var(--card-bg-color, var(--wot-primary-1, #FFFFFF));
  border-radius: var(--radius-xl, 32rpx);
  padding: 40rpx 36rpx;
  /* 边框跟随主题色浅阶，替代中性灰，让卡片更有主题感 */
  border: 2rpx solid var(--border-color, var(--wot-primary-2, #EAECF0));
  box-shadow: var(--shadow-md, 0 8rpx 32rpx rgba(15, 23, 42, 0.04));

  .wot-theme-dark & {
    @apply wot-bg-filled-content;
    border-color: var(--border-color, #2C2C2E);
    box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.2);
  }

  &__title {
    display: block;
    font-size: var(--font-xl, 36rpx);
    font-weight: 600;
    @apply wot-text-text-main;
    margin-bottom: 28rpx;

    /* 暗黑模式下使用纯白，提升卡片标题醒目度 */
    .wot-theme-dark & {
      color: #FFFFFF;
    }
  }
}

.forget-form {
  :deep(.wd-input) {
    border-radius: 24rpx;
    /* 亮色下主题色浅阶边框与卡片边框呼应，白色底在淡色卡片上形成浮层 */
    border: 2rpx solid var(--wot-primary-2, var(--wot-border-main, #EAECF0));
    box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.05);
  }

  /* H5 聚焦态：主题色描边 + 淡色光晕（MP 端不支持 :focus-within，跳过） */
  /* #ifdef H5 */
  :deep(.wd-input:focus-within) {
    border-color: var(--wot-primary-6, #1C64FD);
    box-shadow: 0 0 0 4rpx var(--wot-primary-1, #F5F8FF);
  }
  /* #endif */

  /* 去掉 wd-cell 自带左右内边距，使输入框与登录按钮同宽（与登录页一致） */
  :deep(.wd-form-item) {
    margin-bottom: 14rpx;
    padding-left: 0;
    padding-right: 0;
  }
}

/* cell 容器回归透明：亮色下消除输入框外围的白色方形区域，暗色下消除纯黑块，
   让自带圆角+边框的输入框直接显示在卡片上 */
:deep(.wd-cell) {
  --wot-cell-bg: transparent;
}

.wot-theme-dark .forget-page :deep(.wd-input) {
  /* 比卡片背景（filled-content）亮一档，输入框在暗色卡片上凸起有层次 */
  --wot-input-bg: var(--wot-coolgrey-8, var(--wot-filled-content));
  border-color: var(--wot-border-main, #2C2C2E);
  box-shadow: none;
}

.forget-footer {
  display: flex;
  justify-content: center;
  margin-top: 32rpx;

  &__link {
    font-size: var(--font-md, 28rpx);
  }
}

/* MP 端兼容：wd-form-item 内部 wd-cell 因 uni-app 插槽静态声明（u-s）误判 label/title 插槽被使用，
   showLeft=true 渲染空 left 区域（flex:1 占半宽），H5 端运行时插槽判定无此问题。
   本页 form-item 无 title/label/prefix 内容，隐藏 left 安全，保证输入框与登录按钮同宽 */
.forget-card .wd-form-item .wd-cell__left {
  display: none;
}
</style>
