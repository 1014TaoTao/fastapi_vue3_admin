---
layout: doc
title: 为什么选择 FastApiAdmin？
description: 为什么选择 FastApiAdmin?与其他中后台方案对比分析:异步后端、全栈融合、代码生成、多端统一、模块化设计与活跃社区。
outline: "deep"
---

如果你正在寻找一套快速开发平台来搭建中后台系统，以下是 FastApiAdmin 与其他方案的核心差异。

## 与其他方案对比

| 维度 | FastApiAdmin | Django Admin / Flask-Admin | 纯前端模板（vue-pure-admin 等） |
|------|-------------|---------------------------|-------------------------------|
| **后端** | FastAPI 异步，Pydantic 类型安全 | Django/Flask 同步为主 | 无，需自行搭建 |
| **前端** | Vue3 + TypeScript + Element Plus，开箱即用 | Jinja 模板渲染 | Vue3 + Element Plus |
| **移动端** | UniApp 多端（H5/小程序/App）一体 | 无 | 无 |
| **代码生成** | 内置，数据库表 → 前后端 CRUD | 需额外插件 | 无 |
| **部署** | Docker Compose 一键，含 Nginx + SSL | 需自行配置 | 需自行配置 |
| **架构** | 按业务域竖切分包，插件自动注册 | 按层分包为主 | 按层分包 |
| **数据库** | MySQL / PostgreSQL / SQLite，Alembic 迁移 | Django ORM 迁移 | 无 |

## 技术选型依据

### 为什么是 FastAPI 而不是 Django/Flask？

| 特性 | FastAPI | Django | Flask |
|------|---------|--------|-------|
| 异步原生支持 | ✅ 内置 async/await | ⚠️ 3.1+ 部分支持 | ❌ 需扩展 |
| 自动 API 文档 | ✅ Swagger + Redoc 自动生成 | ❌ 需 drf-spectacular | ❌ 需插件 |
| 类型安全 | ✅ Pydantic 请求/响应验证 | ❌ 运行时校验 | ❌ 无内置 |
| 性能基准 | ~30k req/s | ~10k req/s | ~15k req/s |
| 学习曲线 | 中等 | 陡峭 | 平缓 |

FastAPI 的 **自动类型校验 + 自动文档 + 异步性能** 是组合优势，不需要在速度和开发体验之间做取舍。

### 为什么是 Vue3 而不是 React？

| 特性 | Vue3 | React |
|------|------|-------|
| 上手难度 | 低（模板 + Options/Composition） | 中（JSX + Hooks 心智模型） |
| 官方生态 | Router、Pinia、Vite 一体化 | 第三方选型碎片化 |
| TypeScript | Composition API 天然支持 | 支持良好 |
| 中文社区 | 非常活跃 | 活跃 |

对于中后台场景，Vue3 + Element Plus 的组合在开发效率和组件完整性上更有优势。

### 为什么按「业务域」分包？

```
# 按业务域竖切（本项目）
modules/system/user/            # 用户相关的代码全在这个目录
├── controller.py
├── service.py
├── crud.py
├── model.py
└── schema.py

# 按技术层分包（常见方案）
models/user.py                  # 用户模型在这
schemas/user.py                 # 用户 Schema 在另一个目录
services/user.py                # 用户逻辑又在另一个目录
```

| 场景 | 竖切（本项目） | 按层分包 |
|------|-------------|---------|
| 多人协作（不同人负责不同模块） | ✅ 各自目录独立，零冲突 | ❌ 改同一个 model.py |
| 拆分子仓库/独立部署 | ✅ 整个目录搬走 | ❌ 跨多个目录抽取 |
| 跨模块查看所有 model | ❌ 需 IDE 搜索 | ✅ 一个 models/ 目录看全 |

项目选择竖切，核心考量是**优先团队并行开发和解耦**。查看全量表结构可用 IDE/Alembic/数据库工具。

## 内置功能：你不需要从零写的部分

FastApiAdmin 开箱自带这些，而纯前端模板或裸框架**没有**：

| 功能 | FastApiAdmin | Django Admin | 纯前端模板 |
|------|:-----------:|:-----------:|:---------:|
| RBAC 权限（菜单/按钮/数据级） | ✅ | ⚠️ 基础 | ❌ |
| 代码生成器（表→CRUD） | ✅ | ❌ | ❌ |
| 服务监控 + 缓存监控 | ✅ | ❌ | ❌ |
| 操作日志审计 | ✅ | ✅ | ❌ |
| 定时任务管理 | ✅ | ❌ | ❌ |
| WebSocket 实时推送 | ✅ | ❌ | ❌ |
| 移动端（H5/小程序） | ✅ | ❌ | ❌ |

## 总结

如果你的需求是：
- ✅ Python 技术栈，想用 FastAPI 的异步性能
- ✅ 前端团队熟悉 Vue3，需要开箱即用的后台模板
- ✅ 需要移动端（H5/小程序）支持
- ✅ 不想从零搭建 RBAC、日志、监控等基础功能
- ✅ 多人协作，需要模块间低耦合

那么 FastApiAdmin 是这个场景下**效率最高的选择**。

## 下一步

如果你已经决定要试一下,按这条路径走最顺:

| 顺序 | 文档 | 预计时间 | 目的 |
|:---:|------|:-------:|------|
| 1 | [快速开始](/guide/start) | 10 min | 本地跑起来,看到登录页和仪表盘 |
| 2 | [后端开发指南](/guide/backend) | 15 min | 第一次添加一个业务模块 |
| 3 | [前端开发指南](/guide/frontend) | 15 min | 第一次添加一个页面 |
| 4 | [部署指南](/guide/deployment) | 20 min | 从本地推到生产环境 |

或者直接 [克隆仓库](https://gitee.com/fastapiadmin/FastApiAdmin) 边看代码边查文档。

::: tip 遇到问题?
[常见问题](/guide/why#常见问题)  ·  [GitHub Issues](https://github.com/fastapiadmin/FastapiAdmin/issues)  ·  [Gitee 问答](https://gitee.com/fastapiadmin/FastapiAdmin/issues)
:::
