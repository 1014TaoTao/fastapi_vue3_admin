---
outline: "deep"
---

<div style="text-align: center;">
  <div align="center">
     <img src="/logo.png" width="150" height="150" alt="logo" />
  </div>
  <h1>Fastapi-Vue3-Admin <sup style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.4em; vertical-align: super; margin-left: 5px;">v2.0.0</sup></h1>
  <h3>一套现代、开源、全栈融合的中后台快速开发平台</h3>
  <p>如果你喜欢这个项目，给个 ⭐️ 支持一下吧！</p>
  <p align="center" style="display: flex; justify-content: center; align-items: center; margin-top: 10px;">
    <a href="https://gitee.com/tao__tao/fastapi_vue3_admin"><img src="https://gitee.com/tao__tao/fastapi_vue3_admin/badge/star.svg?theme=dark" alt="Gitee Stars"></a>
    <a href="https://github.com/1014TaoTao/fastapi_vue3_admin"><img src="https://img.shields.io/github/stars/1014TaoTao/fastapi_vue3_admin?style=social" alt="GitHub Stars"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-orange.svg" alt="License"></a>
    <img src="https://img.shields.io/badge/Python-≥3.10-blue" alt="Python">
    <img src="https://img.shields.io/badge/NodeJS-≥20.0-blue" alt="NodeJS">
    <img src="https://img.shields.io/badge/MySQL-≥8.0-blue" alt="MySQL">
    <img src="https://img.shields.io/badge/Redis-≥7.0-blue" alt="Redis">
  </p>
</div>

## 📘项目介绍

**Fastapi-Vue3-Admin** 是一套 **完全开源、高度模块化、技术先进的现代化快速开发平台**，旨在帮助开发者高效搭建高质量的企业级中后台系统。该项目采用 **前后端分离架构**，融合 Python 后端框架 `FastAPI` 和前端主流框架 `Vue3` 实现多端统一开发，提供了一站式开箱即用的开发体验。

> **设计初心**: 以模块化、松耦合为核心，追求丰富的功能模块、简洁易用的接口、详尽的开发文档和便捷的维护方式。通过统一框架和组件，降低技术选型成本，遵循开发规范和设计模式，构建强大的代码分层模型，搭配完善的本地中文化支持，专为团队和企业开发场景量身定制。

## 📦工程结构概览
```sh
fastapi_vue3_admin
├─ backend        # 后端工程
├─ frontend       # 前端工程
├─ devops         # 部署工程
├─ docker-compose.yaml # 部署文件
├─ start.sh       # 一键部署脚本
├─ LICENSE        # 许可协议
|─ README.en.md   # 英文文档
└─ README.md      # 中文文档
```

## ✨核心亮点

| 特性 | 描述 |
| ---- | ---- |
| 🔭 快速开发 |一套完全开源的现代化快速开发平台，旨在帮助开发者高效搭建高质量的中后台系统。|
| 🌐 全栈整合 | 前后端分离，融合 Python (FastAPI) + Vue3 多端开发 |
| 🧱 模块化设计 | 系统功能高度解耦，便于扩展和维护 |
| ⚡️ 高性能异步 | 使用 FastAPI 异步框架 + Redis 缓存优化接口响应速度 |
| 🔒 安全认证 | 支持 JWT OAuth2 认证机制，保障系统安全 |
| 📊 权限管理 | RBAC 模型实现菜单、按钮、数据级别的细粒度权限控制 |
| 🚀 快速部署 | 支持 Docker/Docker Compose/Nginx 一键部署 |
| 📄 开发友好 | 提供完善的中文文档 + 中文化界面 + 可视化工具链，降低学习成本 |
| 🧩 快速接入 |基于 Vue3、Vite5、Pinia、ElementPlus 等主流前端技术栈，开箱即用。|

## 🛠️技术栈概览

| 类型     | 技术选型            | 描述 |
|----------|---------------------|---------------------|
| 后端框架 | FastAPI / Uvicorn / Pydantic 2.0 / Alembic | 现代、高性能的异步框架，强制类型约束，数据迁移。 |
| ORM      | SQLAlchemy 2.0      | 强大的 ORM 库。 |
| 定时任务 | APScheduler         | 轻松实现定时任务。 |
| 权限认证 | PyJWT               | 实现 JWT 认证。 |
| 前端框架 | Vue3 / Vite5 / Pinia / TypeScript | 快速开发 Vue3 应用。 |
| UI 库    | ElementPlus | 快速开发美观的 UI 组件。 |
| 数据库   | MySQL / MongoDB     | 强大的数据库。 |
| 缓存     | Redis               | 强大的缓存数据库。 |
| 文档     | Swagger / Redoc     | 自动生成 API 文档。 |
| 部署     | Docker / Nginx / Docker Compose | 快速部署项目。 |

## 📌内置模块

| 模块名     | 子模块名 | 描述 |
|----------|---------------------|---------------------|
| 仪表盘    | 工作台 、分析页  |常用功能入口 |
| 系统管理  | 包含菜单、部门、岗位、角色、用户、日志、配置、公告、字典、任务等子模块|系统主功能 |
| 监控管理  | 在线用户、服务器监控、缓存监控 |系统监控管理功能 |
| 公共管理  | 接口管理、文档管理|项目接口文档 |