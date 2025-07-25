<!-- 顶部通知公告 -->
<template>
  <el-dropdown trigger="click">
    <el-badge v-if="noticeList.length > 0" :value="noticeList.length" :max="99">
      <div class="i-svg:bell" />
    </el-badge>

    <div v-else class="i-svg:bell" />

    <template #dropdown>
      <div class="p-5">
        <template v-if="noticeList.length > 0">
          <div v-for="(item, index) in noticeList" :key="index" class="w-400px py-3">
            <div class="flex-y-center">
              <el-tag :type="item.notice_type === '1' ? 'primary' : 'warning'">
                {{ item.notice_type === '1' ? '通知' : '公告' }}
              </el-tag>

              <!-- truncated: 超出部分省略 -->
              <el-text size="small" class="w-200px cursor-pointer !ml-2 !flex-1" truncated > 
                {{ item.notice_content }}
              </el-text>

              <!-- 时间 -->
              <div class="text-xs text-gray">
                {{ item.created_at }}
              </div>
            </div>
          </div>
          <el-divider />
          
          <div class="flex-x-between">
            <el-link type="primary" underline="never" @click="handleViewMoreNotice">
              <span class="text-xs">查看更多</span>
              <el-icon class="text-xs">
                <ArrowRight />
              </el-icon>
            </el-link>
            <el-link v-if="noticeList.length > 0" type="primary" underline="never" @click="handleMarkAllAsRead">
              <span class="text-xs">全部已读</span>
            </el-link>
          </div>
        </template>
        <template v-else>
          <div class="flex-center h-150px w-350px">
            <el-empty :image-size="50" description="暂无消息" />
          </div>
        </template>
      </div>
    </template>
  </el-dropdown>

  <el-dialog v-model="noticeDialogVisible" :title="noticeDetail?.notice_title ?? '通知详情'" width="800px" custom-class="notification-detail">
    <div v-if="noticeDetail" class="p-x-20px">
      <div class="flex-y-center mb-16px text-13px text-color-secondary">
        <span class="flex-y-center">
          <el-icon>
            <User />
          </el-icon>
          {{ noticeDetail.creator?.username }}
        </span>
        <span class="ml-2 flex-y-center">
          <el-icon>
            <Timer />
          </el-icon>
          {{ noticeDetail.created_at }}
        </span>
      </div>

      <div class="max-h-60vh pt-16px mb-24px overflow-y-auto border-t border-solid border-color">
        <div v-html="noticeDetail.notice_content"></div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import NoticeAPI, { NoticeTable } from "@/api/system/notice";
import router from "@/router";
import { useNoticeStore } from "@/store";

const noticeStore = useNoticeStore();

const noticeList = ref<NoticeTable[]>([]);
const noticeDialogVisible = ref(false);
const noticeDetail = ref<NoticeTable | null>(null);

/**
 * 获取我的通知公告
 */
async function featchMyNotice() {
  await noticeStore.getNotice()
  noticeList.value = noticeStore.noticeList;
}

// 查看更多
function handleViewMoreNotice() {
  router.push({ name: "Notice" });
}

// 全部已读
function handleMarkAllAsRead() {
  NoticeAPI.batchAvailableNotice({
    ids: noticeList.value.map((item) => item.id).filter((id): id is number => id !== undefined),
    status: true
  }).then(() => {
    noticeList.value = [];
  });
}

onMounted(() => {
  featchMyNotice();
});


</script>

<style lang="scss" scoped></style>
