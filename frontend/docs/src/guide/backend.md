---
layout: doc
title: 后端开发指南
description: FastApiAdmin 后端开发指南,涵盖 FastAPI 路由、SQLAlchemy 2.0 ORM、Alembic 迁移、Redis 缓存、APScheduler 定时任务、日期序列化约定等核心模块使用方法。
outline: "deep"
---

> 目录结构、迁移命令、日期序列化约定等详细说明见 [backend/README.md](https://github.com/fastapiadmin/FastapiAdmin/blob/master/backend/README.md)。

## 技术栈

| 技术 | 说明 |
|------|------|
| FastAPI 0.115+ | 现代异步 Web 框架 |
| SQLAlchemy 2.0 | ORM 框架 |
| Alembic 1.15+ | 数据库迁移工具 |
| Pydantic 2.x | 数据验证与序列化 |
| APScheduler 3.11+ | 定时任务调度 |
| Redis | 缓存与会话存储 |
| Uvicorn | ASGI 服务器 |

## 项目结构

```
backend/app/
├── api/v1/              # 路由清单（仅聚合路由，不含业务逻辑）
│   ├── system.py        #   系统管理路由
│   ├── monitor.py       #   监控路由
│   └── ...
├── modules/             # 业务层（按业务域竖切）
│   ├── system/          #   系统管理业务域（用户、角色、菜单等）
│   ├── monitor/         #   监控业务域（缓存、在线用户、服务器、健康检查）
│   ├── ai/              #   AI 功能业务域
│   ├── task/            #   任务业务域（定时任务）
│   ├── workflow/        #   工作流业务域
│   ├── generator/       #   代码生成业务域
│   └── file/            #   文件管理业务域（上传、下载）
├── common/              # 公共组件（常量、枚举、响应封装）
├── config/              # 项目配置
├── core/                # 核心模块（数据库、安全、权限、中间件）
├── plugin/              # 插件目录（二开目录）
└── utils/               # 工具类
```

## 模块分层

每个业务模块采用统一的分层结构（按业务特性竖切）：

```
modules/<模块>/<子域>/
├── controller.py    # HTTP 请求处理
├── service.py       # 业务逻辑
├── crud.py          # 数据库操作
├── model.py         # ORM 模型
├── schema.py        # Pydantic 验证
└── param.py         # 请求参数
```

> 关于分包理念（按业务竖切 vs 按技术层次分包）的讨论见 [根目录 README](https://github.com/fastapiadmin/FastapiAdmin/blob/master/README.md#packaging-philosophy)。

## 快速开始

```bash
cd backend

# 推荐使用 uv
uv sync
uv run main.py run --env=dev

# 或传统方式
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py run --env=dev
```

**首次启动会自动初始化数据库表与基础数据**。

## 数据库迁移

仅在你修改了 ORM 模型后使用：

```bash
python main.py revision --env=dev
python main.py upgrade --env=dev
# 或 uv run main.py revision/upgrade --env=dev
```

## 环境配置

| 文件 | 说明 |
|------|------|
| `env/.env.example` | 开发环境模板 |
| `env/.env.dev` | 开发环境（需自行创建） |
| `env/.env.prod.example` | 生产环境模板 |

主要配置项：数据库连接、Redis、JWT 密钥、端口等。

## 插件开发（二开）

项目采用**插件化架构**，建议在 `backend/app/plugin/` 下开发：

### 自动路由注册机制

1. 控制器文件命名为 `controller.py`
2. 路由自动映射：`module_xxx` → `/xxx`
3. 系统自动扫描 `plugin/` 下所有 `controller.py` 并注册路由

### 开发步骤

1. 在 `backend/app/plugin/` 下创建 `module_yourfeature/`
2. 依次编写 `model.py` → `schema.py` → `crud.py` → `service.py` → `controller.py`
3. 路由自动注册，无需手动配置

### 控制器示例

```python
from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse

from app.common.response import SuccessResponse
from app.core.router_class import OperationLogRoute
from app.core.dependencies import AuthPermission
from app.modules.system.auth.schema import AuthSchema
from .service import YourFeatureService

YourFeatureRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/yourcontroller",
    tags=["你的功能模块"],
)

@YourFeatureRouter.get("/detail/{id}", summary="获取详情")
async def get_detail(
    id: int = Path(..., description="功能ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_yourfeature:yourcontroller:detail"])),
) -> JSONResponse:
    result = await YourFeatureService.detail_service(id=id, auth=auth)
    return SuccessResponse(data=result)
```

## 代码生成器

内置代码生成器可根据数据库表结构自动生成前后端 CRUD 代码。登录系统后进入「代码生成」模块即可使用。

## 后端约定

- **日期序列化**：使用 Pydantic `PlainSerializer(..., when_used='json')`，ORM 用 `mode='python'`，JSON/Redis 用 `mode='json'`
- **统一响应**：使用 `SuccessResponse` 和 `jsonable_encoder`
- **权限控制**：所有 API 接口需添加 `AuthPermission` 权限控制
- **日志记录**：关键操作使用 `OperationLogRoute` 记录

## 代码规范

```bash
ruff check              # 检查
ruff check --fix        # 自动修复
# 或 uv run ruff check / --fix
```
