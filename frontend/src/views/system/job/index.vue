<template>
    <div>
        <!-- 搜索表单 -->
        <div class="table-search-wrapper">
            <a-card >
                <a-form :model="queryState" @finish="onFinish">
                    <a-flex wrap="wrap" gap="middle">
                        <a-form-item name="name" label="名称">
                            <a-input v-model:value="queryState.name" placeholder="请输入任务名称" allowClear
                                style="width: 200px;"></a-input>
                        </a-form-item>
                        <a-form-item name="status" label="状态">
                            <a-select v-model:value="queryState.status" placeholder="请选择状态" allowClear
                                style="width: 200px;">
                                <a-select-option value="true">启用</a-select-option>
                                <a-select-option value="false">停用</a-select-option>
                            </a-select>
                        </a-form-item>
                        <a-form-item name="date-range-picker" label="创建日期" >
                            <a-range-picker v-model:value="queryState.date_range" value-format="YYYY-MM-DD" />
                        </a-form-item>
                        <a-button type="primary" html-type="submit" :loading="tableLoading">查询</a-button>
                        <a-button  @click="resetFields">重置</a-button>
                    </a-flex>
                </a-form>
            </a-card>
        </div>

        <!-- 表格区域 -->
        <div class="table-wrapper">
            <a-card title="定时任务列表"  
                >
                <template #extra>
                    <a-button type="primary" :icon="h(PlusOutlined)" @click="modalHandle('create')"
                        style="margin-right: 10px;">新建</a-button>
                    <a-button type="primary" :icon="h(DownOutlined)" @click="handleExport"
                        style="margin-right: 10px;">导出
                    </a-button>
                    <a-button type="primary" danger :icon="h(DeleteOutlined)" @click="handleClear"
                        style="margin-right: 10px;">清除
                    </a-button>
                </template>
                <a-table :rowKey="record => record.id" 
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
                        <template v-if="column.dataIndex === 'status'">
                            <span>
                                <a-badge :status="record.status ? 'processing' : 'error'"
                                    :text="record.status ? '启用' : '停用'" />
                            </span>
                        </template>
                        <template v-if="column.dataIndex === 'jobstore'">
                            <span>
                                {{ dictStore.getDictLabel(DictDataStore['sys_job_group'],record.jobstore).dict_label }}
                            </span>
                        </template>
                        <template v-if="column.dataIndex === 'executor'">
                            <span>
                                {{ dictStore.getDictLabel(DictDataStore['sys_job_executor'],record.executor).dict_label
                                }}
                            </span>
                        </template>
                        <template v-if="column.dataIndex === 'func'">
                            <span>
                                {{ dictStore.getDictLabel(DictDataStore['sys_job_function'],record.func).dict_label }}
                            </span>
                        </template>
                        <template v-if="column.dataIndex === 'trigger'">
                            <span>
                                {{ dictStore.getDictLabel(DictDataStore['sys_job_trigger'],record.trigger).dict_label }}
                            </span>
                        </template>
                        <template v-if="column.dataIndex === 'coalesce'">
                            <span>
                                <a-badge :status="record.coalesce ? 'processing' : 'error'"
                                    :text="record.coalesce ? '是' : '否'" />
                            </span>
                        </template>
                        <template v-if="column.dataIndex === 'operation'">
                            <a-space size="middle">
                                <a @click="modalHandle('view', index)">查看</a>
                                <a @click="modalHandle('update', index)">修改</a>
                                <a-popconfirm title="确定删除吗？" ok-text="确定" cancel-text="取消" @confirm="deleteRow(record)">
                                    <a style="color: red;">删除</a>
                                </a-popconfirm>
                                <a-dropdown>
                                    <a>更多
                                        <DownOutlined />
                                    </a>
                                    <template #overlay>
                                        <a-menu>
                                            <a-menu-item @click="handleOption(record, 1)">暂停</a-menu-item>
                                            <a-menu-item @click="handleOption(record, 2)">恢复</a-menu-item>
                                            <!-- <a-menu-item @click="handleOption(record, 3)">重启</a-menu-item> -->
                                        </a-menu>
                                    </template>
                                </a-dropdown>
                            </a-space>
                        </template>
                    </template>
                </a-table>
            </a-card>
        </div>

        <!-- 弹窗区域 -->
        <div class="modal-wrapper">
            <a-modal v-model:open="openModal" @ok="handleModalSumbit" :width="800" :destroyOnClose="true"
                :confirmLoading="modalSubmitLoading" style="top: 30px">
                <template #title>
                    <span>
                        {{ modalTitle === 'create' ? '新建定时任务' : (modalTitle === 'view' ? '查看定时任务' : '修改定时任务') }}
                    </span>
                </template>
                <div v-if="modalTitle === 'view'">
                    <a-spin :spinning="detailStateLoading">
                        <a-descriptions :column="{ xxl: 2, xl: 2, lg: 2, md: 2, sm: 1, xs: 1 }"
                            :labelStyle="{ width: '140px' }" bordered>
                            <a-descriptions-item label="序号">{{ (pagination.current - 1) * pagination.pageSize +
                                detailState.index + 1 }}</a-descriptions-item>
                            <a-descriptions-item label="任务名称">{{ detailState.name }}</a-descriptions-item>
                            <a-descriptions-item label="任务函数">
                                {{ dictStore.getDictLabel(DictDataStore['sys_job_function'],detailState.func).dict_label
                                }}
                            </a-descriptions-item>
                            <a-descriptions-item label="触发器">
                                {{
                                dictStore.getDictLabel(DictDataStore['sys_job_trigger'],detailState.trigger).dict_label
                                }}
                            </a-descriptions-item>
                            <a-descriptions-item label="位置参数">{{ detailState.args }}</a-descriptions-item>
                            <a-descriptions-item label="关键字参数">{{ detailState.kwargs }}</a-descriptions-item>
                            <a-descriptions-item label="是否并行">
                                <a-badge :status="detailState.coalesce ? 'processing' : 'error'"
                                    :text="detailState.coalesce ? '是' : '否'" />
                            </a-descriptions-item>
                            <a-descriptions-item label="最大实例数">{{ detailState.max_instances }}</a-descriptions-item>
                            <a-descriptions-item label="任务存储">
                                {{
                                dictStore.getDictLabel(DictDataStore['sys_job_group'],detailState.jobstore).dict_label
                                }}
                            </a-descriptions-item>
                            <a-descriptions-item label="任务执行器">
                                {{
                                dictStore.getDictLabel(DictDataStore['sys_job_executor'],detailState.executor).dict_label
                                }}
                            </a-descriptions-item>
                            <a-descriptions-item label="触发器参数">{{ detailState.trigger_args }}</a-descriptions-item>
                            <a-descriptions-item label="开始时间">{{ detailState.start_date }}</a-descriptions-item>
                            <a-descriptions-item label="结束时间">{{ detailState.end_date }}</a-descriptions-item>
                            <a-descriptions-item label="任务状态">
                                <a-badge :status="detailState.status ? 'processing' : 'error'"
                                    :text="detailState.status ? '启用' : '停用'" />
                            </a-descriptions-item>
                            <a-descriptions-item label="日志信息">{{ detailState.message }}</a-descriptions-item>
                            <a-descriptions-item label="创建人">{{ detailState.creator ? detailState.creator.name :
                                '-' }}</a-descriptions-item>
                            <a-descriptions-item label="创建时间">{{ detailState.created_at }}</a-descriptions-item>
                            <a-descriptions-item label="修改时间">{{ detailState.updated_at }}</a-descriptions-item>
                            <a-descriptions-item label="备注" :span="2">{{ detailState.description
                                }}</a-descriptions-item>
                        </a-descriptions>
                    </a-spin>
                </div>
                <div v-else-if="modalTitle === 'create'">
                    <a-form ref="createForm" :model="createState" v-bind="{ labelCol: { span: 8 }, wrapperCol: { span: 12 } }">
                        <a-row>
                            <!-- 任务名称和任务存储器 -->
                            <a-col :span="12">
                                <a-form-item name="name" label="任务名称" :rules="[{ required: true, message: '请输入任务名称' }]">
                                    <a-input v-model:value="createState.name" placeholder="请输入任务名称"
                                        allowClear></a-input>
                                </a-form-item>
                            </a-col>
                            <a-col :span="12">
                                <a-form-item name="jobstore" label="任务存储器"
                                    :rules="[{ required: true, message: '请选择任务存储' }]">
                                    <a-select v-model:value="createState.jobstore" placeholder="请选择任务存储" allowClear>
                                        <a-select-option v-for="item in DictDataStore['sys_job_group']" :key="item.id"
                                            :value="item.dict_value">
                                            {{ item.dict_label }}
                                        </a-select-option>
                                    </a-select>
                                </a-form-item>
                            </a-col>
                            <!-- 任务执行器和任务函数 -->
                            <a-col :span="12">
                                <a-form-item name="executor" label="任务执行器"
                                    :rules="[{ required: true, message: '请选择任务执行器' }]">
                                    <a-select v-model:value="createState.executor" placeholder="请选择任务执行器" allowClear>
                                        <a-select-option v-for="item in DictDataStore['sys_job_executor']"
                                            :key="item.id" :value="item.dict_value">
                                            {{ item.dict_label }}
                                        </a-select-option>
                                    </a-select>
                                </a-form-item>
                            </a-col>
                            <a-col :span="12">
                                <a-form-item name="func" label="任务函数"
                                    :rules="[{ required: true, message: '请输入任务函数 module.function' }]">
                                    <a-select v-model:value="createState.func" placeholder="请选择任务函数 module.function"
                                        allowClear>
                                        <a-select-option v-for="item in DictDataStore['sys_job_function']"
                                            :key="item.id" :value="item.dict_value">
                                            {{ item.dict_label }}
                                        </a-select-option>
                                    </a-select>
                                </a-form-item>
                            </a-col>
                            <!-- 位置参数和关键字参数 -->
                            <a-col :span="12">
                                <a-form-item name="args" label="位置参数"
                                    :rules="[{ required: false, message: '请输入位置参数' }]">
                                    <a-input v-model:value="createState.args" placeholder="请输入位置参数"
                                        allowClear></a-input>
                                </a-form-item>
                            </a-col>
                            <a-col :span="12">
                                <a-form-item name="kwargs" label="关键字参数"
                                    :rules="[{ required: false, message: '请输入关键字参数' }]">
                                    <a-input v-model:value="createState.kwargs" placeholder="请输入关键字参数"
                                        allowClear></a-input>
                                </a-form-item>
                            </a-col>
                            <!-- 是否并行和最大实例数 -->
                            <a-col :span="12">
                                <a-form-item name="coalesce" label="是否并行"
                                    :rules="[{ required: true, message: '请选择是否并行' }]">
                                    <a-radio-group v-model:value="createState.coalesce">
                                        <a-radio :value="true">是</a-radio>
                                        <a-radio :value="false">否</a-radio>
                                    </a-radio-group>
                                </a-form-item>
                            </a-col>
                            <a-col :span="12">
                                <a-form-item name="max_instances" label="最大实例数"
                                    :rules="[{ required: true, message: '请输入最大实例数' }]">
                                    <a-input-number v-model:value="createState.max_instances" :min="1"
                                        placeholder="请输入最大实例数" style="width: 100%" />
                                </a-form-item>
                            </a-col>
                            <!-- 任务触发器 -->
                            <a-col :span="12">
                                <a-form-item name="trigger" label="任务触发器"
                                    :rules="[{ required: true, message: '请选择触发器' }]">
                                    <a-select v-model:value="createState.trigger" placeholder="请选择触发器" allowClear>
                                        <a-select-option v-for="item in DictDataStore['sys_job_trigger']" :key="item.id"
                                            :value="item.dict_value">
                                            {{ item.dict_label }}
                                        </a-select-option>
                                    </a-select>
                                </a-form-item>
                            </a-col>
                            <!-- 运行日期、间隔时间或 Cron 表达式 -->
                            <a-col :span="12">
                                <a-form-item v-if="createState.trigger === 'date'" name="trigger_args" label="运行日期"
                                    :rules="[{ required: true, message: '请选择运行日期' }]">
                                    <a-date-picker v-model:value="createState.trigger_args" show-time
                                        format="YYYY-MM-DD HH:mm:ss" value-format="YYYY-MM-DD HH:mm:ss"
                                        placeholder="请选择运行日期" style="width: 100%" />
                                </a-form-item>
                                <a-form-item v-else-if="createState.trigger === 'interval'" name="trigger_args"
                                    label="间隔时间" :rules="[{ required: true, message: '请输入间隔时间' }]">
                                    <a-input v-model:value="createState.trigger_args"
                                        placeholder="请输入 秒-分-时-天-周 (* * * * 1)" allowClear
                                        @click="openIntervalTabHandle('create')" />
                                </a-form-item>
                                <a-form-item v-else-if="createState.trigger === 'cron'" name="trigger_args"
                                    label="Cron表达式" :rules="[{ required: true, message: '请输入Cron表达式' }]">
                                    <a-input v-model:value="createState.trigger_args"
                                        placeholder="请输入 Cron表达式(*/3 * * * *)" @click="handleShowCron" allowClear
                                        readonly>
                                    </a-input>
                                </a-form-item>
                            </a-col>
                            <!-- 开始日期和结束日期 -->
                            <a-col :span="12">
                                <a-form-item v-if="createState.trigger && createState.trigger != 'date'"
                                    name="start_date" label="开始日期" :rules="[{ required: false, message: '请选择开始日期' }]">
                                    <a-date-picker v-model:value="createState.start_date" show-time
                                        format="YYYY-MM-DD HH:mm:ss" value-format="YYYY-MM-DD HH:mm:ss"
                                        placeholder="请选择开始日期" style="width: 100%" />
                                </a-form-item>
                            </a-col>
                            <a-col :span="12">
                                <a-form-item v-if="createState.trigger && createState.trigger != 'date'" name="end_date"
                                    label="结束日期" :rules="[{ required: false, message: '请选择结束日期' }]">
                                    <a-date-picker v-model:value="createState.end_date" show-time
                                        format="YYYY-MM-DD HH:mm:ss" value-format="YYYY-MM-DD HH:mm:ss"
                                        placeholder="请选择结束日期" style="width: 100%" />
                                </a-form-item>
                            </a-col>
                            <!-- 备注 -->
                            <a-col :span="12">
                                <a-form-item name="description" label="备注">
                                    <a-textarea v-model:value="createState.description" placeholder="请输入备注" :rows="4"
                                        allowClear />
                                </a-form-item>
                            </a-col>
                        </a-row>
                    </a-form>
                </div>
                <div v-else>
                    <a-form ref="updateForm" :model="updateState" v-bind="{ labelCol: { span: 8 }, wrapperCol: { span: 12 } }">
                        <a-row>
                            <!-- 任务名称和任务存储器 -->
                            <a-col :span="12">
                                <a-form-item name="name" label="任务名称" :rules="[{ required: true, message: '请输入任务名称' }]">
                                    <a-input v-model:value="updateState.name" placeholder="请输入任务名称"
                                        allowClear></a-input>
                                </a-form-item>
                            </a-col>
                            <a-col :span="12">
                                <a-form-item name="jobstore" label="任务存储器"
                                    :rules="[{ required: true, message: '请选择任务存储' }]">
                                    <a-select v-model:value="updateState.jobstore" placeholder="请选择任务存储" allowClear>
                                        <a-select-option v-for="item in DictDataStore['sys_job_group']" :key="item.id"
                                            :value="item.dict_value">
                                            {{ item.dict_label }}
                                        </a-select-option>
                                    </a-select>
                                </a-form-item>
                            </a-col>
                            <!-- 任务执行器和任务函数 -->
                            <a-col :span="12">
                                <a-form-item name="executor" label="任务执行器"
                                    :rules="[{ required: true, message: '请选择任务执行器' }]">
                                    <a-select v-model:value="updateState.executor" placeholder="请选择任务执行器" allowClear>
                                        <a-select-option v-for="item in DictDataStore['sys_job_executor']"
                                            :key="item.id" :value="item.dict_value">
                                            {{ item.dict_label }}
                                        </a-select-option>
                                    </a-select>
                                </a-form-item>
                            </a-col>
                            <a-col :span="12">
                                <a-form-item name="func" label="任务函数" :rules="[{ required: true, message: '请输入任务函数' }]">
                                    <a-select v-model:value="updateState.func" placeholder="请选择任务函数 module.function"
                                        allowClear>
                                        <a-select-option v-for="item in DictDataStore['sys_job_function']"
                                            :key="item.id" :value="item.dict_value">
                                            {{ item.dict_label }}
                                        </a-select-option>
                                    </a-select>
                                </a-form-item>
                            </a-col>
                            <!-- 位置参数和关键字参数 -->
                            <a-col :span="12">
                                <a-form-item name="args" label="位置参数"
                                    :rules="[{ required: false, message: '请输入位置参数' }]">
                                    <a-input v-model:value="updateState.args" placeholder="请输入位置参数"
                                        allowClear></a-input>
                                </a-form-item>
                            </a-col>
                            <a-col :span="12">
                                <a-form-item name="kwargs" label="关键字参数"
                                    :rules="[{ required: false, message: '请输入关键字参数' }]">
                                    <a-input v-model:value="updateState.kwargs" placeholder="请输入关键字参数"
                                        allowClear></a-input>
                                </a-form-item>
                            </a-col>
                            <!-- 是否并行和最大实例数 -->
                            <a-col :span="12">
                                <a-form-item name="coalesce" label="是否并行"
                                    :rules="[{ required: true, message: '请选择是否并行' }]">
                                    <a-radio-group v-model:value="updateState.coalesce">
                                        <a-radio :value="true">是</a-radio>
                                        <a-radio :value="false">否</a-radio>
                                    </a-radio-group>
                                </a-form-item>
                            </a-col>
                            <a-col :span="12">
                                <a-form-item name="max_instances" label="最大实例数"
                                    :rules="[{ required: true, message: '请输入最大实例数' }]">
                                    <a-input-number v-model:value="updateState.max_instances" :min="1"
                                        placeholder="请输入最大实例数" style="width: 100%" />
                                </a-form-item>
                            </a-col>
                            <!-- 任务触发器 -->
                            <a-col :span="12">
                                <a-form-item name="trigger" label="任务触发器"
                                    :rules="[{ required: true, message: '请选择触发器' }]">
                                    <a-select v-model:value="updateState.trigger" placeholder="请选择触发器" allowClear>
                                        <a-select-option v-for="item in DictDataStore['sys_job_trigger']" :key="item.id"
                                            :value="item.dict_value">
                                            {{ item.dict_label }}
                                        </a-select-option>
                                    </a-select>
                                </a-form-item>
                            </a-col>
                            <!-- 运行日期、间隔时间或 Cron 表达式 -->
                            <a-col :span="12">
                                <a-form-item v-if="updateState.trigger === 'date'" name="trigger_args" label="运行日期"
                                    :rules="[{ required: true, message: '请选择运行日期' }]">
                                    <a-date-picker v-model:value="updateState.trigger_args" format="YYYY-MM-DD HH:mm:ss"
                                        placeholder="请选择运行日期"
                                        :show-time="{ defaultValue: dayjs('00:00:00', 'HH:mm:ss') }" style="width: 100%"
                                        :value-format="'YYYY-MM-DD HH:mm:ss'" />
                                </a-form-item>
                                <a-form-item v-else-if="updateState.trigger === 'interval'" name="trigger_args"
                                    label="间隔时间" :rules="[{ required: true, message: '请输入间隔时间' }]">
                                    <a-input v-model:value="updateState.trigger_args"
                                        placeholder="请输入 秒-分-时-天-周 (* * * * *)" allowClear
                                        @click="openIntervalTabHandle('update')" readonly />
                                </a-form-item>
                                <a-form-item v-else-if="updateState.trigger === 'cron'" name="trigger_args"
                                    label="Cron表达式" :rules="[{ required: true, message: '请输入Cron表达式' }]">
                                    <a-input v-model:value="updateState.trigger_args"
                                        placeholder="请输入 Cron表达式(*/3 * * * *)" @click="handleShowCron" allowClear
                                        readonly></a-input>
                                </a-form-item>
                            </a-col>
                            <!-- 开始日期和结束日期 -->
                            <a-col :span="12">
                                <a-form-item v-if="updateState.trigger && updateState.trigger != 'date'"
                                    name="start_date" label="开始日期" :rules="[{ required: false, message: '请选择开始日期' }]">
                                    <a-date-picker v-model:value="updateState.start_date" show-time
                                        format="YYYY-MM-DD HH:mm:ss" value-format="YYYY-MM-DD HH:mm:ss"
                                        placeholder="请选择开始日期" style="width: 100%" />
                                </a-form-item>
                            </a-col>
                            <a-col :span="12">
                                <a-form-item v-if="updateState.trigger && updateState.trigger != 'date'" name="end_date"
                                    label="结束日期" :rules="[{ required: false, message: '请选择结束日期' }]">
                                    <a-date-picker v-model:value="updateState.end_date" show-time
                                        format="YYYY-MM-DD HH:mm:ss" value-format="YYYY-MM-DD HH:mm:ss"
                                        placeholder="请选择结束日期" style="width: 100%" />
                                </a-form-item>
                            </a-col>
                            <!-- 备注 -->
                            <a-col :span="12">
                                <a-form-item name="description" label="备注">
                                    <a-textarea v-model:value="updateState.description" placeholder="请输入备注" :rows="4"
                                        allowClear />
                                </a-form-item>
                            </a-col>
                        </a-row>
                    </a-form>
                </div>
            </a-modal>
        </div>

        <a-modal v-model:open="openIntervalTab" title="间隔时间设置" @ok="handleIntervalConfirm" :width="600"
            :destroyOnClose="true">
            <IntervalTab ref="intervalTabRef" />
        </a-modal>

        <!-- core组件是由element-plus封装的vue3组件，所以需要使用element-plus -->
        <el-dialog v-model="openCron">
            <Vue3CronPlusPicker @hide="closeDialog" @fill="fillValue" :expression="expression" />
        </el-dialog>

    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, unref, onMounted, h } from 'vue';
import dayjs from 'dayjs';
import { Table, message, Modal } from 'ant-design-vue';
import type { TableColumnsType } from 'ant-design-vue';
import { PlusOutlined, DownOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import { cloneDeep, isEmpty } from '@/utils/util';
import IntervalTab from '@/components/IntervalTab/index.vue';
import { getJobList, createJob, updateJob, deleteJob, exportJob, clearJob, OptionJob } from '@/api/system/job'
import type { searchType, tableJobType } from './types'
import 'vue3-cron-plus-picker/style.css'
import { Vue3CronPlusPicker } from 'vue3-cron-plus-picker'
import { useDictStore } from "@/store/index";

const dictStore = useDictStore();

const DictDataStore = computed(() => {
    return dictStore.dictObj;
})

const createForm = ref();
const updateForm = ref();
const tableLoading = ref(false);
const openModal = ref(false);
const openCron = ref(false);
const cronMode = ref('create');
const modalTitle = ref('');
const modalSubmitLoading = ref(false);
const detailStateLoading = ref(false);
const dataSource = ref<tableJobType[]>([]);
const selectedRowKeys = ref<tableJobType['id'][]>([]);
const queryState = reactive<searchType>({});
const pagination = reactive({
    current: 1,
    pageSize: 10,
    defaultPageSize: 10,
    showSizeChanger: true,
    total: dataSource.value.length,
    showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条 / 总共 ${total} 条`
})
const createState = reactive<tableJobType>({
    name: '',
    func: null,
    trigger: null,
    args: '',
    kwargs: '',
    coalesce: false,
    max_instances: 1,
    jobstore: null,
    executor: null,
    trigger_args: null,
    start_date: null,
    end_date: null,
    status: null,
    message: '',
    description: ''
})
const updateState = reactive<tableJobType>({
    id: undefined,
    name: '',
    func: '',
    trigger: null,
    args: '',
    kwargs: '',
    coalesce: false,
    max_instances: 1,
    jobstore: null,
    executor: null,
    trigger_args: null,
    start_date: null,
    end_date: null,
    status: null,
    message: '',
    description: ''
})
const detailState = ref<tableJobType>({})
const columns: TableColumnsType = [
    {
        title: '序号',
        dataIndex: 'index',
        align: 'center',
        width: 80
    },
    {
        title: '任务名称',
        dataIndex: 'name',
        ellipsis: true
    },
    {
        title: '执行函数',
        dataIndex: 'func',
        ellipsis: true,
    },
    {
        title: '触发器',
        dataIndex: 'trigger',
        ellipsis: true,
        width: 100,
    },
    {
        title: '存储器',
        dataIndex: 'jobstore',
        ellipsis: true,
        // width: 100,
    },
    {
        title: '执行器',
        dataIndex: 'executor',
        ellipsis: true,
        width: 100,
    },
    {
        title: '并发执行',
        dataIndex: 'coalesce',
        align: 'center',
        width: 120,
    },
    {
        title: '状态',
        dataIndex: 'status',
        align: 'center',
        width: 100
    },
    {
        title: '创建时间',
        dataIndex: 'created_at',
        ellipsis: true,
        width: 180
    },
    {
        title: '操作',
        dataIndex: 'operation',
        align: 'center',
        fixed: 'right',
        width: 200
    }
];
// 表格选中配置
const rowSelection = computed(() => {
    return {
        selectedRowKeys: unref(selectedRowKeys),
        onChange: (selectingRowKeys: tableJobType['id'][]) => {
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
const openIntervalTab = ref(false);
const intervalTabRef = ref();
const expression = ref('');

const getOptions = async () => {
    const dictOptions = await dictStore.getDict(['sys_job_group', 'sys_job_executor', 'sys_job_function', 'sys_job_trigger'])
    return dictOptions
}

function openIntervalTabHandle(value: any) {
    openIntervalTab.value = true;
    modalTitle.value = value
}

function handleIntervalConfirm() {

    if (modalTitle.value === 'create') {
        createState.trigger_args = intervalTabRef.value.handleConfirm();
    } else {
        updateState.trigger_args = intervalTabRef.value.handleConfirm();
    }
    openIntervalTab.value = false;
}

const handleShowCron = () => {
    openCron.value = true;
    if (cronMode.value === 'create') {
        expression.value = createState.trigger_args;
    } else {
        expression.value = updateState.trigger_args; // 修正此处
    }
}

const closeDialog = () => {
    openCron.value = false;
}

const fillValue = (cronValue) => {
    if (cronMode.value === 'create') {
        createState.trigger_args = cronValue;
    } else {
        updateState.trigger_args = cronValue;
    }
}

// 加载表格数据
const loadingData = () => {
    tableLoading.value = true;

    let params = {};
    if (queryState.name) {
        params['name'] = queryState.name
    }
    if (queryState.date_range) {
        params['start_time'] = `${queryState.date_range[0]} 00:00:00`;
        params['end_time'] = `${queryState.date_range[1]} 23:59:59`;
    }
    if (queryState.status !== null && queryState.status !== undefined) {
        params['status'] = queryState.status;
    }
    params['page_no'] = pagination.current
    params['page_size'] = pagination.pageSize

    getJobList(params).then(response => {
        const result = response.data;
        dataSource.value = result.data.items;
        pagination.total = result.data.total;
        pagination.current = result.data.page_no;
        pagination.pageSize = result.data.page_size;
    }).catch(error => {
        console.log(error);
    }).finally(() => {
        tableLoading.value = false;
    });
}

// 生命周期钩子
onMounted(async() => {
    await getOptions();
    loadingData();
});

// 查询
const onFinish = () => {
    pagination.current = 1;
    loadingData();
};

// 重置查询
const resetFields = () => {
    Object.keys(queryState).forEach((key: string) => {
        delete queryState[key];
    });
    pagination.current = 1;
    queryState.status = null
    queryState.date_range = null
    loadingData();
}

const handleTableChange = (values: any) => {
    pagination.current = values.current;
    pagination.pageSize = values.pageSize;
    loadingData();
}

const modalHandle = (modalType: string, index?: number) => {
    modalTitle.value = modalType;
    openModal.value = true;

    if (modalType === 'view' && index !== undefined) {
        detailStateLoading.value = true;

        detailState.value = dataSource.value[index];
        detailState.value.index = index;

        detailStateLoading.value = false;

    } else if (modalType === 'update' && index !== undefined) {
        const selected = dataSource.value[index];
        

        if (selected.trigger === 'date' && selected.trigger_args) {
            selected.trigger_args = dayjs(selected.trigger_args).format('YYYY-MM-DD HH:mm:ss');
        }
        else if (selected.start_date && selected.end_date) {
            selected.start_date = dayjs(selected.start_date).format('YYYY-MM-DD HH:mm:ss');
            selected.end_date = dayjs(selected.end_date).format('YYYY-MM-DD HH:mm:ss');
        }
        Object.keys(updateState).forEach(key => {
            updateState[key] = selected[key];
        })
    } 
}

// 删除
const deleteRow = (row: tableJobType) => {
    deleteJob({ id: row.id }).then(() => {
        loadingData();
    }).catch(error => {
        console.log(error)
    })
}

// 弹窗提交（详情/新建/修改）
const handleModalSumbit = () => {
    modalSubmitLoading.value = true;

    if (modalTitle.value === 'view') {
        modalSubmitLoading.value = false;
        openModal.value = false;

    } else if (modalTitle.value === 'create') {
        createForm.value.validate().then(() => {
            const createBody = cloneDeep(createState);
            Object.keys(createBody).forEach(key => {
                if (isEmpty(createBody[key])) {
                    delete createBody[key];
                }
            })

            createJob(createBody).then(() => {
                modalSubmitLoading.value = false;
                openModal.value = false;
                Object.keys(createState).forEach(key => delete createState[key]);
                loadingData();

            }).catch(error => {
                modalSubmitLoading.value = false;
                console.log(error)
            })

        }).catch(error => {
            modalSubmitLoading.value = false;
            console.log(error)
        })

    } else if (modalTitle.value === 'update') {
        updateForm.value.validate().then(() => {
            updateJob(updateState).then(() => {
                modalSubmitLoading.value = false;
                openModal.value = false;
                loadingData();
            }).catch(error => {
                modalSubmitLoading.value = false;
                console.log(error)
            })

        }).catch(error => {
            modalSubmitLoading.value = false;
            console.log(error)
        })
    }
}

// 导出按钮操作
const handleExport = () => {
    Modal.confirm({
        title: '警告',
        content: '是否确认导出所有定时任务数据?',
        onOk() {
            const body = {
                ...queryState,
                page_no: 1,
                page_size: pagination.total
            };
            message.loading('正在导出数据，请稍候...', 0);

            return exportJob(body).then(response => {
                const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                // 从响应头获取文件名
                const contentDisposition = response.headers['content-disposition'];
                let fileName = '定时任务.xlsx';
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

// 清空按钮操作
const handleClear = () => {
    Modal.confirm({
        title: '警告',
        content: '是否确认清空所有定时任务数据?',
        onOk() {
            clearJob().then(() => {
                loadingData();
            })
        }
    })
}

// 操作按钮:操作类型 1: 暂停 2: 恢复 3: 重启（暂时移除重启）
const handleOption = (row: tableJobType, option: number) => {
    OptionJob({ id: row.id, option: option }).then(() => {
        loadingData();
    })
}

</script>

<style lang="scss" scoped>
.table-search-wrapper {
    margin-block-end: 16px;
}
</style>