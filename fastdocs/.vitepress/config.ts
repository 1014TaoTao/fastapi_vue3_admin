import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  base: '/',
  srcDir: 'src',
  outDir: 'dist',
  lang: 'zh-CN',
  title: 'Fastapi Vue3 Admin',
  description: '现代、开源、全栈融合的中后台快速开发平台',
  head: [
    [
      "link",
      {
        rel: "apple-touch-icon",
        sizes: "180x180",
        href: "/favicon.png",
      },
    ],
    [
      "link",
      {
        rel: "icon",
        type: "image/png",
        sizes: "32x32",
        href: "/favicon.png",
      },
    ],
    [
      "link",
      {
        rel: "icon",
        type: "image/png",
        sizes: "16x16",
        href: "/favicon.png",
      },
    ],
    ["link", { rel: "shortcut icon", href: "/favicon.png" }],
  ],
  
  locales: {
    root: { label: '简体中文' },
    en: { label: 'English' },
  },
  lastUpdated: true,
  cleanUrls: true,
  metaChunk: true,
  themeConfig: {
    logo: '/logo.png',
    siteTitle: 'Fastapi Vue3 Admin',
    nav: [
      { text: '首页', link: '/' },
      { text: '指南', link: '/guide_info' },
      { text: '演示环境', link: 'https://service.fastapiadmin.com/web', target: '_blank' },
      { text: '小程序环境', link: 'https://service.fastapiadmin.com/app', target: '_blank' },
      {
        text: '版本',
        items: [
          { text: 'master', link: 'https://github.com/1014TaoTao/fastapi_vue3_admin', target: '_blank' },
          { text: 'V2.0.0', link: 'https://github.com/1014TaoTao/fastapi_vue3_admin/tree/v2.0.0', target: '_blank' },
          { text: 'V1.0.0', link: 'https://github.com/1014TaoTao/fastapi_vue3_admin/tree/v1.0.0', target: '_blank' }
        ]
      },
      { text: '更新日志', link: 'https://github.com/1014TaoTao/fastapi_vue3_admin/commits/master/', target: '_blank' },
      {
        text: '社区',
        items: [
          { text: 'GitHub', link: 'https://github.com/1014TaoTao/fastapi_vue3_admin', target: '_blank' },
          { text: 'Gitee', link: 'https://gitee.com/tao__tao/fastapi_vue3_admin', target: '_blank' },
          { text: 'GitCode', link: 'https://gitcode.com/qq_36002987/fastapi_vue3_admin', target: '_blank' }
        ]
      },
      { text: '关于我们', link: '/about' },
    ],

    sidebar: [
      {
        text: '简介',
        collapsible: true,  // 开启折叠功能
        collapsed: false,   // 默认不折叠（展开状态）
        items: [
          { text: '项目介绍', link: '/guide_info' },
          { text: '快速开始', link: '/guide_start' }
        ]
      },
      {
        text: '关于我们', link: '/about'
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/1014TaoTao/fastapi_vue3_admin' },
      { icon: 'gitee', link: 'https://gitee.com/tao__tao/fastapi_vue3_admin' },
      { icon: 'gitcode', link: 'https://gitcode.com/qq_36002987/fastapi_vue3_admin' }
    ],

    footer: {
      message: '<a href="https://github.com/1014TaoTao/fastapi_vue3_admin/blob/master/LICENSE" target="_blank">MIT License</a>',
      copyright: 'Copyright © 2025-2026 service.fastapiadmin.com 版权所有 |隐私 |条款 陕ICP备2025069493号-1'
    },

    docFooter: {
      prev: "上一页",
      next: "下一页",
    },

    search: {
      provider: 'local',
      options: {
        locales: {
          root: {
            translations: {
              button: {
                buttonText: '搜索文档',
                buttonAriaLabel: '搜索文档'
              },
              modal: {
                footer: {
                  selectText: '选择',
                  navigateText: '切换',
                  closeText: '关闭',
                },
              },
            },
          },
        },
      },
    },
    outline: {
      level: [2, 3],
      label: "页面导航",
    },

    lastUpdated: {
      text: "最后更新于",
      formatOptions: {
        dateStyle: "short", // full
        timeStyle: "short", // medium
      },
    },

    langMenuLabel: "多语言",
    returnToTopLabel: "回到顶部",
    sidebarMenuLabel: "菜单",
    darkModeSwitchLabel: "主题",
    lightModeSwitchTitle: "切换到浅色模式",
    darkModeSwitchTitle: "切换到深色模式",
  }
})
