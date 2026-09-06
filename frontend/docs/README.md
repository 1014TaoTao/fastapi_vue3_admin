# FastapiAdmin 文档工程

FastapiAdmin 官网文档工程，基于 [VitePress](https://vitepress.dev/) 构建。

> **与仓库根文档的关系**：项目总览、一键前后端启动、演示账号、Docker 部署等请以 [根目录 README.md](../../README.md) 为准；**本文档**侧重 `frontend/docs/` 文档工程的开发与维护。

## 项目结构

```sh
frontend/docs/
├── .vitepress/              # VitePress 配置
│   ├── cache/               # 构建缓存（自动生成）
│   ├── components/          # 首页营销组件（HomeSections / StickyCta 等）
│   ├── composables/         # 组合式函数（滚动显现、CTA 显隐）
│   ├── theme/               # 自定义主题
│   │   ├── Layout.vue       # 布局组件
│   │   ├── index.ts         # 主题入口
│   │   ├── setup.ts         # 主题增强逻辑
│   │   └── styles/          # 样式（tokens / base / dark / print 等）
│   └── config.mts           # 主配置文件（导航、侧边栏、多语言）
├── src/                     # 文档源文件
│   ├── guide/               # 指南
│   │   ├── overview.md      # 项目概述
│   │   ├── start.md         # 快速开始
│   │   ├── why.md           # 为什么选择 FastapiAdmin
│   │   ├── frontend.md      # 前端开发
│   │   ├── backend.md       # 后端开发
│   │   ├── miniprogram.md   # 移动端开发
│   │   ├── guidelines.md    # 开发规范
│   │   ├── changelog.md     # 更新日志
│   │   └── deployment.md    # 部署指南
│   ├── about/               # 关于
│   │   └── about.md         # 关于我们
│   ├── data/                # 文档用数据（changelog.ts）
│   ├── en/                  # 英文文档（结构同中文）
│   ├── public/              # 静态资源（logo、showcase 截图等）
│   ├── 404.md               # 404 页面
│   ├── env.d.ts             # 环境类型声明
│   └── index.md             # 根首页
├── package.json             # 项目依赖文件
└── pnpm-lock.yaml           # pnpm 锁定文件
```

## 快速开始

```bash
cd frontend/docs
pnpm install
pnpm run dev          # 运行文档工程（默认 http://127.0.0.1:5173）
pnpm run build        # 构建文档工程
```

构建产物在 `dist/` 下，可部署到 Nginx 等静态服务器。

## 在线文档

- 🌐 [https://service.fastapiadmin.com/](https://service.fastapiadmin.com/)

## 文档编写规范

- 文档使用 Markdown 编写，放在 `src/guide/` 或 `src/about/` 对应目录下
- 英文文档放在 `src/en/` 下，结构与中文一致
- 图片等静态资源放在 `src/public/` 下
- 修改导航/侧边栏需编辑 `.vitepress/config.mts`
