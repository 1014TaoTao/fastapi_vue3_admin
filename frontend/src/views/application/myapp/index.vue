<!-- 我的应用管理 -->
<template> 
  <div class="app-container">
      <!-- 顶部搜索和操作区域 -->
      <div class="search-container mb-4">
        <el-form ref="queryFormRef" :model="queryFormData" :inline="true" label-suffix=":">
          <el-form-item prop="name" label="应用名称">
            <el-input v-model="queryFormData.name" placeholder="请输入应用名称" clearable style="width: 200px" />
          </el-form-item>
          <el-form-item prop="status" label="状态">
            <el-select v-model="queryFormData.status" placeholder="请选择状态" clearable style="width: 120px">
              <el-option label="启用" :value="true" />
              <el-option label="停用" :value="false" />
            </el-select>
          </el-form-item>
          <el-form-item prop="creator" label="创建人">
            <el-input v-model="queryFormData.creator" placeholder="请输入创建人" clearable style="width: 150px" />
          </el-form-item>
          <el-form-item class="search-buttons">
            <el-button type="primary" icon="search" @click="handleQuery">查询</el-button>
            <el-button icon="refresh" @click="handleResetQuery">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 应用卡片展示区域 -->
      <el-card shadow="hover" class="app-grid-card">
        <template #header>
          <div class="card-header">
            <span>应用市场</span>
            <el-button type="primary" icon="plus" @click="handleCreateApp">
              创建应用
            </el-button>
          </div>
        </template>

        <!-- 应用网格 -->
        <div v-loading="loading" class="app-grid">
        <div 
          v-for="app in applicationList" 
          :key="app.id"
          class="app-card"
        >
          <div class="app-card-header">
            <el-avatar :size="48" :src="app.icon_url" class="app-avatar">
              <el-icon size="24"><Monitor /></el-icon>
            </el-avatar>
            <div class="app-info">
              <h3 class="app-name">{{ app.name }}</h3>
              <el-tag :type="app.status ? 'success' : 'danger'" size="small">
                {{ app.status ? '启用' : '停用' }}
              </el-tag>
            </div>
            <el-dropdown trigger="click" @command="(command) => handleAppAction(command, app)">
              <el-button type="text" icon="MoreFilled" size="small" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit" icon="Edit">编辑</el-dropdown-item>
                  <el-dropdown-item command="delete" icon="Delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          
          <div class="app-card-body">
            <p class="app-desc">{{ app.description || '暂无描述' }}</p>
            <div class="app-meta">
              <span class="app-creator">{{ app.creator?.name || '未知' }}</span>
              <span class="app-time">{{ formatTime(app.created_at) }}</span>
            </div>
          </div>
          
          <div class="app-card-footer">
            <el-button 
              type="primary" 
              icon="Link" 
              size="small"
              @click="openAppExternal(app.access_url)"
              :disabled="!app.status"
            >
              外部打开
            </el-button>
            <el-button 
              type="default" 
              icon="View" 
              size="small"
              @click="openAppInternal(app)"
              :disabled="!app.status"
            >
              内部打开
            </el-button>
          </div>
        </div>
        </div>
        
        <!-- 空状态 -->
        <div v-if="applicationList.length === 0 && !loading" class="empty-state">
          <el-empty :image-size="120" description="暂无应用" />
        </div>

        <!-- 分页区域 -->
        <template #footer>
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="queryFormData.page_no"
              v-model:page-size="queryFormData.page_size"
              :total="total"
              :page-sizes="[12, 24, 48]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </template>
      </el-card>

    <!-- 应用创建/编辑弹窗 -->
    <el-drawer
      v-model="dialogVisible"
      :title="dialogTitle"
      :size="drawerSize"
      direction="rtl"
      @close="handleCloseDialog"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="应用名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入应用名称" />
        </el-form-item>
        
        <el-form-item label="访问地址" prop="access_url">
          <el-input v-model="formData.access_url" placeholder="请输入访问地址" />
        </el-form-item>
        
        <el-form-item label="图标地址" prop="icon_url">
          <el-input v-model="formData.icon_url" placeholder="请输入图标地址" />
        </el-form-item>
        
        <el-form-item label="应用状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio :value="true">启用</el-radio>
            <el-radio :value="false">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="应用描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="4"
            placeholder="请输入应用描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCloseDialog">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: "MyApplication",
  inheritAttrs: false,
});

import { useAppStore } from "@/store/modules/app.store";
import { useTagsViewStore } from "@/store";
import { useRouter } from "vue-router";
import { DeviceEnum } from "@/enums/settings/device.enum";
import ApplicationAPI, { type ApplicationForm, type ApplicationInfo, type ApplicationPageQuery } from "@/api/application/myapp";
import { formatToDateTime } from "@/utils/dateUtil";

const appStore = useAppStore();
const tagsViewStore = useTagsViewStore();
const router = useRouter();

// 响应式数据
const queryFormRef = ref();
const formRef = ref();
const loading = ref(false);
const total = ref(0);
const dialogVisible = ref(false);
const dialogType = ref<'create' | 'edit'>('create');
const currentApp = ref<ApplicationInfo | null>(null);

// 分页查询参数
const queryFormData = reactive<ApplicationPageQuery>({
  page_no: 1,
  page_size: 12,
  name: undefined,
  status: undefined,
  creator: undefined,
});

// 应用列表数据
const applicationList = ref<ApplicationInfo[]>([]);

// 表单数据
const formData = reactive<ApplicationForm>({
  name: '',
  access_url: '',
  icon_url: '',
  status: true,
  description: '',
});

// 表单验证规则
const formRules = reactive({
  name: [{ required: true, message: "请输入应用名称", trigger: "blur" }],
  access_url: [
    { required: true, message: "请输入访问地址", trigger: "blur" },
    { type: 'url' as const, message: "请输入正确的URL格式", trigger: "blur" }
  ],
  icon_url: [
    { required: true, message: "请输入图标地址", trigger: "blur" },
    { type: 'url' as const, message: "请输入正确的URL格式", trigger: "blur" }
  ],
  status: [{ required: true, message: "请选择应用状态", trigger: "change" }],
});

// 计算属性
const drawerSize = computed(() => (appStore.device === DeviceEnum.DESKTOP ? "500px" : "90%"));
const dialogTitle = computed(() => dialogType.value === 'create' ? '创建应用' : '编辑应用');

// 格式化时间
const formatTime = (time: string | undefined) => {
  if (!time) return '未知';
  return formatToDateTime(time, 'YYYY-MM-DD HH:mm:ss');
};

// 加载应用列表
async function loadApplicationList() {
  loading.value = true;
  try {
    const response = await ApplicationAPI.getApplicationList(queryFormData);
    applicationList.value = response.data.data.items;
    total.value = response.data.data.total;
  } catch (error) {
    console.error('加载应用列表失败:', error);
  } finally {
    loading.value = false;
  }
}

// 查询
async function handleQuery() {
  queryFormData.page_no = 1;
  await loadApplicationList();
}

// 重置查询
async function handleResetQuery() {
  queryFormRef.value?.resetFields();
  queryFormData.page_no = 1;
  await loadApplicationList();
}

// 分页大小改变
async function handleSizeChange(size: number) {
  queryFormData.page_size = size;
  queryFormData.page_no = 1;
  await loadApplicationList();
}

// 当前页改变
async function handleCurrentChange(page: number) {
  queryFormData.page_no = page;
  await loadApplicationList();
}

// 创建应用
function handleCreateApp() {
  dialogType.value = 'create';
  resetForm();
  dialogVisible.value = true;
}

// 编辑应用
function handleEditApp(app: ApplicationInfo) {
  dialogType.value = 'edit';
  currentApp.value = app;
  Object.assign(formData, app);
  dialogVisible.value = true;
}

// 删除应用
async function handleDeleteApp(app: ApplicationInfo) {
  try {
    await ElMessageBox.confirm('确认删除该应用？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    
    await ApplicationAPI.deleteApplication([app.id!]);
    await loadApplicationList();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除应用失败:', error);
    }
  }
}

// 应用操作
async function handleAppAction(command: string, app: ApplicationInfo) {
  switch (command) {
    case 'edit':
      handleEditApp(app);
      break;
    case 'delete':
      await handleDeleteApp(app);
      break;
  }
}

// 外部打开应用
function openAppExternal(url: string | undefined) {
  if (url) {
    window.open(url, '_blank');
  }
}

// 内部打开应用
function openAppInternal(app: ApplicationInfo) {
  if (!app.status) {
    ElMessage.warning('应用已停用，无法打开');
    return;
  }
  
  if (!app.access_url) {
    ElMessage.warning('应用访问地址不存在');
    return;
  }
  
  // 创建一个动态路由路径
  const appPath = `/internal-app/${app.id}`;
  const appName = `InternalApp${app.id}`;
  const appTitle = app.name || '未命名应用';
  
  // 先导航到路由，这样可以动态设置路由的meta信息
  router.push({
    path: appPath,
    query: { url: app.access_url, appId: app.id?.toString() || '', appName: appTitle }
  }).then(() => {
    // 导航完成后，手动添加或更新标签视图
    nextTick(() => {
      // 查找是否已存在该标签
      const existingTag = tagsViewStore.visitedViews.find(tag => tag.path === appPath);
      
      if (existingTag) {
        // 如果存在，更新标题
        tagsViewStore.updateVisitedView({
          ...existingTag,
          title: appTitle,
        });
      } else {
        // 如果不存在，添加新标签
        tagsViewStore.addView({
          name: appName,
          title: appTitle,
          path: appPath,
          fullPath: appPath + `?url=${encodeURIComponent(app.access_url || '')}&appId=${app.id || ''}&appName=${encodeURIComponent(appTitle)}`,
          icon: 'Monitor',
          affix: false,
          keepAlive: false,
          query: { url: app.access_url, appId: app.id?.toString() || '', appName: appTitle },
        });
      }
    });
  });
}

// 重置表单
function resetForm() {
  Object.assign(formData, {
    name: '',
    access_url: '',
    icon_url: '',
    status: true,
    description: '',
  });
  formRef.value?.resetFields();
}

// 关闭弹窗
function handleCloseDialog() {
  dialogVisible.value = false;
  resetForm();
}

// 提交表单
async function handleSubmit() {
  try {
    await formRef.value?.validate();
    
    if (dialogType.value === 'create') {
      await ApplicationAPI.createApplication(formData);
    } else {
      await ApplicationAPI.updateApplication(currentApp.value!.id!, formData);
    }
    
    dialogVisible.value = false;
    resetForm();
    await loadApplicationList();
  } catch (error) {
    console.error('提交失败:', error);
  }
}

// 初始化
onMounted(() => {
  loadApplicationList();
});
</script>

<style lang="scss" scoped>
.app-container {
  padding: 20px;
  background-color: var(--el-bg-color-page);
  min-height: calc(100vh - 84px);
}

.search-container {
  background: var(--el-bg-color);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.app-grid-card {
  height: calc(100vh - 200px);
  position: relative;
  display: flex;
  flex-direction: column;
  
  :deep(.el-card__footer) {
    margin-top: auto;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.app-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
  padding: 20px 0;
  flex: 1;
  overflow-y: auto;
}

.app-card {
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  padding: 10px;
  background: var(--el-bg-color);
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  
  &:hover {
    border-color: var(--el-color-primary);
    box-shadow: var(--el-box-shadow-light);
  }
}

.app-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.app-avatar {
  flex-shrink: 0;
}

.app-info {
  flex: 1;
  min-width: 0;
}

.app-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 3px 0;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-card-body {
  flex: 1;
  margin-bottom: 8px;
}

.app-desc {
  font-size: 11px;
  color: var(--el-text-color-regular);
  margin: 0 0 4px 0;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.app-meta {
  display: flex;
  align-items: center;
  font-size: 10px;
  color: var(--el-text-color-secondary);
  gap: 12px;
}

.app-card-footer {
  display: flex;
  gap: 4px;
  
  .el-button {
    font-size: 11px;
    padding: 3px 6px;
    flex: 1;
    width: 40%;
  }
}


.pagination-container {
  display: flex;
  justify-content: flex-end;
}

// 空状态样式
.empty-state {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

</style>
