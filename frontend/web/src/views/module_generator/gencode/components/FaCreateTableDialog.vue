<template>
  <FaDialog
    v-model="visible"
    title="创建数据表"
    width="min(800px, 94vw)"
    append-to-body
    dialog-class="create-table-dialog"
    @opened="onDialogOpened"
  >
    <ElAlert type="info" :closable="false" show-icon class="mb-3">
      <template #title>
        <span class="text-sm leading-relaxed"
          >自带示例一键插入；会写 DDL 的可直接粘贴，支持多条语句。</span
        >
      </template>
    </ElAlert>

    <div class="sql-pane mt-3">
      <div class="mb-2 flex flex-wrap items-center gap-2">
        <ElDropdown trigger="click" @command="onSqlPresetCommand">
          <ElButton type="primary" size="small">
            插入示例模板
            <ElIcon class="el-icon--right"><ArrowDown /></ElIcon>
          </ElButton>
          <template #dropdown>
            <ElDropdownMenu>
              <ElDropdownItem command="single-mysql">单表 · MySQL</ElDropdownItem>
              <ElDropdownItem command="single-postgres">单表 · PostgreSQL</ElDropdownItem>
              <ElDropdownItem command="master-mysql" divided>主子表 · MySQL</ElDropdownItem>
              <ElDropdownItem command="master-postgres">主子表 · PostgreSQL</ElDropdownItem>
            </ElDropdownMenu>
          </template>
        </ElDropdown>
        <span class="text-xs text-(--el-text-color-secondary)">从模板开始比自己写更省事</span>
      </div>

      <ElScrollbar max-height="min(52vh, 420px)" class="sql-editor-scroll">
        <div class="absolute z-36 right-5 top-2">
          <ElLink type="primary" @click="copySql">
            <ElIcon><CopyDocument /></ElIcon>
            复制
          </ElLink>
        </div>
        <Codemirror
          ref="sqlRef"
          v-model:value="sqlText"
          :options="sqlOptions"
          border
          height="360px"
          width="100%"
        />
      </ElScrollbar>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <ElButton type="primary" :loading="loading" @click="handleConfirm">创建表</ElButton>
        <ElButton @click="handleCancel">取消</ElButton>
      </div>
    </template>
  </FaDialog>
</template>

<script setup lang="ts">
import "codemirror/mode/sql/sql.js";
import "codemirror/theme/dracula.css";
import Codemirror from "codemirror-editor-vue3";
import type { EditorConfiguration } from "codemirror";
import type { CmComponentRef } from "codemirror-editor-vue3";
import { ElMessage } from "element-plus";
import { ArrowDown, CopyDocument } from "@element-plus/icons-vue";
import { useClipboard } from "@vueuse/core";
import { useSettingsStore } from "@stores";
import { ThemeMode } from "@/enums/settings/theme.enum";
import {
  getExampleFromPresetMasterSub,
  getExampleFromPresetSingle,
} from "../utils/createTableSqlExamples";
import FaDialog from "@/components/modal/fa-dialog/index.vue";

defineOptions({ name: "CreateTableDialog" });

const visible = defineModel<boolean>({ default: false });

defineProps<{
  loading?: boolean;
}>();

interface Emits {
  submit: [sql: string];
}

const emit = defineEmits<Emits>();

const { copy } = useClipboard();
const settingsStore = useSettingsStore();

const sqlText = ref("");
const sqlRef = ref<CmComponentRef>();

const codeTheme = ref(settingsStore.theme === ThemeMode.DARK ? "dracula" : "default");

const sqlOptions: EditorConfiguration = {
  mode: "text/x-sql",
  lineNumbers: true,
  smartIndent: true,
  indentUnit: 2,
  tabSize: 2,
  readOnly: false,
  theme: codeTheme.value,
  lineWrapping: true,
  autofocus: false,
};

watch(
  () => settingsStore.theme,
  (t) => {
    const newTheme = t === ThemeMode.DARK ? "dracula" : "default";
    codeTheme.value = newTheme;
    sqlOptions.theme = newTheme;
    if (sqlRef.value?.cminstance) {
      sqlRef.value.cminstance.setOption("theme", newTheme);
    }
  }
);

function onDialogOpened() {
  sqlText.value = "";
}

function onSqlPresetCommand(cmd: string) {
  switch (cmd) {
    case "single-mysql":
      sqlText.value = getExampleFromPresetSingle("mysql");
      break;
    case "single-postgres":
      sqlText.value = getExampleFromPresetSingle("postgres");
      break;
    case "master-mysql":
      sqlText.value = getExampleFromPresetMasterSub("mysql");
      break;
    case "master-postgres":
      sqlText.value = getExampleFromPresetMasterSub("postgres");
      break;
  }
}

function copySql() {
  if (!sqlText.value) {
    ElMessage.warning("没有可复制的内容");
    return;
  }
  copy(sqlText.value);
  ElMessage.success("已复制");
}

function handleConfirm() {
  const sql = sqlText.value.trim();
  if (!sql) {
    ElMessage.error("请填写 SQL");
    return;
  }
  emit("submit", sql);
}

function handleCancel() {
  visible.value = false;
}
</script>
