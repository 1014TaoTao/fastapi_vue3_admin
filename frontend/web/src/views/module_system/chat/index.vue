<template>
  <div class="flex h-[calc(100vh-220px)] min-h-120 gap-3">
    <!-- 左：会话列表 -->
    <div
      class="flex w-72 shrink-0 flex-col overflow-hidden rounded-xl border border-(--el-border-color-lighter) bg-(--el-bg-color)"
    >
      <div class="flex gap-2 border-b border-(--el-border-color-lighter) p-2.5">
        <ElInput v-model="searchKeyword" placeholder="搜索会话" clearable size="default">
          <template #prefix>
            <ElIcon><Search /></ElIcon>
          </template>
        </ElInput>
        <ElDropdown trigger="click" @command="handleCreate">
          <ElButton type="primary" :icon="Plus" />
          <template #dropdown>
            <ElDropdownMenu>
              <ElDropdownItem command="private"
                ><ElIcon><ChatLineRound /></ElIcon>发起私聊</ElDropdownItem
              >
              <ElDropdownItem command="group"
                ><ElIcon><UserFilled /></ElIcon>创建群聊</ElDropdownItem
              >
            </ElDropdownMenu>
          </template>
        </ElDropdown>
      </div>
      <ElScrollbar class="flex-1">
        <div
          v-if="filteredConversations.length === 0"
          class="py-16 text-center text-xs text-(--el-text-color-secondary)"
        >
          暂无会话，点击右上角发起聊天
        </div>
        <div
          v-for="conv in filteredConversations"
          :key="conv.conversation_type + '-' + conv.id"
          class="mx-2 mb-1 flex cursor-pointer items-center gap-2.5 rounded-lg px-2 py-2.5 transition-colors"
          :class="
            isActive(conv) ? 'bg-(--el-color-primary-light-9)' : 'hover:bg-(--el-fill-color-light)'
          "
          @click="openConversation(conv)"
        >
          <div class="relative shrink-0">
            <ElAvatar :size="40" :src="conv.avatar || defaultAvatar" :icon="UserFilled" />
            <span
              v-if="conv.conversation_type === 1"
              class="absolute right-0 bottom-0 size-2.5 rounded-full border-2 border-white"
              :class="conv.online ? 'bg-success' : 'bg-(--el-border-color)'"
            ></span>
          </div>
          <div class="flex min-w-0 flex-1 flex-col">
            <div class="flex items-center justify-between gap-2">
              <span class="truncate text-sm font-medium text-(--el-text-color-primary)">{{
                conv.name
              }}</span>
              <span class="shrink-0 text-[10px] text-(--el-text-color-secondary)">{{
                formatTime(conv.last_time)
              }}</span>
            </div>
            <div class="mt-0.5 flex items-center justify-between gap-2">
              <span class="truncate text-xs text-(--el-text-color-secondary)">{{
                conv.last_message ||
                (conv.conversation_type === 2 ? `群聊(${conv.member_count}人)` : "暂无消息")
              }}</span>
              <span
                v-if="conv.unread > 0"
                class="shrink-0 rounded-full bg-(--el-color-danger) px-1.5 py-0.5 text-[10px] leading-none text-white"
              >
                {{ conv.unread > 99 ? "99+" : conv.unread }}
              </span>
            </div>
          </div>
        </div>
      </ElScrollbar>
    </div>

    <!-- 右：聊天窗 -->
    <div
      class="flex min-w-0 flex-1 flex-col overflow-hidden rounded-xl border border-(--el-border-color-lighter) bg-(--el-bg-color)"
    >
      <template v-if="currentConversation">
        <!-- 头部 -->
        <div
          class="flex items-center justify-between border-b border-(--el-border-color-lighter) px-4 py-3"
        >
          <div class="flex items-center gap-2.5">
            <ElAvatar
              :size="36"
              :src="currentConversation.avatar || defaultAvatar"
              :icon="UserFilled"
            />
            <div class="leading-tight">
              <div class="text-sm font-medium text-(--el-text-color-primary)">
                {{ currentConversation.name }}
              </div>
              <div class="text-xs text-(--el-text-color-secondary)">
                <template v-if="currentConversation.conversation_type === 1">
                  {{ currentConversation.online ? "在线" : "离线" }}
                </template>
                <template v-else> {{ currentConversation.member_count }} 名成员 </template>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <ElTag v-if="chatStore.wsConnected" type="success" effect="plain" size="small"
              >实时连接</ElTag
            >
            <ElButton
              v-if="currentConversation.conversation_type === 2"
              size="small"
              text
              type="primary"
              :icon="MoreFilled"
              @click="openGroupDetail"
            >
              群管理
            </ElButton>
          </div>
        </div>

        <!-- 消息区 -->
        <ElScrollbar ref="messageScrollbarRef" class="flex-1 px-4 py-5">
          <div class="mb-3 text-center">
            <ElButton
              v-if="hasMore"
              text
              type="primary"
              size="small"
              :loading="loadingHistory"
              @click="() => loadHistory()"
            >
              加载更早的消息
            </ElButton>
          </div>
          <div
            v-if="messages.length === 0"
            class="py-20 text-center text-xs text-(--el-text-color-secondary)"
          >
            暂无消息，打个招呼吧
          </div>
          <template v-for="msg in messages" :key="msg.id">
            <div
              :class="[
                'mb-5 flex w-full items-start gap-2.5',
                msg.sender_id === myId ? 'flex-row-reverse' : 'flex-row',
              ]"
            >
              <ElAvatar
                :size="32"
                :src="msg.sender_avatar || defaultAvatar"
                :icon="UserFilled"
                class="shrink-0"
              />
              <div
                :class="[
                  'flex max-w-[70%] flex-col',
                  msg.sender_id === myId ? 'items-end' : 'items-start',
                ]"
              >
                <div
                  :class="[
                    'mb-1 flex items-center gap-2 text-xs',
                    msg.sender_id === myId ? 'flex-row-reverse' : 'flex-row',
                  ]"
                >
                  <span class="font-medium text-(--el-text-color-primary)">{{
                    msg.sender_id === myId ? "我" : msg.sender_name
                  }}</span>
                  <span class="text-(--el-text-color-secondary)">{{
                    formatTime(msg.created_time)
                  }}</span>
                </div>
                <div
                  :class="[
                    'rounded-lg px-3.5 py-2.5 text-sm leading-normal wrap-break-word whitespace-pre-wrap',
                    msg.sender_id === myId
                      ? 'rounded-tr-sm bg-(--el-color-primary) text-white'
                      : 'rounded-tl-sm bg-(--el-fill-color-light) text-(--el-text-color-primary)',
                  ]"
                >
                  {{ msg.content }}
                </div>
              </div>
            </div>
          </template>
        </ElScrollbar>

        <!-- 输入区 -->
        <div class="border-t border-(--el-border-color-lighter) p-3">
          <ElInput
            v-model="draft"
            type="textarea"
            :rows="3"
            resize="none"
            placeholder="输入消息，Enter 发送，Shift+Enter 换行"
            :disabled="sending"
            @keydown.enter.exact.prevent="handleSend"
          />
          <div class="mt-2 flex items-center justify-between">
            <span class="text-xs text-(--el-text-color-secondary)">Enter 发送</span>
            <ElButton type="primary" :loading="sending" @click="handleSend">发送</ElButton>
          </div>
        </div>
      </template>
      <div
        v-else
        class="flex flex-1 flex-col items-center justify-center gap-3 text-(--el-text-color-secondary)"
      >
        <ElIcon :size="56"><ChatDotRound /></ElIcon>
        <span class="text-sm">选择一个会话开始聊天</span>
      </div>
    </div>

    <!-- 发起聊天 / 创建群 -->
    <ElDialog
      v-model="createDialogVisible"
      :title="createMode === 'group' ? '创建群聊' : '发起私聊'"
      width="460px"
      :close-on-click-modal="false"
    >
      <template v-if="createMode === 'group'">
        <div class="mb-3">
          <div class="mb-1.5 text-xs text-(--el-text-color-secondary)">群名称</div>
          <ElInput v-model="groupName" placeholder="请输入群名称" maxlength="64" />
        </div>
        <div class="mb-1.5 text-xs text-(--el-text-color-secondary)">选择成员（可选）</div>
      </template>
      <template v-else>
        <div class="mb-1.5 text-xs text-(--el-text-color-secondary)">选择用户</div>
      </template>
      <ElSelect
        v-model="selectedUserIds"
        multiple
        filterable
        remote
        :remote-method="searchUsers"
        :loading="userLoading"
        placeholder="输入姓名或用户名搜索"
        class="w-full"
      >
        <ElOption
          v-for="u in userOptions"
          :key="u.id"
          :label="u.name + '（' + u.username + '）'"
          :value="u.id"
        />
      </ElSelect>
      <template #footer>
        <ElButton @click="createDialogVisible = false">取消</ElButton>
        <ElButton type="primary" :loading="createLoading" @click="confirmCreate">确定</ElButton>
      </template>
    </ElDialog>

    <!-- 群详情管理 -->
    <ElDrawer v-model="groupDetailVisible" title="群管理" size="380px">
      <template v-if="groupDetail">
        <div class="mb-4 flex items-center gap-3">
          <ElAvatar :size="48" :src="groupDetail.avatar || defaultAvatar" :icon="UserFilled" />
          <div>
            <div class="text-sm font-medium">{{ groupDetail.name }}</div>
            <div class="text-xs text-(--el-text-color-secondary)">
              {{ groupDetail.member_count }} 名成员
            </div>
          </div>
        </div>
        <div
          v-if="groupDetail.announcement"
          class="mb-4 rounded-lg bg-(--el-fill-color-light) p-3 text-xs text-(--el-text-color-secondary)"
        >
          公告：{{ groupDetail.announcement }}
        </div>
        <div class="mb-2 flex items-center justify-between">
          <span class="text-sm font-medium">成员列表</span>
          <ElButton
            v-if="isOwner"
            size="small"
            type="primary"
            text
            :icon="Plus"
            @click="openAddMember"
            >添加成员</ElButton
          >
        </div>
        <ElScrollbar max-height="320px">
          <div
            v-for="m in groupDetail.members"
            :key="m.id"
            class="mb-1 flex items-center justify-between rounded-lg px-2 py-2 hover:bg-(--el-fill-color-light)"
          >
            <div class="flex items-center gap-2.5">
              <ElAvatar :size="32" :src="m.avatar || defaultAvatar" :icon="UserFilled" />
              <div class="leading-tight">
                <div class="text-sm">{{ m.name }}</div>
                <div class="text-[10px] text-(--el-text-color-secondary)">{{ m.username }}</div>
              </div>
            </div>
            <div class="flex items-center gap-1.5">
              <ElTag v-if="m.id === groupDetail.owner_id" size="small" type="warning" effect="light"
                >群主</ElTag
              >
              <ElButton
                v-if="isOwner && m.id !== groupDetail.owner_id"
                size="small"
                text
                type="danger"
                @click="removeMember(m)"
                >移除</ElButton
              >
            </div>
          </div>
        </ElScrollbar>
        <div class="mt-5 border-t border-(--el-border-color-lighter) pt-4">
          <template v-if="isOwner">
            <ElInput v-model="announcementDraft" placeholder="修改群公告" class="mb-2" />
            <div class="flex gap-2">
              <ElButton type="primary" @click="saveAnnouncement">保存公告</ElButton>
              <ElButton type="danger" plain @click="confirmDeleteGroup">解散群组</ElButton>
            </div>
          </template>
          <ElButton v-else type="danger" plain @click="confirmQuitGroup">退出群组</ElButton>
        </div>
      </template>
    </ElDrawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  ChatDotRound,
  ChatLineRound,
  MoreFilled,
  Plus,
  Search,
  UserFilled,
} from "@element-plus/icons-vue";
import type { ElScrollbar as ElScrollbarType } from "element-plus";

import ChatAPI, {
  ChatMessageItem,
  ChatUserItem,
  ConversationItem,
  ChatGroupDetail,
} from "@/api/module_system/chat";
import { useUserStore } from "@stores";
import { useChatStore } from "@/store/modules/chat.store";
import defaultAvatar from "@imgs/avatar/avatar5.webp";

defineOptions({ name: "SystemChat" });

const userStore = useUserStore();
const chatStore = useChatStore();
const myId = computed(() => userStore.basicInfo?.id ?? userStore.basicInfo?.user_id ?? 0);

// ── 会话列表 ──────────────────────────────────────────────────
const conversations = ref<ConversationItem[]>([]);
const searchKeyword = ref("");
const currentConversation = ref<ConversationItem | null>(null);

const filteredConversations = computed(() => {
  const kw = searchKeyword.value.trim().toLowerCase();
  if (!kw) return conversations.value;
  return conversations.value.filter((c) => c.name.toLowerCase().includes(kw));
});

const isActive = (conv: ConversationItem) =>
  currentConversation.value?.conversation_type === conv.conversation_type &&
  currentConversation.value?.id === conv.id;

async function loadConversations() {
  const response = await ChatAPI.listConversations();
  conversations.value = Array.isArray(response.data?.data) ? response.data.data : [];
  chatStore.unreadTotal = conversations.value.reduce((sum, c) => sum + (c.unread || 0), 0);
  // 更新在线状态缓存
  const online: Record<number, boolean> = {};
  conversations.value.forEach((c) => {
    if (c.conversation_type === 1 && c.id) online[c.id] = c.online;
  });
  chatStore.onlineUsers = { ...chatStore.onlineUsers, ...online };
}

// ── 聊天窗 ──────────────────────────────────────────────────
const messages = ref<ChatMessageItem[]>([]);
const draft = ref("");
const sending = ref(false);
const hasMore = ref(false);
const loadingHistory = ref(false);
const messageScrollbarRef = ref<InstanceType<typeof ElScrollbarType>>();

function scrollToBottom() {
  setTimeout(() => {
    const wrap = messageScrollbarRef.value?.wrapRef;
    if (wrap) wrap.scrollTop = wrap.scrollHeight;
  }, 50);
}

async function openConversation(conv: ConversationItem) {
  if (isActive(conv)) return;
  currentConversation.value = conv;
  messages.value = [];
  hasMore.value = false;
  await loadHistory(false);
  chatStore.setActiveConversation({ type: conv.conversation_type, id: conv.id! }, (msg) => {
    if (messages.value.some((m) => m.id === msg.id)) return;
    messages.value.push(msg);
    scrollToBottom();
  });
  await chatStore.markRead({ type: conv.conversation_type, id: conv.id! });
  conv.unread = 0;
}

async function loadHistory(appendTop = true) {
  const conv = currentConversation.value;
  if (!conv || conv.id == null) return;
  loadingHistory.value = true;
  try {
    const beforeId = appendTop ? messages.value[0]?.id : undefined;
    const response = await ChatAPI.listMessages({
      conversation_type: conv.conversation_type,
      receiver_id: conv.id,
      before_id: beforeId,
      page_size: 20,
    });
    const data = response.data?.data;
    const items = data?.items ?? [];
    hasMore.value = data?.has_more ?? false;
    if (appendTop) {
      messages.value = [...items, ...messages.value];
    } else {
      messages.value = items;
      scrollToBottom();
    }
  } finally {
    loadingHistory.value = false;
  }
}

async function handleSend() {
  const conv = currentConversation.value;
  const content = draft.value.trim();
  if (!conv || conv.id == null || !content) return;
  sending.value = true;
  try {
    const response = await ChatAPI.sendMessage({
      conversation_type: conv.conversation_type,
      receiver_id: conv.id,
      content,
    });
    const msg = response.data?.data;
    if (msg) {
      messages.value.push(msg);
      conv.last_message = msg.content;
      conv.last_time = msg.created_time;
      scrollToBottom();
    }
    draft.value = "";
  } finally {
    sending.value = false;
  }
}

// ── 时间格式化 ──────────────────────────────────────────────────
function formatTime(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  const now = new Date();
  const sameDay = date.toDateString() === now.toDateString();
  const pad = (n: number) => String(n).padStart(2, "0");
  const hm = `${pad(date.getHours())}:${pad(date.getMinutes())}`;
  if (sameDay) return hm;
  return `${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${hm}`;
}

// ── 发起聊天 / 创建群 ──────────────────────────────────────────────────
const createDialogVisible = ref(false);
const createMode = ref<"private" | "group">("private");
const groupName = ref("");
const selectedUserIds = ref<number[]>([]);
const userOptions = ref<ChatUserItem[]>([]);
const userLoading = ref(false);
const createLoading = ref(false);

function handleCreate(command: string) {
  createMode.value = command as "private" | "group";
  groupName.value = "";
  selectedUserIds.value = [];
  userOptions.value = [];
  createDialogVisible.value = true;
  searchUsers("");
}

async function searchUsers(keyword: string) {
  userLoading.value = true;
  try {
    const response = await ChatAPI.listUsers(keyword);
    userOptions.value = Array.isArray(response.data?.data) ? response.data.data : [];
  } finally {
    userLoading.value = false;
  }
}

async function confirmCreate() {
  createLoading.value = true;
  try {
    if (createMode.value === "private") {
      if (selectedUserIds.value.length !== 1) {
        ElMessage.warning("请选择一个用户");
        return;
      }
      const userId = selectedUserIds.value[0]!;
      const exists = conversations.value.some((c) => c.conversation_type === 1 && c.id === userId);
      if (exists) {
        createDialogVisible.value = false;
        openConversation(
          conversations.value.find((c) => c.conversation_type === 1 && c.id === userId)!
        );
        return;
      }
      const response = await ChatAPI.listUsers();
      const users = Array.isArray(response.data?.data) ? response.data.data : [];
      const user = users.find((u) => u.id === userId);
      const conv: ConversationItem = {
        id: userId,
        conversation_type: 1,
        name: user?.name ?? "用户",
        avatar: user?.avatar ?? null,
        online: !!chatStore.onlineUsers[userId],
        member_count: 0,
        last_message: null,
        last_time: null,
        unread: 0,
      };
      conversations.value.unshift(conv);
      createDialogVisible.value = false;
      openConversation(conv);
    } else {
      if (!groupName.value.trim()) {
        ElMessage.warning("请输入群名称");
        return;
      }
      const response = await ChatAPI.createGroup({
        name: groupName.value.trim(),
        member_ids: selectedUserIds.value,
      });
      const detail = response.data?.data;
      createDialogVisible.value = false;
      ElMessage.success("创建群聊成功");
      await loadConversations();
      if (detail?.id) {
        const conv = conversations.value.find(
          (c) => c.conversation_type === 2 && c.id === detail.id
        );
        if (conv) openConversation(conv);
      }
    }
  } finally {
    createLoading.value = false;
  }
}

// ── 群管理 ──────────────────────────────────────────────────
const groupDetailVisible = ref(false);
const groupDetail = ref<ChatGroupDetail | null>(null);
const announcementDraft = ref("");

const isOwner = computed(() => groupDetail.value?.owner_id === myId.value);

async function openGroupDetail() {
  const conv = currentConversation.value;
  if (!conv || conv.id == null) return;
  const response = await ChatAPI.getGroupDetail(conv.id);
  groupDetail.value = response.data?.data ?? null;
  announcementDraft.value = groupDetail.value?.announcement ?? "";
  groupDetailVisible.value = true;
}

async function openAddMember() {
  const conv = currentConversation.value;
  if (!conv || conv.id == null) return;
  const result = await ElMessageBox.prompt("输入用户名或姓名（多个用英文逗号分隔）", "添加成员", {
    confirmButtonText: "添加",
    cancelButtonText: "取消",
    inputPlaceholder: "例：zhangsan, lisi",
  }).catch(() => null);
  if (!result) return;
  const keywords = result.value.split(/[,，\s]+/).filter(Boolean);
  const members = (await ChatAPI.listUsers()).data?.data ?? [];
  const ids = keywords
    .flatMap((kw) =>
      members.filter((u) => u.name.includes(kw) || u.username.includes(kw)).map((u) => u.id)
    )
    .filter((id, index, arr) => arr.indexOf(id) === index);
  if (ids.length === 0) {
    ElMessage.warning("未找到匹配用户");
    return;
  }
  await ChatAPI.addGroupMembers(conv.id, ids);
  ElMessage.success("添加成员成功");
  await openGroupDetail();
}

async function removeMember(m: ChatUserItem) {
  const conv = currentConversation.value;
  if (!conv || conv.id == null) return;
  await ElMessageBox.confirm(`确定移除成员「${m.name}」吗？`, "移除成员", { type: "warning" });
  await ChatAPI.removeGroupMembers(conv.id, [m.id]);
  ElMessage.success("已移除");
  await openGroupDetail();
}

async function saveAnnouncement() {
  const conv = currentConversation.value;
  if (!conv || conv.id == null) return;
  await ChatAPI.updateGroup(conv.id, { announcement: announcementDraft.value });
  ElMessage.success("公告已保存");
  await openGroupDetail();
}

async function confirmDeleteGroup() {
  const conv = currentConversation.value;
  if (!conv || conv.id == null) return;
  await ElMessageBox.confirm("解散后群聊记录将无法继续查看，确定解散？", "解散群组", {
    type: "error",
  });
  await ChatAPI.deleteGroup(conv.id);
  ElMessage.success("群组已解散");
  groupDetailVisible.value = false;
  currentConversation.value = null;
  await loadConversations();
}

async function confirmQuitGroup() {
  const conv = currentConversation.value;
  if (!conv || conv.id == null) return;
  await ElMessageBox.confirm("确定退出该群组吗？", "退出群组", { type: "warning" });
  await ChatAPI.quitGroup(conv.id);
  ElMessage.success("已退出群组");
  groupDetailVisible.value = false;
  currentConversation.value = null;
  await loadConversations();
}

// ── 生命周期 ──────────────────────────────────────────────────
onMounted(async () => {
  chatStore.initChat();
  await loadConversations();
  // 私聊在线状态实时同步
  if (currentConversation.value?.conversation_type === 1 && currentConversation.value.id) {
    currentConversation.value.online = !!chatStore.onlineUsers[currentConversation.value.id];
  }
});

onUnmounted(() => {
  chatStore.clearActiveConversation();
});
</script>
