<template>
    <a-tabs 
        v-model:activeKey="activeKey" 
        hide-add 
        :animated="false"
        type="editable-card" 
        @edit="onEdit" 
        @change="onChange"
    >
        
        <a-tab-pane 
            v-for="pane in panes" 
            :key="pane.key" 
            :tab="pane.title" 
            :closable="pane.closable"
        />
        <!-- 使用 rightExtra 插槽添加关闭全部按钮 -->
        <template #rightExtra>
            <!-- 修改为以 icon 显示的刷新缓存按钮 -->
            <a-button type="link" @click="refreshCache">
                <template #icon>
                    <ReloadOutlined />
                </template>
            </a-button>
            <a-button type="link" @click="closeAllTabs">关闭全部</a-button>
        </template>
    </a-tabs>
    
</template>
<script lang="ts" setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute, useRouter } from "vue-router";
import { ReloadOutlined } from '@ant-design/icons-vue'; // 导入刷新图标
interface Pane {
    title: string;
    path: string;
    key: string;
    closable?: boolean;
}
const router = useRouter();
const route = useRoute();
const panes = ref<Pane[]>([
    { 
        title: '工作台', 
        path: '/dashboard/workplace', 
        key: '/dashboard/workplace', 
        closable: false 
    }
]);
const activeKey = ref(panes.value[0].key);
const getRoute = () => {
    const existingPane = panes.value.some(pane => pane.key === route.path);
    if (!existingPane) {
        panes.value.push({
            title: route.meta.title?.toString() || '未命名',
            path: route.path,
            key: route.path,
            closable: true
        });
    }
    activeKey.value = route.path;
}
const removePane = (targetKey: string) => {
    const paneIndex = panes.value.findIndex(pane => pane.key === targetKey);
    panes.value = panes.value.filter(pane => pane.key !== targetKey);
    
    if (activeKey.value === targetKey && panes.value.length) {
        const newIndex = Math.max(0, paneIndex - 1);
        activeKey.value = panes.value[newIndex].key;
        router.push(activeKey.value);
    }
};

const onEdit = (targetKey: string | MouseEvent, action: string) => {
    if (action === 'remove') {
        removePane(targetKey as string);
    }
};

const onChange = (targetKey: string) => {
    if (targetKey !== 'close-all') {
        router.push(targetKey);
    } else {
        // 防止跳转到不存在的路由
        activeKey.value = panes.value[0].key;
    }
};

// 新增关闭所有标签的方法
const closeAllTabs = () => {
    // 过滤出不可关闭的标签
    panes.value = panes.value.filter(pane => !pane.closable);
    if (panes.value.length > 0) {
        activeKey.value = panes.value[0].key;
        router.push(activeKey.value);
    }
};

// 新增刷新缓存的方法
const refreshCache = () => {
    // 刷新页面
    window.location.reload();
};

onMounted(getRoute);
watch(() => route.path, getRoute);
</script>

<style scoped>
/* 添加以下样式 */
:deep(.ant-tabs-nav) {
    will-change: transform;
    backface-visibility: hidden;
    margin: 0;
}

:deep(.ant-tabs-tab) {
    transition: none !important;
}

:deep(.ant-tabs-ink-bar) {
    transition: transform 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
}
</style>