/**
 * 仪表盘首页模拟数据
 * 后续对接真实接口后只需替换此文件中的函数实现即可。
 */
import type { DashboardStats } from "@/api/module_monitor/dashboard";

export interface TimelineItem {
  time: string;
  status: string;
  content: string;
  code?: string;
}

export interface DataListItem {
  icon: string;
  class: string;
  title: string;
  status: string;
  time: string;
}

export interface HealthItem {
  icon: string;
  class: string;
  title: string;
  status: string;
  time: string;
}

export interface DashboardMock {
  stats: DashboardStats;
  timeline: TimelineItem[];
  dataList: DataListItem[];
  health: HealthItem[];
}

/** 返回仪表盘首页所需的全部模拟数据 */
export function getDashboardMock(): DashboardMock {
  return {
    stats: {
      online_users: 128,
      total_users: 3842,
      today_login_count: 47,
      today_unique_users: 89,
      week_user_created: 216,
      recent_logins: [
        {
          username: "admin",
          status: 1,
          login_time: "2026-07-17T09:30:00",
          login_ip: "192.168.1.100",
          login_location: "北京",
        },
        {
          username: "张伟",
          status: 1,
          login_time: "2026-07-17T09:28:00",
          login_ip: "10.0.0.52",
          login_location: "上海",
        },
        {
          username: "李娜",
          status: 2,
          login_time: "2026-07-17T09:25:00",
          login_ip: "172.16.0.18",
          login_location: "广州",
        },
        {
          username: "王磊",
          status: 1,
          login_time: "2026-07-17T09:20:00",
          login_ip: "192.168.2.88",
          login_location: "深圳",
        },
        {
          username: "赵敏",
          status: 1,
          login_time: "2026-07-17T09:15:00",
          login_ip: "10.10.10.5",
          login_location: "杭州",
        },
        {
          username: "陈强",
          status: 2,
          login_time: "2026-07-17T09:10:00",
          login_ip: "203.0.113.42",
          login_location: "成都",
        },
      ],
    },
    timeline: [
      {
        time: "上午 09:30",
        status: "rgb(73, 190, 255)",
        content: "收到 John Doe 支付的 385.90 美元",
      },
      { time: "上午 10:00", status: "rgb(54, 158, 255)", content: "新销售记录", code: "ML-3467" },
      { time: "上午 12:00", status: "rgb(103, 232, 207)", content: "向 Michael 支付了 64.95 美元" },
      { time: "下午 14:30", status: "rgb(255, 193, 7)", content: "系统维护通知", code: "MT-2023" },
      {
        time: "下午 15:45",
        status: "rgb(255, 105, 105)",
        content: "紧急订单取消提醒",
        code: "OR-9876",
      },
      { time: "下午 17:00", status: "rgb(103, 232, 207)", content: "完成每日销售报表" },
      { time: "上午 09:30", status: "rgb(73, 190, 255)", content: "收到订单 #38291 支付 ¥385.90" },
      { time: "上午 10:00", status: "rgb(54, 158, 255)", content: "新商品上架", code: "SKU-3467" },
      { time: "上午 12:00", status: "rgb(103, 232, 207)", content: "向供应商支付了 ¥6495.00" },
      {
        time: "下午 14:30",
        status: "rgb(255, 193, 7)",
        content: "促销活动开始",
        code: "PROMO-2023",
      },
      {
        time: "下午 15:45",
        status: "rgb(255, 105, 105)",
        content: "订单取消提醒",
        code: "ORD-9876",
      },
      { time: "下午 17:00", status: "rgb(103, 232, 207)", content: "完成日销售报表" },
    ],
    dataList: [
      {
        icon: "ri:camera-4-line",
        class: "bg-theme/12 text-theme",
        title: "新加坡之行",
        status: "进行中",
        time: "5分钟",
      },
      {
        icon: "ri:bar-chart-box-line",
        class: "bg-secondary/12 text-secondary",
        title: "归档数据",
        status: "进行中",
        time: "10分钟",
      },
      {
        icon: "ri:user-3-line",
        class: "bg-warning/12 text-warning",
        title: "客户会议",
        status: "待处理",
        time: "15分钟",
      },
      {
        icon: "ri:account-circle-line",
        class: "bg-error/12 text-error",
        title: "筛选任务团队",
        status: "进行中",
        time: "20分钟",
      },
      {
        icon: "ri:message-3-line",
        class: "bg-success/12 text-success",
        title: "发送信封给小王",
        status: "已完成",
        time: "20分钟",
      },
      {
        icon: "ri:account-circle-line",
        class: "bg-error/12 text-error",
        title: "筛选任务团队",
        status: "进行中",
        time: "20分钟",
      },
    ],
    health: [
      {
        icon: "ri:database-2-line",
        class: "bg-success/12 text-success",
        title: "数据库",
        status: "正常",
        time: "",
      },
      {
        icon: "ri:server-line",
        class: "bg-success/12 text-success",
        title: "Redis",
        status: "正常",
        time: "",
      },
    ],
  };
}
