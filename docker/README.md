# FastapiAdmin 部署说明

> **与仓库根文档的关系**：项目总览、快速开始、演示账号等请以 [根目录 README.md](../README.md) 为准；**本文档**侧重 Docker 部署的详细操作。

## 项目结构

```
docker/
├── backend/                # 后端服务配置
│   └── Dockerfile          # 后端 Dockerfile（依赖安装 + 代码复制，配合根 .dockerignore）
├── nginx/                  # Nginx 配置
│   ├── nginx.conf          # Nginx 配置文件
│   ├── ssl/                # SSL 证书目录（放置 server.key / server.pem，.gitignore 已排除）
│   ├── web/                # 前端静态文件（构建后自动放置 dist/）
│   └── app/ + docs/        # 移动端 H5 / 文档站点（按需启用）
├── mysql/                  # MySQL 持久化 & 初始化
│   ├── init/               # 首次启动时执行的 SQL 脚本（可选）
│   └── data/               # 数据库数据文件（自动生成）
├── redis/                  # Redis 持久化 & 配置
│   ├── conf/
│   │   └── redis.conf      # Redis 持久化配置文件
│   └── data/               # Redis 数据文件（自动生成）
├── docker-compose.yaml     # Docker Compose 编排文件
├── .env                    # 环境变量配置文件（.gitignore 已排除）
├── .env.example            # 环境变量示例文件
└── README.md               # 本文档
```

> `.gitkeep` 仅用于保留空目录结构，不包含任何实际内容。

## 部署准备

### 系统依赖

- Docker (>= 20.10)
- Docker Compose (v2，Docker 内置的 `docker compose` 命令)
- 如需构建前端：Node.js (>= 18) 和 npm / pnpm

### 环境配置

1. **配置环境变量**

   ```bash
   cp docker/.env.example docker/.env
   chmod 600 docker/.env  # 限制权限，防止其他用户读取密码
   ```

   主要配置项：

   | 变量 | 必填 | 默认值 | 说明 |
   |------|------|--------|------|
   | `MYSQL_ROOT_PASSWORD` | 是 | - | MySQL root 密码 |
   | `MYSQL_DATABASE` | 否 | `fastapiadmin` | 数据库名 |
   | `MYSQL_USER` | 否 | `fastapiadmin` | 数据库用户 |
   | `MYSQL_PASSWORD` | 是 | - | 数据库密码 |
   | `REDIS_PASSWORD` | 是 | - | Redis 密码 |
   | `BACKEND_PORT` | 否 | `8001` | 后端服务宿主机端口 |
   | `HTTP_PORT` | 否 | `80` | HTTP 宿主机端口 |
   | `HTTPS_PORT` | 否 | `443` | HTTPS 宿主机端口 |
   | `DEPLOY_ENV` | 否 | `prod` | 部署环境（dev/prod） |
   | `BACKEND_IMAGE_TAG` | 否 | `3.0.0` | 后端镜像标签 |
   | `BUILD_WEB` | 否 | `false` | 部署时构建前端 Web |
   | `NGINX_SERVER_NAME` | 否 | `service.fastapiadmin.com` | Nginx 域名 |

2. **SSL 证书配置**（可选，但生产环境必须）

   ```bash
   # 自签名证书（测试用）：
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout docker/nginx/ssl/server.key \
     -out docker/nginx/ssl/server.pem \
     -subj "/CN=service.fastapiadmin.com"

   # 生产环境请使用正规 CA 签发的证书
   ```

## 部署方式

### 方式一：使用部署脚本（推荐）

在项目根目录执行：

```bash
./deploy.sh
```

脚本会自动执行：检查依赖 → 创建目录 → 停止旧容器 → 更新代码 → 构建镜像 → 启动容器 → 验证部署 → 清理旧资源。

**命令选项**

| 命令 | 说明 |
|------|------|
| `./deploy.sh` | 完整部署（跳过前端构建） |
| `./deploy.sh start` | 启动所有容器 |
| `./deploy.sh stop` | 停止所有容器 |
| `./deploy.sh restart` | 重启所有容器 |
| `./deploy.sh logs` | 查看所有容器日志 |
| `./deploy.sh verify` | 验证部署状态 |
| `./deploy.sh clean` | 清理旧镜像和构建缓存 |
| `./deploy.sh --build-frontend` | 完整部署并构建前端（web / app / docs） |
| `./deploy.sh --skip-frontend` | 完整部署并跳过前端构建（默认） |

或在 `.env` 中设置 `BUILD_WEB=true` 使部署脚本自动构建前端。

### 方式二：手动操作

```bash
cd docker

# 启动所有服务
docker compose --env-file .env up -d

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f [service_name]

# 停止服务
docker compose down

# 仅重建某个服务
docker compose up -d --no-deps --build [service_name]
```

## 访问信息

部署完成后，可以通过以下地址访问：

| 服务 | 地址 |
|------|------|
| 前端 | `https://your-domain/web` |
| Swagger API 文档 | `https://your-domain/docs` |
| ReDoc API 文档 | `https://your-domain/redoc` |
| API 健康检查 | `https://your-domain/health` |
| 后台登录 | 默认账号 `admin`，密码 `123456` |

> **注意**: `docs`（官网）和 `app`（移动端 H5）默认不参与部署，如需启用请取消 docker-compose.yaml 中相关卷挂载注释。

## 容器资源限制

| 服务 | CPU 限制 | 内存限制 | 内存预留 |
|------|----------|----------|----------|
| MySQL | 无限制 | 1 GB | 256 MB |
| Redis | 无限制 | 512 MB | 128 MB |
| Backend | 1 核 | 1 GB | 256 MB |
| Nginx | 0.5 核 | 256 MB | 64 MB |

如需调整，修改 `docker-compose.yaml` 中对应服务的 `deploy.resources` 字段。

## 日志管理

```bash
# 查看所有容器日志
./deploy.sh logs

# 查看实时日志
cd docker
docker compose logs -f [服务名]

# 服务名：backend, nginx, mysql, redis
```

各容器的日志会被 Docker 自动轮转，限制为每个容器最多保留 3 个日志文件，每个最大 10MB。可在 `docker-compose.yaml` 中调整 `logging` 配置。

## 前端构建

构建前端有三种方式：

1. **本地构建后手动部署**（推荐）
   ```bash
   cd frontend/web
   npm install && npm run build
   cp -r dist ../docker/nginx/web/
   ```

2. **使用部署脚本**
   ```bash
   ./deploy.sh --build-frontend
   ```

3. **自动构建**：在 `.env` 中设置
   ```env
   BUILD_WEB=true
   # BUILD_APP=true
   # BUILD_DOCS=true
   ```

## 生产部署建议

1. **移除开发卷挂载**：生产环境下，在 `docker-compose.yaml` 中注释掉 `backend` 服务的 `volumes` 挂载，使用镜像内自带的代码
2. **使用正规 SSL 证书**：将 CA 签发的证书替换 `nginx/ssl/` 下的文件
3. **修改域名**：在 `nginx/nginx.conf` 和 `.env` 中修改 `server_name`
4. **关闭调试**：确保 `.env` 中 `DEPLOY_ENV=prod`
5. **限制数据库端口**：生产环境建议注释 MySQL/Redis 的 `ports` 映射，仅通过容器内部网络访问

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| 环境变量文件不存在 | 部署脚本会自动从 `.env.example` 创建，或手动 `cp docker/.env.example docker/.env` |
| 前端构建失败 | 建议在本地构建前端，将 `dist` 目录复制到 `docker/nginx/web/` 目录 |
| 容器启动失败 | `cd docker && docker compose logs [服务名]` 查看具体错误 |
| 数据库连接失败 | 确保 `.env` 中数据库配置正确，MySQL 容器正常运行 |
| 端口冲突 | 修改 `.env` 中的端口配置，重新部署 |
| MySQL 数据目录权限问题 | `sudo chown -R 999:999 docker/mysql/data && sudo chmod -R 755 docker/mysql/data` |
| 后端健康检查失败 | 确保 MySQL 和 Redis 容器已就绪，查看后端日志：`docker compose logs backend` |

## 安全建议

1. **修改默认密码**：部署后请修改 `.env` 中的密码
2. **保护 `.env` 文件**：已加入 `.gitignore`，请勿手动提交
3. **使用正规 SSL 证书**：生产中不要使用自签名证书
4. **限制端口访问**：通过防火墙只开放 80/443 端口
5. **及时更新**：定期执行部署脚本获取最新版本

## 版本更新

```bash
./deploy.sh    # 自动拉取最新代码 → 构建新镜像 → 重启容器
```
