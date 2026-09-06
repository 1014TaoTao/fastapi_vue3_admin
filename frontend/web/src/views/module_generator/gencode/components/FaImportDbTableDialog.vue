<template>
  <FaDialog ref="dialogRef" v-model="open" title="导入表" append-to-body>
    <ElForm ref="importQueryRef" :model="query" :inline="true">
      <ElFormItem label="表名称" prop="table_name">
        <ElInput
          v-model="query.table_name"
          placeholder="请输入表名称"
          clearable
          :style="'width: 180px'"
          @keyup.enter="emit('query')"
        />
      </ElFormItem>
      <ElFormItem label="表描述" prop="table_comment">
        <ElInput
          v-model="query.table_comment"
          placeholder="请输入表描述"
          clearable
          :style="'width: 180px'"
          @keyup.enter="emit('query')"
        />
      </ElFormItem>
      <ElFormItem>
        <ElButton
          v-hasPerm="['module_generator:dblist:query']"
          type="primary"
          :icon="Search"
          @click="emit('query')"
        >
          搜索
        </ElButton>
        <ElButton
          v-hasPerm="['module_generator:dblist:query']"
          :icon="Refresh"
          @click="emit('reset')"
        >
          重置
        </ElButton>
      </ElFormItem>
    </ElForm>
    <ElTable
      ref="tableRef"
      :data="data"
      height="calc(100vh - 400px)"
      @row-click="onRowClick"
      @selection-change="onSelectionChange"
      class="mb-5"
    >
      <template #empty>
        <ElEmpty :image-size="80" description="暂无数据" />
      </template>
      <ElTableColumn type="selection" width="55"></ElTableColumn>
      <ElTableColumn label="序号" type="index" min-width="30" align="center" fixed>
        <template #default="scope">
          <span>
            {{ ((query.page_no ?? 1) - 1) * (query.page_size ?? 10) + scope.$index + 1 }}
          </span>
        </template>
      </ElTableColumn>
      <ElTableColumn
        prop="database_name"
        label="数据库名称"
        :show-overflow-tooltip="true"
      ></ElTableColumn>
      <ElTableColumn prop="table_name" label="表名称" :show-overflow-tooltip="true"></ElTableColumn>
      <ElTableColumn
        prop="table_comment"
        label="表描述"
        :show-overflow-tooltip="true"
      ></ElTableColumn>
      <ElTableColumn prop="table_type" label="表类型"></ElTableColumn>
    </ElTable>
    <FaPagination
      v-model:page="query.page_no"
      v-model:limit="query.page_size"
      :total="total"
      @pagination="emit('fetch')"
    />
    <template #footer>
      <div class="dialog-footer">
        <ElButton type="primary" :loading="confirmLoading" @click="emit('confirm')">确 定</ElButton>
        <ElButton @click="open = false">取 消</ElButton>
      </div>
    </template>
  </FaDialog>
</template>

<script setup lang="ts">
import type { FormInstance, TableInstance } from "element-plus";
import { Search, Refresh } from "@element-plus/icons-vue";
import type { DBTableSchema, GenTablePageQuery } from "@/api/module_generator/gencode";
import FaDialog from "@/components/modal/fa-dialog/index.vue";

defineOptions({ name: "ImportDbTableDialog" });

defineProps<{
  data: DBTableSchema[];
  total: number;
  confirmLoading: boolean;
}>();

const open = defineModel<boolean>({ required: true });
const query = defineModel<GenTablePageQuery>("query", { required: true });

interface Emits {
  query: [];
  reset: [];
  confirm: [];
  fetch: [];
  "selection-change": [rows: { table_name: string; table_comment: string }[]];
}

const emit = defineEmits<Emits>();

const importQueryRef = ref<FormInstance>();
const tableRef = ref<TableInstance>();

function onRowClick(row: DBTableSchema) {
  tableRef.value?.toggleRowSelection(row);
}

function onSelectionChange(selection: DBTableSchema[]) {
  emit(
    "selection-change",
    selection.map((item) => ({
      table_name: item.table_name || "",
      table_comment: item.table_comment || "",
    }))
  );
}

defineExpose({
  resetQueryForm: () => importQueryRef.value?.resetFields(),
});
</script>
