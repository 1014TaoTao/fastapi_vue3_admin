<template>
  <div>
    <!-- 表格搜索区域 -->
    <div class="table-search-wrapper">
      <a-card >
        <a-form :model="queryState" @finish="onFinish">
          <a-flex wrap="wrap" gap="middle">
            <a-form-item name="username" label="账号">
              <a-input v-model:value="queryState.username" placeholder="请输入账号" allowClear
                style="width: 200px;"></a-input>
            </a-form-item>
            <a-form-item name="name" label="用户名">
              <a-input v-model:value="queryState.name" placeholder="请输入用户名" allowClear style="width: 200px;"></a-input>
            </a-form-item>
            <a-form-item name="available" label="状态">
              <a-select v-model:value="queryState.available" placeholder="请选择状态" allowClear style="width: 200px;">
                <a-select-option value="true">启用</a-select-option>
                <a-select-option value="false">停用</a-select-option>
              </a-select>
            </a-form-item>
            <a-button type="primary" html-type="submit" :loading="tableLoading">查询</a-button>
            <a-button  @click="resetFields">重置</a-button>
          </a-flex>
        </a-form>
      </a-card>
    </div>

    <!-- 表格区域 -->
    <div class="table-wrapper">
      <a-card title="用户管理"  >
        <template #extra>
          <a-button type="primary" :icon="h(PlusOutlined)" @click="modalHandle('create')" style="margin-right: 10px;">
            新建
          </a-button>
          <a-button type="primary" :icon="h(UploadOutlined)" @click="handleImport" style="margin-right: 10px;">
            导入
          </a-button>
          <a-button type="primary" :icon="h(DownloadOutlined)" @click="handleExport" style="margin-right: 10px;">
            导出
          </a-button>
          <a-dropdown>
            <template #overlay>
              <a-menu @click="handleMoreClick">
                <a-menu-item key="1"><span style="margin-right: 10px;">
                    <CheckOutlined />
                  </span><span>批量启用</span></a-menu-item>
                <a-menu-item key="2"><span style="margin-right: 10px;">
                    <StopOutlined />
                  </span><span>批量停用</span></a-menu-item>
              </a-menu>
            </template>
            <a-button>更多
              <DownOutlined />
            </a-button>
          </a-dropdown>
        </template>

        <!-- 使用 a-row 和 a-col 划分左右布局 -->
        <a-row :gutter="16">
          <!-- 左侧部门树 -->
          <a-col :span="4">
            <a-tree ref="deptTree" v-if="deptTreeData.length" 
              :tree-data="deptTreeData" 
              :show-line="true"
              :defaultExpandAll="true" 
              :field-names="{ children: 'children', title: 'name', key: 'id' }"
              :selected-keys="selectedKeys" 
              @select="onSelectDept">
            </a-tree>
          </a-col>

          <!-- 右侧用户列表 -->
          <a-col :span="20">
            <a-table 
              :rowKey="record => record.id" 
              :columns="columns" 
              :data-source="dataSource"
              :row-selection="rowSelection" 
              :loading="tableLoading" 
              @change="handleTableChange"
              :pagination="pagination"
              :scroll="{ x: 500, y: 'calc(100vh - 490px)' }"
              :style="{ minHeight: 'calc(100vh - 430px)' }"
              >
              <template #bodyCell="{ column, record, index }">
                <template v-if="column.dataIndex === 'index'">
                  <span>{{ (pagination.current - 1) * pagination.pageSize + index + 1 }}</span>
                </template>
                <template v-if="column.dataIndex === 'avatar'">
                  <a-avatar :src="record.avatar" :shape="record.avatar ? 'square' : 'circle'"
                    :icon="record.avatar ? undefined : h(UserOutlined)">
                  </a-avatar>
                </template>
                <template v-if="column.dataIndex === 'dept'">
                  <span>{{ record.dept_name }}</span>
                </template>
                <template v-if="column.dataIndex === 'roles'">
                  <span>{{ record.roleNames }}</span>
                </template>
                <template v-if="column.dataIndex === 'positions'">
                  <span>{{ record.positionNames }}</span>
                </template>
                <template v-if="column.dataIndex === 'gender'">
                  <a-tag :color="dictStore.getDictLabel(DictDataStore['sys_user_sex'], record.gender).css_class">
                    {{ dictStore.getDictLabel(DictDataStore['sys_user_sex'], record.gender).dict_label }}
                  </a-tag>
                </template>
                <template v-if="column.dataIndex === 'available'">
                  <span>
                    <a-badge :status="record.available ? 'processing' : 'error'"
                      :text="record.available ? '启用' : '停用'" />
                  </span>
                </template>
                <template v-if="column.dataIndex === 'is_superuser'">
                  <span>
                    <a-badge :status="record.is_superuser ? 'processing' : 'error'"
                      :text="record.is_superuser ? '是' : '否'" />
                  </span>
                </template>
                <template v-if="column.dataIndex === 'operation'">
                  <a-space size="middle">
                    <a v-on:click="modalHandle('view', index)">查看</a>
                    <a v-on:click="modalHandle('update', index)">修改</a>
                    <a-popconfirm title="确定删除吗？" ok-text="确定" cancel-text="取消" @confirm="deleteRow(record)">
                      <a style="color: red;">删除</a>
                    </a-popconfirm>
                  </a-space>
                </template>
              </template>
            </a-table>
          </a-col>
        </a-row>
      </a-card>
    </div>

    <!-- 弹窗区域 -->
    <div class="modal-wrapper">
      <!-- 主模态框 -->
      <a-modal v-model:open="openModal" @ok="handleModalSumbit" :width="800" :destroyOnClose="true"
        :confirmLoading="modalSubmitLoading">
        <template #title>
          <span>{{ modalTitle === 'create' ? '新建用户' : (modalTitle === 'view' ? '查看用户' : '修改用户') }}</span>
        </template>
        <div v-if="modalTitle === 'view'">
          <a-spin :spinning="detailStateLoading">
            <a-descriptions :column="{ xxl: 2, xl: 2, lg: 2, md: 2, sm: 1, xs: 1 }" :labelStyle="{ width: '140px' }"
              bordered>
              <a-descriptions-item label="序号">{{ (pagination.current - 1) * pagination.pageSize + detailState.index + 1
                }}</a-descriptions-item>
              <a-descriptions-item label="头像">
                <a-avatar :src="detailState.avatar" :shape="detailState.avatar?'square' : 'circle'"
                  :icon="detailState.avatar? undefined : h(UserOutlined)" />
              </a-descriptions-item>
              <a-descriptions-item label="账号">{{ detailState.username }}</a-descriptions-item>
              <a-descriptions-item label="用户名">{{ detailState.name }}</a-descriptions-item>
              <a-descriptions-item label="性别">
                {{ dictStore.getDictLabel(DictDataStore['sys_user_sex'],detailState.gender).dict_label }}
              </a-descriptions-item>
              <a-descriptions-item label="部门" :span="2">{{ detailState.dept_name }}</a-descriptions-item>
              <a-descriptions-item label="角色" :span="2">{{ detailState.roleNames }}</a-descriptions-item>
              <a-descriptions-item label="岗位" :span="2">{{ detailState.positionNames }}</a-descriptions-item>
              <a-descriptions-item label="邮箱">{{ detailState.email }}</a-descriptions-item>
              <a-descriptions-item label="联系电话">{{ detailState.mobile }}</a-descriptions-item>
              <a-descriptions-item label="是否超管">
                <a-badge :status="detailState.is_superuser ? 'processing': 'error'"
                  :text="detailState.is_superuser ? '是' : '否'" />
              </a-descriptions-item>
              <a-descriptions-item label="状态">
                <a-badge :status="detailState.available ? 'processing': 'error'"
                  :text="detailState.available ? '启用' : '停用'" />
              </a-descriptions-item>
              <a-descriptions-item label="上次登录时间">{{ detailState.last_login }}</a-descriptions-item>
              <a-descriptions-item label="创建人">{{ detailState.creator ? detailState.creator.name : '-'
                }}</a-descriptions-item>
              <a-descriptions-item label="创建时间">{{ detailState.created_at }}</a-descriptions-item>
              <a-descriptions-item label="修改时间">{{ detailState.updated_at }}</a-descriptions-item>
              <a-descriptions-item label="备注" :span="2">{{ detailState.description }}</a-descriptions-item>
            </a-descriptions>
          </a-spin>
        </div>
        <div v-else-if="modalTitle === 'create'">
          <a-form ref="createForm" :model="createState" v-bind="{ labelCol: { span: 5 }, wrapperCol: { span: 15 } }">
            <a-row>
              <!-- 账号和用户名 -->
              <a-col :span="12">
                <a-form-item name="username" label="账号" :rules="[{ required: true, message: '请输入账号' }]">
                  <a-input v-model:value="createState.username" placeholder="请输入账号" allowClear></a-input>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="name" label="用户名" :rules="[{ required: true, message: '请输入用户名' }]">
                  <a-input v-model:value="createState.name" placeholder="请输入用户名" allowClear></a-input>
                </a-form-item>
              </a-col>
              <!-- 部门和角色 -->
              <a-col :span="12">
                <a-form-item name="dept_id" label="部门" :rules="[{ required: true, message: '请选择部门' }]">
                  <a-tree-select v-model:value="createState.dept_id"
                    :dropdown-style="{ maxHeight: '400px', overflow: 'auto' }" :tree-data="deptTreeData"
                    :field-names="{ children: 'children', label: 'name', value: 'id' }" placeholder="请选择部门"
                    tree-node-filter-prop="name" style="width: 100%" show-search allow-clear></a-tree-select>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="role_ids" label="角色">
                  <a-select v-model:value="createState.roleNames" :open="false" @click="selectModalHandle('role')"
                    placeholder="请选择角色">
                    <template #suffixIcon>
                      <SearchOutlined />
                    </template>
                  </a-select>
                </a-form-item>
              </a-col>
              <!-- 岗位和密码 -->
              <a-col :span="12">
                <a-form-item name="position_ids" label="岗位">
                  <a-select v-model:value="createState.positionNames" :open="false"
                    @click="selectModalHandle('position')" placeholder="请选择岗位">
                    <template #suffixIcon>
                      <SearchOutlined />
                    </template>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="password" label="密码" :rules="[{ required: true, message: '请输入密码' }]">
                  <a-input-password v-model:value="createState.password" placeholder="请输入密码"
                    allowClear></a-input-password>
                </a-form-item>
              </a-col>
              <!-- 性别和邮箱 -->
              <a-col :span="12">
                <a-form-item name="gender" label="性别" :rules="[{ required: true, message: '请选择性别' }]">
                  <a-select v-model:value="createState.gender" placeholder="请选择性别" allowClear>
                    <a-select-option v-for="item in DictDataStore['sys_user_sex']" :key="item.id"
                      :value="item.dict_value">
                      {{ item.dict_label }}
                    </a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="email" label="邮箱">
                  <a-input v-model:value="createState.email" placeholder="请输入邮箱" allowClear></a-input>
                </a-form-item>
              </a-col>
              <!-- 联系电话和是否超管 -->
              <a-col :span="12">
                <a-form-item name="mobile" label="联系电话">
                  <a-input v-model:value="createState.mobile" placeholder="请输入电话" allowClear></a-input>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="is_superuser" label="是否超管" :rules="[{ required: true, message: '请选择是否超管' }]">
                  <a-radio-group v-model:value="createState.is_superuser">
                    <a-radio :value="true">是</a-radio>
                    <a-radio :value="false">否</a-radio>
                  </a-radio-group>
                </a-form-item>
              </a-col>
              <!-- 状态和备注 -->
              <a-col :span="12">
                <a-form-item name="available" label="状态" :rules="[{ required: true, message: '请选择状态' }]">
                  <a-radio-group v-model:value="createState.available">
                    <a-radio :value="true">启用</a-radio>
                    <a-radio :value="false">停用</a-radio>
                  </a-radio-group>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="description" label="备注">
                  <a-textarea v-model:value="createState.description" placeholder="请输入备注" :rows="4" allowClear />
                </a-form-item>
              </a-col>
            </a-row>
          </a-form>
        </div>
        <div v-else>
          <a-form ref="updateForm" :model="updateState" v-bind="{ labelCol: { span: 5 }, wrapperCol: { span: 15 } }">
            <a-row>
              <!-- 账号和用户名 -->
              <a-col :span="12">
                <a-form-item name="username" label="账号" :rules="[{ required: true, message: '请输入账号' }]">
                  <a-input v-model:value="updateState.username" placeholder="请输入账号" allowClear></a-input>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="name" label="用户名" :rules="[{ required: true, message: '请输入用户名' }]">
                  <a-input v-model:value="updateState.name" placeholder="请输入用户名" allowClear></a-input>
                </a-form-item>
              </a-col>
              <!-- 部门和角色 -->
              <a-col :span="12">
                <a-form-item name="dept_id" label="部门" :rules="[{ required: true, message: '请选择部门' }]">
                  <a-tree-select v-model:value="updateState.dept_id"
                    :dropdown-style="{ maxHeight: '400px', overflow: 'auto' }" :tree-data="deptTreeData"
                    :field-names="{ children: 'children', label: 'name', value: 'id' }" placeholder="请选择部门"
                    tree-node-filter-prop="name" style="width: 100%" show-search allow-clear></a-tree-select>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="role_ids" label="角色">
                  <a-select v-model:value="updateState.roleNames" :open="false" @click="selectModalHandle('role')"
                    placeholder="请选择角色">
                    <template #suffixIcon>
                      <SearchOutlined />
                    </template>
                  </a-select>
                </a-form-item>
              </a-col>
              <!-- 岗位和修改密码 -->
              <a-col :span="12">
                <a-form-item name="position_ids" label="岗位">
                  <a-select v-model:value="updateState.positionNames" :open="false"
                    @click="selectModalHandle('position')" placeholder="请选择岗位">
                    <template #suffixIcon>
                      <SearchOutlined />
                    </template>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item v-if="!showPasswordInput" label="修改密码">
                  <a-checkbox v-model:checked="showPasswordInput"></a-checkbox>
                </a-form-item>
                <a-form-item v-else name="password" label="密码">
                  <a-input-password v-model:value="updateState.password" placeholder="请输入密码"
                    allowClear></a-input-password>
                </a-form-item>
              </a-col>
              <!-- 性别和邮箱 -->
              <a-col :span="12">
                <a-form-item name="gender" label="性别" :rules="[{ required: true, message: '请选择性别' }]">
                  <a-select v-model:value="updateState.gender" placeholder="请选择性别" allowClear>
                    <a-select-option v-for="item in DictDataStore['sys_user_sex']" :key="item.id"
                      :value="item.dict_value">
                      {{ item.dict_label }}
                    </a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="email" label="邮箱">
                  <a-input v-model:value="updateState.email" placeholder="请输入邮箱" allowClear></a-input>
                </a-form-item>
              </a-col>
              <!-- 联系电话和是否超管 -->
              <a-col :span="12">
                <a-form-item name="mobile" label="联系电话">
                  <a-input v-model:value="updateState.mobile" placeholder="请输入电话" allowClear></a-input>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="is_superuser" label="是否超管" :rules="[{ required: true, message: '请选择是否超管' }]">
                  <a-radio-group v-model:value="updateState.is_superuser">
                    <a-radio :value="true">是</a-radio>
                    <a-radio :value="false">否</a-radio>
                  </a-radio-group>
                </a-form-item>
              </a-col>
              <!-- 状态和备注 -->
              <a-col :span="12">
                <a-form-item name="available" label="状态" :rules="[{ required: true, message: '请选择状态' }]">
                  <a-radio-group v-model:value="updateState.available">
                    <a-radio :value="true">启用</a-radio>
                    <a-radio :value="false">停用</a-radio>
                  </a-radio-group>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="description" label="备注">
                  <a-textarea v-model:value="updateState.description" placeholder="请输入备注" :rows="4" allowClear />
                </a-form-item>
              </a-col>
            </a-row>
          </a-form>
        </div>
      </a-modal>

      <!-- 导入对话框 -->
      <a-modal v-model:open="upload.open" title="导入用户" :width="500" @ok="submitFileForm"
        :confirmLoading="upload.isUploading" :bodyStyle="{ padding: '24px' }">
        <div class="import-container">
          <a-alert message="请先下载模板，按照模板格式填写数据后再导入" type="info" show-icon style="margin-bottom: 16px" />
          <a-upload ref="uploadRef" :accept="'.xlsx, .xls'" :showUploadList="true" :beforeUpload="beforeUpload"
            :customRequest="customRequest" :maxCount="1" :fileList="upload.fileList" @remove="handleRemove">
            <a-button type="primary">
              <upload-outlined></upload-outlined>
              选择文件
            </a-button>
            <template #itemRender="{ file }">
              <a-space>
                <a-typography-text>
                  {{ file.name }}
                </a-typography-text>
                <a-progress v-if="file.status === 'uploading'" :percent="file.percent" size="small"
                  style="width: 100px" />
              </a-space>
            </template>
          </a-upload>
          <div class="import-options" style="margin-top: 16px">
            <a-checkbox v-model:checked="upload.updateSupport">是否更新已经存在的用户数据</a-checkbox>
          </div>
          <div class="template-download" style="margin-top: 16px">
            <a-button type="link" @click="handleDownloadTemplate">
              <download-outlined /> 下载导入模板
            </a-button>
          </div>
          <div class="import-tips" style="margin-top: 16px">
            <h4>注意事项：</h4>
            <ul>
              <li>仅支持 xls、xlsx 格式文件</li>
              <li>文件大小不能超过 5MB</li>
              <li>必填项：账号、用户名、性别</li>
              <li>选填项：邮箱、手机号、部门、角色、岗位等</li>
            </ul>
          </div>
        </div>
      </a-modal>
    </div>

    <!-- 选择器弹窗 -->
    <SelectorModal ref="selectorModal" @event="handleSelectorModalEvent" />
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, unref, onMounted, h } from 'vue';
import { Table, message, Modal } from 'ant-design-vue';
import type { TableColumnsType, MenuProps } from 'ant-design-vue';
import { UserOutlined, PlusOutlined, DownOutlined, UploadOutlined, DownloadOutlined, CheckOutlined, StopOutlined, SearchOutlined } from '@ant-design/icons-vue';
import { isEmpty, listToTree } from '@/utils/util';
import { getDeptList } from '@/api/system/dept'
import { getUserList, createUser, updateUser, deleteUser, batchAvailableUser, exportUser, downloadTemplate, importUser } from '@/api/system/user'
import SelectorModal from './SelectorModal.vue'
import type { searchDataType, tableDataType, deptTreeType, roleSelectorType, positionSelectorType } from './types'
import storage from 'store';
import { useDictStore } from "@/store/index";

const dictStore = useDictStore();

const DictDataStore = computed(() => {
    return dictStore.dictObj;
})

const getOptions = async () => {
    const dictOptions = await dictStore.getDict(['sys_user_sex'])
    return dictOptions
}
const deptTree = ref(null);
const tableLoading = ref(false);
const treeLoading = ref(false);
const openModal = ref(false);
const modalTitle = ref('');
const modalSubmitLoading = ref(false);
const detailStateLoading = ref(false);
const showPasswordInput = ref(false);
const createForm = ref();
const updateForm = ref();
const selectorModal = ref();
const dataSource = ref<tableDataType[]>([]);
const selectedRowKeys = ref<tableDataType['id'][]>([]);
const deptTreeData = ref<deptTreeType[]>([]);

const queryState = reactive<searchDataType>({
  username: null,
  name: null,
  available: null
});
const pagination = reactive({
  current: 1,
  pageSize: 10,
  defaultPageSize: 10,
  showSizeChanger: true,
  total: dataSource.value.length,
  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条 / 总共 ${total} 条`
})
const createState = reactive<tableDataType>({
  username: '',
  name: '',
  dept_id: undefined,
  dept_name: '',
  role_ids: undefined,
  roleNames: undefined,
  position_ids: undefined,
  positionNames: undefined,
  password: '',
  gender: undefined,
  email: '',
  mobile: '',
  is_superuser: false,
  available: true,
  description: ''
})
const updateState = reactive<tableDataType>({
  id: undefined,
  username: '',
  name: '',
  dept_id: undefined,
  dept_name: '',
  role_ids: [],
  roleNames: undefined,
  position_ids: [],
  positionNames: undefined,
  password: '',
  gender: undefined,
  email: '',
  mobile: '',
  is_superuser: false,
  available: true,
  description: '',
})
const detailState = ref<tableDataType>({});

const columns = reactive<TableColumnsType>([
  {
    title: '序号',
    dataIndex: 'index',
    align: 'center',
    ellipsis: true,
    width: 80
  },
  {
    title: '头像',
    dataIndex: 'avatar',
    align: 'center',
    width: 80,
  },
  {
    title: '账号',
    dataIndex: 'username',
    ellipsis: true,
    align: 'center',
    width: 100
  },
  {
    title: '用户名',
    dataIndex: 'name',
    ellipsis: true,
    align: 'center',
    width: 80
  },
  {
    title: '是否超管',
    dataIndex: 'is_superuser',
    align: 'center',
    ellipsis: true,
    width: 100
  },
  {
    title: '部门',
    dataIndex: 'dept',
    ellipsis: true,
    align: 'center',
    width: 100
  },
  {
    title: '角色',
    dataIndex: 'roles',
    ellipsis: true,
    align: 'center',
    width: 100
  },
  {
    title: '岗位',
    dataIndex: 'positions',
    ellipsis: true,
    align: 'center',
    width: 100
  },
  {
    title: '性别',
    dataIndex: 'gender',
    align: 'center',
    ellipsis: true,
    width: 100
  },
  {
    title: '状态',
    dataIndex: 'available',
    align: 'center',
    ellipsis: true,
    width: 100
  },
  {
    title: '操作',
    dataIndex: 'operation',
    fixed: 'right',
    ellipsis: true,
    align: 'center',
    width: 150
  }
]);
const rowSelection = computed(() => {
  return {
    selectedRowKeys: unref(selectedRowKeys),
    onChange: (selectingRowKeys: tableDataType['id'][]) => {
      selectedRowKeys.value = selectingRowKeys;
    },
    hideDefaultSelections: true,
    selections: [
      Table.SELECTION_ALL,
      Table.SELECTION_INVERT,
      Table.SELECTION_NONE
    ]
  }
});
const selectedKeys = ref<number[]>([]);

// 生命周期钩子
onMounted(async () => {
    await getOptions();
    loadingDeptTree();
    loadingData();
});
// 查询
const onFinish = () => {
  pagination.current = 1;
  loadingDeptTree();
  loadingData();
};

// 加载表格数据
const loadingData = async () => {
  try {
    tableLoading.value = true;

    let params = {};
    if (queryState.username) {
      params['username'] = queryState.username 
    }
    if (queryState.name) {
      params['name'] = queryState.name 
    }
    if (queryState.available !== null && queryState.available !== undefined) {
      params['available'] = queryState.available; 
    }
    if (queryState.dept_id) {
      params['dept_id'] = queryState.dept_id; 
      selectedKeys.value = [queryState.dept_id]; 
    } else {
      selectedKeys.value = []; // 清除选中状态 
    }
    
    params['page_no'] = pagination.current 
    params['page_size'] = pagination.pageSize 

    const response = await getUserList(params);

    // 检查响应数据结构
    if (!response || !response.data || !response.data.data) {
      message.error('响应数据结构异常，请联系管理员');
      return;
    }

    const result = response.data;
    dataSource.value = result.data.items.map((item: tableDataType) => { 
      item.roleNames = item.roles ? item.roles.map(role => role.name).join(",") : null; 
      item.positionNames = item.positions ? item.positions.map(position => position.name).join(",") : null; 
      return item; 
    }); 

    pagination.total = result.data.total;
    pagination.current = result.data.page_no;
    pagination.pageSize = result.data.page_size;
  } catch (error) {
    console.error(error);
    message.error('数据加载失败，请检查网络或联系管理员');
  } finally {
    tableLoading.value = false;
  }
}

const loadingDeptTree = async () => {
  try {
    treeLoading.value = true;
    const response = await getDeptList()
    deptTreeData.value = listToTree(response.data.data.items);
  } catch (error) {
    console.error(error);
  } finally {
    treeLoading.value = false;
  }
}
// 重置查询
const resetFields = () => {
  Object.keys(queryState).forEach((key: string) => {
    delete queryState[key];
  });
  pagination.current = 1;
  queryState.available = null;
  queryState.dept_id = null;

  selectedKeys.value = [];

  loadingData();
}

// 删除
const deleteRow = (row: tableDataType) => {
  deleteUser({ id: row.id }).then(() => {
    loadingData();
  }).catch(error => {
    console.log(error);
  })
}

// 批量启用/停用
const handleMoreClick: MenuProps['onClick'] = e => {
  if (!selectedRowKeys.value || !(selectedRowKeys.value.length > 0)) {
    message.warning('请先勾选数据');
    return;
  }

  Modal.confirm({
    title: '提示',
    content: e.key == 1 ? '是否确定启用选择项？' : '是否确定停用选择项？',
    onOk() {
      const body = { ids: selectedRowKeys.value, available: e.key == 1 ? true : false };
      batchAvailableUser(body).then(() => {
        selectedRowKeys.value = [];
        loadingData();
      }).catch(error => {
        console.log(error);
      })
    }
  });
}

// 表格分页
const handleTableChange = (values: any) => {
  pagination.current = values.current;
  pagination.pageSize = values.pageSize;
  loadingData();
}

// 弹窗关键字处理
const modalHandle = (modalType: string, index?: number) => {
  modalTitle.value = modalType;
  openModal.value = true;

  // 重新创建 createState 和 updateState 以重置为初始状态
  Object.assign(createState, {
    username: '',
    name: '',
    dept_id: undefined,
    dept_name: '',
    role_ids: undefined,
    roleNames: undefined,
    position_ids: undefined,
    positionNames: undefined,
    password: '',
    gender: undefined,
    email: '',
    mobile: '',
    is_superuser: false,
    available: true,
    description: ''
  });

  Object.assign(updateState, {
    id: undefined,
    username: '',
    name: '',
    dept_id: undefined,
    dept_name: '',
    role_ids: [],
    roleNames: undefined,
    position_ids: [],
    positionNames: undefined,
    password: '',
    gender: undefined,
    email: '',
    mobile: '',
    is_superuser: false,
    available: true,
    description: '',
  });

  if (modalType === 'view' && index !== undefined) {
    detailStateLoading.value = true;

    detailState.value = dataSource.value[index];
    detailState.value.index = index;

    detailStateLoading.value = false;

  } else if (modalType === 'update' && index !== undefined) {
    const selected = dataSource.value[index];

    Object.keys(updateState).forEach(key => {
      if (selected[key] !== undefined) {
        updateState[key] = selected[key];
      }
    })

    if (selected['roles']) {
      updateState.role_ids = selected.roles.map(role => role.id);
    }
    if (selected['positions']) {
      updateState.position_ids = selected.positions.map(position => position.id);
    }
  }
}

// 弹窗提交（详情/新建/修改）
const handleModalSumbit = () => {
  modalSubmitLoading.value = true;

  if (modalTitle.value === 'view') {
    modalSubmitLoading.value = false;
    openModal.value = false;

  } else if (modalTitle.value === 'create') {
    createForm.value.validate().then(() => {
      const createBody = {
        username: createState.username,
        name: createState.name,
        password: createState.password,
        dept_id: createState.dept_id,
        role_ids: createState.role_ids,
        position_ids: createState.position_ids,
        gender: createState.gender,
        email: createState.email,
        mobile: createState.mobile,
        available: createState.available,
        description: createState.description,
        is_superuser: createState.is_superuser
      }
      Object.keys(createBody).forEach(key => {
        if (isEmpty(createBody[key])) {
          delete createBody[key];
        }
      })

      createUser(createBody).then(() => {
        modalSubmitLoading.value = false;
        openModal.value = false;
        Object.keys(createState).forEach(key => delete createState[key]);
        loadingData();

      }).catch(error => {
        modalSubmitLoading.value = false;
        console.error(error);
      })

    }).catch(error => {
      modalSubmitLoading.value = false;
      console.error(error);
    })

  } else if (modalTitle.value === 'update') {
    updateForm.value.validate().then(() => {
      const updateBody = {
        id: updateState.id,
        username: updateState.username,
        name: updateState.name,
        dept_id: updateState.dept_id,
        role_ids: updateState.role_ids,
        position_ids: updateState.position_ids,
        gender: updateState.gender,
        email: updateState.email,
        mobile: updateState.mobile,
        available: updateState.available,
        description: updateState.description,
        is_superuser: updateState.is_superuser
      }
      if (showPasswordInput.value && updateState.password) {
        updateBody['password'] = updateState.password;
      }

      updateUser(updateBody).then(() => {
        modalSubmitLoading.value = false;
        openModal.value = false;
        loadingData();

      }).catch(error => {
        modalSubmitLoading.value = false;
        console.error(error)
      })

    }).catch(error => {
      modalSubmitLoading.value = false;
      console.error(error)
    })
  }
}

// 选择器弹窗
const selectModalHandle = (subject: string) => {
  selectorModal.value.subject = subject;
  selectorModal.value.openModal = true;

  const ids_key = subject === 'role' ? 'role_ids' : 'position_ids';
  const names_key = subject === 'role' ? 'roleNames' : 'positionNames';

  const selectedKeys = modalTitle.value === 'create' ? createState[ids_key] : updateState[ids_key];
  const selectedRowItemNames = modalTitle.value === 'create' ? (createState[names_key] ?? '') : (updateState[names_key] ?? '');

  selectorModal.value.selectedRowKeys = selectedKeys;
  selectorModal.value.selectedRowItemNames = selectedRowItemNames.split(', ');

  selectorModal.value.loadingData();
}

// 选择器弹窗事件
const handleSelectorModalEvent = (
  subject: string,
  selectedSelectorRowKeys: roleSelectorType['id'][] | positionSelectorType['id'][],
  selectedSelectorRowNames: roleSelectorType['name'][] | positionSelectorType['name'][]
) => {
  const ids_key = subject === 'role' ? 'role_ids' : 'position_ids';
  const names_key = subject === 'role' ? 'roleNames' : 'positionNames';

  if (modalTitle.value === 'create') {
    createState[ids_key] = selectedSelectorRowKeys;
    createState[names_key] = selectedSelectorRowNames.join(', ');
  } else {
    updateState[ids_key] = selectedSelectorRowKeys;
    updateState[names_key] = selectedSelectorRowNames.join(', ');
  }
}

// 部门选择器事件
const onSelectDept = (selectedKeys: number[], info: any) => {
  if (selectedKeys.length > 0) {
    queryState.dept_id = selectedKeys[0]; // 获取选中的部门 ID
  } else {
    queryState.dept_id = null; // 如果没有选中部门，则删除 dept_id 参数
  }
  loadingData(); // 重新加载用户列表
};

// 上传配置
const token = storage.get('Access-Token');

// 导入相关方法
const uploadRef = ref();

// 用户导入参数
const upload = reactive({
  open: false,
  headers: token ? { Authorization: 'Bearer ' + token } : {},
  isUploading: false,
  updateSupport: false,
  fileList: [],
});

// 打开导入对话框
const handleImport = () => {
  upload.open = true;
  upload.isUploading = false;
  upload.updateSupport = false;
  upload.fileList = [];
};

// 文件上传前校验
const beforeUpload = (file: File) => {
  const isExcel = file.type === 'application/vnd.ms-excel' || file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
  const isLt5M = file.size / 1024 / 1024 < 5;

  if (!isExcel) {
    message.error('只能上传 Excel 文件!');
    return false;
  }
  if (!isLt5M) {
    message.error('文件大小不能超过 5MB!');
    return false;
  }
  return true;
};

// 移除文件
const handleRemove = () => {
  upload.fileList = [];
};

// 自定义上传
const customRequest = ({ file, onSuccess, onError, onProgress }: any) => {
  upload.isUploading = true;
  const formData = new FormData();
  formData.append('file', file);
  formData.append('updateSupport', upload.updateSupport.toString());
  
  // 更新文件状态
  const fileItem = {
    uid: file.uid,
    name: file.name,
    status: 'uploading',
    percent: 0
  };
  upload.fileList = [fileItem];
  
  importUser(formData)
    .then((response) => {
      fileItem.status = 'success';
      fileItem.percent = 100;
      upload.isUploading = false;
      upload.open = false;
      onSuccess(response);
      loadingData(); // 刷新数据
    })
    .catch((error) => {
      fileItem.status = 'error';
      upload.isUploading = false;
      onError(error);
      console.error('导入失败:', error);
    });
};

// 提交上传
const submitFileForm = () => {
  if (upload.fileList.length === 0) {
    message.warning('请先选择要上传的文件');
    return;
  }
  uploadRef.value?.upload?.();
};

// 导出按钮操作
const handleExport = () => {
  Modal.confirm({
    title: '警告',
    content: '是否确认导出所有用户数据?',
    onOk() {
      const body = {
        ...queryState,
        page_no: 1,
        page_size: pagination.total
      };
      message.loading('正在导出数据，请稍候...', 0);

      return exportUser(body).then(response => {
        const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        // 从响应头获取文件名
        const contentDisposition = response.headers['content-disposition'];
        let fileName = '用户.xlsx';
        if (contentDisposition) {
          const fileNameMatch = contentDisposition.match(/filename=(.*?)(;|$)/);
          if (fileNameMatch) {
            fileName = decodeURIComponent(fileNameMatch[1]);
          }
        }
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        message.destroy();
        message.success('导出成功');
      }).catch((error) => {
        message.destroy();
        console.error('导出错误:', error);
        message.error('文件处理失败');
      });
    },
    onCancel() {
      message.info('已取消导出');
    }
  });
};

// 下载模板
const handleDownloadTemplate = () => {
  downloadTemplate().then(response => {
    const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    // 从响应头获取文件名
    const contentDisposition = response.headers['content-disposition'];
    let fileName = '用户.xlsx';
    if (contentDisposition) {
      const fileNameMatch = contentDisposition.match(/filename=(.*?)(;|$)/);
      if (fileNameMatch) {
        fileName = decodeURIComponent(fileNameMatch[1]);
      }
    }
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    message.destroy();
    message.success('下载成功');
  }).catch((error) => {
    message.destroy();
    console.error('下载错误:', error);
    message.error('下载失败');
  });
};

</script>

<style lang="scss" scoped>
.table-search-wrapper {
  margin-block-end: 16px;
}
</style>