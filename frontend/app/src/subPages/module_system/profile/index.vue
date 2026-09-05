<script setup lang="ts">
import type { UserInfo, UserProfileForm } from '@/api/module_system/user'
import { onLoad } from '@dcloudio/uni-app'
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import UserAPI from '@/api/module_system/user'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'
import { useUserStore } from '@/store/userStore'

definePage({
  name: 'profile',
  layout: 'default',
  style: { navigationBarTitleText: '个人资料' },
})
useI18nNavTitle('profile.navTitle')

const { t } = useI18n()
const toast = useToast()
const userStore = useUserStore()

const loading = ref(false)
const saving = ref(false)
const userProfile = ref<UserInfo>()

/** 头像上传：后端通用文件上传（upload_type=avatar），字段名 file */
const uploadAvatarAction = `${import.meta.env.VITE_API_BASE_URL || ''}${import.meta.env.VITE_APP_BASE_API || ''}/file/upload?upload_type=avatar`
const uploadHeader = { Authorization: `Bearer ${userStore.getAccessToken() || ''}` }
const avatarFileList = ref<{ url: string }[]>([])

const genderText = computed(() => {
  const gender = userProfile.value?.gender
  return gender === '0' ? t('profile.male') : gender === '1' ? t('profile.female') : t('profile.unknown')
})
const deptText = computed(() => userProfile.value?.dept_name || '-')
const roleText = computed(() => userProfile.value?.role_names?.join('、') || '-')

async function loadUserProfile() {
  loading.value = true
  try {
    userProfile.value = await UserAPI.getCurrentUserInfo()
  }
  catch {
    // http 层已统一错误提示
  }
  finally {
    loading.value = false
  }
}

/** 保存个人资料（昵称/性别/头像变更均走此接口） */
async function saveProfile(patch: Partial<UserProfileForm>) {
  const profile = userProfile.value
  if (!profile)
    return
  saving.value = true
  try {
    await UserAPI.updateCurrentUserInfo({
      name: patch.name ?? profile.name ?? '',
      gender: patch.gender ?? profile.gender ?? '0',
      mobile: profile.mobile || '',
      email: profile.email || '',
      username: profile.username || '',
      dept_name: profile.dept_name || '',
      positions: profile.positions || [],
      roles: profile.roles || [],
      avatar: patch.avatar ?? (profile.avatar || ''),
    })
    toast.success(t('common.saveSuccess'))
    await loadUserProfile()
    // 同步全局用户信息，使「我的」页展示最新昵称/头像
    userStore.setUserInfo({ ...userStore.userInfo, ...patch })
  }
  catch {
    // http 层已统一错误提示
  }
  finally {
    saving.value = false
  }
}

/** 头像上传成功：wd-upload 的 response 为字符串，解析后保存 */
function handleAvatarSuccess(e: { file: { response?: string | Record<string, any> } }) {
  try {
    const raw = typeof e.file.response === 'string' ? e.file.response : JSON.stringify(e.file.response || {})
    const res = JSON.parse(raw) as { code: number, msg?: string, data?: { file_url?: string } }
    if (res.code === 0 && res.data?.file_url) {
      avatarFileList.value = []
      saveProfile({ avatar: res.data.file_url })
    }
    else {
      toast.error(res.msg || t('profile.uploadFailed'))
      avatarFileList.value = []
    }
  }
  catch {
    toast.error(t('profile.uploadFailed'))
    avatarFileList.value = []
  }
}
function handleAvatarFail() {
  toast.error(t('profile.uploadFailed'))
  avatarFileList.value = []
}

/** 昵称 / 性别编辑弹窗 */
const editDialog = reactive<{ visible: boolean, field: 'name' | 'gender' }>({ visible: false, field: 'name' })
const editForm = reactive<{ name: string, gender: string }>({ name: '', gender: '0' })
const editTitle = computed(() => editDialog.field === 'name' ? t('profile.editNickname') : t('profile.selectGender'))

function openEdit(field: 'name' | 'gender') {
  editDialog.field = field
  editDialog.visible = true
  if (field === 'name')
    editForm.name = userProfile.value?.name || ''
  else
    editForm.gender = userProfile.value?.gender || '0'
}

async function handleEditSubmit() {
  if (editDialog.field === 'name') {
    const name = editForm.name.trim()
    if (!name) {
      toast.warning(t('profile.nicknameRequired'))
      return
    }
    await saveProfile({ name })
  }
  else {
    await saveProfile({ gender: editForm.gender })
  }
  editDialog.visible = false
}

onLoad(() => {
  loadUserProfile()
})
</script>

<template>
  <view class="page-wraper py-3">
    <SkeletonPage v-if="loading && !userProfile" :rows="6" />

    <template v-else>
      <!-- 头像 + 昵称（点击头像即上传更换） -->
      <view class="mx-3 mb-3 flex flex-col items-center gap-2 py-4">
        <wd-upload
          v-model:file-list="avatarFileList"
          :action="uploadAvatarAction"
          :header="uploadHeader"
          :limit="1"
          accept="image"
          :max-size="5242880"
          :source-type="['album', 'camera']"
          @success="handleAvatarSuccess"
          @fail="handleAvatarFail"
        >
          <view class="relative">
            <wd-avatar
              size="80px"
              round
              :src="userProfile?.avatar || ''"
              :text="(userProfile?.name || userProfile?.username || '?').charAt(0)"
            />
            <!-- 相机角标：示意可更换头像 -->
            <view
              class="wot-bg-primary-6 absolute h-6 w-6 flex items-center justify-center rounded-full -bottom-0.5 -right-0.5"
              style="border: 3rpx solid var(--wot-filled-content, #FFFFFF);"
            >
              <wd-icon name="camera" size="12px" color="#FFFFFF" />
            </view>
          </view>
        </wd-upload>
        <wd-text class="wot-text-text-main text-4" :text="userProfile?.name || userProfile?.username || '-'" bold />
      </view>

      <!-- 资料列表 -->
      <view class="mx-3 mb-3">
        <wd-cell-group border custom-class="rounded-2! overflow-hidden">
          <wd-cell :title="t('profile.nickname')" is-link @click="openEdit('name')">
            <wd-text class="wot-text-text-secondary" :text="userProfile?.name || t('profile.notSet')" />
          </wd-cell>
          <wd-cell :title="t('profile.gender')" is-link @click="openEdit('gender')">
            <wd-text class="wot-text-text-secondary" :text="genderText" />
          </wd-cell>
          <wd-cell :title="t('profile.username')" :value="userProfile?.username || '-'" />
          <wd-cell :title="t('profile.mobile')">
            <wd-text class="wot-text-text-secondary" :text="userProfile?.mobile || t('profile.notBound')" />
          </wd-cell>
          <wd-cell :title="t('profile.email')">
            <wd-text class="wot-text-text-secondary" :text="userProfile?.email || t('profile.notBound')" />
          </wd-cell>
          <wd-cell :title="t('profile.dept')" :value="deptText" />
          <wd-cell :title="t('profile.roles')" :value="roleText" />
        </wd-cell-group>
      </view>

      <!-- 昵称 / 性别编辑弹窗 -->
      <wd-popup
        v-model="editDialog.visible"
        position="bottom"
        round
        custom-style="padding-bottom: env(safe-area-inset-bottom);"
      >
        <view class="wot-text-text-main px-4 pb-4 pt-4 text-center text-4 font-bold">
          {{ editTitle }}
        </view>
        <view class="px-4 pb-4">
          <wd-input
            v-if="editDialog.field === 'name'"
            v-model="editForm.name"
            :placeholder="t('profile.nickname')"
            clearable
          />
          <wd-radio-group v-else v-model="editForm.gender" direction="horizontal">
            <wd-radio value="0">
              {{ t('profile.male') }}
            </wd-radio>
            <wd-radio value="1">
              {{ t('profile.female') }}
            </wd-radio>
          </wd-radio-group>
          <view class="mt-4">
            <wd-button type="primary" round block :loading="saving" @click="handleEditSubmit">
              {{ t('common.save') }}
            </wd-button>
          </view>
        </view>
        <wd-gap :height="20" />
      </wd-popup>
    </template>
  </view>
</template>
