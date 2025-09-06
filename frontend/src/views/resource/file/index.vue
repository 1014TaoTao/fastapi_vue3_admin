<template>
  <div class="resource-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>资源管理</h2>
        <el-breadcrumb separator="/">
          <el-breadcrumb-item
            v-for="(item, index) in breadcrumbList"
            :key="index"
            @click="handleBreadcrumbClick(item, index)"
            :class="{ 'is-link': index < breadcrumbList.length - 1 }"
          >
            {{ item.name }}
          </el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleUpload">
          <el-icon><Upload /></el-icon>
          上传文件
        </el-button>
        <el-button @click="handleCreateDir">
          <el-icon><FolderAdd /></el-icon>
          新建文件夹
        </el-button>
        <el-button @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <el-form :model="searchForm" inline>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="请输入文件名或关键词"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="文件类型">
          <el-select v-model="searchForm.file_type" placeholder="请选择" clearable>
            <el-option label="图片" value="image" />
            <el-option label="文档" value="document" />
            <el-option label="视频" value="video" />
            <el-option label="音频" value="audio" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="文件大小">
          <el-input-number
            v-model="searchForm.min_size"
            placeholder="最小"
            :min="0"
            controls-position="right"
          />
          <span style="margin: 0 8px">-</span>
          <el-input-number
            v-model="searchForm.max_size"
            placeholder="最大"
            :min="0"
            controls-position="right"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleResetSearch">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-checkbox
          v-model="showHiddenFiles"
          @change="handleShowHiddenChange"
        >
          显示隐藏文件
        </el-checkbox>
        <el-checkbox
          v-model="recursiveMode"
          @change="handleRecursiveChange"
        >
          递归显示
        </el-checkbox>
      </div>
      <div class="toolbar-right">
        <el-button-group>
          <el-button
            :type="viewMode === 'list' ? 'primary' : ''"
            @click="viewMode = 'list'"
          >
            <el-icon><List /></el-icon>
          </el-button>
          <el-button
            :type="viewMode === 'grid' ? 'primary' : ''"
            @click="viewMode = 'grid'"
          >
            <el-icon><Grid /></el-icon>
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 文件列表 -->
    <div class="file-list">
      <el-table
        v-if="viewMode === 'list'"
        :data="fileList"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        @row-dblclick="handleRowDoubleClick"
        row-key="path"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column label="名称" min-width="200">
          <template #default="{ row }">
            <div class="file-name">
              <el-icon class="file-icon">
                <Folder v-if="row.is_directory" />
                <Document v-else />
              </el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="120">
          <template #default="{ row }">
            <span v-if="!row.is_directory">{{ formatFileSize(row.size) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.file_type" size="small">{{ row.file_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="修改时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.modified_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_directory"
              type="primary"
              link
              @click="handleDownload(row)"
            >
              下载
            </el-button>
            <el-button type="primary" link @click="handleRename(row)">
              重命名
            </el-button>
            <el-button type="primary" link @click="handleMove(row)">
              移动
            </el-button>
            <el-button type="primary" link @click="handleCopy(row)">
              复制
            </el-button>
            <el-button type="danger" link @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 网格视图 -->
      <div v-else class="grid-view">
        <div
          v-for="item in fileList"
          :key="item.path"
          class="grid-item"
          @dblclick="handleItemDoubleClick(item)"
        >
          <div class="item-icon">
            <el-icon v-if="item.is_directory" size="48">
              <Folder />
            </el-icon>
            <el-icon v-else size="48">
              <Document />
            </el-icon>
          </div>
          <div class="item-name">{{ item.name }}</div>
          <div class="item-size" v-if="!item.is_directory">
            {{ formatFileSize(item.size) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="pagination.page_no"
        v-model:page-size="pagination.page_size"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传文件"
      width="500px"
      :before-close="handleUploadClose"
    >
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :multiple="true"
        :file-list="uploadFileList"
        @change="handleUploadChange"
        drag
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持多文件上传，单个文件不超过100MB
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUploadConfirm" :loading="uploading">
          确定上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 新建文件夹对话框 -->
    <el-dialog
      v-model="createDirDialogVisible"
      title="新建文件夹"
      width="400px"
    >
      <el-form :model="createDirForm" label-width="80px">
        <el-form-item label="文件夹名" required>
          <el-input
            v-model="createDirForm.dir_name"
            placeholder="请输入文件夹名称"
            @keyup.enter="handleCreateDirConfirm"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDirDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateDirConfirm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 重命名对话框 -->
    <el-dialog
      v-model="renameDialogVisible"
      title="重命名"
      width="400px"
    >
      <el-form :model="renameForm" label-width="80px">
        <el-form-item label="新名称" required>
          <el-input
            v-model="renameForm.new_name"
            placeholder="请输入新名称"
            @keyup.enter="handleRenameConfirm"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="renameDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleRenameConfirm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload,
  FolderAdd,
  Refresh,
  Search,
  RefreshLeft,
  List,
  Grid,
  Folder,
  Document,
  UploadFilled
} from '@element-plus/icons-vue'
import { ResourceAPI, type ResourceItem, type ResourceListQuery, type ResourceSearchQuery } from '@/api/resource/resource'

// 响应式数据
const loading = ref(false)
const fileList = ref<ResourceItem[]>([])
const selectedItems = ref<ResourceItem[]>([])
const currentPath = ref('/')
const breadcrumbList = ref([{ name: '根目录', path: '/' }])
const showHiddenFiles = ref(false)
const recursiveMode = ref(false)
const viewMode = ref<'list' | 'grid'>('list')
const total = ref(0)

// 分页
const pagination = reactive({
  page_no: 1,
  page_size: 20
})

// 搜索表单
const searchForm = reactive<ResourceSearchQuery>({
  keyword: '',
  file_type: '',
  min_size: undefined,
  max_size: undefined
})

// 对话框状态
const uploadDialogVisible = ref(false)
const createDirDialogVisible = ref(false)
const renameDialogVisible = ref(false)
const uploading = ref(false)

// 上传相关
const uploadRef = ref()
const uploadFileList = ref<any[]>([])

// 表单数据
const createDirForm = reactive({
  dir_name: ''
})

const renameForm = reactive({
  new_name: '',
  old_path: ''
})

// 计算属性
const currentQuery = computed(() => ({
  path: currentPath.value,
  recursive: recursiveMode.value,
  include_hidden: showHiddenFiles.value
}))

// 方法
const loadFileList = async () => {
  try {
    loading.value = true
    const response = await ResourceAPI.getResourceList(currentQuery.value)
    fileList.value = response.data.data || []
    total.value = fileList.value.length
  } catch (error) {
    ElMessage.error('加载文件列表失败')
    console.error('Load file list error:', error)
  } finally {
    loading.value = false
  }
}

const handleBreadcrumbClick = (item: any, index: number) => {
  if (index < breadcrumbList.value.length - 1) {
    currentPath.value = item.path
    updateBreadcrumb()
    loadFileList()
  }
}

const updateBreadcrumb = () => {
  const pathParts = currentPath.value.split('/').filter(Boolean)
  breadcrumbList.value = [
    { name: '根目录', path: '/' },
    ...pathParts.map((part, index) => ({
      name: part,
      path: '/' + pathParts.slice(0, index + 1).join('/')
    }))
  ]
}

const handleRowDoubleClick = (row: ResourceItem) => {
  if (row.is_directory) {
    currentPath.value = row.path
    updateBreadcrumb()
    loadFileList()
  }
}

const handleItemDoubleClick = (item: ResourceItem) => {
  if (item.is_directory) {
    currentPath.value = item.path
    updateBreadcrumb()
    loadFileList()
  }
}

const handleSelectionChange = (selection: ResourceItem[]) => {
  selectedItems.value = selection
}

const handleUpload = () => {
  uploadDialogVisible.value = true
  uploadFileList.value = []
}

const handleUploadChange = (file: any, fileList: any[]) => {
  uploadFileList.value = fileList
}

const handleUploadConfirm = async () => {
  if (uploadFileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  try {
    uploading.value = true
    const formData = new FormData()
    uploadFileList.value.forEach((file: any) => {
      formData.append('file', file.raw)
    })
    formData.append('target_path', currentPath.value)

    await ResourceAPI.uploadFile(formData)
    ElMessage.success('上传成功')
    uploadDialogVisible.value = false
    loadFileList()
  } catch (error) {
    ElMessage.error('上传失败')
    console.error('Upload error:', error)
  } finally {
    uploading.value = false
  }
}

const handleUploadClose = () => {
  uploadDialogVisible.value = false
  uploadFileList.value = []
}

const handleCreateDir = () => {
  createDirForm.dir_name = ''
  createDirDialogVisible.value = true
}

const handleCreateDirConfirm = async () => {
  if (!createDirForm.dir_name.trim()) {
    ElMessage.warning('请输入文件夹名称')
    return
  }

  try {
    await ResourceAPI.createDirectory({
      parent_path: currentPath.value,
      dir_name: createDirForm.dir_name.trim()
    })
    ElMessage.success('创建成功')
    createDirDialogVisible.value = false
    loadFileList()
  } catch (error) {
    ElMessage.error('创建失败')
    console.error('Create directory error:', error)
  }
}

const handleRefresh = () => {
  loadFileList()
}

const handleSearch = async () => {
  try {
    loading.value = true
    const response = await ResourceAPI.searchResource(searchForm)
    fileList.value = response.data.data || []
    total.value = fileList.value.length
  } catch (error) {
    ElMessage.error('搜索失败')
    console.error('Search error:', error)
  } finally {
    loading.value = false
  }
}

const handleResetSearch = () => {
  Object.assign(searchForm, {
    keyword: '',
    file_type: '',
    min_size: undefined,
    max_size: undefined
  })
  loadFileList()
}

const handleShowHiddenChange = () => {
  loadFileList()
}

const handleRecursiveChange = () => {
  loadFileList()
}

const handleDownload = async (item: ResourceItem) => {
  try {
    const response = await ResourceAPI.downloadFile(item.path)
    const blob = response.data
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = item.name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error('下载失败')
    console.error('Download error:', error)
  }
}

const handleRename = (item: ResourceItem) => {
  renameForm.old_path = item.path
  renameForm.new_name = item.name
  renameDialogVisible.value = true
}

const handleRenameConfirm = async () => {
  if (!renameForm.new_name.trim()) {
    ElMessage.warning('请输入新名称')
    return
  }

  try {
    await ResourceAPI.renameResource({
      old_path: renameForm.old_path,
      new_name: renameForm.new_name.trim()
    })
    ElMessage.success('重命名成功')
    renameDialogVisible.value = false
    loadFileList()
  } catch (error) {
    ElMessage.error('重命名失败')
    console.error('Rename error:', error)
  }
}

const handleMove = (item: ResourceItem) => {
  // TODO: 实现移动功能
  ElMessage.info('移动功能待实现')
}

const handleCopy = (item: ResourceItem) => {
  // TODO: 实现复制功能
  ElMessage.info('复制功能待实现')
}

const handleDelete = async (item: ResourceItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${item.name} 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await ResourceAPI.deleteResource([item.path])
    ElMessage.success('删除成功')
    loadFileList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('Delete error:', error)
    }
  }
}

const handleSizeChange = (size: number) => {
  pagination.page_size = size
  loadFileList()
}

const handleCurrentChange = (page: number) => {
  pagination.page_no = page
  loadFileList()
}

// 工具函数
const formatFileSize = (size?: number) => {
  if (!size) return '-'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let unitIndex = 0
  let fileSize = size

  while (fileSize >= 1024 && unitIndex < units.length - 1) {
    fileSize /= 1024
    unitIndex++
  }

  return `${fileSize.toFixed(1)} ${units[unitIndex]}`
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

// 生命周期
onMounted(() => {
  loadFileList()
})
</script>

<style lang="scss" scoped>
.resource-management {
  padding: 20px;
  background: #f5f5f5;
  min-height: 100vh;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

    .header-left {
      h2 {
        margin: 0 0 10px 0;
        color: #303133;
      }
    }

    .header-right {
      display: flex;
      gap: 10px;
    }
  }

  .search-section {
    margin-bottom: 20px;
    padding: 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 15px 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

    .toolbar-left {
      display: flex;
      gap: 20px;
    }
  }

  .file-list {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    overflow: hidden;

    .file-name {
      display: flex;
      align-items: center;
      gap: 8px;

      .file-icon {
        color: #409eff;
      }
    }

    .grid-view {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
      gap: 20px;
      padding: 20px;

      .grid-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 15px;
        border: 1px solid #e4e7ed;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s;

        &:hover {
          border-color: #409eff;
          box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
        }

        .item-icon {
          margin-bottom: 10px;
          color: #409eff;
        }

        .item-name {
          font-size: 14px;
          text-align: center;
          word-break: break-all;
          margin-bottom: 5px;
        }

        .item-size {
          font-size: 12px;
          color: #909399;
        }
      }
    }
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: center;
  }
}

:deep(.el-breadcrumb__item) {
  &.is-link {
    cursor: pointer;
    color: #409eff;

    &:hover {
      color: #66b1ff;
    }
  }
}
</style>
