---
layout: doc
outline: "deep"
title: 部署指南
description: FastApiAdmin 多种部署方式详解:Docker Compose 一键部署、生产环境 Nginx + SSL 配置、CI/CD 自动化、多节点架构与性能调优。
---

## 部署方式概述

FastApiAdmin 支持以下部署方式：

- **Docker Compose 部署**（推荐）：快速、便捷、可移植
- **手动部署**：适用于需要高度定制的场景
- **云服务部署**：可部署到阿里云、腾讯云等

## 🐳 Docker Compose 部署（推荐）

> 详细说明见项目根目录 [docker/README.md](https://github.com/fastapiadmin/FastapiAdmin/blob/master/docker/README.md)。

### 1. 环境准备

- Docker ≥ 20.10
- Docker Compose v2
- 确保服务器开放 80、443 端口

### 2. 安装 Docker

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install docker.io docker-compose -y

# CentOS / RHEL
sudo yum install docker docker-compose -y

# 启动并开机自启
sudo systemctl start docker && sudo systemctl enable docker
```

### 3. 部署步骤

```bash
git clone https://github.com/fastapiadmin/FastApiAdmin.git
cd FastApiAdmin

# 配置环境变量
cp docker/.env.example docker/.env
# 编辑 docker/.env，填写数据库密码、Redis 密码等

# 一键部署
chmod +x deploy.sh
./deploy.sh
```

### 4. 部署后配置

#### SSL 证书

```bash
# 测试用自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/nginx/ssl/server.key \
  -out docker/nginx/ssl/server.pem \
  -subj "/CN=your-domain.com"

# 生产环境使用 Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
# 将证书复制到 docker/nginx/ssl/ 目录
```

#### 域名配置

在域名注册商添加 A 记录，指向服务器 IP。

### 5. 服务管理

| 命令 | 说明 |
|------|------|
| `./deploy.sh` | 完整部署 |
| `./deploy.sh logs` | 查看日志 |
| `./deploy.sh stop` | 停止服务 |
| `./deploy.sh restart` | 重启服务 |

### 6. 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | `https://域名/web` |
| API 文档 | `https://域名/api/v1/docs` |

## 📦 手动部署

### 后端部署

```bash
# 依赖安装
cd FastapiAdmin/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 配置环境
cp env/.env.example env/.env.prod
# 编辑 env/.env.prod

# 启动（使用 Gunicorn + Uvicorn）
pip install gunicorn uvloop
gunicorn -w 4 -k uvicorn.workers.UvicornWorker 'app.init_app:create_app()' --bind 0.0.0.0:8001 --daemon
```

### 前端部署

```bash
cd FastapiAdmin/frontend/web
pnpm install && pnpm run build
# 将 dist/ 目录部署到 Nginx 或其他 Web 服务器
```

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location /web {
        root /path/to/FastapiAdmin/frontend/web;
        index index.html;
        try_files $uri $uri/ /web/index.html;
    }

    # 后端 API
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 📱 移动端部署

### H5 部署

```bash
cd FastapiAdmin/frontend/app
pnpm install && pnpm run build:h5
# 将 dist/build/h5 目录部署到 Nginx

# Nginx 配置片段
location /app {
    alias /path/to/FastapiAdmin/frontend/app/dist/build/h5;
    index index.html;
    try_files $uri $uri/ /app/index.html;
}
```

### 小程序部署

```bash
# 构建微信小程序
pnpm run build:mp-weixin
# 在微信开发者工具中导入 dist/build/mp-weixin 目录
# 上传并提交审核
```

## 🔧 常见部署问题

| 问题 | 解决方案 |
|------|----------|
| Docker 容器启动失败 | `cd docker && docker compose logs [服务名]` |
| 环境变量文件不存在 | `cp docker/.env.example docker/.env` |
| 数据库连接失败 | 确保 `.env` 中密码正确，MySQL 容器正常运行 |
| Nginx 502 Bad Gateway | 检查后端服务是否启动，端口是否正确 |
| SSL 证书错误 | 检查证书路径和有效期 |
| 端口冲突 | 修改 `.env` 中端口配置 |
