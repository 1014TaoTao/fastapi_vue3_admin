---
layout: home
editLink: true
lastUpdated: true

hero:
  name: "FastApiAdmin"
  text: "Web · H5 · 小程序,一套全栈"
  tagline: 基于 FastAPI + Vue3 + TypeScript,前后端类型共享。200+ REST 接口开箱即用,AI 代码生成器选表即出全栈 CRUD,Docker Compose 一条命令上线。
  image:
    src: /logo.svg
    alt: AI 代码生成器 - 选表即生成完整 CRUD
  actions:
    - theme: brand
      text: 立即开始
      link: /guide/start
    - theme: alt
      text: 在线预览
      link: https://service.fastapiadmin.com/web
      target: _blank
    - theme: alt
      text: 移动端
      link: https://service.fastapiadmin.com/app
      target: _blank

features:
  - icon: 📦
    title: 全栈开箱即用
    details: 前后端 + 移动端完整交付。FastAPI 异步后端 + Vue3 Web + UniApp 移动端，克隆即跑，零额外配置。

  - icon: ⚡
    title: 高性能异步架构
    details: FastAPI 原生 async/await 支持，Pydantic 自动类型校验，Redis 缓存加速，轻松应对高并发场景。

  - icon: 🤖
    title: AI 代码生成器
    details: 选数据库表 → AI 自动生成 Controller / Service / Model / Vue 页面代码。常规 CRUD 几乎不用手写，团队聚焦业务逻辑。

  - icon: 🛡️
    title: 企业级 RBAC 权限
    details: JWT + OAuth2 认证，菜单 / 按钮 / 数据三级粒度权限控制，操作日志全审计。

  - icon: 🐳
    title: Docker 一键部署
    details: Docker Compose 编排全栈服务（含 Nginx + SSL），一条命令上线。支持多环境配置管理。

  - icon: 📱
    title: Web + 移动端一体
    details: 基于 UniApp 的移动端，一套代码同时生成 H5、微信小程序、支付宝小程序、App 等多端应用。
---

<script setup lang="ts">
import HomeSections from "../.vitepress/components/HomeSections.vue";
</script>

<HomeSections />
