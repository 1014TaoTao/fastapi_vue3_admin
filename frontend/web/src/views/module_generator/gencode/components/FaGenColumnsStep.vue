<template>
  <div>
    <ElAlert
      v-if="info.sub && !info.master_sub_hint && info.sub_table_name"
      class="mb-3"
      type="success"
      :closable="false"
      show-icon
      title="当前已启用主子表：以下为「主表」字段配置；子表字段来自数据库结构，保存后可在预览中查看子表生成代码。"
    />
    <ElAlert
      v-else-if="info.master_sub_hint"
      class="mb-3"
      type="warning"
      :closable="false"
      show-icon
      :title="info.master_sub_hint"
    />
    <ElAlert
      v-if="columnKeyword.trim() && displayColumns.length === 0 && (info.columns?.length ?? 0) > 0"
      class="mb-2"
      type="warning"
      :closable="false"
      show-icon
      title="无匹配列，请调整筛选词或清空筛选框"
    />
    <div class="mt-3 mb-2.5 flex flex-wrap items-center gap-2">
      <ElInput
        v-model="columnKeyword"
        clearable
        placeholder="筛选列名或注释"
        style="width: 240px"
        :prefix-icon="Search"
      />
      <span class="text-xs text-(--el-text-color-secondary) select-none">批量设置：</span>
      <ElSpace size="small">
        <ElDropdown>
          <ElButton size="small" type="primary" plain>查询</ElButton>
          <template #dropdown>
            <ElDropdownMenu>
              <ElDropdownItem @click="bulkSet('is_query', true)">全选</ElDropdownItem>
              <ElDropdownItem @click="bulkSet('is_query', false)">全不选</ElDropdownItem>
            </ElDropdownMenu>
          </template>
        </ElDropdown>
        <ElDropdown>
          <ElButton size="small" type="success" plain>列表</ElButton>
          <template #dropdown>
            <ElDropdownMenu>
              <ElDropdownItem @click="bulkSet('is_list', true)">全选</ElDropdownItem>
              <ElDropdownItem @click="bulkSet('is_list', false)">全不选</ElDropdownItem>
            </ElDropdownMenu>
          </template>
        </ElDropdown>
        <ElDropdown>
          <ElButton size="small" type="warning" plain>新增</ElButton>
          <template #dropdown>
            <ElDropdownMenu>
              <ElDropdownItem @click="bulkSet('is_insert', true)">全选</ElDropdownItem>
              <ElDropdownItem @click="bulkSet('is_insert', false)">全不选</ElDropdownItem>
            </ElDropdownMenu>
          </template>
        </ElDropdown>
        <ElDropdown>
          <ElButton size="small" type="danger" plain>编辑</ElButton>
          <template #dropdown>
            <ElDropdownMenu>
              <ElDropdownItem @click="bulkSet('is_edit', true)">全选</ElDropdownItem>
              <ElDropdownItem @click="bulkSet('is_edit', false)">全不选</ElDropdownItem>
            </ElDropdownMenu>
          </template>
        </ElDropdown>
      </ElSpace>
    </div>
    <div class="data-table__content">
      <ElTable
        ref="dragTable"
        v-loading="loading"
        :data="displayColumns"
        row-key="id"
        :height="tableHeight"
        highlight-current-row
        border
        stripe
      >
        <template #empty>
          <ElEmpty :image-size="80" description="暂无数据" />
        </template>
        <ElTableColumn label="拖拽" width="56" fixed align="center">
          <template #default>
            <span
              class="gencode-drag-handle inline-flex items-center justify-center w-7 h-5.5 text-sm leading-none text-(--el-text-color-secondary) cursor-grab select-none"
              :class="{
                disabled: !!columnKeyword.trim(),
                'cursor-not-allowed opacity-35': !!columnKeyword.trim(),
              }"
              title="拖拽排序（筛选时禁用）"
            >
              <ElIcon><Rank /></ElIcon>
            </span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="序号" type="index" width="60" fixed />
        <ElTableColumn
          label="列名"
          prop="column_name"
          min-width="60"
          :show-overflow-tooltip="true"
        />
        <ElTableColumn
          label="类型"
          prop="column_type"
          min-width="60"
          :show-overflow-tooltip="true"
        />
        <ElTableColumn label="长度" prop="column_length" width="80" :show-overflow-tooltip="true">
          <template #default="scope">
            <ElInput v-model="scope.row.column_length" :disabled="!!scope.row.is_pk" />
          </template>
        </ElTableColumn>
        <ElTableColumn label="注释" min-width="60">
          <template #default="scope">
            <ElInput v-model="scope.row.column_comment"></ElInput>
          </template>
        </ElTableColumn>
        <ElTableColumn label="后端类型" min-width="60">
          <template #default="scope">
            <ElSelect v-model="scope.row.python_type">
              <ElOption label="str" value="str" />
              <ElOption label="int" value="int" />
              <ElOption label="float" value="float" />
              <ElOption label="Decimal" value="Decimal" />
              <ElOption label="date" value="date" />
              <ElOption label="time" value="time" />
              <ElOption label="datetime" value="datetime" />
              <ElOption label="bytes" value="bytes" />
              <ElOption label="dict" value="dict" />
              <ElOption label="list" value="list" />
            </ElSelect>
          </template>
        </ElTableColumn>
        <ElTableColumn label="后端属性" min-width="60">
          <template #default="scope">
            <ElInput v-model="scope.row.python_field"></ElInput>
          </template>
        </ElTableColumn>
        <ElTableColumn label="新增" width="60">
          <template #default="scope">
            <ElCheckbox v-model="scope.row.is_insert" />
          </template>
        </ElTableColumn>
        <ElTableColumn label="编辑" width="60">
          <template #default="scope">
            <ElCheckbox v-model="scope.row.is_edit" />
          </template>
        </ElTableColumn>
        <ElTableColumn label="列表" width="60">
          <template #default="scope">
            <ElCheckbox v-model="scope.row.is_list" />
          </template>
        </ElTableColumn>
        <ElTableColumn label="查询" width="60">
          <template #default="scope">
            <ElCheckbox v-model="scope.row.is_query" />
          </template>
        </ElTableColumn>
        <ElTableColumn label="查询方式" min-width="60">
          <template #default="scope">
            <ElSelect v-model="scope.row.query_type">
              <ElOption label="=" value="EQ" />
              <ElOption label="!=" value="NE" />
              <ElOption label=">" value="GT" />
              <ElOption label=">=" value="GTE" />
              <ElOption label="<" value="LT" />
              <ElOption label="<=" value="LTE" />
              <ElOption label="LIKE" value="LIKE" />
              <ElOption label="BETWEEN" value="BETWEEN" />
            </ElSelect>
          </template>
        </ElTableColumn>
        <ElTableColumn
          label="默认值"
          prop="column_default"
          min-width="60"
          :show-overflow-tooltip="true"
        >
          <template #default="scope">
            <ElInput v-model="scope.row.column_default" :disabled="!!scope.row.is_pk" />
          </template>
        </ElTableColumn>
        <ElTableColumn label="自增" width="60">
          <template #default="scope">
            <ElCheckbox v-model="scope.row.is_increment" />
          </template>
        </ElTableColumn>
        <ElTableColumn label="可空" width="60">
          <template #default="scope">
            <ElCheckbox v-model="scope.row.is_nullable" />
          </template>
        </ElTableColumn>
        <ElTableColumn label="唯一" width="60">
          <template #default="scope">
            <ElCheckbox v-model="scope.row.is_unique" />
          </template>
        </ElTableColumn>
        <ElTableColumn label="主键" width="60">
          <template #default="scope">
            <ElCheckbox v-model="scope.row.is_pk" />
          </template>
        </ElTableColumn>
        <ElTableColumn label="表单类型">
          <template #default="scope">
            <ElSelect v-model="scope.row.html_type">
              <ElOption label="文本框" value="input" />
              <ElOption label="文本域" value="textarea" />
              <ElOption label="下拉框" value="select" />
              <ElOption label="单选框" value="radio" />
              <ElOption label="复选框" value="checkbox" />
              <ElOption label="日期控件" value="datetime" />
              <ElOption label="图片上传" value="imageUpload" />
              <ElOption label="文件上传" value="fileUpload" />
              <ElOption label="富文本控件" value="editor" />
            </ElSelect>
          </template>
        </ElTableColumn>
        <ElTableColumn label="字典类型" fixed="right">
          <template #default="scope">
            <ElSelect v-model="scope.row.dict_type" clearable filterable placeholder="请选择">
              <ElOption
                v-for="dict in dictOptions"
                :key="dict.dict_type"
                :label="dict.dict_name"
                :value="dict.dict_type || ''"
              >
                <span :style="'float: left'">{{ dict.dict_name }}</span>
                <span :style="'float: right; font-size: 13px; color: #8492a6'">
                  {{ dict.dict_type }}
                </span>
              </ElOption>
            </ElSelect>
          </template>
        </ElTableColumn>
      </ElTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Rank, Search } from "@element-plus/icons-vue";
import { useDraggable } from "vue-draggable-plus";
import type { GenTableSchema, GenTableColumnSchema } from "@/api/module_generator/gencode";
import type { DictTable } from "@/api/module_system/dict";

defineOptions({ name: "GenColumnsStep" });

const info = defineModel<GenTableSchema>("info", { required: true });

defineProps<{
  dictOptions: DictTable[];
  loading: boolean;
  bulkSet: (field: string | string[], value: unknown) => void;
}>();

const columnKeyword = ref("");
const dragTable = ref<any>(null);
const dragContainer = ref<HTMLElement | null>(null);
let draggableApi: { destroy?: () => void; pause?: () => void; start?: () => void } | null = null;

// 计算表格高度：视口高度 - 顶部导航栏 - 步骤条 - 提示文字 - 筛选栏 - 底部按钮 - 边距
// 大约：60(顶部) + 60(步骤) + 30(提示) + 50(筛选) + 80(底部按钮) + 100(边距) = 380px
const tableHeight = computed(() => {
  return "calc(100vh - 270px)"; // -80 底部按钮
});

const columnsModel = computed({
  get: () => info.value.columns || [],
  set: (v) => {
    info.value.columns = v as GenTableColumnSchema[];
  },
});

const displayColumns = computed(() => {
  const cols = info.value.columns || [];
  const q = columnKeyword.value.trim().toLowerCase();
  if (!q) return cols;
  return cols.filter((c) => {
    const name = String(c.column_name ?? "").toLowerCase();
    const comment = String(c.column_comment ?? "").toLowerCase();
    return name.includes(q) || comment.includes(q);
  });
});

function syncSortNumbers() {
  const cols = columnsModel.value || [];
  cols.forEach((c, idx) => {
    c.sort = idx + 1;
  });
}

async function setupRowDraggable() {
  // 筛选状态下禁用拖拽：displayColumns 是子集，直接拖拽会导致索引映射混乱
  if (columnKeyword.value.trim()) {
    draggableApi?.destroy?.();
    draggableApi = null;
    dragContainer.value = null;
    return;
  }

  await nextTick();
  const el = dragTable.value?.$el as HTMLElement | undefined;
  const tbody = el?.querySelector?.(".el-table__body-wrapper tbody") as HTMLElement | null;
  if (!tbody) return;
  dragContainer.value = tbody;

  // 重新绑定
  draggableApi?.destroy?.();
  draggableApi = useDraggable(dragContainer, columnsModel, {
    animation: 150,
    draggable: "tr",
    handle: ".gencode-drag-handle:not(.disabled)",
    onEnd() {
      syncSortNumbers();
    },
  });
}

onMounted(() => {
  void setupRowDraggable();
});

watch(
  () => [columnKeyword.value, (info.value.columns || []).length],
  async () => {
    await setupRowDraggable();
  }
);

onBeforeUnmount(() => {
  draggableApi?.destroy?.();
  draggableApi = null;
});
</script>
