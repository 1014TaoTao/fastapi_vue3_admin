---
layout: doc
outline: "deep"
title: 快速开始
description: "15-30 分钟跑通一个可演示的 MVP:环境准备、代码拉取、Docker Compose 一键启动、初始化数据、本地访问 Web 端与 App 端,常见问题排查。"
---

## 🍪 演示环境

- 官网：[https://service.fastapiadmin.com](https://service.fastapiadmin.com)
- Web 端：[https://service.fastapiadmin.com/web](https://service.fastapiadmin.com/web)
- 移动端：[https://service.fastapiadmin.com/app](https://service.fastapiadmin.com/app)
- 演示账号：`admin` / `123456`（**仅限官方演示站使用，请勿用于生产环境**；首次部署后请立即修改默认密码）

## 环境准备

| 类型 | 技术栈 | 版本 |
|------|--------|------|
| 后端 | Python | ≥ 3.10（推荐 3.12） |
| 后端 | FastAPI | 0.109+ |
| 前端 | Node.js | ≥ 20.0 |
| 前端 | pnpm | ≥ 9.0 |
| Web UI | Element Plus | 2.10+ |
| 移动端 | UniApp | 3.0+ |
| App UI | Wot Design Uni | 1.9+ |
| 数据库 | MySQL | 8.0+ / PostgreSQL 13+ / SQLite |
| 中间件 | Redis | 7.0+ |

## 获取代码

```bash
git clone https://github.com/fastapiadmin/FastApiAdmin.git
# 或使用 Gitee
git clone https://gitee.com/fastapiadmin/FastApiAdmin.git
```

## 后端启动

### 1. 配置环境变量

```bash
cd FastapiAdmin/backend
cp env/.env.example env/.env.dev
# 编辑 env/.env.dev，填写数据库连接、Redis、JWT 密钥等
```

### 2. 安装依赖并启动

```bash
# 推荐使用 uv（与 pyproject.toml 一致）
uv sync
uv run main.py run --env=dev

# 或使用传统 pip / venv
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py run --env=dev
```

**首次启动会自动初始化数据库表与基础数据**，一般无需先执行 `upgrade`。

### 3. 数据库迁移（模型变更时使用）

```bash
python main.py revision --env=dev
python main.py upgrade --env=dev

# 或使用 uv
uv run main.py revision --env=dev
uv run main.py upgrade --env=dev
```

## 前端启动

```bash
# Web 前端 (Vue3)
cd FastapiAdmin/frontend/web
pnpm install
pnpm run dev

# 移动端 (UniApp)
cd FastapiAdmin/frontend/app
pnpm install
pnpm run dev:h5

# 文档网站 (VitePress)
cd FastapiAdmin/frontend/docs
pnpm install
pnpm run dev
```

## 本地访问地址

| 服务 | 地址 |
|------|------|
| Web 前端 | `http://127.0.0.1:5173` |
| 移动端 H5 | `http://127.0.0.1:8080` |
| 文档网站 | `http://127.0.0.1:5174` |
| 后端 API | `http://127.0.0.1:8001` |
| Swagger | `http://127.0.0.1:8001/docs` |
| API 前缀 | `http://127.0.0.1:8001/api/v1` |

## 🐳 Docker 部署

详见 [部署指南](./deployment)，快速命令：

```bash
chmod +x deploy.sh
./deploy.sh              # 完整部署
./deploy.sh logs         # 查看日志
./deploy.sh stop         # 停止
./deploy.sh restart      # 重启
```

## 💡 常见问题

| 问题 | 解答 |
|------|------|
| 后端启动报数据库连接失败 | 确保已创建空数据库，`.env.dev` 中连接信息正确 |
| 前端请求后端报 CORS 错误 | 确认后端已启动，`.env.development` 中 `VITE_API_BASE_URL` 正确 |
| 首次启动需要执行迁移吗 | **不需要**——后端首次启动自动初始化表与数据 |
| Node.js 版本不符 | 使用 nvm 安装对应版本：`nvm install 20` |
