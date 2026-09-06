<template>
  <div class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <div class="logo-section">
        <ElIcon class="logo-icon" :size="28"><ChatDotRound /></ElIcon>
        <span v-if="!isCollapsed" class="project-name">FA智能助手</span>
      </div>
    </div>

    <ElScrollbar class="sidebar-content" view-class="p-4">
      <template v-if="!isCollapsed">
        <div class="new-session-section">
          <ElButton
            v-hasPerm="['module_ai:chat:create']"
            type="primary"
            class="new-session-btn"
            @click="handleNewSession"
          >
            <ElIcon class="btn-icon"><Plus /></ElIcon>
            <span>开启新对话</span>
          </ElButton>
        </div>

        <div class="history-section">
          <div class="search-section">
            <ElInput
              v-model="searchQuery"
              placeholder="搜索会话历史"
              :prefix-icon="Search"
              clearable
              @input="handleSearch"
            />
          </div>
          <div class="history-groups">
            <div v-for="group in groupedSessions" :key="group.title" class="history-group">
              <div class="group-title" @click="toggleGroup(group.title)">
                <span>{{ group.title }}</span>
                <ElIcon
                  class="collapse-icon"
                  :class="{ collapsed: collapsedGroups.has(group.title) }"
                >
                  <ArrowDown />
                </ElIcon>
              </div>
              <div v-show="!collapsedGroups.has(group.title)" class="session-list">
                <div
                  v-for="session in group.sessions"
                  :key="session.id"
                  class="session-item"
                  :class="{ active: currentSessionId === session.id }"
                  @click="handleSelectSession(session)"
                >
                  <ElIcon class="session-icon"><ChatLineRound /></ElIcon>
                  <span class="session-title">
                    {{ session.title || session.session_data?.session_name || "未命名会话" }}
                  </span>
                  <ElDropdown
                    trigger="click"
                    @command="(cmd) => handleSessionCommand(cmd, session)"
                  >
                    <ElIcon class="more-icon" @click.stop><MoreFilled /></ElIcon>
                    <template #dropdown>
                      <ElDropdownMenu>
                        <div v-hasPerm="['module_ai:chat:update']" style="display: contents">
                          <ElDropdownItem command="rename">重命名</ElDropdownItem>
                        </div>
                        <div v-hasPerm="['module_ai:chat:delete']" style="display: contents">
                          <ElDropdownItem command="delete" divided>删除</ElDropdownItem>
                        </div>
                      </ElDropdownMenu>
                    </template>
                  </ElDropdown>
                </div>
              </div>
            </div>
            <div v-if="filteredSessions.length === 0" class="empty-state">
              <ElEmpty description="暂无会话历史" :image-size="60" />
            </div>
          </div>
        </div>
      </template>
    </ElScrollbar>

    <div class="sidebar-footer">
      <div v-if="!isCollapsed" class="user-info">
        <ElAvatar :size="32" :src="userInfo.avatar">
          <ElIcon><User /></ElIcon>
        </ElAvatar>
        <div class="user-details">
          <div class="user-name">{{ userInfo.name }}</div>
          <div class="user-status">在线</div>
        </div>
        <ElDropdown trigger="click" @command="handleUserCommand">
          <ElIcon class="user-menu-icon"><Setting /></ElIcon>
          <template #dropdown>
            <ElDropdownMenu>
              <ElDropdownItem command="profile">个人中心</ElDropdownItem>
              <ElDropdownItem command="settings">设置</ElDropdownItem>
              <ElDropdownItem command="logout" divided>退出登录</ElDropdownItem>
            </ElDropdownMenu>
          </template>
        </ElDropdown>
      </div>
      <div v-else class="collapsed-user">
        <ElDropdown trigger="click" @command="handleUserCommand">
          <ElAvatar :size="32" :src="userInfo.avatar">
            <ElIcon><User /></ElIcon>
          </ElAvatar>
          <template #dropdown>
            <ElDropdownMenu>
              <ElDropdownItem command="profile">个人中心</ElDropdownItem>
              <ElDropdownItem command="settings">设置</ElDropdownItem>
              <ElDropdownItem command="logout" divided>退出登录</ElDropdownItem>
            </ElDropdownMenu>
          </template>
        </ElDropdown>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  ChatDotRound,
  ChatLineRound,
  User,
  Setting,
  MoreFilled,
  Plus,
  Search,
  ArrowDown,
} from "@element-plus/icons-vue";
import { useUserStoreHook } from "@stores";
import { ChatSession, SessionGroup, UserInfo } from "@/api/module_ai/chat";
import AiChatAPI from "@/api/module_ai/chat";

interface Props {
  currentSessionId?: string | null;
  isCollapsed?: boolean;
}

interface Emits {
  (e: "select-session", session: ChatSession): void;
  (e: "new-session"): void;
  (e: "open-config"): void;
}

const { currentSessionId, isCollapsed = false } = defineProps<Props>();
const emit = defineEmits<Emits>();

const router = useRouter();
const userStore = useUserStoreHook();

const sessions = ref<ChatSession[]>([]);
const searchQuery = ref("");
const collapsedGroups = ref<Set<string>>(new Set());

const userInfo = computed<UserInfo>(() => ({
  id: userStore.basicInfo.id || 0,
  name: userStore.basicInfo.name || "用户",
  username: userStore.basicInfo.username || "",
  avatar: userStore.basicInfo.avatar || "",
  email: userStore.basicInfo.email || "",
}));

const filteredSessions = computed<ChatSession[]>(() => {
  if (!searchQuery.value.trim()) {
    return sessions.value;
  }
  const query = searchQuery.value.toLowerCase();
  return sessions.value.filter((session: ChatSession) =>
    (session.title || "").toLowerCase().includes(query)
  );
});

const groupedSessions = computed<SessionGroup[]>(() => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayStart = today.getTime();
  const yesterdayStart = todayStart - 24 * 60 * 60 * 1000;
  const weekAgo = todayStart - 7 * 24 * 60 * 60 * 1000;

  const todaySessions: ChatSession[] = [];
  const yesterdaySessions: ChatSession[] = [];
  const weekSessions: ChatSession[] = [];
  const earlierSessions: ChatSession[] = [];

  filteredSessions.value.forEach((session) => {
    if (!session.updated_at) return;
    // Unix 时间戳（秒）转换为毫秒
    const updatedTime = session.updated_at * 1000;

    if (updatedTime >= todayStart) {
      todaySessions.push(session);
    } else if (updatedTime >= yesterdayStart) {
      yesterdaySessions.push(session);
    } else if (updatedTime >= weekAgo) {
      weekSessions.push(session);
    } else {
      earlierSessions.push(session);
    }
  });

  const groups: SessionGroup[] = [];

  if (todaySessions.length > 0) {
    groups.push({ id: "today", title: "今天", sessions: todaySessions });
  }

  if (yesterdaySessions.length > 0) {
    groups.push({ id: "yesterday", title: "昨天", sessions: yesterdaySessions });
  }

  if (weekSessions.length > 0) {
    groups.push({ id: "week", title: "本周", sessions: weekSessions });
  }

  if (earlierSessions.length > 0) {
    groups.push({ id: "earlier", title: "更早", sessions: earlierSessions });
  }

  return groups;
});

const handleSearch = () => {};

const toggleGroup = (groupTitle: string) => {
  const newCollapsed = new Set(collapsedGroups.value);
  if (newCollapsed.has(groupTitle)) {
    newCollapsed.delete(groupTitle);
  } else {
    newCollapsed.add(groupTitle);
  }
  collapsedGroups.value = newCollapsed;
};

const handleSelectSession = (session: ChatSession) => {
  emit("select-session", session);
};

const handleNewSession = () => {
  emit("new-session");
};

const handleSessionCommand = async (command: string, session: ChatSession) => {
  if (command === "rename") {
    try {
      const { value } = await ElMessageBox.prompt("请输入新的会话名称", "重命名", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        inputPattern: /.+/,
        inputErrorMessage: "会话名称不能为空",
      });
      await AiChatAPI.updateSession(session.id, { title: value });
      session.title = value;
    } catch (error) {
      if (error === "cancel") {
        ElMessage.info("已取消重命名");
      }
      // 非 cancel 的接口错误已由拦截器提示
    }
  } else if (command === "delete") {
    try {
      await confirmDelete(`确定删除「${session.title}」吗？`);
      await AiChatAPI.deleteSession([session.id]);
      const index = sessions.value.findIndex((s: ChatSession) => s.id === session.id);
      if (index > -1) {
        sessions.value.splice(index, 1);
      }
    } catch (error) {
      if (error === "cancel") {
        ElMessage.info("已取消删除");
      }
      // 非 cancel 的接口错误已由拦截器提示
    }
  }
};

const handleUserCommand = (command: string) => {
  if (command === "profile") {
    router.push("/fastlink/profile");
  } else if (command === "settings") {
    emit("open-config");
  } else if (command === "logout") {
    userStore.logout();
  }
};

const loadSessions = async () => {
  try {
    const res = await AiChatAPI.getSessionList({ page_no: 1, page_size: 100 });
    const responseData = res.data;
    const data = responseData?.data;

    if (data?.items && Array.isArray(data.items)) {
      sessions.value = data.items
        .filter((item: any) => item.session_id !== undefined)
        .map((item: any) => ({
          id: item.session_id,
          title: item.session_data?.session_name || item.session_id?.slice(0, 8) || "新会话",
          created_at: item.created_at,
          updated_at: item.updated_at,
          message_count: item.message_count ?? item.runs?.length ?? 0,
          session_id: item.session_id,
          session_type: item.session_type,
          agent_id: item.agent_id,
          user_id: item.user_id,
          team_id: item.team_id,
          team_name: item.team_name,
          workflow_id: item.workflow_id,
          summary: item.summary,
          metadata: item.metadata,
          runs: item.runs,
          session_data: item.session_data,
          agent_data: item.agent_data,
          team_data: item.team_data,
          workflow_data: item.workflow_data,
          created_time: item.created_at ? new Date(item.created_at * 1000).toISOString() : null,
          updated_time: item.updated_at ? new Date(item.updated_at * 1000).toISOString() : null,
          messages: item.messages || [],
        }));
    }
  } catch (error) {
    console.error("加载会话列表失败:", error);
  }
};

onMounted(() => {
  loadSessions();
});

defineExpose({
  loadSessions,
});
</script>

<style lang="scss" scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  border-right: 1px solid var(--el-border-color-light);
  transition: width 0.3s ease;

  .sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px;

    .logo-section {
      display: flex;
      gap: 12px;
      align-items: center;

      .logo-icon {
        color: var(--el-color-primary);
      }

      .project-name {
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
    }
  }

  .sidebar-content {
    flex: 1;

    .new-session-section {
      margin-bottom: 16px;

      .new-session-btn {
        display: flex;
        gap: 8px;
        align-items: center;
        justify-content: center;
        width: 100%;
        border-radius: 20px;
        transition: all 0.2s ease;

        .btn-icon {
          font-size: 16px;
        }

        &:hover {
          box-shadow: var(--el-box-shadow);
          transform: translateY(-1px);
        }

        &:active {
          transform: translateY(0);
        }
      }
    }

    .history-section {
      .search-section {
        margin-bottom: 16px;

        :deep(.el-input__wrapper) {
          border-radius: 20px;
          box-shadow: 0 0 0 1px var(--el-border-color) inset;
          transition: all 0.2s ease;

          &:hover {
            box-shadow: 0 0 0 1px var(--el-color-primary) inset;
          }

          &.is-focus {
            box-shadow: 0 0 0 1px var(--el-color-primary) inset;
          }
        }

        :deep(.el-input__inner) {
          font-size: 13px;
        }
      }

      .history-groups {
        .history-group {
          margin-bottom: 24px;

          &:last-child {
            margin-bottom: 0;
          }

          .group-title {
            display: flex;
            gap: 6px;
            align-items: center;
            justify-content: space-between;
            padding: 0 4px;
            margin-bottom: 10px;
            font-size: 12px;
            font-weight: 500;
            color: var(--el-text-color-secondary);
            cursor: pointer;
            user-select: none;
            transition: color 0.2s;

            &::before {
              width: 3px;
              height: 12px;
              content: "";
              background: var(--el-color-primary);
              border-radius: 2px;
            }

            &:hover {
              color: var(--el-text-color-primary);
            }

            .collapse-icon {
              font-size: 14px;
              transition: transform 0.2s ease;

              &.collapsed {
                transform: rotate(-90deg);
              }
            }
          }

          .session-list {
            .session-item {
              position: relative;
              display: flex;
              gap: 10px;
              align-items: center;
              padding: 4px;
              margin-bottom: 6px;
              cursor: pointer;
              border: 1px solid transparent;
              border-radius: 14px;
              transition: all 0.2s ease;

              &:hover {
                background: var(--el-fill-color-light);
                border-color: var(--el-border-color-light);
                transform: translateX(2px);
              }

              &.active {
                color: var(--el-color-primary);
                background: var(--el-color-primary-light-9);
                border-color: var(--el-border-color-light);
                box-shadow: none;
              }

              .session-icon {
                flex-shrink: 0;
                font-size: 18px;
                color: var(--el-text-color-secondary);
                transition: color 0.2s;
              }

              &.active .session-icon {
                color: var(--el-color-primary);
              }

              .session-title {
                flex: 1;
                overflow: hidden;
                text-overflow: ellipsis;
                font-size: 14px;
                font-weight: 400;
                white-space: nowrap;
                transition: font-weight 0.2s;
              }

              &.active .session-title {
                font-weight: 500;
              }

              .more-icon {
                flex-shrink: 0;
                padding: 4px;
                font-size: 16px;
                border-radius: 4px;
                opacity: 0;
                transition: all 0.2s;

                &:hover {
                  color: var(--el-color-primary);
                  background: var(--el-fill-color);
                }
              }

              &:hover .more-icon {
                opacity: 1;
              }
            }
          }
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          gap: 8px;
          align-items: center;
          justify-content: center;
          padding: 40px 20px;
          color: var(--el-text-color-secondary);
        }
      }
    }
  }

  .sidebar-footer {
    padding: 12px;
    border-top: 1px solid var(--el-border-color-light);

    .user-info {
      display: flex;
      gap: 12px;
      align-items: center;

      .user-details {
        flex: 1;
        overflow: hidden;

        .user-name {
          overflow: hidden;
          text-overflow: ellipsis;
          font-size: 14px;
          font-weight: 500;
          color: var(--el-text-color-primary);
          white-space: nowrap;
        }

        .user-status {
          font-size: 12px;
          color: var(--el-color-success);
        }
      }

      .user-menu-icon {
        font-size: 18px;
        color: var(--el-text-color-secondary);
        cursor: pointer;

        &:hover {
          color: var(--el-color-primary);
        }
      }
    }

    .collapsed-user {
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
}
</style>
