# FastApiAdmin - Backend

基于 FastAPI 框架构建的企业级后端架构，为前端 Vue3 管理系统提供完整的 API 服务支持。

> **与仓库根文档的关系**：项目总览、一键前后端启动、演示账号、Docker 部署、架构图与默认端口等请以 [根目录 README.md](../README.md) 为准；**本文档**侧重 `backend/` 目录结构、迁移命令与后端开发约定。

## 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| FastAPI | 0.115.2 | 现代 Web 框架 |
| SQLAlchemy | 2.0.36 | ORM 框架 |
| Alembic | 1.15.1 | 数据库迁移工具 |
| Pydantic | 2.x | 数据验证与序列化 |
| APScheduler | 3.11.0 | 定时任务调度 |
| Redis | 5.2.1 | 缓存与会话存储 |
| Uvicorn | 0.30.6 | ASGI 服务器 |
| Python | 3.12+ | 运行环境 |

## 项目结构

```txt
backend/
├── app/                     # 项目核心代码
│   ├── alembic/             # 数据库迁移管理
│   ├── api/                 # 路由装配层（v1 聚合各模块路由）
│   ├── modules/             # 业务模块层（按业务域竖切）
│   │   ├── system/          #   系统管理
│   │   ├── monitor/         #   系统监控
│   │   ├── ai/              #   AI 功能
│   │   ├── task/            #   定时任务
│   │   ├── workflow/        #   工作流
│   │   ├── generator/       #   代码生成
│   │   └── common/          #   文件 / 健康检查
│   ├── common/              # 公共组件（常量、枚举、响应封装）
│   ├── config/              # 项目配置文件
│   ├── core/                # 核心模块（数据库、中间件、安全）
│   ├── plugin/              # 插件模块（二开目录）
│   ├── scripts/             # 初始化脚本和数据
│   └── utils/               # 工具类（验证码、文件上传等）
├── env/                     # 环境配置文件
├── logs/                    # 日志输出目录
├── sql/                     # SQL 初始化脚本
├── static/                  # 静态资源文件
├── main.py                  # 项目启动入口
├── alembic.ini              # Alembic 迁移配置
├── requirements.txt         # Python 依赖包
└── pyproject.toml           # 项目配置（uv / ruff）
```

### 模块分层

每个业务模块采用统一的分层结构：

```txt
modules/<模块>/<子域>/
├── controller.py    # 控制器 - HTTP 请求处理
├── service.py       # 服务层 - 业务逻辑处理
├── crud.py          # 数据层 - 数据库操作
├── model.py         # ORM 模型 - 数据库表定义
├── schema.py        # Pydantic 模型 - 数据验证
└── param.py         # 参数模型 - 请求参数
```

分包理念（按业务竖切 vs 按技术层次分包）详见 [项目概述](https://service.fastapiadmin.com/guide/overview)。

## 快速开始

### 环境要求

- **Python**: 3.12+
- **数据库**: MySQL 8.0+ / PostgreSQL 13+ / SQLite 3.x（连接串在 `env/.env.dev`）
- **Redis**: 与 `.env.dev` 中配置一致

### 第一次在本机跑起来

1. 复制 `env/.env.example` → `env/.env.dev`，填写数据库、Redis 等（先在 DB 中建好空库）。
2. 在 **`backend/` 目录下** 安装依赖：推荐 **`uv sync`**；或 `pip install -r requirements.txt`。
3. **启动**：`uv run main.py run --env=dev`（或 `python main.py run --env=dev`）。**首次启动会自动初始化数据库表与基础数据**，一般**无需**先执行 `upgrade`。接口文档示例：`http://127.0.0.1:8001/docs`（端口见 `.env.dev` 中 `SERVER_PORT`）。

### 数据库迁移命令（模型变更时使用）

日常**首次启动不必手动执行**；当你**修改了 ORM 模型**并需用 Alembic 管理结构变更时再使用：

```bash
# 生成迁移文件（模型变更后）
python main.py revision --env=dev
# 应用迁移
python main.py upgrade --env=dev

# 使用 uv 时
uv run main.py revision --env=dev
uv run main.py upgrade --env=dev
```

### 安装依赖与启动服务

```bash
# 推荐使用 uv（与 pyproject.toml 一致）
uv sync
uv run main.py run --env=dev

# 或使用传统 pip / venv
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py run --env=dev
```

### 代码格式化（ruff）

```bash
ruff check
ruff check --fix
ruff check --watch

# 使用 uv 时
uv run ruff check
uv run ruff check --fix
uv run ruff check --watch
```

## 后端约定（日期与序列化）

使用 **Pydantic v2** 与 **PostgreSQL（asyncpg）** 时：ORM 写入需要 Python 原生日期时间，JSON 输出需要可序列化字符串。

- 自定义 `DateStr` / `TimeStr` / `DateTimeStr`（`app/core/validator.py`）使用 **`PlainSerializer(..., when_used='json')`**
- `model_dump(mode='python')` 供 ORM 使用原生类型；JSON / Redis 使用 `model_dump(mode='json')`
- 统一 HTTP 响应见 `app/common/response.py` 中的 **`jsonable_encoder`**
- 写入 Redis 时请使用 **`model_dump(mode='json')`** 再序列化

## 相关链接

- **FastAPI 官方文档**: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
- **SQLAlchemy 文档**: [https://docs.sqlalchemy.org/](https://docs.sqlalchemy.org/)
- **Pydantic 文档**: [https://pydantic-docs.helpmanual.io/](https://pydantic-docs.helpmanual.io/)
