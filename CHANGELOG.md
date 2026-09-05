# SaaS 多租户平台需求文档

> 版本：v3.6.0
> 最后更新：2026-06-03

---

# Part 1：平台架构与基础设施

---

## 1. 概述

### 1.1 背景

FastapiAdmin 是一个基于 FastAPI + SQLAlchemy 的管理后台框架，需要支持 SaaS 多租户模式。平台提供完善的多租户隔离和授权体系，包含平台管理端、套餐体系、租户独立授权、插件系统、工单系统等能力。

### 1.2 核心目标

1. **数据隔离**：不同租户间的业务数据严格隔离，通过 `tenant_id` 行级过滤实现
2. **权限分层**：平台层（菜单/套餐/插件）→ 租户层（可见菜单/配额/配置）→ 用户层（角色/数据权限）
3. **灵活授权**：通过套餐体系预设权限 + 自定义授权相结合，简化租户开通流程
4. **资源管控**：租户配额管理（用户数/角色数/存储空间等）防止资源滥用

### 1.3 角色定义

| 角色 | 说明 | 租户范围 |
|------|------|---------|
| **超级管理员 (Super Admin)** | 平台拥有者，管理所有租户和套餐，不受租户过滤 | 平台 |
| **租户管理员 (Tenant Admin)** | 被指定为租户的 owner/admin，管理租户内部资源 | 单个租户 |
| **租户用户 (Tenant User)** | 普通业务用户，使用租户内的功能 | 单个租户 |

### 1.4 模块总览

| 模块 | 类型 | 租户隔离 | 核心用途 |
|------|------|---------|---------|
| Auth | 系统 | 无 | 登录认证、OAuth、JWT |
| User | 系统 | ✅ TenantMixin | 用户管理、角色/岗位分配 |
| Role | 系统 | ✅ TenantMixin | 角色定义、菜单/部门权限分配 |
| Dept | 系统 | ✅ TenantMixin | 树形部门管理 |
| Position | 系统 | ✅ TenantMixin | 岗位管理 |
| Menu | 系统 | **无** | 平台菜单树（纯平台资源） |
| Dict | 系统 | ✅ TenantMixin（平台共享） | 字典类型+数据 |
| Notice | 系统 | ✅ TenantMixin | 通知公告 |
| Params | 系统 | ✅ TenantMixin | 系统参数配置 |
| LoginLog | 平台 | **无** | 登录日志（平台级） |
| OperationLog | 系统 | ✅ TenantMixin | 操作日志（租户级） |
| Tenant | 平台 | **无**（自身为租户定义） | 租户管理 |
| Package | 平台 | **无** | 套餐管理 |
| Ticket | 系统 | ✅ TenantMixin | 工单反馈 |
| Plugin | 平台 | **无**（平台资源） | 插件注册表 |
| Cronjob | 插件 | ✅ TenantMixin | 定时任务 |
| Workflow | 插件 | ✅ TenantMixin | 工作流引擎 |
| AI Chat | 插件 | ✅ TenantMixin | AI 对话 |
| CodeGen | 插件 | ✅ TenantMixin | 代码生成器 |
| Invoice | 平台 | **无**（关联 order） | 发票管理（普票/专票） |
| AuditLog | 平台 | **无** | 审计日志（不可篡改） |
| Dashboard | 平台 | **无** | 运营数据大盘 |

---

## 2. 平台架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────┐
│                  Controller 层                    │
│    路由定义 / 参数校验 / 响应封装 / 操作日志      │
├─────────────────────────────────────────────────┤
│                  Service 层                       │
│    业务逻辑编排 / 数据校验 / 权限检查             │
├─────────────────────────────────────────────────┤
│                   CRUD 层                         │
│    CRUDBase 通用增删改查 / 租户过滤 / 权限过滤     │
├─────────────────────────────────────────────────┤
│                   Model 层                        │
│    SQLAlchemy ORM / Mixin 体系 / 关系定义         │
├─────────────────────────────────────────────────┤
│   DB (MySQL/PgSQL/SQLite)    │    Redis 缓存      │
└─────────────────────────────────────────────────┘
```

### 2.2 请求链路

```
请求 → Middleware链 → 租户中间件(解析token,设置ContextVar) →
路由匹配 → 依赖注入(DI) → Controller → Service → CRUD →
ORM(自动注入tenant_id) → DB → 反向响应 → ContextVar清理
```

### 2.3 模块目录结构

每个业务模块遵循统一结构：

```
module_xxx/
├── __init__.py
├── controller.py    # API 路由定义
├── service.py       # 业务逻辑
├── crud.py          # 数据操作（继承 CRUDBase）
├── model.py         # SQLAlchemy 模型
└── schema.py        # Pydantic 请求/响应模型
```

---

## 3. 数据隔离模型

### 3.1 核心设计原则

```
平台资源（无 tenant_id）
  ├── platform_menu              ← 菜单定义，纯平台资源
  ├── platform_package      ← 套餐定义
  ├── platform_plugin       ← 插件注册表
  └── platform_tenant       ← 租户定义

租户资源（含 tenant_id，ORM 自动过滤）
  ├── sys_user              ← 用户
  ├── sys_role              ← 角色
  ├── sys_dept              ← 部门
  ├── sys_position          ← 岗位
  ├── sys_notice            ← 通知公告
  ├── sys_param             ← 系统参数
  ├── sys_log               ← 日志
  ├── platform_ticket       ← 工单
  └── 插件业务表

平台共享资源（tenant_id=1 的平台数据对所有租户可读）
  ├── sys_dict_type         ← 字典类型
  └── sys_dict_data         ← 字典数据
```

### 3.2 三层隔离机制

| 层级 | 实现文件 | 机制说明 |
|------|---------|---------|
| **ORM 事件层** | `tenant_filter.py` | SQLAlchemy `do_orm_execute` 事件自动注入 `WHERE tenant_id = ?` |
| **CRUD 层** | `base_crud.py` | `__build_conditions` / `__tenant_condition` 二次确认 |
| **权限策略层** | `permission.py` | 基于角色 `data_scope` 字段精细化控制 |

#### ORM 事件层行为

| 操作 | 超管 | 普通用户 |
|------|------|---------|
| SELECT | 不过滤 | 自动追加 `WHERE tenant_id = ?`（`__platform_data_shared__` 模型跳过此层过滤，由 CRUD 层处理） |
| INSERT | 不自动设置 | 自动设置 `tenant_id = 当前租户` |
| UPDATE/DELETE | 不过滤 | 自动追加 `WHERE tenant_id = ?` |
| 系统表(platform_tenant) | 不过滤 | 不过滤 |

> **⚠️ 特别注意**：标记了 `__platform_data_shared__ = True` 的模型（DictType/DictData），ORM 事件层**跳过**自动 tenant_id 过滤，由 CRUD 层的 `__tenant_condition(read_mode=True)` 统一处理 `WHERE tenant_id = current OR tenant_id = 1` 逻辑。防止 ORM 事件层覆盖了"平台共享"读取策略。

#### 权限策略层

| 策略 | 枚举值 | 说明 | 适用模型 |
|------|--------|------|---------|
| `ROLE_BASED` | 1 | 仅显示用户角色授权的数据 | Menu |
| `DEPT_BASED` | 2 | 基于部门范围过滤 | Dept |
| `USER_ROLE` | 3 | 仅显示用户绑定的角色 | Role |
| `SELF_ONLY` | 4 | 仅本人数据 | 预留 |
| `DATA_SCOPE` | 5 | 基于 data_scope 字段 | Tenant（通用） |

#### data_scope 数据范围

| 值 | 说明 |
|----|------|
| 1 | 仅本人数据 |
| 2 | 本部门数据 |
| 3 | 本部门及以下数据 |
| 4 | 全部数据 |
| 5 | 自定义数据（通过 sys_role_depts 指定可见部门） |

### 3.3 Mixin 体系

```
MappedBase (声明式基类)
  ├── ModelMixin (id, uuid, status, description, 时间戳, 软删除)
  ├── TenantMixin (tenant_id FK → platform_tenant.id, NOT NULL, default=1, ON DELETE RESTRICT)
  └── UserMixin (created_id, updated_id, deleted_id FK → sys_user)
```

#### ModelMixin 通用字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK AI | 主键 |
| `uuid` | String(64) UNIQUE | UUID 全局唯一标识 |
| `status` | Integer | default=0 | 状态（0:启动 1:停用） |
| `description` | Text nullable | 备注/描述 |
| `created_time` | DateTime | 创建时间 |
| `updated_time` | DateTime | 更新时间（onupdate） |
| `is_deleted` | Boolean default=False | 软删除标记 |
| `deleted_time` | DateTime nullable | 删除时间 |

#### __platform_data_shared__ 机制

标记了 `__platform_data_shared__ = True` 的模型（DictType/DictData），在 CRUD 层查询时：
- 超管：不过滤，可查看/修改所有租户的数据
- 普通用户：`WHERE tenant_id = current_tenant_id OR tenant_id = 1`

---

# Part 2：核心业务模块需求

---

## 4. Auth 认证模块

### 4.1 业务描述

提供用户认证、授权、会话管理功能，支持多种登录方式（密码登录、OAuth2 第三方登录），支持验证码安全校验。

### 4.2 业务流程

```
登录请求 → 验证码校验(启用时) → 用户认证(用户名+密码) →
检查用户状态 → 更新最后登录时间 → 查询用户关联租户列表 →
判断租户数量:
  ├── 单租户: 直接生成 JWT(含 tenant_id) → 返回 token
  └── 多租户: 生成临时 JWT(不含 tenant_id, 仅限调用 /auth/select-tenant) →
           返回 租户选择 token + 租户列表 →
           用户选择 → /auth/select-tenant/{id} → 生成含 tenant_id 的正式 token
记录在线会话 → 返回正式 token
```

> **多租户登录说明**：
> - **临时 token**（不含 tenant_id）：仅能调用 `POST /auth/select-tenant/{id}`，其他任何接口均返回 403
> - **正式 token**（含 tenant_id）：正常访问所有已授权的 API
> - 超管用户跳过租户选择，直接生成含 `is_super_admin=True` 的正式 token（不绑定任何 tenant_id）

### 4.3 核心规则

| 规则 | 说明 |
|------|------|
| **验证码** | 配置控制是否启用，API 文档请求（docs/redoc）跳过验证码 |
| **密码校验** | Bcrypt 哈希比对 |
| **状态检查** | 用户 status="1"（禁用）时拒绝登录 |
| **JWT 载荷** | 包含 session_id, user_id, tenant_id, is_super_admin, 登录信息 |
| **Token 刷新** | refresh_token 专用，不可用 access_token 刷新 |
| **多租户登录** | 登录后判断：单租户用户直接签发含 tenant_id 的正式 token；多租户用户签**临时 token**（不含 tenant_id，仅可访问 `POST /auth/select-tenant/{id}`），选择租户后签正式 token |
| **在线记录** | 登录成功后 Redis 记录在线会话，含 IP/OS/浏览器/登录位置 |
| **日志记录** | 操作日志路由类自动记录登录日志 |

### 4.4 数据模型

无独立数据表，使用 Redis 存储会话和验证码。

### 4.5 用户自助注册

```
POST /auth/register
  ├── 接收：username, password, email, tenant_name(可选)
  ├── 校验：用户名/邮箱唯一性
  ├── 创建租户记录（platform_tenant）
  │     ├── name = tenant_name 或 "{username}的租户"（默认名）
  │     ├── code = 自动生成（基于 name 拼音首字母 + 4位随机数）
  │     ├── package_id → 取全局默认套餐（platform_package.is_default=true 的第一条，若无则 id=1）
  │     ├── end_time = now + trial_days(取套餐的 trial_days，默认 7 天)
  │     ├── max_users/max_roles/max_depts → 取套餐配额默认值（见 §16.2）
  │     └── status = 0(active)
  ├── 创建用户记录（sys_user，tenant_id=新租户ID）
  ├── 创建 owner 角色（sys_role，code="owner"）
  ├── 将用户绑定到 owner 角色
  ├── 将租户可用菜单全量分配给 owner 角色
  └── 返回注册成功（用户需邮箱验证后激活）
```

> **默认套餐获取优先级**：套餐 `is_default=true` > id=1 > 无套餐(仅自定义菜单)。若平台未配置任何套餐，新租户仅有自定义菜单体系，需超管后续手动配置。

### 4.6 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | 登录（多租户用户返回临时 token + 租户列表） |
| POST | `/auth/token/refresh` | 刷新 token |
| POST | `/auth/logout` | 退出登录（清除 Redis 会话） |
| GET | `/auth/captcha` | 获取验证码（Base64 图片） |
| POST | `/auth/register` | 用户注册（创建用户 → 自动创建默认租户并设为 owner） |
| POST | `/auth/select-tenant/{id}` | 选择/切换租户（生成含 tenant_id 的正式 token） |
| POST | `/auth/forgot-password` | 忘记密码（发送重置邮件） |
| GET | `/auth/auto-login/{token}` | 免登录（用于邮件/消息免登链接） |
| GET | `/auth/oauth/{provider}/login` | OAuth2 授权跳转 |
| GET | `/auth/oauth/{provider}/callback` | OAuth2 回调处理（需用户预绑定第三方账号；首次 OAuth 登录不绑定租户，需选择/创建租户） |

---

## 5. User 用户模块

### 5.1 业务描述

管理平台和租户下的用户账号，支持角色分配、岗位分配、部门归属、密码管理、Excel 导入导出。用户数据按租户严格隔离。

### 5.2 数据模型

**表名**：`sys_user`（TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `username` | String(64) | NOT NULL, UNIQUE(tenant_id) | 用户名/登录账号 |
| `password` | String(255) | NOT NULL | Bcrypt 密码哈希 |
| `name` | String(32) | NOT NULL | 昵称/姓名 |
| `mobile` | String(11) | nullable | 手机号 |
| `email` | String(64) | nullable | 邮箱 |
| `gender` | String(1) | default="2" | 性别（0:男 1:女 2:未知） |
| `avatar` | String(255) | nullable | 头像 URL |
| `is_superuser` | Boolean | default=False | 是否超级管理员 |
| `last_login` | DateTime | nullable | 最后登录时间 |
| `dept_id` | FK→sys_dept.id | nullable, ON DELETE SET NULL | 所属部门 |
| `gitee_login` | String(32) | nullable | Gitee 第三方登录 |
| `github_login` | String(32) | nullable | Github 第三方登录 |
| `wx_login` | String(32) | nullable | 微信第三方登录 |
| `qq_login` | String(32) | nullable | QQ 第三方登录 |

**关联关系**：

| 关联表 | 关系类型 | 说明 |
|--------|---------|------|
| `sys_user_roles` | 多对多 | 用户 ↔ 角色 |
| `sys_user_positions` | 多对多 | 用户 ↔ 岗位 |
| `platform_user_tenant` | 多对多 | 用户 ↔ 租户（跨租户支持） |

### 5.3 业务规则

| 类别 | 规则 |
|------|------|
| **创建** | username 字母开头、3~32位；不允许创建超管；username/mobile/email 唯一 |
| **修改** | 不可修改超管；username/mobile/email 唯一性检查；部门必须存在且可用 |
| **删除** | 仅已禁用(status=1)用户可删除；不可删除超管；不可删除当前登录用户 |
| **密码** | Bcrypt 加密存储；修改需验证原密码；重置不可操作超管 |
| **导入导出** | 支持 Excel 导入导出；导入时密码字段处理策略：密码列为空 → 系统自动生成12位随机密码并通过邮件发送给用户；密码列有值 → Bcrypt 加密后存储，首次登录强制修改密码 |
| **状态** | 批量启用/禁用；不可操作超管 |

### 5.4 当前用户菜单权限

```
get_current_user_info_service:
  ├── 超管 → 返回全部 PC 端菜单（type=1/2/4, client=pc）
  └── 普通用户：
        ├── 收集角色菜单 ID（角色→菜单，去重）
        ├── 与租户可用菜单取交集
        └── 构建菜单树返回
```

### 5.5 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/user/detail/{id}` | 用户详情 |
| GET | `/user/list` | 用户列表 |
| POST | `/user/create` | 创建用户 |
| PUT | `/user/update/{id}` | 更新用户 |
| DELETE | `/user/delete` | 删除用户（批量） |
| PATCH | `/user/status/batch` | 批量设置用户状态 |
| GET | `/user/current/info` | 获取当前用户信息（含菜单树） |
| PUT | `/user/current/update` | 更新当前用户信息 |
| PUT | `/user/current/password/change` | 修改密码（本人操作，需验证原密码） |
| PUT | `/user/password/reset` | 重置密码（管理员操作，跳过原密码） |
| POST | `/user/import` | 导入用户（Excel） |
| POST | `/user/export` | 导出用户（Excel） |

---

## 6. Role 角色模块

### 6.1 业务描述

角色是权限分配的核心载体，每个角色可绑定多个菜单（功能权限）和多个部门（数据权限）。角色数据按租户严格隔离。

### 6.2 数据模型

**表名**：`sys_role`（TenantMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(64) | NOT NULL | 角色名称 |
| `code` | String(64) | NOT NULL, UNIQUE(tenant_id) | 角色编码 |
| `order` | Integer | default=999 | 显示排序 |
| `data_scope` | Integer | default=1 | 数据权限范围（1~5） |

**关联关系**：

| 关联表 | 关系类型 | 说明 |
|--------|---------|------|
| `sys_role_menus` | 多对多 | 角色 ↔ 菜单 |
| `sys_role_depts` | 多对多 | 角色 ↔ 部门（仅 data_scope=5 时使用） |
| `sys_user_roles` | 多对多 | 用户 ↔ 角色 |

### 6.3 业务规则

| 规则 | 说明 |
|------|------|
| **编码规则** | 字母开头，仅含字母/数字/下划线 |
| **租户唯一** | (tenant_id, code) 唯一约束 |
| **权限策略** | `USER_ROLE` — 非超管用户只能看到自己绑定的角色 |
| **菜单约束** | 非超管只能为角色分配租户可用菜单内的菜单，越权时抛出异常含菜单名称 |
| **数据范围** | 1=仅本人 2=本部门 3=本部门及以下 4=全部 5=自定义（绑定部门） |
| **默认 owner 角色** | 创建租户时自动创建 code="owner" 的角色，不可删除、不可禁用。自动分配租户全部可用菜单 |

### 6.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/role/detail/{id}` | 角色详情 |
| GET | `/role/list` | 角色列表 |
| POST | `/role/create` | 创建角色 |
| PUT | `/role/update/{id}` | 更新角色 |
| DELETE | `/role/delete` | 删除角色（批量） |
| PATCH | `/role/status/batch` | 批量设置角色状态 |
| PUT | `/role/menus` | 设置角色菜单 |
| PUT | `/role/permission` | 设置角色权限（含数据范围+部门） |

---

## 7. Dept 部门模块

### 7.1 业务描述

部门是组织架构的核心，采用树形结构支持无限层级。部门数据按租户严格隔离。

### 7.2 数据模型

**表名**：`sys_dept`（TenantMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(64) | NOT NULL | 部门名称 |
| `code` | String(64) | NOT NULL, UNIQUE(tenant_id, code) | 部门编码 |
| `parent_id` | Integer FK | nullable | 父级部门 |
| `order` | Integer | default=999 | 显示排序 |
| `leader` | String(32) | nullable | 负责人 |
| `phone` | String(20) | nullable | 联系电话 |
| `email` | String(128) | nullable | 邮箱 |

### 7.3 业务规则

| 规则 | 说明 |
|------|------|
| **树形结构** | parent_id 自引用，支持无限层级。创建/更新 parent_id 时需检测循环引用 |
| **编码规则** | 字母开头，仅含字母/数字/下划线 |
| **租户唯一** | (tenant_id, code) 唯一约束 |
| **权限策略** | `DEPT_BASED` — 基于部门范围过滤 |
| **删除约束** | 有子部门的父部门不可删除 |
| **状态级联** | 父部门禁用时子部门同步禁用（业务层实现） |

### 7.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/dept/detail/{id}` | 部门详情 |
| GET | `/dept/list` | 部门列表（树形） |
| POST | `/dept/create` | 创建部门 |
| PUT | `/dept/update/{id}` | 更新部门 |
| DELETE | `/dept/delete` | 删除部门（批量） |
| PATCH | `/dept/status/batch` | 批量设置部门状态 |

---

## 8. Position 岗位模块

### 8.1 业务描述

岗位用于定义用户在组织内的职务角色，一个用户可绑定多个岗位。

### 8.2 数据模型

**表名**：`sys_position`（TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(64) | NOT NULL | 岗位名称 |
| `order` | Integer | default=1 | 显示排序 |

### 8.3 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/position/detail/{id}` | 岗位详情 |
| GET | `/position/list` | 岗位列表 |
| POST | `/position/create` | 创建岗位 |
| PUT | `/position/update/{id}` | 更新岗位 |
| DELETE | `/position/delete` | 删除岗位（批量） |
| PATCH | `/position/status/batch` | 批量设置岗位状态 |

---

## 9. Menu 菜单模块

### 9.1 业务描述

菜单是系统功能权限的基础定义单元，属于**平台级资源**（无 tenant_id），由超级管理员统一管理。菜单以树形结构组织，支撑前端动态路由和后端权限控制。

### 9.2 数据模型

**表名**：`platform_menu`（ModelMixin，**无 TenantMixin**）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(50) | NOT NULL | 菜单名称 |
| `type` | Integer | NOT NULL, default=2 | 类型（1:目录 2:菜单 3:按钮 4:外链） |
| `order` | Integer | NOT NULL, default=999 | 显示排序 |
| `permission` | String(100) | nullable | 权限标识（如 `system:user:query`） |
| `icon` | String(50) | nullable | 菜单图标 |
| `route_name` | String(100) | nullable | 路由名称 |
| `route_path` | String(200) | nullable | 路由路径（以 `/` 开头） |
| `component_path` | String(200) | nullable | 组件路径（不能以 `/` 开头） |
| `redirect` | String(200) | nullable | 重定向地址 |
| `hidden` | Boolean | default=False | 是否隐藏 |
| `keep_alive` | Boolean | default=True | 是否缓存 |
| `always_show` | Boolean | default=False | 是否始终显示 |
| `title` | String(50) | nullable | 菜单标题 |
| `params` | JSON | nullable | 路由参数 |
| `affix` | Boolean | default=False | 是否固定标签页 |
| `client` | String(20) | NOT NULL, default="pc" | 终端（pc/app） |
| `parent_id` | FK→platform_menu.id | nullable, ON DELETE SET NULL | 父菜单 |

### 9.3 菜单类型

| 类型 | 说明 | 路由 | 前端行为 |
|------|------|------|---------|
| 1 | 目录 | 无 | 展开项，不可点击 |
| 2 | 菜单 | 有 | 可点击进入页面 |
| 3 | 按钮/权限 | 无 | 页面内操作权限标识 |
| 4 | 外部链接 | 有 | 跳转外部 URL |

### 9.4 业务规则

| 规则 | 说明 |
|------|------|
| **平台资源** | 无 tenant_id，所有租户共享菜单池 |
| **路由规则** | `route_path` 以 `/` 开头，`component_path` 不能以 `/` 开头 |
| **类型校验** | ge=1, le=4 |
| **client 过滤** | 前端菜单渲染仅取 `client="pc"` 的菜单 |
| **权限策略** | `ROLE_BASED` — 非超管用户按角色菜单过滤 |
| **树形结构** | parent_id 自引用，children 按 order 排序。创建/更新 parent_id 时需检测循环引用（如 A→B→C→A），禁止导致循环的操作 |

### 9.5 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/menu/detail/{id}` | 菜单详情 |
| GET | `/menu/list` | 菜单列表（树形） |
| POST | `/menu/create` | 创建菜单 |
| PUT | `/menu/update/{id}` | 更新菜单 |
| DELETE | `/menu/delete` | 删除菜单（批量） |
| PATCH | `/menu/status/batch` | 批量设置菜单状态 |

---

## 10. Dict 字典模块

### 10.1 业务描述

字典模块提供统一的类型-数据管理，用于维护系统中固定的下拉选项和枚举值。字典数据支持**平台共享**（tenant_id=1 的平台字典对所有租户可读）。

### 10.2 数据模型

#### DictType（sys_dict_type）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `dict_name` | String(64) | NOT NULL | 字典名称 |
| `dict_type` | String(255) | NOT NULL, UNIQUE(tenant_id) | 字典类型编码 |

**平台共享**：`__platform_data_shared__ = True`

#### DictData（sys_dict_data）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `dict_sort` | Integer | default=0 | 排序 |
| `dict_label` | String(255) | NOT NULL | 字典标签 |
| `dict_value` | String(255) | NOT NULL | 字典键值 |
| `css_class` | String(255) | nullable | 样式属性 |
| `list_class` | String(255) | nullable | 表格回显样式 |
| `is_default` | Boolean | default=False | 是否默认 |
| `dict_type` | String(255) | NOT NULL | 字典类型（冗余字段） |
| `dict_type_id` | FK→sys_dict_type.id | NOT NULL, ON DELETE CASCADE | 字典类型 ID |

### 10.3 业务规则

| 规则 | 说明 |
|------|------|
| **平台共享** | tenant_id=1 的字典对所有租户可读。**写保护**：修改/删除 tenant_id=1 的平台字典数据时，仅允许超管操作，普通租户管理员不可修改平台字典 |
| **编码规则** | dict_type 以小写字母开头，仅含小写字母/数字/下划线 |
| **级联删除** | 删除 DictType 时，关联的 DictData 自动级联删除 |
| **双关联** | DictData 同时保留 dict_type（字符串冗余）和 dict_type_id（FK）双重关联。`dict_type` 为冗余字段，用于避免频繁 JOIN DictType 表获取类型编码。两者应保持一致，业务层插入时自动填充 dict_type 并与 dict_type_id 对应 |
| **唯一约束** | DictData 表：`UNIQUE(tenant_id, dict_type_id, dict_value)`，同一字典类型下不可有重复的 dict_value |

### 10.4 API 端点

#### 字典类型

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/dict/type/detail/{id}` | 字典类型详情 |
| GET | `/dict/type/list` | 字典类型列表 |
| POST | `/dict/type/create` | 创建字典类型 |
| PUT | `/dict/type/update/{id}` | 更新字典类型 |
| DELETE | `/dict/type/delete` | 删除字典类型（批量） |
| PATCH | `/dict/type/status/batch` | 批量设置字典类型状态 |

#### 字典数据

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/dict/data/detail/{id}` | 字典数据详情 |
| GET | `/dict/data/list` | 字典数据列表 |
| POST | `/dict/data/create` | 创建字典数据 |
| PUT | `/dict/data/update/{id}` | 更新字典数据 |
| DELETE | `/dict/data/delete` | 删除字典数据（批量） |
| PATCH | `/dict/data/status/batch` | 批量设置字典数据状态 |

---

## 11. Notice 通知公告模块

### 11.1 业务描述

管理租户内部的通知和公告发布。通知数据按租户严格隔离。

### 11.2 数据模型

**表名**：`sys_notice`（TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `notice_title` | String(64) | NOT NULL | 公告标题 |
| `notice_type` | String(1) | NOT NULL | 类型（1:通知 2:公告） |
| `notice_content` | Text | nullable | 公告内容（富文本，XSS 过滤） |

**已读状态表**：`sys_notice_read`（按租户隔离）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `user_id` | FK→sys_user.id | PK, ON DELETE CASCADE | 用户ID |
| `notice_id` | FK→sys_notice.id | PK, ON DELETE CASCADE | 通知ID |
| `read_time` | DateTime | NOT NULL, default=now | 已读时间 |

> 唯一约束：`UNIQUE(user_id, notice_id)`。未建立记录即代表未读。

### 11.3 业务规则

| 规则 | 说明 |
|------|------|
| **类型校验** | 仅支持 "1"(通知) 和 "2"(公告) |
| **XSS 防护** | notice_content 经过 `sanitize_html` 清洗 |
| **已读追踪** | 使用后端 `sys_notice_read` 表记录已读状态（多设备同步）。未读数量通过 LEFT JOIN 统计；通知列表返回未读数量标记 |

### 11.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/notice/detail/{id}` | 公告详情 |
| GET | `/notice/list` | 公告列表 |
| POST | `/notice/create` | 创建公告 |
| PUT | `/notice/update/{id}` | 更新公告 |
| DELETE | `/notice/delete` | 删除公告（批量） |
| PATCH | `/notice/status/batch` | 批量设置公告状态 |
| POST | `/notice/read/{id}` | 标记已读（写入 sys_notice_read） |
| POST | `/notice/read-all` | 全部标记已读 |
| GET | `/notice/unread-count` | 获取当前用户未读通知数量 |

---

## 12. Params 系统参数模块

### 12.1 业务描述

管理系统级别的配置参数，支持区分系统内置参数（不可删除）和自定义参数。参数数据按租户隔离。

### 12.2 数据模型

**表名**：`sys_param`（TenantMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `config_name` | String(64) | NOT NULL | 参数名称 |
| `config_key` | String(500) | NOT NULL | 参数键名 |
| `config_value` | String(500) | nullable | 参数键值 |
| `config_type` | Boolean | default=False | 是否系统内置 |

### 12.3 业务规则

| 规则 | 说明 |
|------|------|
| **键名规则** | 小写字母开头，仅含小写字母/数字/_.- |
| **系统内置** | config_type=True 的参数不允许删除（业务层实现） |

### 12.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/params/detail/{id}` | 参数详情 |
| GET | `/params/list` | 参数列表 |
| POST | `/params/create` | 创建参数 |
| PUT | `/params/update/{id}` | 更新参数 |
| DELETE | `/params/delete` | 删除参数（批量） |

---

## 13. LoginLog 登录日志模块

### 13.1 业务描述

记录用户登录行为，用于安全审计和登录统计。登录日志为平台级资源，不受租户隔离限制，平台管理员可查看所有租户的登录记录。

### 13.2 数据模型

**表名**：`platform_login_log`（ModelMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `status` | Integer | NOT NULL, default=1 | 登录状态（1:成功 2:失败） |
| `login_ip` | String(50) | nullable | 登录 IP |
| `login_location` | String(255) | nullable | 登录位置 |
| `request_os` | String(64) | nullable | 操作系统 |
| `request_browser` | String(64) | nullable | 浏览器 |
| `msg` | String(255) | nullable | 提示消息 |

### 13.3 API 端点

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/platform/loginlog/detail/{id}` | 登录日志详情 | 平台管理员 |
| GET | `/platform/loginlog/list` | 登录日志列表 | 平台管理员 |
| DELETE | `/platform/loginlog/delete` | 删除登录日志（批量） | 平台管理员 |

---

## 14. OperationLog 操作日志模块

### 14.1 业务描述

记录系统的操作日志，用于审计和问题追踪。通过 `OperationLogRoute` 路由类自动记录操作日志。日志数据按租户隔离，租户管理员仅能查看本租户的操作日志。

### 14.2 数据模型

**表名**：`sys_operation_log`（ModelMixin, TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `request_path` | String(255) | NOT NULL | 请求路径 |
| `request_method` | String(10) | NOT NULL | 请求方法 |
| `request_payload` | LONGTEXT/TEXT | nullable | 请求体 |
| `request_ip` | String(50) | nullable | 请求 IP |
| `request_os` | String(64) | nullable | 操作系统 |
| `request_browser` | String(64) | nullable | 浏览器 |
| `response_code` | Integer | NOT NULL | 响应状态码 |
| `response_json` | LONGTEXT/TEXT | nullable | 响应体 |
| `process_time` | String(20) | nullable | 处理耗时 |

### 14.3 存储适配

| 数据库 | 大字段类型 |
|--------|-----------|
| MySQL | LONGTEXT |
| PostgreSQL | TEXT |
| SQLite | Text |

### 14.4 API 端点

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/system/operationlog/detail/{id}` | 操作日志详情 | 租户管理员 |
| GET | `/system/operationlog/list` | 操作日志列表 | 租户管理员 |
| DELETE | `/system/operationlog/delete` | 删除操作日志（批量） | 租户管理员 |

### 14.5 日志保留策略

操作日志表数据量大（生产环境可能每天数十万条），需配置自动清理机制：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `operation_log_retention_days` | 日志保留天数 | 90 天 |
| `operation_log_cleanup_enabled` | 是否启用自动清理 | true |
| `operation_log_cleanup_cron` | 定时清理 cron 表达式 | 每天凌晨 3:00 |

- 定时任务 `cleanup_operation_log` 删除 `create_time < now - retention_days` 的记录
- 清理前可选归档到外部存储（OSS/本地文件），由 `operation_log_archive_enabled` 控制
- 登录日志（`platform_login_log`）同样受此策略管理

---

## 15. Tenant 租户管理模块

### 15.1 业务描述

租户是 SaaS 平台的核心概念，代表一个独立的组织。租户管理包含：租户定义、配额管理、配置管理、用户关联、自定义菜单授权。

### 15.2 数据模型

#### 核心表：platform_tenant（ModelMixin，无 TenantMixin）- **单一大表设计**

将配额和配置字段直接集成到主表，简化结构便于管理。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(100) | NOT NULL, UNIQUE | 租户名称 |
| `code` | String(100) | NOT NULL, UNIQUE | 租户编码（字母数字） |
| `contact_name` | String(64) | nullable | 联系人 |
| `contact_phone` | String(20) | nullable | 联系电话 |
| `contact_email` | String(128) | nullable | 联系邮箱 |
| `address` | String(255) | nullable | 地址 |
| `domain` | String(255) | nullable | 自定义域名 |
| `logo_url` | String(500) | nullable | Logo URL |
| `description` | Text | nullable | 租户描述 |
| `version` | String(20) | nullable | 版本号 |
| `sort` | Integer | default=0 | 排序 |
| `status` | Integer | NOT NULL, default=0 | 生命周期：0=active(正常) 1=grace(宽限期) 2=suspended(暂停) 3=frozen(冻结) 4=expired(过期) 5=archived(归档) |
| `package_id` | FK→platform_package.id | nullable, ON DELETE SET NULL | 关联套餐 |
| `start_time` | DateTime | nullable | 开始时间 |
| `end_time` | DateTime | nullable | 结束时间 |
| `grace_period_days` | Integer | default=7, ge=0 | 宽限期天数（到期后延迟禁用天数） |
| `grace_start_time` | DateTime | nullable | 宽限期开始时间（自动写入） |
| `max_users` | Integer | default=50, ge=1 | 最大用户数 |
| `max_roles` | Integer | default=20, ge=1 | 最大角色数 |
| `max_storage_mb` | Integer | default=500, ge=1 | 最大存储(MB) |
| `max_depts` | Integer | default=50, ge=1 | 最大部门数 |
| `favicon` | String(500) | nullable | 网站图标 |
| `login_bg` | String(500) | nullable | 登录背景图 |
| `copyright` | String(255) | nullable | 版权信息 |
| `help_doc` | String(500) | nullable | 帮助文档地址 |
| `privacy` | String(500) | nullable | 隐私政策地址 |
| `clause` | String(500) | nullable | 服务条款地址 |
| `keep_record` | String(100) | nullable | ICP 备案号 |
| `git_code` | String(500) | nullable | 源码地址 |

#### 关联表（必要的多对多关系）

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `platform_user_tenant` | 用户-租户关联 | user_id, tenant_id, role(owner/admin/member), is_default |
| `platform_tenant_menu` | 租户自定义菜单 | tenant_id, menu_id, UNIQUE(tenant_id, menu_id) |

### 15.3 核心业务流程

#### 创建租户

```
POST /tenant/create
  ├── 创建租户记录（platform_tenant）
  ├── 生成初始管理员：{code}_admin + 随机12位密码（含特殊字符）
  ├── 密码不返回、不记录日志；生成一次性密码重置链接（含时效 Token，有效期24小时）
  ├── 向 contact_email 发送重置链接邮件（若未填 contact_email 则跳过，超管需手动处理）
  ├── 创建默认 owner 角色（sys_role），编码固定为 "owner"
  ├── 将初始管理员绑定到 owner 角色（sys_user_roles）
  ├── 将租户可用菜单（套餐菜单 + 自定义授权菜单）全量分配给 owner 角色（sys_role_menus）
  ├── 初始化租户配额（默认值写入 platform_tenant 主表）
  └── 返回租户信息（不含密码）
```

> **安全说明**：初始管理员密码仅通过邮件中的一次性链接设置，不通过日志、API 响应等任何渠道明文传递。首次登录强制修改密码。

#### 删除租户

```
DELETE /tenant/delete
  ├── 系统租户(id=1)不可删除
  ├── 仅支持删除 archived 状态的租户
  ├── 有关联数据时拒绝删除，提示需先清理
  └── 通过则物理删除（不可恢复）
```

#### 租户生命周期状态机

```
                    ┌── 冻结 ──┐
                    ↓          │
创建 → active(0) ──┤          ├→ archived(5) → deleted(已删除)
                    │          │      ↑
                    └→ grace(1) → suspended(2) → expired(4) ┘
                         ↑            │
                         └── 续期 ←──┘
```

**状态说明**：

| 状态 | 编码 | 触发方式 | 说明 |
|------|------|---------|------|
| `active` | 0 | 创建/续期/恢复 | 正常访问，读写开放 |
| `grace` | 1 | 到期后自动 | 宽限期：可登录但提示续费，功能正常 |
| `suspended` | 2 | 宽限期结束后自动 | 暂停：禁止写操作，仅可查看数据 |
| `expired` | 4 | 暂停超过保留期后自动 | 过期：禁止登录，数据保留待归档 |
| `frozen` | 3 | 超管手动冻结 | 冻结：立即禁止访问（不经过宽限期），可恢复为 active。保留全部数据 |
| `archived` | 5 | 冻结/过期后定时归档 | 归档：禁止访问，数据保留。唯一可被物理删除的状态 |
| `deleted` | — | 物理删除 | 已移除记录，不可逆 |

**冻结/归档/删除操作流**：
```
冻结(PATCH /tenant/status/batch → status=3)
  ├── 仅超管可操作
  ├── 系统租户(id=1)不可冻结
  ├── 仅 active(0) 状态可冻结
  └── 租户内所有用户 session 失效（Redis token 缓存清除）

归档(定时任务自动或手动)
  ├── 扫描 status=3 且冻结超过 archive_after_days(默认30天) 的租户
  ├── 扫描 status=4 且过期超过 archive_after_days 的租户
  └── 自动将 status 设置为 5(archived)

物理删除(DELETE /tenant/delete)
  ├── 仅 archived(status=5)状态的租户可删除
  ├── 系统租户(id=1)不可删除
  ├── 检查关联数据：用户/部门/角色/岗位
  ├── 有关联数据时拒绝删除，提示需先清理
  └── 无关联数据 → 物理删除
```

#### 套餐变更影响预览

套餐变更前，系统返回影响预览，超管确认后再执行：

```
PUT /tenant/update/{id} (package_id 变更)
  ├── 仅超管可操作
  ├── 调用预检接口 GET /tenant/{id}/package-change-preview?new_package_id=xxx
  │     返回：
  │     - 受影响的角色列表（名称、用户数）
  │     - 将被移除的菜单清单（名称、路径）
  │     - 配额变化对比（max_users/max_roles/max_depts 当前值 → 新值）
  │     - 受影响用户数总计
  ├── 前端展示影响明细，超管确认
  ├── 更新 tenant.package_id
  ├── 获取新可用菜单 ID（套餐菜单 ∪ 自定义菜单）
  ├── 清理角色中不在可用菜单内的 RoleMenus 记录
  ├── 更新租户配额（max_users/max_roles/max_depts 同步为新套餐限制值）
  │     ├── 升级：配额只增不减（新值 > 旧值时才更新）
  │     └── 降级：当前使用量 > 新配额时降级操作可执行但不缩减已有数据，仅限制后续新增
  ├── 发送通知给租户管理员（站内信，列出被回收的菜单和配额变化）
  └── 完成
```

> 预检接口：`GET /platform/tenant/{id}/package-change-preview?new_package_id={id}`
> 通知内容：本次套餐变更收回了 X 个菜单权限，涉及 Y 个角色，请知悉。

### 15.4 业务规则

| 类别 | 规则 |
|------|------|
| **系统租户** | id=1 不可删除、禁用（冻结/归档）、修改编码 |
| **编码** | 仅含字母和数字，用于生成初始管理员用户名 |
| **初始管理员** | 自动创建，用户名 `{code}_admin`，密码 12 位随机（含特殊字符）。同时自动创建 owner 角色，将初始管理员绑定为 owner，并将租户当前可用菜单（套餐菜单 ∪ 自定义菜单）全量分配给该角色。初始管理员登录后即可看到完整的租户菜单，无需超管手动介入 |
| **配额** | 创建租户时，配额默认值从所选套餐的 max_users/max_roles/max_depts 复制到 platform_tenant 主表。无套餐时使用硬编码默认值（users=10, roles=5, depts=10）。超管可在租户管理页手动调整 |
| **owner 保护** | 每个租户至少保留一个 owner。从租户移除用户时，检查该用户是否为该租户的唯一 owner，是则拒绝移除。修改用户租户角色时，禁止将最后一个 owner 降级为 member。默认 owner 角色（code="owner"）不可删除、不可禁用，确保租户始终有可用角色来管理 |
| **配额执行** | 租户配额在创建资源时执行检查。UserCRUD.create 检查 max_users，RoleCRUD.create 检查 max_roles，DeptCRUD.create 检查 max_depts。达到上限时拒绝创建并提示 |
| **默认租户** | 用户首次加入的租户自动设为默认，设置新默认时清除旧默认 |
| **多租户** | 一个用户可关联多个租户 |
| **生命周期** | 租户状态流转：active(0)→grace(1)→suspended(2)→expired(4)→archived(5)→物理删除。超管可人工冻结 active→frozen(3)→archived(5)。frozen 可恢复为 active。仅 archived 状态可物理删除。expired/frozen 超过 archive_after_days(默认30天) 后由定时任务自动归档为 archived(5) |
| **冻结后失效** | 租户冻结后，Redis 中该租户所有用户的 token 缓存立即清除，用户下次请求时因 token 无效被拒绝访问 |
| **续期** | active/grace/suspended 状态的租户可通过 `PUT /tenant/renew/{id}` 续期，传入 `end_time` 延长有效期并恢复为 active(0)；expired/frozen/archived 状态不可续期 |

### 15.5 配置缓存策略

| 机制 | 说明 |
|------|------|
| **缓存 key** | `tenant_config:{tenant_id}:{config_key}` |
| **读取策略** | 优先读 Redis，未命中回源 DB 并写回缓存 |
| **更新策略** | 更新后自动同步刷新 Redis |
| **预热** | 应用启动时 `init_tenant_config_cache` 预加载所有配置 |

### 15.6 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/tenant/detail/{id}` | 租户详情 |
| GET | `/tenant/list` | 租户列表 |
| POST | `/tenant/create` | 创建租户（自动配管理员） |
| PUT | `/tenant/update/{id}` | 修改租户 |
| DELETE | `/tenant/delete` | 删除租户（仅 archived 状态可删） |
| PATCH | `/tenant/status/batch` | 批量修改状态（含冻结/恢复） |
| PUT | `/tenant/status/{id}` | 启/禁用（冻结/恢复） |
| PUT | `/tenant/renew/{id}` | 续期（延长 end_time） |
| GET | `/tenant/{id}/users` | 获取租户用户列表 |
| POST | `/tenant/{id}/users` | 向租户添加用户 |
| DELETE | `/tenant/{id}/users/{uid}` | 从租户移除用户 |
| GET | `/tenant/{id}/quota` | 获取租户配额 |
| PUT | `/tenant/{id}/quota` | 修改租户配额 |
| GET | `/tenant/{id}/config` | 获取租户配置 |
| GET | `/tenant/{id}/config/info` | 获取租户配置（公开，缓存） |
| PUT | `/tenant/{id}/config` | 批量更新配置 |
| GET | `/tenant/{id}/menus` | 获取租户自定义菜单 |
| PUT | `/tenant/{id}/menus` | 设置租户自定义菜单 |

---

## 16. Package 套餐模块（module_package）

### 16.1 业务描述

套餐模块是独立的功能模块，用于管理租户的功能套餐配置。套餐是预定义的功能菜单集合，用于标准化租户授权流程。通过套餐体系可以减少逐个分配菜单的工作量，实现基础版/专业版/企业版等分级授权。

### 16.2 数据模型

#### platform_package

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(100) | NOT NULL, UNIQUE | 套餐名称 |
| `code` | String(100) | NOT NULL, UNIQUE | 套餐编码 |
| `status` | Integer | default=0 | 状态（0:启动 1:停用） |
| `is_default` | Boolean | default=False | 是否为默认套餐（自助注册时自动选用） |
| `price` | Integer | default=0 | 价格（分），0=免费 |
| `period` | String(10) | nullable | 计费周期：month/year/once |
| `trial_days` | Integer | default=0 | 试用天数，0=无试用 |
| `max_users` | Integer | default=10 | 套餐用户数上限 |
| `max_roles` | Integer | default=5 | 套餐角色数上限 |
| `max_depts` | Integer | default=10 | 套餐部门数上限 |
| `max_tenants` | Integer | nullable | 该套餐最大租户数限制（平台运营管控），null=不限制 |
| `sort` | Integer | default=0 | 排序 |

#### platform_package_menu

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `package_id` | FK→platform_package.id | PK, ON DELETE CASCADE | 套餐 ID |
| `menu_id` | FK→platform_menu.id | PK, ON DELETE CASCADE | 菜单 ID |

唯一约束：`(package_id, menu_id)`

### 16.3 核心流程

#### 租户可用菜单合并逻辑

```
get_tenant_available_menu_ids(tenant_id):
  可用菜单 = set()
  
  # 1. 如果租户关联了套餐，取出套餐的所有菜单
  if tenant.package_id:
      可用菜单.add(套餐菜单...)
  
  # 2. 取出租户自定义授权菜单（platform_tenant_menu）
  可用菜单.add(自定义菜单...)
  
  return list(可用菜单)  # 并集
```

#### 套餐变更后清理

```
套餐变更 → 取新可用菜单 ID →
查询该租户所有角色 → 删除角色中不在可用菜单内的 RoleMenus 记录 → 完成
```

### 16.4 业务规则

| 规则 | 说明 |
|------|------|
| **套餐变更** | 仅超管可操作 |
| **删除约束** | 删除前检查是否有租户使用，有则拒绝 |
| **级联策略** | 套餐删除时，租户 package_id SET NULL |
| **菜单设置** | 套餐菜单全量替换（先删后插） |
| **套餐禁用** | 套餐 status=1 时，已关联该套餐的租户在 `get_tenant_available_menu_ids` 中**不再计入**套餐菜单，仅保留租户自定义菜单（platform_tenant_menu）。恢复 status=0 后套餐菜单自动恢复 |
| **套餐已删** | 套餐被删除（package_id SET NULL）后，租户降级为仅有自定义菜单，需及时为受影响租户迁移或补配权限 |

### 16.5 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/platform/package/detail/{id}` | 套餐详情 |
| GET | `/platform/package/list` | 套餐列表 |
| POST | `/platform/package/create` | 创建套餐 |
| PUT | `/platform/package/update/{id}` | 修改套餐 |
| DELETE | `/platform/package/delete` | 删除套餐 |
| GET | `/platform/package/{id}/menus` | 获取套餐菜单 |
| PUT | `/platform/package/{id}/menus` | 设置套餐菜单（全量替换） |

---

## 17. Ticket 工单模块

### 17.1 业务描述

工单系统用于用户提交反馈、建议和缺陷报告，支持指派处理人进行跟踪处理。工单数据按租户隔离。

### 17.2 数据模型

**表名**：`platform_ticket`（TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `title` | String(200) | NOT NULL | 工单标题 |
| `ticket_content` | Text | nullable | 工单内容（富文本） |
| `summary` | Text | nullable | 工单内容（纯文本摘要） |
| `ticket_type` | String(20) | NOT NULL, default="suggestion" | 类型（suggestion/bug/optimize/other） |
| `status` | Integer | NOT NULL, default=0 | 状态（0:待处理 1:处理中 2:已完成 3:已关闭） |
| `images` | Text | nullable | 图片 URL 列表（JSON 数组） |
| `reply` | Text | nullable | 回复内容 |
| `assigned_id` | FK→sys_user.id | nullable, ON DELETE SET NULL | 处理人 |

### 17.3 状态流转

```
待处理(0) → 处理中(1) → 已完成(2)
   ↑            │
   └──── 已关闭(3)
```

#### 状态转换规则

| 源状态 | 目标状态 | 允许角色 | 说明 |
|-------|---------|---------|------|
| 待处理(0) | 处理中(1) | 创建人/处理人/超管 | 确认受理 |
| 待处理(0) | 已关闭(3) | 创建人/超管 | 取消提交 |
| 处理中(1) | 已完成(2) | 处理人/超管 | 处理完成 |
| 处理中(1) | 已关闭(3) | 创建人/处理人/超管 | 强行关闭（需填写原因） |
| 已完成(2) | 已关闭(3) | 创建人/超管 | 确认关闭 |
| 已关闭(3) | 待处理(0) | 超管 | 仅超管可重新打开 |

> 非法转换（如已完成→处理中）应在 Service 层校验并拒绝 |

### 17.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/ticket/detail/{id}` | 工单详情 |
| GET | `/ticket/list` | 工单列表 |
| POST | `/ticket/create` | 创建工单 |
| PUT | `/ticket/update/{id}` | 更新工单 |
| DELETE | `/ticket/delete` | 删除工单（批量） |
| PUT | `/ticket/batch/status` | 批量更新工单状态 |

---

## 18. Plugin 插件模块

### 18.1 业务描述

插件系统是平台的扩展机制。`platform_plugin` 作为插件注册表（平台级资源），记录所有可用插件的元数据。租户通过 `platform_tenant_plugin` 关联表安装插件。

### 18.2 数据模型

#### platform_plugin（平台资源，无 TenantMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(100) | NOT NULL, UNIQUE | 插件名称 |
| `code` | String(50) | NOT NULL, UNIQUE | 插件编码（module_xxx） |
| `description` | Text | nullable | 插件描述 |
| `version` | String(20) | NOT NULL, default="1.0.0" | 版本号 |
| `author` | String(100) | nullable | 作者 |
| `icon` | String(500) | nullable | 图标 URL |
| `category` | String(20) | NOT NULL, default="tool" | 分类（tool/ai/monitor/business） |
| `price` | Integer | NOT NULL, default=0 | 价格（分，0=免费） |
| `menu_path` | String(200) | nullable | 菜单路径（安装后显示） |
| `permission_prefix` | String(100) | nullable | 权限前缀 |
| `dependencies` | Text | nullable | 依赖插件编码（JSON 数组） |
| `sort` | Integer | NOT NULL, default=0 | 排序 |

#### platform_tenant_plugin

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `tenant_id` | FK→platform_tenant.id | NOT NULL, ON DELETE CASCADE | 租户 ID |
| `plugin_id` | FK→platform_plugin.id | NOT NULL, ON DELETE CASCADE | 插件 ID |
| `enabled` | String(1) | NOT NULL, default="1" | 启用（1:启用 0:禁用） |
| `installed_time` | DateTime | NOT NULL | 安装时间 |

唯一约束：`(tenant_id, plugin_id)`

### 18.3 插件目录结构

```
plugin/module_xxx/
├── __init__.py
├── plugin.toml          # 插件元数据（名称、版本、路由前缀等）
├── controller.py
├── service.py
├── crud.py
├── model.py
└── schema.py
```

已内置插件：
- `module_ai/chat` — AI 对话
- `module_example/demo` — 示例
- `module_generator/gencode` — 代码生成器
- `module_task/cronjob` — 定时任务
- `module_task/workflow` — 工作流引擎

### 18.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/plugin/detail/{id}` | 插件详情 |
| GET | `/plugin/list` | 插件列表（含当前租户安装状态） |
| POST | `/plugin/create` | 创建插件 |
| PUT | `/plugin/update/{id}` | 更新插件 |
| DELETE | `/plugin/delete` | 删除插件（批量） |
| POST | `/plugin/install` | 租户安装插件 |
| POST | `/plugin/uninstall` | 租户卸载插件 |

---

## 19. 到期处理

### 19.1 到期阶段定义

租户到期后分三个阶段处理，避免粗暴直接禁用（编码与 §15.2 生命周期统一）：

| 阶段 | 编码 | 说明 |
|------|------|------|
| `active` | 0 | 正常，在有效期内 |
| `grace` | 1 | 宽限期：到期后可登录但每次登录提示续费，功能正常 |
| `suspended` | 2 | 暂停：宽限期结束后禁用写操作，仅可查看数据 |
| `expired` | 4 | 过期：暂停超过保留期后，禁止登录 |

**阶段流转**（与生命周期统一）：
```
active(0) → grace(1) → suspended(2) → expired(4) → archived(5)
   ↑            │            │
   └── 续期 ←──┘────────────┘
```

### 19.2 自动处理逻辑

定时任务 `check_tenant_expiry` 定期扫描所有正常状态的租户：

1. 遍历 status=0(active) 或 status=1(grace) 或 status=2(suspended) 的租户
2. **未到达生效时间**：`start_time` 存在且 `start_time > now` → 暂不处理，登录时提示"租户尚未生效"
3. **进入宽限期**：status=0 且 `end_time` 存在且 `now > end_time` → 设 `status=1`，记录 `grace_start_time`
4. **进入暂停**：status=1(grace) 且 `now > grace_start_time + grace_period_days`（默认7天）→ 设 `status=2`(suspended)
5. **进入过期**：status=2(suspended) 且暂停超过 `expire_after_days`（默认30天）→ 设 `status=4`(expired)
6. **宽限期内续期**：若 status=1/2 时发现 `end_time` 已续期至未来 → 恢复 `status=0`(active)，清除 `grace_start_time`
7. **即将到期提醒**：`end_time` 在 30天/7天/1天 内 → 触发到期提醒

### 19.3 各阶段行为

| 阶段 | 登录 | 读操作 | 写操作 | 提示 |
|------|------|--------|--------|------|
| active(0) | ✅ | ✅ | ✅ | 无 |
| grace(1) | ✅ | ✅ | ✅ | 每次登录弹窗提示"您的租户已到期，请尽快续费" |
| suspended(2) | ✅ | ✅ | ❌ 拒绝写入 | 提示"租户已暂停，请联系管理员续费" |
| expired(4) | ❌ | — | — | 提示"租户已过期" |

### 19.4 到期配置参数

| 字段 | 位置 | 说明 |
|------|------|------|
| `grace_period_days` | `platform_tenant` 表，Integer，default=7 | 宽限期天数 |
| `expire_after_days` | 全局配置，Integer，default=30 | 暂停→过期天数（suspended 超过此天数后自动标记为 expired） |
| `archive_after_days` | 全局配置，Integer，default=30 | frozen/expired 超过此天数后自动归档为 archived(5) |

### 19.5 提醒方式

| 触点 | 触发时机 | 渠道 |
|------|---------|------|
| 30天前 | `end_time - 30d <= now` | 站内信（sys_notice） |
| 7天前 | `end_time - 7d <= now` | 站内信 + 邮件（contact_email） |
| 1天前 | `end_time - 1d <= now` | 站内信 + 邮件 + 短信（contact_phone，可选） |
| 已到期（grace） | 每次登录 | 弹窗提示 |

当前邮件/短信为预留扩展点，未配置渠道时降级为站内信。

---

# Part 3：附录

---

## 20. API 接口汇总

### 20.1 认证模块

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | 登录 |
| POST | `/auth/token/refresh` | 刷新 token |
| POST | `/auth/logout` | 退出登录 |
| GET | `/auth/captcha` | 验证码 |
| POST | `/auth/register` | 用户注册（自动创建默认租户） |
| POST | `/auth/select-tenant/{id}` | 选择租户（生成正式 token） |
| GET | `/auth/tenants` | 获取可选租户列表 |
| POST | `/auth/forgot-password` | 忘记密码 |
| GET | `/auth/auto-login/users` | 获取免登录用户列表 |
| POST | `/auth/auto-login/token` | 获取免登录Token |
| POST | `/auth/auto-login` | 免登录 |
| GET | `/auth/oauth/{provider}/login` | OAuth2 授权跳转 |
| GET | `/auth/oauth/{provider}/callback` | OAuth2 回调处理 |

### 20.2 用户模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/user/detail/{id}` | user:query | 详情 |
| GET | `/user/list` | user:query | 列表 |
| POST | `/user/create` | user:create | 创建 |
| PUT | `/user/update/{id}` | user:update | 更新 |
| DELETE | `/user/delete` | user:delete | 删除 |
| PATCH | `/user/status/batch` | user:patch | 批量设状态 |
| GET | `/user/current/info` | - | 当前用户信息 |
| PUT | `/user/current/info/update` | - | 更新当前用户 |
| PUT | `/user/password/change` | - | 改密码（本人操作） |
| PUT | `/user/password/reset/{id}` | user:update | 重置密码（管理员操作） |
| GET | `/user/import/template` | user:download | 导入模板 |
| POST | `/user/import/data` | user:import | 导入 |
| POST | `/user/export` | user:query | 导出 |

### 20.3 角色模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/role/detail/{id}` | role:query | 详情 |
| GET | `/role/list` | role:query | 列表 |
| POST | `/role/create` | role:create | 创建 |
| PUT | `/role/update/{id}` | role:update | 更新 |
| DELETE | `/role/delete` | role:delete | 删除 |
| PATCH | `/role/status/batch` | role:patch | 批量设状态 |
| PUT | `/role/menus` | role:update | 设置菜单 |
| PUT | `/role/permission` | role:update | 设置权限 |

### 20.4 部门模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/dept/detail/{id}` | dept:query | 详情 |
| GET | `/dept/list` | dept:query | 列表 |
| POST | `/dept/create` | dept:create | 创建 |
| PUT | `/dept/update/{id}` | dept:update | 更新 |
| DELETE | `/dept/delete` | dept:delete | 删除 |
| PATCH | `/dept/status/batch` | dept:patch | 批量设状态 |

### 20.5 岗位模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/position/detail/{id}` | position:query | 详情 |
| GET | `/position/list` | position:query | 列表 |
| POST | `/position/create` | position:create | 创建 |
| PUT | `/position/update/{id}` | position:update | 更新 |
| DELETE | `/position/delete` | position:delete | 删除 |
| PATCH | `/position/status/batch` | position:patch | 批量设状态 |

### 20.6 菜单模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/menu/detail/{id}` | menu:query | 详情 |
| GET | `/menu/list` | menu:query | 列表 |
| POST | `/menu/create` | menu:create | 创建 |
| PUT | `/menu/update/{id}` | menu:update | 更新 |
| DELETE | `/menu/delete` | menu:delete | 删除 |
| PATCH | `/menu/status/batch` | menu:patch | 批量设状态 |

### 20.7 字典模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/dict/type/detail/{id}` | dict:query | 字典类型详情 |
| GET | `/dict/type/list` | dict:query | 字典类型列表 |
| POST | `/dict/type/create` | dict:create | 创建字典类型 |
| PUT | `/dict/type/update/{id}` | dict:update | 更新字典类型 |
| DELETE | `/dict/type/delete` | dict:delete | 删除字典类型 |
| PATCH | `/dict/type/status/batch` | dict:patch | 批量设状态 |
| GET | `/dict/data/detail/{id}` | dict:query | 字典数据详情 |
| GET | `/dict/data/list` | dict:query | 字典数据列表 |
| POST | `/dict/data/create` | dict:create | 创建字典数据 |
| PUT | `/dict/data/update/{id}` | dict:update | 更新字典数据 |
| DELETE | `/dict/data/delete` | dict:delete | 删除字典数据 |

### 20.8 通知公告

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/notice/detail/{id}` | notice:query | 详情 |
| GET | `/notice/list` | notice:query | 列表 |
| POST | `/notice/create` | notice:create | 创建 |
| PUT | `/notice/update/{id}` | notice:update | 更新 |
| DELETE | `/notice/delete` | notice:delete | 删除 |
| PATCH | `/notice/status/batch` | notice:patch | 批量设状态 |

### 20.9 系统参数

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/param/detail/{id}` | params:query | 详情 |
| GET | `/param/list` | params:query | 列表 |
| POST | `/param/create` | params:create | 创建 |
| PUT | `/param/update/{id}` | params:update | 更新 |
| DELETE | `/param/delete` | params:delete | 删除 |
| PATCH | `/param/status/batch` | params:patch | 批量设置状态 |

### 20.10 登录日志模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/platform/loginlog/detail/{id}` | module_platform:loginlog:query | 详情 |
| GET | `/platform/loginlog/list` | module_platform:loginlog:query | 列表 |
| DELETE | `/platform/loginlog/delete` | module_platform:loginlog:delete | 删除（批量） |

### 20.11 操作日志模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/system/operationlog/detail/{id}` | module_system:operationlog:query | 详情 |
| GET | `/system/operationlog/list` | module_system:operationlog:query | 列表 |
| DELETE | `/system/operationlog/delete` | module_system:operationlog:delete | 删除（批量） |

### 20.12 工单模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/ticket/detail/{id}` | ticket:query | 详情 |
| GET | `/ticket/list` | ticket:query | 列表 |
| POST | `/ticket/create` | ticket:create | 创建 |
| PUT | `/ticket/update/{id}` | ticket:update | 更新 |
| DELETE | `/ticket/delete` | ticket:delete | 删除 |
| PATCH | `/ticket/status/batch` | ticket:patch | 批量设置状态 |

### 20.13 插件模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/plugin/detail/{id}` | plugin:query | 详情 |
| GET | `/plugin/list` | plugin:query | 列表 |
| POST | `/plugin/create` | plugin:create | 创建 |
| PUT | `/plugin/update/{id}` | plugin:update | 更新 |
| DELETE | `/plugin/delete` | plugin:delete | 删除 |
| PATCH | `/plugin/status/batch` | plugin:patch | 批量设置状态 |
| POST | `/plugin/install` | - | 安装插件 |
| POST | `/plugin/uninstall` | - | 卸载插件 |

### 20.14 租户模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/tenant/detail/{id}` | tenant:query | 详情 |
| GET | `/tenant/list` | tenant:query | 列表 |
| POST | `/tenant/create` | tenant:create | 创建 |
| PUT | `/tenant/update/{id}` | tenant:update | 更新 |
| DELETE | `/tenant/delete` | tenant:delete | 删除 |
| PATCH | `/tenant/status/batch` | tenant:patch | 批量设置状态 |
| PUT | `/tenant/status/{id}` | tenant:update | 启/禁用 |
| GET | `/tenant/{id}/users` | tenant:query | 用户列表 |
| POST | `/tenant/{id}/users` | tenant:update | 添加用户 |
| DELETE | `/tenant/{id}/users/{uid}` | tenant:update | 移除用户 |
| GET | `/tenant/{id}/quota` | tenant:query | 获取配额 |
| PUT | `/tenant/{id}/quota` | tenant:update | 修改配额 |
| GET | `/tenant/{id}/config` | tenant:query | 获取配置 |
| PUT | `/tenant/{id}/config` | tenant:update | 更新配置 |

### 20.15 套餐模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/platform/package/detail/{id}` | package:query | 详情 |
| GET | `/platform/package/list` | package:query | 列表 |
| POST | `/platform/package/create` | package:create | 创建 |
| PUT | `/platform/package/update/{id}` | package:update | 更新 |
| DELETE | `/platform/package/delete` | package:delete | 删除 |
| GET | `/platform/package/{id}/menus` | package:query | 获取菜单 |
| PUT | `/platform/package/{id}/menus` | package:update | 设置菜单 |

### 20.16 监控模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/monitor/online/list` | module_monitor:online:query | 在线用户列表 |
| DELETE | `/monitor/online/delete` | module_monitor:online:delete | 强制下线 |
| DELETE | `/monitor/online/clear` | module_monitor:online:delete | 清空所有在线用户 |
| GET | `/monitor/cache/info` | module_monitor:cache:query | 获取缓存监控统计 |
| GET | `/monitor/cache/get/names` | module_monitor:cache:query | 获取缓存名称列表 |
| GET | `/monitor/cache/get/keys/{cache_name}` | module_monitor:cache:query | 获取缓存键名列表 |
| GET | `/monitor/cache/get/value/{cache_name}/{cache_key}` | module_monitor:cache:query | 获取缓存值 |
| DELETE | `/monitor/cache/delete/name/{cache_name}` | module_monitor:cache:delete | 清除指定缓存名称 |
| DELETE | `/monitor/cache/delete/key/{cache_key}` | module_monitor:cache:delete | 清除指定缓存键 |
| DELETE | `/monitor/cache/clear` | module_monitor:cache:delete | 清除所有缓存 |
| GET | `/monitor/resource/list` | module_monitor:resource:query | 目录列表(分页) |
| POST | `/monitor/resource/upload` | module_monitor:resource:upload | 上传文件 |
| GET | `/monitor/resource/download` | module_monitor:resource:download | 下载文件 |
| DELETE | `/monitor/resource/delete` | module_monitor:resource:delete | 删除文件 |
| POST | `/monitor/resource/move` | module_monitor:resource:move | 移动文件 |
| POST | `/monitor/resource/copy` | module_monitor:resource:copy | 复制文件 |
| POST | `/monitor/resource/rename` | module_monitor:resource:rename | 重命名文件 |
| POST | `/monitor/resource/mkdir` | module_monitor:resource:mkdir | 创建目录 |
| POST | `/monitor/resource/export` | module_monitor:resource:export | 导出资源列表 |
| GET | `/monitor/server/info` | module_monitor:server:query | 服务器监控信息 |

### 20.17 文件与健康探针

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| POST | `/file/upload` | module_common:file:upload | 上传文件 |
| POST | `/file/download` | module_common:file:download | 下载文件 |
| GET | `/monitor/health` | — | 基础健康检查 |
| GET | `/monitor/health/live` | — | 存活探针 |
| GET | `/monitor/health/ready` | — | 就绪探针 |
| GET | `/monitor/health/stream` | — | 健康实时流（SSE，30s 快照） |
| GET | `/metrics` | — | Prometheus 指标端点 |

### 20.18 邮件服务

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/platform/email/config` | platform:email:query | 获取 SMTP 配置 |
| PUT | `/platform/email/config` | platform:email:update | 更新 SMTP 配置 |
| POST | `/platform/email/test` | platform:email:update | 发送测试邮件 |
| GET | `/platform/email/template/list` | platform:email:query | 模板列表 |
| POST | `/platform/email/template/create` | platform:email:create | 创建模板 |
| PUT | `/platform/email/template/update/{id}` | platform:email:update | 更新模板 |
| GET | `/platform/email/log/list` | platform:email:query | 发送日志列表 |

### 20.19 订单与支付

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| POST | `/platform/order/create` | platform:order:create | 创建订单 |
| GET | `/platform/order/detail/{id}` | platform:order:query | 订单详情 |
| GET | `/platform/order/list` | platform:order:query | 订单列表 |
| POST | `/platform/order/cancel/{id}` | platform:order:update | 取消订单 |
| POST | `/platform/payment/callback/alipay` | — | 支付宝回调 |
| POST | `/platform/payment/callback/wxpay` | — | 微信支付回调 |
| GET | `/platform/payment/record/list` | platform:payment:query | 支付记录列表 |

### 20.20 租户自助服务

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/tenant/package/available` | tenant:package:query | 可选套餐列表 |
| GET | `/tenant/package/preview` | tenant:package:query | 套餐变更影响预览 |
| POST | `/tenant/order/create` | tenant:order:create | 创建自助订单 |
| GET | `/tenant/order/list` | tenant:order:query | 我的订单列表 |
| GET | `/tenant/order/detail/{id}` | tenant:order:query | 订单详情 |

### 20.21 用量统计

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/platform/api-usage/daily` | platform:api_usage:query | 按天用量统计 |
| GET | `/platform/api-usage/tenant/{id}` | platform:api_usage:query | 指定租户用量 |
| GET | `/platform/api-usage/rank` | platform:api_usage:query | 租户用量排行 |
| GET | `/platform/api-usage/anomalies` | platform:api_usage:query | 异常调用记录 |

### 20.22 用户邀请

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| POST | `/tenant/invite/send` | tenant:invite:create | 发送邀请 |
| GET | `/tenant/invite/list` | tenant:invite:query | 邀请列表 |
| DELETE | `/tenant/invite/cancel/{id}` | tenant:invite:delete | 取消邀请 |
| GET | `/invite/validate/{code}` | — | 校验邀请码（公开） |
| POST | `/invite/accept/{code}` | — | 接受邀请（需登录） |

### 20.23 发票管理

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| POST | `/tenant/invoice/apply` | tenant:invoice:create | 申请开票 |
| GET | `/tenant/invoice/list` | tenant:invoice:query | 我的发票列表 |
| GET | `/tenant/invoice/{id}/download` | tenant:invoice:download | 下载发票 PDF |
| GET | `/platform/invoice/list` | platform:invoice:query | 全部发票列表 |
| PUT | `/platform/invoice/issue/{id}` | platform:invoice:update | 开具发票 |
| PUT | `/platform/invoice/void/{id}` | platform:invoice:update | 作废发票 |

### 20.24 审计日志

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/platform/audit/list` | platform:audit:query | 审计日志列表 |
| GET | `/platform/audit/detail/{id}` | platform:audit:query | 审计日志详情 |
| GET | `/platform/audit/export` | platform:audit:export | 导出审计日志 |

### 20.25 运营大盘

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/platform/dashboard/overview` | platform:dashboard:query | 运营概览 |
| GET | `/platform/dashboard/revenue` | platform:dashboard:query | 收入趋势 |
| GET | `/platform/dashboard/tenants` | platform:dashboard:query | 租户统计 |
| GET | `/platform/dashboard/api-usage` | platform:dashboard:query | API 用量趋势 |

---

## 21. 数据库表结构

### 21.1 平台资源表（无 tenant_id）

| 表名 | 说明 | 关键索引 |
|------|------|---------|
| `platform_tenant` | 租户（单一大表，含配额+配置字段） | UNIQUE(name), UNIQUE(code) |
| `platform_package` | 套餐 | UNIQUE(name), UNIQUE(code) |
| `platform_package_menu` | 套餐-菜单关联 | UNIQUE(package_id, menu_id) |
| `platform_menu` | 菜单 | - |
| `platform_plugin` | 插件注册表 | UNIQUE(name), UNIQUE(code) |
| `platform_email_config` | 邮件 SMTP 配置 | 单例表 |
| `platform_email_template` | 邮件模板 | UNIQUE(code) |
| `platform_email_log` | 邮件发送日志 | - |
| `platform_order` | 订单 | UNIQUE(order_no) |
| `platform_payment_record` | 支付记录 | UNIQUE(transaction_id) |

### 21.2 租户关联表（FK→tenant，无独立 tenant_id 列）

| 表名 | 说明 | 关键索引 |
|------|------|---------|
| `platform_tenant_menu` | 租户自定义菜单 | UNIQUE(tenant_id, menu_id) |
| `platform_tenant_plugin` | 租户安装插件 | UNIQUE(tenant_id, plugin_id) |
| `platform_user_tenant` | 用户-租户关联 | UNIQUE(user_id, tenant_id) |

### 21.3 平台级租户关联业务表（含 tenant_id）

| 表名 | 说明 | 关键索引 |
|------|------|---------|
| `platform_invite_record` | 用户邀请记录 | UNIQUE(invite_code) |
| `platform_api_usage_daily` | API 用量日统计 | UNIQUE(tenant_id, date, api_path) |

### 21.4 租户隔离业务表（含 tenant_id）

| 表名 | 说明 | 关键索引 |
|------|------|---------|
| `sys_user` | 用户 | UNIQUE(tenant_id, username) |
| `sys_role` | 角色 | UNIQUE(tenant_id, code) |
| `sys_dept` | 部门 | UNIQUE(tenant_id, code) |
| `sys_position` | 岗位 | - |
| `sys_notice` | 通知公告 | - |
| `sys_param` | 系统参数 | - |
| `sys_operation_log` | 操作日志（租户隔离） | - |
| `platform_login_log` | 登录日志（平台级，无 tenant_id） | - |
| `platform_ticket` | 工单 | - |

### 21.4 平台共享业务表（含 tenant_id，__platform_data_shared__）

| 表名 | 说明 | 关键索引 |
|------|------|---------|
| `sys_dict_type` | 字典类型 | UNIQUE(tenant_id, dict_type) |
| `sys_dict_data` | 字典数据 | UNIQUE(tenant_id, dict_type_id, dict_value) |

### 21.5 关联表

| 表名 | 说明 | 约束 |
|------|------|------|
| `sys_user_roles` | 用户-角色关联 | PK(user_id, role_id)，ON DELETE CASCADE |
| `sys_user_positions` | 用户-岗位关联 | PK(user_id, position_id)，ON DELETE CASCADE |
| `sys_role_menus` | 角色-菜单关联 | PK(role_id, menu_id)，ON DELETE CASCADE |
| `sys_role_depts` | 角色-部门关联 | PK(role_id, dept_id)，ON DELETE CASCADE |
| `sys_notice_read` | 通知已读记录 | PK(user_id, notice_id)，ON DELETE CASCADE |

### 21.6 插件表

| 表名 | 模块 | 说明 | 前缀规则 |
|------|------|------|---------|
| `task_workflow` | module_task/workflow | 工作流定义 | `task_` = module_task |
| `task_workflow_node_type` | module_task/workflow | 工作流节点类型 | `task_` = module_task |
| `task_node` | module_task/cronjob | 定时任务节点类型 | `task_` = module_task |
| `task_job` | module_task/cronjob | 任务执行日志 | `task_` = module_task |
| `gen_table` | module_generator/gencode | 代码生成表 | `gen_` = module_generator |
| `gen_table_column` | module_generator/gencode | 代码生成字段 | `gen_` = module_generator |
| `example_demo` | module_example/demo | 示例表 | `example_` = module_example |
| `example_demo01` | module_example/demo01 | 示例表01 | `example_` = module_example |

> **命名规范**：`platform_` = 平台模块，`sys_` = 系统模块，`task_` = 任务插件，`gen_` = 生成器插件，`example_` = 示例模块

### 21.7 商业运营表

| 表名 | 模块 | 说明 |
|------|------|------|
| `platform_invoice` | Invoice | 发票记录 |
| `platform_refund` | Order | 退款记录 |
| `platform_audit_log` | AuditLog | 审计日志 |

---

## 22. 安全性要求

1. **JWT 租户上下文**：从 Token 中提取 `tenant_id` 和 `is_super_admin`，通过 ContextVar 在整个请求周期传递
2. **白名单路径**：登录、验证码、健康检查等公开接口不设置租户上下文
3. **系统租户保护**：
   - id=1 不可删除
   - id=1 不可禁用
   - id=1 的编码不可修改
4. **数据删除保护**：删除租户前检查关联数据，防止孤立记录
5. **租户 owner 保护**：每个租户至少保留一个 owner
6. **菜单越权防护**：非超管用户只能在租户可用菜单范围内分配角色菜单
7. **ContextVar 清理**：请求结束后清理 ContextVar，防止跨请求泄漏
8. **密码安全**：Bcrypt 哈希存储，不存储明文；普通用户密码最低 8 位（含字母+数字）；初始管理员密码 12 位随机（含大小写字母+数字+特殊字符）
9. **XSS 防护**：通知公告内容经过 `sanitize_html` 清洗
10. **登录限流**：同一 IP/账号连续登录失败 5 次后锁定 15 分钟（Redis 计数 + TTL），防止暴力破解
11. **级联策略**：所有 FK 均有 ON DELETE/ON UPDATE 级联策略，保证数据完整性
12. **路径越权防护**：文件资源管理禁止路径遍历（`..`），防止越权访问
13. **CORS 配置**：通过白名单配置允许的来源域名，拒绝未授权的跨域请求

---

## 23. Email 邮件服务模块

### 23.1 业务描述

邮件服务是 SaaS 平台的通信基础设施，为密码重置、邀请通知、到期提醒、工单通知等业务提供统一的邮件发送能力。支持 SMTP 配置、模板管理、发送日志追踪。

### 23.2 数据模型

#### platform_email_config

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `smtp_host` | String(255) | NOT NULL | SMTP 服务器地址 |
| `smtp_port` | Integer | NOT NULL, default=465 | SMTP 端口 |
| `smtp_username` | String(255) | NOT NULL | SMTP 用户名 |
| `smtp_password` | String(255) | NOT NULL, 加密存储 | SMTP 密码 |
| `sender_name` | String(100) | NOT NULL | 发件人名称 |
| `sender_email` | String(255) | NOT NULL | 发件人邮箱 |
| `use_tls` | Boolean | default=True | 是否使用 TLS |
| `status` | Integer | default=0 | 状态（0:启用 1:禁用） |

> 单例表：仅一条记录。超管在平台配置中管理。

#### platform_email_template

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `code` | String(50) | NOT NULL, UNIQUE | 模板编码（如 `password_reset`、`tenant_invite`、`expiry_reminder`、`ticket_notify`） |
| `name` | String(100) | NOT NULL | 模板名称 |
| `subject` | String(255) | NOT NULL | 邮件主题（支持 `{变量}` 占位符） |
| `body` | Text | NOT NULL | 邮件正文（HTML，支持 `{变量}` 占位符） |
| `variables` | Text | nullable | 可用变量说明（JSON 数组，如 `["{username}", "{reset_link}"]`） |
| `status` | Integer | default=0 | 状态（0:启用 1:禁用） |

#### platform_email_log

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `template_code` | String(50) | nullable | 使用的模板编码 |
| `to_email` | String(255) | NOT NULL | 收件人邮箱 |
| `to_user_id` | FK→sys_user.id | nullable | 收件人用户 ID |
| `subject` | String(255) | NOT NULL | 实际发送的主题 |
| `body` | Text | NOT NULL | 实际发送的正文（渲染后） |
| `status` | Integer | NOT NULL, default=0 | 发送状态（0:待发送 1:成功 2:失败） |
| `error_msg` | Text | nullable | 失败原因 |
| `sent_time` | DateTime | nullable | 实际发送时间 |
| `retry_count` | Integer | default=0 | 重试次数 |

### 23.3 业务规则

| 规则 | 说明 |
|------|------|
| **发送模式** | 支持同步发送和异步队列两种模式。默认异步（Redis 队列），避免阻塞主请求 |
| **重试策略** | 发送失败自动重试，最多 3 次，间隔 5 分钟。3 次仍失败则标记失败状态 |
| **频率限制** | 同一收件人同一模板 1 小时内最多发送 5 封，防止滥用 |
| **模板渲染** | 调用 `send_email(template_code, to, variables)` 时，自动从模板渲染 `subject` 和 `body` |
| **链路追踪** | 每次发送记录 `platform_email_log`，关联 `template_code` 和 `to_user_id` |

### 23.4 业务集成点

| 场景 | 模板编码 | 触发时机 | 变量 |
|------|---------|---------|------|
| **密码重置** | `password_reset` | 创建租户初始管理员 / 用户忘记密码 | `{username}`, `{reset_link}` |
| **租户邀请** | `tenant_invite` | 管理员邀请用户加入租户 | `{inviter}`, `{tenant_name}`, `{invite_link}` |
| **到期提醒(30/7/1天)** | `expiry_reminder` | 定时任务检测到期 | `{tenant_name}`, `{expire_date}`, `{days_left}` |
| **工单通知** | `ticket_notify` | 工单创建/分配/关闭 | `{ticket_title}`, `{status}`, `{assignee}` |
| **套餐变更通知** | `package_change` | 租户套餐被超管变更 | `{old_package}`, `{new_package}`, `{removed_menus}` |

### 23.5 降级策略

当邮件服务不可用时（SMTP 故障、配置缺失），自动降级为**站内信**（`sys_notice`），确保关键信息不丢失。

### 23.6 API 端点

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/platform/email/config` | 获取 SMTP 配置 | 超管 |
| PUT | `/platform/email/config` | 更新 SMTP 配置 | 超管 |
| POST | `/platform/email/test` | 发送测试邮件 | 超管 |
| GET | `/platform/email/template/list` | 模板列表 | 超管 |
| POST | `/platform/email/template/create` | 创建模板 | 超管 |
| PUT | `/platform/email/template/update/{id}` | 更新模板 | 超管 |
| GET | `/platform/email/log/list` | 发送日志列表 | 超管 |

---

## 24. Order 订单与支付模块

### 24.1 业务描述

订单与支付模块是 SaaS 平台的商业化基础，覆盖订单创建、支付回调、开通激活、续费/升级的完整交易闭环。对接支付宝和微信支付，支持套餐购买、续费和升级三种业务场景。

### 24.2 业务流程

```
用户/超管选择套餐 → 生成订单 → 跳转支付 → 支付回调 → 激活/变更套餐
                             ↓ 超时(15分钟)
                          订单自动取消
```

### 24.3 数据模型

#### platform_order

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `order_no` | String(32) | NOT NULL, UNIQUE | 订单号（年月日+6位随机数） |
| `tenant_id` | FK→platform_tenant.id | NOT NULL | 购买租户 |
| `package_id` | FK→platform_package.id | NOT NULL | 购买套餐 |
| `order_type` | String(20) | NOT NULL | 类型：`new`(新购) `renew`(续费) `upgrade`(升级) `downgrade`(降级) |
| `amount` | Integer | NOT NULL | 金额（分，≥0；0=免费套餐） |
| `period_count` | Integer | NOT NULL, default=1 | 购买周期数（1个月=1） |
| `status` | Integer | NOT NULL, default=0 | 状态：0=待支付 1=已支付 2=已取消 3=已退款 |
| `pay_method` | String(20) | nullable | 支付方式：`alipay`(支付宝) / `wxpay`(微信支付) |
| `pay_time` | DateTime | nullable | 支付时间 |
| `expire_time` | DateTime | NOT NULL | 订单过期时间（创建后+15分钟），超时未支付自动取消 |

#### platform_payment_record

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `order_id` | FK→platform_order.id | NOT NULL | 关联订单 |
| `transaction_id` | String(64) | nullable | 第三方交易号 |
| `pay_method` | String(20) | NOT NULL | 支付方式 |
| `amount` | Integer | NOT NULL | 支付金额（分） |
| `status` | Integer | NOT NULL | 支付结果：0=处理中 1=成功 2=失败 |
| `raw_response` | Text | nullable | 支付平台原始回调数据（JSON） |
| `pay_time` | DateTime | nullable | 支付完成时间 |

### 24.4 支付回调处理流程

```
POST /platform/payment/callback/{method}
  ├── IP 白名单校验（仅允许支付宝/微信支付官方 IP 段）
  ├── 验证签名（支付宝 RSA / 微信支付 APIv3 签名）
  ├── 分布式锁（Redis SETNX，key=callback_lock:{transaction_id}，TTL=30s）
  ├── 校验金额一致性（回调金额 == 订单金额）
  ├── 校验订单状态（仅 status=0(待支付) 可处理，防止重复激活）
  ├── 更新 platform_order.status=1、pay_time=now
  ├── 写入 platform_payment_record（transaction_id UNIQUE 约束，第二次写入自动失败）
  ├── 根据 order_type 执行激活逻辑：
  │   ├── new/renew → 更新 tenant.end_time、恢复 status=0(active)
  │   ├── upgrade   → 更新 tenant.package_id、执行套餐变更影响预览逻辑（菜单+配额同步）
  │   └── downgrade → 更新 tenant.package_id、清理超出的菜单关联、更新配额
  ├── 发送通知给租户管理员（邮件 + 站内信）
  ├── 释放分布式锁
  └── 返回 success 给支付平台（防止重复回调）
```

> **安全要点**：
> - IP 白名单：仅允许支付宝/微信支付的官方回调 IP，在 Nginx/LB 层配置
> - 分布式锁：解决支付平台可能同时回调多条相同交易的并发问题
> - 状态校验：status≠0 的订单拒绝处理，防止恶意/重复回调
> - 金额校验：回调金额与订单金额不一致时，标记异常并人工介入

### 24.5 业务规则

| 规则 | 说明 |
|------|------|
| **订单号生成** | `{YYYYMMDD}{6位随机数字}`，创建时检查唯一性 |
| **过期取消** | 定时任务 `cancel_expired_orders` 每分钟扫描 status=0 且 `expire_time < now` 的订单，设为 status=2(已取消) |
| **幂等性** | 同一 `transaction_id` 的回调只处理一次（transaction_id UNIQUE 约束 + 分布式锁双重保障） |
| **金额校验** | 回调金额必须与订单金额一致，不一致则拒绝并告警 |
| **IP 白名单** | 回调接口仅允许支付宝/微信支付官方 IP 调用，在 Nginx/负载均衡层配置 |
| **免费套餐** | amount=0 时不跳转支付，直接走激活流程 |
| **退款** | 退款为预留扩展，当前仅支持手动标记 status=3 |

### 24.7 退款流程

```
租户管理员申请退款
  ├── POST /tenant/order/refund/apply/{order_id}
  │     条件：订单 status=1(已支付) 且支付时间在 7 天内
  │     body: {reason: "误购/重复支付/服务不满意"}
  ├── 更新 platform_order.refund_status=1(申请中)
  ├── 创建 platform_refund 记录
  ├── 通知超管审核（站内信）
  └── 返回申请结果

超管审核退款
  ├── GET /platform/refund/list（待审核列表）
  ├── PUT /platform/refund/approve/{id}
  │     触发原路退款（调用支付宝/微信退款 API）
  │     更新 platform_refund.status=2(已退款)
  │     更新 platform_order.status=3(已退款)
  │     更新租户套餐（撤销本次购买升级效果，恢复至购买前套餐/到期时间）
  └── PUT /platform/refund/reject/{id}
        更新 platform_refund.status=3(已驳回)
        记录驳回原因
```

#### platform_refund

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `order_id` | FK→platform_order.id | NOT NULL, UNIQUE | 关联订单 |
| `refund_no` | String(32) | NOT NULL, UNIQUE | 退款单号 |
| `amount` | Integer | NOT NULL | 退款金额（分） |
| `reason` | Text | NOT NULL | 退款原因 |
| `status` | Integer | NOT NULL, default=1 | 1=申请中 2=已退款 3=已驳回 4=已取消 |
| `refund_transaction_id` | String(64) | nullable | 退款交易号（第三方返回） |
| `reviewer_id` | FK→sys_user.id | nullable | 审核人 |
| `review_time` | DateTime | nullable | 审核时间 |
| `reject_reason` | Text | nullable | 驳回原因 |

| **退款规则** | 说明 |
|------|------|
| **可退款条件** | 支付后 7 天内，订单 status=1(已支付) |
| **退款金额** | 全额退款（暂不支持部分退款） |
| **退款方式** | 原路退回（支付宝→支付宝，微信→微信） |
| **套餐回退** | 退款后恢复至购买前的套餐和到期时间（若为升级/降级订单） |
| **降级补偿** | 若退款订单为降级类型，退款后套餐回升至降级前套餐 |
| **免费套餐** | amount=0 的免费套餐订单不支持退款 |

### 24.8 API 端点

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/platform/order/create` | 创建订单 | 超管 |
| GET | `/platform/order/detail/{id}` | 订单详情 | 超管 |
| GET | `/platform/order/list` | 订单列表 | 超管 |
| POST | `/platform/order/cancel/{id}` | 取消订单 | 超管 |
| POST | `/platform/payment/callback/alipay` | 支付宝回调（外网可访问，签名验证） | 公开 |
| POST | `/platform/payment/callback/wxpay` | 微信支付回调（外网可访问，签名验证） | 公开 |
| GET | `/platform/payment/record/list` | 支付记录列表 | 超管 |
| POST | `/tenant/order/create` | 租户端创建订单（自助购买/续费/升级） | 租户管理员 |
| POST | `/tenant/order/refund/apply/{id}` | 申请退款 | 租户管理员 |
| GET | `/platform/refund/list` | 退款审核列表 | 超管 |
| PUT | `/platform/refund/approve/{id}` | 批准退款（触发原路退回） | 超管 |
| PUT | `/platform/refund/reject/{id}` | 驳回退款 | 超管 |

---

## 25. TenantSelfService 租户自助服务（代码位于 module_platform/self_service）

### 25.1 业务描述

租户管理员可在租户管理后台自助选择套餐、购买、续费或升级，无需超管介入。是 SaaS 产品商业化的核心用户侧功能。

### 25.2 自助套餐选择流程

```
GET /tenant/package/available
  ├── 返回所有启用的套餐列表
  ├── 标注当前套餐（is_current=true）
  ├── 展示价格/周期/试用天数/功能对比
  ├── 标注可执行的操作：[购买][续费][升级][降级]
  └── 限制：同一套餐已是当前套餐时不展示"升级"按钮

用户选择操作 → 创建订单 → 支付 → 自动激活
```

### 25.3 套餐变更影响预览（自助版）

```json
// GET /tenant/package/preview?target_package_id=xxx 返回
{
  "current_package": "basic",
  "target_package": "pro",
  "action": "upgrade",
  "amount": 29900,
  "period": "month",
  "gained_menus": [
    {"name": "数据报表", "path": "/report/dashboard"},
    {"name": "API 管理", "path": "/api/manage"}
  ],
  "lost_menus": [],
  "affected_roles": [],
  "affected_users": 0
}
```

### 25.4 自助升级/降级流程

```
POST /tenant/order/create (body: {package_id, order_type: "upgrade"})
  ├── 校验权限：租户管理员及以上
  ├── 校验租户状态：仅 active(0)/grace(1)/suspended(2) 可操作
  ├── 校验目标套餐：状态启用且不等于当前套餐
  ├── amount > 0 → 跳转支付 → 支付回调激活
  ├── amount = 0 → 直接激活（免费套餐切换）
  └── 激活时执行套餐变更影响预览逻辑（同超管操作 §15.3）
```

### 25.5 API 端点

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/tenant/package/available` | 获取可选套餐列表（含当前套餐标记和可执行操作） | 租户管理员 |
| GET | `/tenant/package/preview` | 套餐变更影响预览 | 租户管理员 |
| POST | `/tenant/order/create` | 创建自助订单（购买/续费/升级/降级） | 租户管理员 |
| GET | `/tenant/order/list` | 我的订单列表 | 租户管理员 |
| GET | `/tenant/order/detail/{id}` | 我的订单详情 | 租户管理员 |

---

## 26. APIUsage 用量统计模块

### 26.1 业务描述

租户级别 API 调用量/频率统计，按天/月聚合，支持计费挂钩、安全异常检测和运营分析。

### 26.2 数据模型

#### platform_api_usage_daily

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `tenant_id` | FK→platform_tenant.id | NOT NULL | 租户 |
| `date` | Date | NOT NULL | 统计日期 |
| `api_path` | String(255) | NOT NULL | API 路径 |
| `request_count` | Integer | NOT NULL, default=0 | 请求次数 |
| `total_duration_ms` | BigInt | NOT NULL, default=0 | 总耗时（毫秒） |
| `error_count` | Integer | NOT NULL, default=0 | 错误次数（4xx/5xx） |

> 唯一约束：`UNIQUE(tenant_id, date, api_path)`

### 26.3 统计机制

```
请求中间件（每个 API 调用）
  ├── 提取 tenant_id、api_path、status_code、响应时间
  ├── Redis 计数器原子递增：api_usage:{tenant_id}:{date}:{api_path}:count
  ├── Redis 计数器：api_usage:{tenant_id}:{date}:{api_path}:duration
  ├── 错误计数（status_code >= 400）：api_usage:{tenant_id}:{date}:{api_path}:errors
  └── 定时任务（每小时）：读取 Redis → UPSERT 到 platform_api_usage_daily → 清理旧 Redis key
```

### 26.4 异常检测规则

| 规则 | 条件 | 动作 |
|------|------|------|
| **频率突变** | 同一 API 调用量超过过去 7 天均值的 5 倍 | 站内信告警 |
| **错误率过高** | 错误率 > 20% 且请求数 > 100 | 站内信告警 |
| **高频调用** | 单租户单 API 超过 1000 次/分钟 | 临时限流（返回 429） |

> 限流配置：`rate_limit_enabled`（全局开关），`rate_limit_threshold`（阈值），均可在平台配置中调整。

### 26.5 API 端点

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/platform/api-usage/daily` | 按天用量统计（支持租户/日期范围筛选） | 超管 |
| GET | `/platform/api-usage/tenant/{id}` | 指定租户用量详情 | 超管 |
| GET | `/platform/api-usage/rank` | 租户用量排行 | 超管 |
| GET | `/platform/api-usage/anomalies` | 异常调用记录 | 超管 |

---

## 27. UserInvite 用户邀请流程

### 27.1 业务描述

租户管理员可通过邀请链接或邀请码邀请新用户加入租户。被邀请人通过邮箱接收邀请，点击链接完成注册并自动关联到指定租户和角色。

### 27.2 数据模型

#### platform_invite_record

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `invite_code` | String(32) | NOT NULL, UNIQUE | 邀请码（UUID，一次性链接参数） |
| `tenant_id` | FK→platform_tenant.id | NOT NULL | 目标租户 |
| `target_role_id` | FK→sys_role.id | NOT NULL | 预设角色 |
| `inviter_id` | FK→sys_user.id | NOT NULL | 邀请人 |
| `invitee_email` | String(255) | NOT NULL | 被邀请人邮箱 |
| `status` | Integer | NOT NULL, default=0 | 状态：0=待接受 1=已接受 2=已过期 3=已取消 |
| `expire_time` | DateTime | NOT NULL | 过期时间（创建后+7天） |
| `accepted_user_id` | FK→sys_user.id | nullable | 接受邀请后创建的用户 ID |
| `accepted_time` | DateTime | nullable | 接受时间 |

### 27.3 邀请流程

```
租户管理员发起邀请
  ├── POST /tenant/invite/send
  │     body: {emails: [...], role_id, message?}
  ├── 批量创建 platform_invite_record 行，生成唯一 invite_code
  ├── 发送邮件（模板 `tenant_invite`，含邀请链接）
  ├── 邮件内容：{inviter} 邀请你加入 {tenant_name}，点击链接注册
  └── 链接格式：{domain}/invite/{invite_code}，有效期 7 天

被邀请人接受邀请
  ├── 访问 /invite/{code} 页面
  ├── 校验邀请码：存在、未过期(expire_time > now)、未使用(status=0)
  ├── 如果用户已注册：
  │   ├── 直接关联到租户（sys_user_tenant 插入记录）
  │   ├── 分配预设角色（sys_user_role 插入记录）
  │   └── 更新 invite_record.status=1
  ├── 如果用户未注册：
  │   ├── 跳转到注册页面（邮箱已预填，不可修改）
  │   ├── 用户完成注册
  │   ├── 自动关联到租户，分配预设角色
  │   └── 更新 invite_record.status=1, accepted_user_id
  └── 通知邀请人"XXX 已接受您的邀请"
```

### 27.4 业务规则

| 规则 | 说明 |
|------|------|
| **邀请码唯一性** | 每次生成全局唯一的 UUID，即使同一邮箱被重复邀请也不同 |
| **有效期** | 默认 7 天，到期后自动标记 status=2（过期），不再可用 |
| **重复邀请** | 同一租户内，同一邮箱有"待接受"的邀请时，提示"该邮箱已有待接受的邀请"，不重复发送 |
| **角色预分配** | 被邀请人加入租户时自动获得 `target_role_id` 指定的角色 |
| **权限** | 仅租户管理员(owner/admin)可发送邀请 |
| **邀请人可见** | 可查看自己发出的邀请列表及状态 |
| **降级** | 若邮件服务不可用，邀请码可通过站内消息手动复制链接 |

### 27.5 过期清理

定时任务 `cleanup_expired_invites` 每天扫描 `status=0` 且 `expire_time < now` 的记录，标记为 status=2。

### 27.6 API 端点

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/tenant/invite/send` | 发送邀请 | 租户管理员 |
| GET | `/tenant/invite/list` | 邀请列表（含状态） | 租户管理员 |
| DELETE | `/tenant/invite/cancel/{id}` | 取消邀请 | 租户管理员 |
| GET | `/invite/validate/{code}` | 校验邀请码（公开接口，返回租户名/邀请人） | 公开 |
| POST | `/invite/accept/{code}` | 接受邀请（需登录） | 登录用户 |

---

## 28. 未来扩展建议

### 28.1 已规划（短期）

1. **知识库/帮助中心**：租户自助查阅帮助文档、常见问题。富文本编辑器管理，支持多语言
2. **数据导出/备份**：租户自助数据导出（CSV/JSON），满足 GDPR/个保法合规要求。平台级全量备份还原（数据库级）
3. **租户自定义域名**：支持通过 `domain` 字段实现租户专属域名，需配合 Nginx 反向代理配置

### 28.2 中期扩展

| 能力 | 说明 | 优先级 |
|------|------|--------|
| **单点登录（SSO）** | 支持 SAML/OIDC 协议，企业客户可使用自有 IdP（如 Okta/Azure AD/自有 LDAP）登录 | 低 |
| **多语言支持** | 租户级 i18n 配置，支持不同租户使用不同语言 | 低 |
| **Webhook 通知** | 关键事件（支付成功/到期提醒/套餐变更）的 webhook 回调，支持第三方集成 | 中 |

### 28.3 API 路径规范

| 问题 | 当前 | 建议 |
|------|------|------|
| 参数模块名不一致 | `/param/`（单数）vs 模块名 `params`（复数） | 统一为 `/param/`（与代码一致） |
| 日志层级问题 | 操作日志 `/system/operationlog/` 与其他模块不统一 | 建议保持现状。登录日志为平台级、操作日志为租户级，层级分开是合理的 |

### 28.4 非功能性需求（NFR）

| 指标 | 要求 |
|------|------|
| **API 响应时间** | P95 ≤ 500ms（查询），P95 ≤ 2s（写入/批操作） |
| **并发用户** | 单实例支持 500+ 并发租户用户（需压测验证） |
| **可用性** | 99.5%（不包含计划运维窗口） |
| **数据安全** | 传输层 TLS 1.3，存储层 Bcrypt/AES-256，日志脱敏（手机号/邮箱部分掩码） |
| **兼容性** | 支持 MySQL 8.0+ / PostgreSQL 14+ / SQLite（开发环境）；Python ≥ 3.12；Node.js ≥ 20 |
| **数据库备份** | 每日全量备份（保留 30 天），每小时增量备份（保留 7 天）。备份异地存储，定期恢复演练（每季度 1 次） |
| **容灾恢复** | RTO ≤ 4 小时，RPO ≤ 1 小时。主库故障时自动切换只读副本，30 分钟内完成主从切换 |
| **版本升级策略** | 数据库迁移采用 Alembic 管理，所有 schema 变更通过 migration 脚本执行。升级前自动备份，升级失败可回滚至上一个备份点。主版本升级需提前通知租户（7 天），次版本/补丁版可灰度发布 |
| **i18n 基础** | 后端 API 错误消息统一使用 i18n key（如 `errors.user.not_found`），前端使用 vue-i18n。初始版本仅提供中文，保留英文翻译文件占位。租户级语言首选项存储在 `platform_tenant.lang` 字段（预留） |
| **缓存键命名规范** | 格式：`{namespace}:{sub_namespace}:{identifier}`。示例：`tenant:config:123`、`api:usage:456:2026-06-03`、`auth:session:abc123`。所有 key 设置 TTL，禁止无过期时间的 key |

---

## 29. 术语表（Glossary）

| 术语 | 英文 | 说明 |
|------|------|------|
| **租户** | Tenant | SaaS 平台上的一个独立组织/客户 |
| **平台资源** | Platform Resource | 无 tenant_id 的资源，所有租户共享（菜单/套餐/插件） |
| **租户资源** | Tenant Resource | 含 tenant_id 的资源，按租户隔离（用户/角色/部门等） |
| **平台共享数据** | Shared Platform Data | tenant_id=1 的字典数据，所有租户可读 |
| **超管** | Super Admin | 平台级管理员，`is_super_admin=true`，可管理所有租户 |
| **租户管理员** | Tenant Admin | 租户内的管理员，角色为 owner/admin |
| **数据权限范围** | Data Scope | 角色绑定的数据可见范围（全部/本部门及子部门/仅本部门等） |
| **RBAC** | Role-Based Access Control | 基于角色的访问控制 |
| **Mixin** | Mixin | SQLAlchemy 混入模式，用于给模型添加通用字段（如 TenantMixin 自动添加 tenant_id） |
| **处理人** | Assignee | 工单中指派的处理人员 |
| **生命周期** | Lifecycle | 租户的完整状态流转路径：active(0)→grace(1)→suspended(2)→expired(4)→archived(5)→deleted。人工冻结路径：active(0)→frozen(3)→archived(5) |
| **宽限期** | Grace Period | 租户到期后的缓冲期（默认7天），允许正常使用但提示续费 |
| **订单** | Order | 套餐购买/续费/升级的交易凭证，关联支付回调激活套餐 |
| **邀请码** | Invite Code | 租户管理员邀请用户加入的一次性链接参数（UUID，7天有效） |
| **用量统计** | API Usage | 租户级别 API 调用量按天聚合统计，用于计费和安全分析 |
| **邮件模板** | Email Template | 预定义的邮件格式（密码重置/邀请/到期提醒），支持变量占位符渲染 |
| **支付回调** | Payment Callback | 支付宝/微信支付完成后异步通知平台更新订单状态的机制 |
| **默认套餐** | Default Package | 标记 is_default=true 的套餐，自助注册时自动选用 |
| **分布式锁** | Distributed Lock | Redis SETNX 实现的并发互斥机制，防止支付回调等场景的重复处理 |
| **数据库迁移** | Database Migration | 使用 Alembic 管理的版本化 schema 变更脚本，支持升级和回滚 |
| **发票** | Invoice | 订单支付后开具的电子发票（增值税普票/专票），一单一票 |
| **审计日志** | Audit Log | 不可篡改的合规操作记录，仅超管可查阅，保留 3 年 |
| **运营大盘** | Dashboard | 平台运营数据的可视化看板，聚合租户/收入/API 用量等核心指标 |
| **原路退回** | Refund | 支付退款按原支付路径返回（支付宝→支付宝，微信→微信） |

---

## 30. 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v3.1.0 | 2026-06-01 | 初始版本，完整的模块化需求文档 |
| v3.2.0 | 2026-06-02 | 新增 Plugin 子模块需求：AI Chat/Cronjob/Workflow/CodeGen/Demo；新增 Monitor 监控模块：Online/Cache/Resource/Server；新增 Common 公共模块：File/Health/Metrics |
| v3.2.1 | 2026-06-03 | **需求审查修复**：修复全部章节子标题编号错位；统一表名为 `platform_*` 前缀（与代码一致）；移除已废弃的 `sys_tenant_quota`/`sys_tenant_config` 独立表引用；拆分 `sys_log` 为 `sys_operation_log` + `platform_login_log`；统一 Auth 端点路径；明确多租户登录临时/正式 token 机制；补充用户注册租户自动创建流程；添加 `start_time` 未生效校验；补充通知公告已读机制；补全 Tenant 模型遗漏字段（description/version/privacy 等）；新增安全性要求（登录限流/密码复杂度/CORS）；更新未来扩展建议 |
| v3.2.2 | 2026-06-03 | **命名规范统一**：修复文档中 `sys_login_log`→`platform_login_log`、`sys_ticket`→`platform_ticket` 两处表名错误；在 §21 新增 §21.6 插件表汇总（8 张 task_/gen_ 表）；明确全模块命名规范：`platform_`=平台模块，`sys_`=系统模块，`task_`=任务插件，`gen_`=生成器插件 |
| v3.3.0 | 2026-06-03 | **SaaS 产品需求审查修订**：P0-1 租户生命周期状态机（active→frozen→archived→deleted）；P0-2 定时任务/工作流代码执行安全性（任意代码→预定义处理器白名单）；P0-3 套餐模型补充定价字段（price/period/trial_days/max_tenants）；P0-4 初始管理员密码交付改为邮件一次性重置链接；P1-1 通知已读机制改为后端 sys_notice_read 表；P1-2 工单增加 close_reason/closed_time/closed_by 字段；P1-3 租户到期增加宽限期和阶段性处理（grace→suspended→expired）；P1-4 用户导入密码处理策略；P1-5 套餐变更增加影响预览和确认流程；P2 操作日志保留策略、API 路径规范、缺失 SaaS 能力规划（用户邀请/数据导出/API用量/审计日志/SSO）；新增 NFR 非功能性需求、术语表 |
| v3.4.0 | 2026-06-03 | **业务架构闭环补全**：Fix-1 统一 status 编码（String(1)→Integer，合并生命周期与到期阶段编码：0=active/1=grace/2=suspended/3=frozen/4=expired/5=archived）；Fix-2 新增 §23 Email 邮件服务模块（SMTP 配置/模板管理/发送日志/5大业务集成点/站内信降级）；Fix-3 新增 §24 Order 订单与支付模块（订单表/支付记录表/支付宝&微信支付回调/开通续费升级流程）；Fix-4 新增 §25 TenantSelfService 租户自助服务（套餐选择/影响预览/自助升级降级）；Fix-5 新增 §26 APIUsage 用量统计模块（按天聚合/Redis计数器/异常检测/限流）；Fix-6 新增 §27 UserInvite 用户邀请流程（邀请码/邮件邀请/角色预分配/过期清理）；Fix-7 清理残留与全面重编号（移除 §19.4 残留 TODO、§20 新增 §20.18-§20.22 API端点、§21 新增7张新表、§28-§30 重编号、§31-§37 Plugin模块重编号、§29 术语表扩充8个词条、§30 变更记录更新） |
| v3.5.0 | 2026-06-03 | **PRD 正式评审修复**：P0-1 修正 Part 4 Plugin 子模块编号（§31-§37 子节编号 25.x-31.x→31.x-37.x，共 34 处）；P0-2 修复初始管理员体验断层（创建租户时自动创建 owner 角色并分配全量菜单，§6.3/§15.3/§15.4 同步更新）；P0-3 统一 status 字段类型（package/ticket/order/payment/invite 全部从 String→Integer，保持与 tenant.status 一致）；P1-1 标题版本号修正（v3.2.2→v3.5.0）；P1-2 自助注册新增默认套餐/配额/到期时间来源（§4.5 注册流程、§16.2 is_default 字段）；P1-3 套餐配额体系补充（§16.2 新增 max_users/max_roles/max_depts 配额字段）；P1-4 套餐变更同步更新配额（§15.3 增加配额对比预览和升级/降级处理逻辑）；P1-5 支付回调安全细节增强（§24.4/§24.5 新增 IP 白名单、分布式锁、状态校验）；P2-1 API 路径规范（§16.5 套餐路径统一为 /platform/package/）；P2-2 新增数据备份与容灾策略（§28.4 NFR）；P2-3 新增版本升级/迁移策略（§28.4 NFR）；P2-4 新增 i18n 基础设计（§28.4 NFR）；P2-5 新增 Redis 缓存键命名规范（§28.4 NFR）；术语表扩充 4 个词条（默认套餐/分布式锁/数据库迁移/冗余恢复） |
| v3.6.0 | 2026-06-03 | **PRD 100% 完整度达标**：Fix-1 修正 §26.2/§27.2 子节编号错误（32.2→26.2、33.2→27.2）；Fix-2 修正 §28 节编号排序（28.5→28.3、删除重复 28.5）；Fix-3 §24.7 新增退款流程（platform_refund 表、申请→审核→原路退回、套餐回退逻辑）；Fix-4 新增 §38 Invoice 发票管理模块（普票/专票、百望云等第三方对接、一单一票、30天开票时限）；Fix-5 新增 §39 AuditLog 审计日志模块（不可篡改、JSON 变更对比、13 种审计事件、3年保留策略）；Fix-6 新增 §40 Dashboard 运营大盘模块（MRR/退款率/API用量/套餐分布/收入趋势 9 项指标）；Fix-7 更新 §1.4 模块总览（新增 3 个模块）、§20 新增 §20.23-§20.25 API端点、§21 新增 §21.7 商业运营表、§28 移除已实现项、§29 术语表扩充 4 个词条 |



---

# Part 4：Plugin 子模块需求

---

## 31. AI Chat 聊天模块（module_ai/chat）

### 31.1 业务描述

AI 对话模块，提供用户与大模型进行对话的能力。支持多会话管理、WebSocket 流式对话、非流式对话。ChatSession 数据按租户隔离。

### 31.2 数据模型

聊天会话数据存储在 ChatService 后端（支持内存存储/Redis/数据库三种模式，由配置决定）。Schema 层定义如下：

#### ChatSessionCreateSchema

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `title` | str | NOT NULL, min_length=1, max_length=200 | 会话标题 |

#### ChatSessionUpdateSchema

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `title` | str | NOT NULL, min_length=1, max_length=200 | 会话标题 |

#### AiChatRequestSchema

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `message` | str | NOT NULL, min_length=1 | 用户消息内容 |
| `session_id` | str | nullable | 会话ID，不传则创建新会话 |

#### AiChatResponseSchema

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `response` | str | NOT NULL | AI 回复内容 |
| `session_id` | str | NOT NULL | 会话ID |
| `function_calls` | list[dict] | nullable | 函数调用信息 |
| `action` | dict | nullable | 建议执行的操作 |

### 31.3 API 端点

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/chat/detail/{session_id}` | module_ai:chat:detail | 会话详情 |
| GET | `/chat/list` | module_ai:chat:query | 会话列表 |
| POST | `/chat/create` | module_ai:chat:create | 创建会话 |
| PUT | `/chat/update/{session_id}` | module_ai:chat:update | 更新会话 |
| DELETE | `/chat/delete` | module_ai:chat:delete | 删除会话 |
| POST | `/chat/ai-chat` | module_ai:chat:query | AI 对话（非流式） |
| WS | `/chat/ws` | — | WebSocket 流式对话 |

---

## 32. Cronjob 定时任务模块（module_task/cronjob）

### 32.1 业务描述

定时任务模块提供动态节点定义（NodeModel）和任务执行日志记录（JobModel）。节点定义执行代码块、触发器和参数，通过 APScheduler 调度执行。

### 32.2 数据模型

#### NodeModel（task_node，TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(64) | NOT NULL | 节点名称 |
| `code` | String(32) | NOT NULL, UNIQUE(tenant_id, code) | 节点编码 |
| `jobstore` | String(64) | nullable, default="default" | 存储器 |
| `executor` | String(64) | nullable, default="default" | 执行器 |
| `trigger` | String(64) | nullable | 触发器 |
| `trigger_args` | Text | nullable | 触发器参数 |
| `func` | Text | NOT NULL | 预定义处理器标识符（如 `handlers.send_email`）。禁止租户提交任意代码 |
| `args` | Text | nullable | 位置参数 |
| `kwargs` | Text | nullable | 关键字参数 |
| `coalesce` | Boolean | nullable, default=False | 是否合并运行 |
| `max_instances` | Integer | nullable, default=1 | 最大并发实例数 |
| `start_date` | String(64) | nullable | 开始时间 |
| `end_date` | String(64) | nullable | 结束时间 |

#### JobModel（task_job，TenantMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `job_id` | String(64) | NOT NULL, index | 任务ID |
| `job_name` | String(128) | nullable | 任务名称 |
| `trigger_type` | String(32) | nullable | 触发方式：cron/interval/date/manual |
| `status` | String(16) | NOT NULL, default="pending" | 执行状态：pending/running/success/failed/timeout/cancelled |
| `next_run_time` | String(64) | nullable | 下次执行时间 |
| `job_state` | Text | nullable | 任务状态信息 |
| `result` | Text | nullable | 执行结果 |
| `error` | Text | nullable | 错误信息 |

### 32.3 业务规则

| 规则 | 说明 |
|------|------|
| **Node 编码** | 字母开头，仅含字母/数字/下划线 |
| **触发器类型** | 仅支持 now/cron/interval/date |
| **非立即执行** | trigger != "now" 时必须提供 trigger_args |
| **时间校验** | end_date 不能早于 start_date |
| **func 必填** | Node 创建时 func 不能为空，须为已注册的处理器标识符 |
| **处理器白名单** | func 字段只能填写平台预注册的处理器（如 `handlers.send_email`、`handlers.call_api`），禁止填写任意代码。超管可在 `platform_handler_registry` 中注册新处理器 |
| **Job 状态** | 仅支持 pending/running/success/failed/timeout/cancelled |
| **trigger_type** | 仅支持 cron/interval/date/manual |

### 32.4 API 端点

#### Node（节点）

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/cronjob/node/detail/{id}` | module_task:cronjob:query | 节点详情 |
| GET | `/cronjob/node/list` | module_task:cronjob:query | 节点列表 |
| POST | `/cronjob/node/create` | module_task:cronjob:create | 创建节点 |
| PUT | `/cronjob/node/update/{id}` | module_task:cronjob:update | 更新节点 |
| DELETE | `/cronjob/node/delete` | module_task:cronjob:delete | 删除节点 |
| PATCH | `/cronjob/node/status/batch` | module_task:cronjob:patch | 批量设置状态 |
| POST | `/cronjob/node/execute/{id}` | module_task:cronjob:update | 执行节点 |

#### Job（执行日志）

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/cronjob/job/detail/{id}` | module_task:cronjob:query | 日志详情 |
| GET | `/cronjob/job/list` | module_task:cronjob:query | 日志列表 |
| DELETE | `/cronjob/job/delete` | module_task:cronjob:delete | 删除日志 |

---

## 33. Workflow 工作流模块（module_task/workflow）

### 33.1 业务描述

工作流模块提供可视化流程编排和执行能力。基于 Vue Flow 画布定义流程节点和连线，通过 Prefect 引擎执行。数据按租户隔离。

### 33.2 数据模型

#### WorkflowModel（task_workflow，TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(128) | NOT NULL | 流程名称 |
| `code` | String(64) | NOT NULL, UNIQUE(tenant_id, code) | 流程编码 |
| `workflow_status` | String(32) | NOT NULL, default="draft" | 状态：draft/published/archived |
| `nodes` | JSON | nullable | Vue Flow nodes JSON |
| `edges` | JSON | nullable | Vue Flow edges JSON |

#### WorkflowNodeTypeModel（task_workflow_node_type，TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(128) | NOT NULL | 显示名称 |
| `code` | String(64) | NOT NULL, UNIQUE(tenant_id, code) | 节点编码，对应画布 node.type |
| `category` | String(32) | NOT NULL, default="action" | 分类：trigger/action/condition/control |
| `func` | Text | NOT NULL | 预定义处理器标识符（如 `handlers.approve`、`handlers.send_http`）。禁止租户提交任意代码 |
| `args` | Text | nullable | 默认位置参数，逗号分隔 |
| `kwargs` | Text | nullable | 默认关键字参数 JSON |
| `sort_order` | Integer | NOT NULL, default=0 | 排序 |
| `is_active` | Boolean | NOT NULL, default=True | 是否启用 |

### 33.3 业务规则

| 规则 | 说明 |
|------|------|
| **Workflow 编码** | 字母开头，仅含字母/数字/下划线 |
| **Workflow 状态** | 仅支持 draft（草稿）、published（已发布）、archived（已归档） |
| **NodeType 分类** | 仅支持 trigger（触发器）、action（动作）、condition（条件）、control（控制） |
| **发布流程** | 发布时可选备注（remark），由 draft → published |
| **执行流程** | 需传入 workflow_id 和可选的 variables/business_key/job_id |
| **执行结果** | 返回 completed/failed 状态及各节点执行结果 |

### 33.4 API 端点

#### Workflow（流程定义）

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/workflow/flow/detail/{id}` | module_task:workflow:query | 流程详情 |
| GET | `/workflow/flow/list` | module_task:workflow:query | 流程列表 |
| POST | `/workflow/flow/create` | module_task:workflow:create | 创建流程 |
| PUT | `/workflow/flow/update/{id}` | module_task:workflow:update | 更新流程 |
| DELETE | `/workflow/flow/delete` | module_task:workflow:delete | 删除流程 |
| POST | `/workflow/flow/publish/{id}` | module_task:workflow:update | 发布流程 |
| POST | `/workflow/flow/execute/{id}` | module_task:workflow:update | 执行流程 |

#### NodeType（节点类型）

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/workflow/nodes/detail/{id}` | module_task:workflow:query | 节点详情 |
| GET | `/workflow/nodes/list` | module_task:workflow:query | 节点列表 |
| POST | `/workflow/nodes/create` | module_task:workflow:create | 创建节点 |
| PUT | `/workflow/node-type/update/{id}` | module_task:workflow:update | 更新节点 |
| DELETE | `/workflow/node-type/delete` | module_task:workflow:delete | 删除节点 |

---

## 34. CodeGen 代码生成器模块（module_generator/gencode）

### 34.1 业务描述

代码生成器模块，通过读取数据库表结构自动生成 CRUD 代码（Python 后端 + Vue 前端 + TypeScript API 层）。支持主子表结构。数据按租户隔离。

### 34.2 数据模型

#### GenTableModel（gen_table，TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `table_name` | String(200) | NOT NULL | 数据库表名 |
| `table_comment` | String(500) | nullable | 表描述 |
| `class_name` | String(100) | NOT NULL | 实体类名称 |
| `package_name` | String(100) | nullable | 生成包路径（module_xxx） |
| `module_name` | String(30) | nullable | 生成模块名 |
| `business_name` | String(30) | nullable | 功能子目录/路由段 |
| `function_name` | String(100) | nullable | 生成功能名 |
| `sub_table_name` | String(64) | nullable | 关联子表的表名 |
| `sub_table_fk_name` | String(64) | nullable | 子表关联的外键名 |
| `parent_menu_id` | Integer | nullable | 父菜单ID |

#### GenTableColumnModel（gen_table_column，TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `table_id` | FK→gen_table.id | NOT NULL, ON DELETE CASCADE | 归属表ID |
| `column_name` | String(200) | NOT NULL | 列名称 |
| `column_comment` | String(500) | nullable | 列描述 |
| `column_type` | String(100) | NOT NULL | 列类型 |
| `column_length` | String(50) | nullable | 列长度 |
| `column_default` | String(200) | nullable | 列默认值 |
| `is_pk` | Boolean | NOT NULL, default=False | 是否主键 |
| `is_increment` | Boolean | NOT NULL, default=False | 是否自增 |
| `is_nullable` | Boolean | NOT NULL, default=True | 是否允许为空 |
| `is_unique` | Boolean | NOT NULL, default=False | 是否唯一 |
| `python_type` | String(100) | nullable | Python 类型 |
| `python_field` | String(200) | nullable | Python 字段名 |
| `is_insert` | Boolean | NOT NULL, default=True | 是否为新增字段 |
| `is_edit` | Boolean | NOT NULL, default=True | 是否编辑字段 |
| `is_list` | Boolean | NOT NULL, default=True | 是否列表字段 |
| `is_query` | Boolean | NOT NULL, default=False | 是否查询字段 |
| `query_type` | String(50) | nullable | 查询方式 |
| `html_type` | String(100) | nullable, default="input" | 显示类型 |
| `dict_type` | String(200) | nullable, default="" | 字典类型 |
| `sort` | Integer | NOT NULL, default=0 | 排序 |

### 34.3 业务规则

| 规则 | 说明 |
|------|------|
| **表名校验** | table_name/class_name 非空去空白 |
| **包名规范** | package_name 必须以 module_ 开头 |
| **业务名规范** | business_name 支持斜杠多段（如 demo/demo01） |
| **同步预览** | 支持 DB→Gen 差异预览（新增/删除/变更字段） |
| **建表SQL** | 支持从 CREATE TABLE SQL 导入表结构 |
| **模板生成** | 支持 Python/TS/Vue 三端代码模板（Jinja2） |
| **主子表** | 通过 sub_table_name/sub_table_fk_name 配置主子表关联 |

### 34.4 API 端点

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/gencode/detail/{id}` | module_generator:gencode:query | 业务表详情 |
| GET | `/gencode/list` | module_generator:gencode:query | 业务表列表 |
| POST | `/gencode/create` | module_generator:gencode:create | 创建业务表 |
| PUT | `/gencode/update/{id}` | module_generator:gencode:update | 更新业务表 |
| DELETE | `/gencode/delete` | module_generator:gencode:delete | 删除业务表 |
| PATCH | `/gencode/status/batch` | module_generator:gencode:patch | 批量设置状态 |
| GET | `/gencode/db/list` | module_generator:gencode:query | 数据库表列表 |
| POST | `/gencode/import` | module_generator:gencode:create | 导入表结构 |
| POST | `/gencode/sync/preview/{id}` | module_generator:gencode:query | 同步预览 |
| POST | `/gencode/sync/{id}` | module_generator:gencode:update | 同步表结构 |
| POST | `/gencode/create/table` | module_generator:gencode:create | 从SQL建表 |
| POST | `/gencode/preview/{id}` | module_generator:gencode:query | 预览代码 |
| POST | `/gencode/zip/{id}` | module_generator:gencode:query | 下载代码ZIP |
| POST | `/gencode/gen/{id}` | module_generator:gencode:update | 生成代码到本地 |
| POST | `/gencode/current/select` | module_generator:gencode:query | 切换当前业务表 |

---

## 35. Demo 示例模块（module_example/demo）

### 35.1 业务描述

示例模块，演示 CRUD 标准开发模式和多种数据类型的用法。数据按租户隔离。

### 35.2 数据模型

#### DemoModel（example_demo，TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(64) | NOT NULL | 名称 |
| `a` | Integer | nullable | 整数 |
| `b` | BIGINT | nullable | 大整数 |
| `c` | Float | nullable | 浮点数 |
| `d` | Boolean | NOT NULL, default=True | 布尔型 |
| `e` | Date | nullable | 日期 |
| `f` | Time | nullable | 时间 |
| `g` | DateTime | nullable | 日期时间 |
| `h` | Text | nullable | 长文本 |
| `i` | JSON | nullable | 元数据 JSON |

#### Demo01Model（example_demo01，TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(64) | NOT NULL | 名称 |

### 35.3 业务规则

| 规则 | 说明 |
|------|------|
| **名称校验** | 2-50 位，仅含字母/数字/下划线/中划线 |
| **状态校验** | 仅支持 0(正常)、1(禁用) |

### 35.4 API 端点

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/example/demo/detail/{id}` | module_example:demo:query | 详情 |
| GET | `/example/demo/list` | module_example:demo:query | 列表 |
| POST | `/example/demo/create` | module_example:demo:create | 创建 |
| PUT | `/example/demo/update/{id}` | module_example:demo:update | 更新 |
| DELETE | `/example/demo/delete` | module_example:demo:delete | 删除 |
| PATCH | `/example/demo/status/batch` | module_example:demo:patch | 批量设置状态 |

#### Demo01

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/example/demo01/detail/{id}` | module_example:demo01:query | 详情 |
| GET | `/example/demo01/list` | module_example:demo01:query | 列表 |
| POST | `/example/demo01/create` | module_example:demo01:create | 创建 |
| PUT | `/example/demo01/update/{id}` | module_example:demo01:update | 更新 |
| DELETE | `/example/demo01/delete` | module_example:demo01:delete | 删除 |
| PATCH | `/example/demo01/status/batch` | module_example:demo01:patch | 批量设置状态 |

---

## 36. Monitor 监控模块（module_monitor）

### 36.1 业务描述

监控模块提供系统运行状态的实时监控能力，包括在线用户追踪、Redis 缓存监控、服务器资源监控和文件系统管理。该模块属于平台级功能，不受租户隔离限制，超级管理员可查看所有数据。

### 36.2 在线用户（online）

#### 36.2.1 业务描述

在线用户监控来自 Redis 存储的会话数据，实时追踪当前登录用户。数据不按租户隔离，超级管理员可查看所有在线用户。

#### 36.2.2 数据模型

**OnlineOutSchema（Redis 数据结构）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `user_id` | int | NOT NULL | 用户ID |
| `tenant_id` | int | NOT NULL | 租户ID |
| `user_name` | str | NOT NULL | 用户名 |
| `name` | str | NOT NULL | 用户名称 |
| `session_id` | str | NOT NULL | 会话编号 |
| `is_super_admin` | bool | NOT NULL, default=False | 是否超管 |
| `ipaddr` | str | nullable | 登录IP |
| `login_location` | str | nullable | 登录地 |
| `os` | str | nullable | 操作系统 |
| `browser` | str | nullable | 浏览器 |
| `login_time` | DateTime | nullable | 登录时间 |
| `login_type` | str | nullable | 登录类型(PC/移动) |

#### 36.2.3 业务规则

| 规则 | 说明 |
|------|------|
| **数据来源** | 数据存储在 Redis，会话过期自动移除 |
| **强制下线** | 超级管理员可强制指定用户下线 |
| **清空全部** | 超级管理员可清空所有在线用户会话 |

#### 36.2.4 API 端点

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/monitor/online/list` | module_monitor:online:query | 在线用户列表 |
| DELETE | `/monitor/online/delete` | module_monitor:online:delete | 强制下线 |
| DELETE | `/monitor/online/clear` | module_monitor:online:delete | 清空所有在线用户 |

---

### 36.3 缓存监控（cache）

#### 36.3.1 业务描述

Redis 缓存监控，提供缓存统计信息、缓存名称列表、键值查看和清除功能。数据不按租户隔离，属于平台级功能。

#### 36.3.2 数据模型

**CacheMonitorSchema**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `command_stats` | list[dict] | NOT NULL, default=[] | Redis 命令统计 |
| `db_size` | int | NOT NULL, default=0 | Key 总数 |
| `info` | dict | NOT NULL, default={} | Redis 服务器信息 |

**CacheInfoSchema**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `cache_key` | str | NOT NULL | 缓存键名 |
| `cache_name` | str | NOT NULL | 缓存名称 |
| `cache_value` | Any | nullable | 缓存值 |
| `remark` | str | nullable | 备注说明 |

#### 36.3.3 业务规则

| 规则 | 说明 |
|------|------|
| **统计信息** | 获取 Redis 命令统计和服务器信息 |
| **键值管理** | 支持查看和清除指定缓存 |
| **批量清除** | 支持按名称清除和清空所有缓存 |

#### 36.3.4 API 端点

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/monitor/cache/info` | module_monitor:cache:query | 获取缓存监控统计 |
| GET | `/monitor/cache/get/names` | module_monitor:cache:query | 获取缓存名称列表 |
| GET | `/monitor/cache/get/keys/{cache_name}` | module_monitor:cache:query | 获取缓存键名列表 |
| GET | `/monitor/cache/get/value/{cache_name}/{cache_key}` | module_monitor:cache:query | 获取缓存值 |
| DELETE | `/monitor/cache/delete/name/{cache_name}` | module_monitor:cache:delete | 清除指定缓存名称 |
| DELETE | `/monitor/cache/delete/key/{cache_key}` | module_monitor:cache:delete | 清除指定缓存键 |
| DELETE | `/monitor/cache/clear` | module_monitor:cache:delete | 清除所有缓存 |

---

### 36.4 资源管理（resource）

#### 36.4.1 业务描述

资源文件管理，提供服务器文件系统的浏览、上传、下载、删除、移动、复制、重命名、创建目录等操作。支持文件列表分页、关键词搜索和 Excel 导出。

#### 36.4.2 数据模型

**ResourceItemSchema**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | str | NOT NULL | 文件名 |
| `file_url` | str | NOT NULL | 文件URL路径 |
| `relative_path` | str | NOT NULL | 相对路径 |
| `is_file` | bool | NOT NULL | 是否为文件 |
| `is_dir` | bool | NOT NULL | 是否为目录 |
| `size` | int | nullable | 文件大小(字节) |
| `created_time` | DateTime | nullable | 创建时间 |
| `modified_time` | DateTime | nullable | 修改时间 |
| `is_hidden` | bool | NOT NULL, default=False | 是否隐藏文件 |

**ResourceUploadSchema**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `filename` | str | NOT NULL | 文件名 |
| `file_url` | str | NOT NULL | 访问URL |
| `file_size` | int | NOT NULL | 文件大小 |
| `upload_time` | DateTime | NOT NULL | 上传时间 |

**ResourceMoveSchema**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `source_path` | str | NOT NULL | 源路径 |
| `target_path` | str | NOT NULL | 目标路径 |
| `overwrite` | bool | NOT NULL, default=False | 是否覆盖 |

**ResourceRenameSchema**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `old_path` | str | NOT NULL | 原路径 |
| `new_name` | str | NOT NULL, max_length=255 | 新名称 |

**ResourceCreateDirSchema**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `parent_path` | str | NOT NULL | 父目录路径 |
| `dir_name` | str | NOT NULL, max_length=255 | 目录名称 |

#### 36.4.3 业务规则

| 规则 | 说明 |
|------|------|
| **路径安全** | 禁止路径遍历(`..`)，防止越权访问 |
| **文件/目录互斥** | 不能同时为文件和目录 |
| **隐藏文件** | 以 `.` 开头的文件自动标记为隐藏 |
| **分页查询** | 目录列表支持分页和关键词搜索 |
| **上传限制** | 仅 resource 类型支持指定目标目录 |
| **导出功能** | 支持将资源列表导出为 Excel |

#### 36.4.4 API 端点

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/monitor/resource/list` | module_monitor:resource:query | 目录列表(分页) |
| POST | `/monitor/resource/upload` | module_monitor:resource:upload | 上传文件 |
| GET | `/monitor/resource/download` | module_monitor:resource:download | 下载文件 |
| DELETE | `/monitor/resource/delete` | module_monitor:resource:delete | 删除文件 |
| POST | `/monitor/resource/move` | module_monitor:resource:move | 移动文件 |
| POST | `/monitor/resource/copy` | module_monitor:resource:copy | 复制文件 |
| POST | `/monitor/resource/rename` | module_monitor:resource:rename | 重命名文件 |
| POST | `/monitor/resource/mkdir` | module_monitor:resource:mkdir | 创建目录 |
| POST | `/monitor/resource/export` | module_monitor:resource:export | 导出资源列表 |

---

### 36.5 服务器监控（server）

#### 36.5.1 业务描述

服务器监控，采集服务器运行时的 CPU、内存、磁盘、Python 进程等信息，供运维人员了解系统资源使用情况。

#### 36.5.2 数据模型

**CpuInfoSchema**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `cpu_num` | int | NOT NULL | CPU 核心数 |
| `used` | float | NOT NULL, 0-100 | 用户使用率(%) |
| `sys` | float | NOT NULL, 0-100 | 系统使用率(%) |
| `free` | float | NOT NULL, 0-100 | 空闲率(%) |

**MemoryInfoSchema**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `total` | str | NOT NULL | 内存总量 |
| `used` | str | NOT NULL | 已用内存 |
| `free` | str | NOT NULL | 剩余内存 |
| `usage` | float | NOT NULL, 0-100 | 使用率(%) |

**SysInfoSchema**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `computer_ip` | str | NOT NULL | 服务器IP |
| `computer_name` | str | NOT NULL | 服务器名称 |
| `os_arch` | str | NOT NULL | 系统架构 |
| `os_name` | str | NOT NULL | 操作系统 |
| `user_dir` | str | NOT NULL | 项目路径 |

**PyInfoSchema**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | str | NOT NULL | Python 名称 |
| `version` | str | NOT NULL | Python 版本 |
| `start_time` | str | NOT NULL | 启动时间 |
| `run_time` | str | NOT NULL | 运行时长 |
| `home` | str | NOT NULL | 安装路径 |
| `memory_used` | str | NOT NULL | 内存占用 |
| `memory_usage` | float | NOT NULL, 0-100 | 内存使用率(%) |
| `memory_total` | str | NOT NULL | 总内存 |
| `memory_free` | str | NOT NULL | 剩余内存 |

**DiskInfoSchema**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `dir_name` | str | NOT NULL | 磁盘路径 |
| `sys_type_name` | str | NOT NULL | 文件系统类型 |
| `type_name` | str | NOT NULL | 磁盘类型 |
| `total` | str | NOT NULL | 总容量 |
| `used` | str | NOT NULL | 已用容量 |
| `free` | str | NOT NULL | 可用容量 |
| `usage` | float | NOT NULL, 0-100 | 使用率(%) |

**ServerMonitorSchema**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `cpu` | CpuInfoSchema | NOT NULL | CPU 信息 |
| `mem` | MemoryInfoSchema | NOT NULL | 内存信息 |
| `py` | PyInfoSchema | NOT NULL | Python 信息 |
| `sys` | SysInfoSchema | NOT NULL | 系统信息 |
| `disks` | list[DiskInfoSchema] | NOT NULL | 磁盘信息列表 |

#### 36.5.3 业务规则

| 规则 | 说明 |
|------|------|
| **实时采集** | 每次请求实时采集系统信息 |
| **百分比范围** | 使用率字段限制在 0-100 范围 |

#### 36.5.4 API 端点

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/monitor/server/info` | module_monitor:server:query | 服务器监控信息 |

---

## 37. Common 公共模块（module_common）

### 37.1 业务描述

公共模块提供跨模块复用的基础服务，包括统一文件上传下载、健康检查和指标监控。该模块属于平台级基础设施，不受租户隔离限制。

### 37.2 文件管理（file）

#### 37.2.1 业务描述

统一文件上传下载服务，支持多种上传类型（通用文件、头像、参数配置、监控资源），支持指定目标目录。预留 Excel 导入功能，待后续实现。

#### 37.2.2 数据模型

**上传响应数据**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `file_name` | str | NOT NULL | 文件名 |
| `file_url` | str | NOT NULL | 访问URL |
| `file_size` | int | NOT NULL | 文件大小 |
| `upload_time` | DateTime | NOT NULL | 上传时间 |

**预留：Excel导入字段映射模型（ImportFieldModel）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `base_column` | str | nullable | 数据库字段名 |
| `excel_column` | str | nullable | Excel 字段名 |
| `default_value` | str | nullable | 默认值 |
| `is_required` | bool | nullable | 是否必传 |
| `selected` | bool | nullable | 是否勾选 |

**预留：Excel导入请求模型（ImportModel）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `table_name` | str | nullable | 目标表名 |
| `sheet_name` | str | nullable | Sheet 名 |
| `filed_info` | list[ImportFieldModel] | nullable | 字段映射列表 |
| `file_name` | str | nullable | 文件名 |

#### 37.2.3 业务规则

| 规则 | 说明 |
|------|------|
| **上传类型** | file=通用, avatar=头像, param=参数配置, resource=监控资源 |
| **目标目录** | 仅 resource 类型支持指定 target_path |
| **下载选项** | 支持下载后自动删除源文件 |
| **Excel导入预留** | ImportFieldModel 和 ImportModel 为预留功能，当前未实现对应接口 |

#### 37.2.4 API 端点

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| POST | `/file/upload` | module_common:file:upload | 上传文件 |
| POST | `/file/download` | module_common:file:download | 下载文件 |

---

### 37.3 健康检查（health）

#### 37.3.1 业务描述

三级健康检查体系，用于不同场景的健康探测：
- `/monitor/health`: 基础健康检查（负载均衡器探测）
- `/monitor/health/live`: 存活探针（K8s livenessProbe）
- `/monitor/health/ready`: 就绪探针（K8s readinessProbe，检测数据库和 Redis）
- `/monitor/health/stream`: 健康实时流（SSE；服务端单例快照循环每 30s 一拍，探活成本与连接数无关）

#### 37.3.2 数据模型

**健康检查响应**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `status` | str | NOT NULL | healthy/alive/ready/not_ready |
| `timestamp` | DateTime | NOT NULL | 检查时间戳 |
| `version` | str | NOT NULL | 系统版本 |
| `uptime_seconds` | float | NOT NULL | 运行时间(秒) |
| `dependencies` | dict | nullable | 依赖检查结果 |
| `disk_usage` | float | nullable | 磁盘使用率(%) |

**依赖检查结果**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `database` | dict | NOT NULL | 数据库状态 {status, latency_ms} |
| `redis` | dict | NOT NULL | Redis 状态 {status, latency_ms} |

#### 37.3.3 业务规则

| 规则 | 说明 |
|------|------|
| **基础检查** | 仅检查进程是否存活，返回 healthy |
| **存活探针** | 进程已启动即可返回 200 |
| **就绪探针** | 检测数据库和 Redis 连接，失败返回 503 |
| **依赖状态** | up=正常, down=异常, disabled=已禁用 |

#### 37.3.4 API 端点

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/health` | — | 基础健康检查 |
| GET | `/health/live` | — | 存活探针 |
| GET | `/health/ready` | — | 就绪探针 |
| GET | `/health/stream` | — | 健康实时流（SSE，事件名 health，30s 快照一拍） |

---

### 37.4 指标监控（metrics）

#### 37.4.1 业务描述

Prometheus 指标监控，集成 prometheus-fastapi-instrumentator 自动采集 HTTP 请求指标，暴露 `/metrics` 端点供 Prometheus 抓取。

#### 37.4.2 采集指标

| 指标名称 | 类型 | 说明 |
|---------|------|------|
| `http_requests_total` | Counter | HTTP 请求总数（按 method/endpoint/status 分组） |
| `http_request_duration_seconds` | Histogram | 请求延迟直方图 |
| `http_requests_in_progress` | Gauge | 当前处理中的请求数 |
| `http_request_size_bytes` | Histogram | 请求体大小 |
| `http_response_size_bytes` | Histogram | 响应体大小 |

#### 37.4.3 排除端点

以下端点不纳入指标采集：
- `/metrics`: Prometheus 抓取端点
- `/health`, `/health/live`, `/health/ready`: 健康检查端点
- `/docs`, `/redoc`, `/openapi.json`: API 文档
- `/static/*`, `/favicon.ico`: 静态资源

#### 37.4.4 API 端点

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/metrics` | — | Prometheus 指标端点 |

---

# Part 5：商业运营模块

---

## 38. Invoice 发票管理模块

### 38.1 业务描述

发票管理是中国 B2B SaaS 的法律合规要求。租户在完成订单支付后可申请开具电子发票（增值税普通发票/增值税专用发票），平台审核后对接第三方开票 API（如百望云/票通）生成电子发票，支持下载 PDF。

### 38.2 发票类型

| 类型 | 编码 | 适用场景 | 税率 |
|------|------|---------|------|
| **增值税普通发票** | `vat_normal` | 个人/小规模纳税人，不可抵扣 | 1%/3%/6% |
| **增值税专用发票** | `vat_special` | 一般纳税人，可抵扣进项税额 | 6%/13% |

### 38.3 数据模型

#### platform_invoice

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `invoice_no` | String(32) | NOT NULL, UNIQUE | 发票号码（平台自增号） |
| `order_id` | FK→platform_order.id | NOT NULL, UNIQUE | 关联订单（一单一票） |
| `tenant_id` | FK→platform_tenant.id | NOT NULL | 开票租户 |
| `invoice_type` | String(20) | NOT NULL | 类型：`vat_normal`(普票) `vat_special`(专票) |
| `title` | String(200) | NOT NULL | 发票抬头（公司全称/个人姓名） |
| `tax_no` | String(50) | nullable | 纳税人识别号（普票可选，专票必填） |
| `bank_info` | Text | nullable | 开户行及账号（专票必填） |
| `address_info` | Text | nullable | 注册地址及电话（专票必填） |
| `amount` | Integer | NOT NULL | 发票金额（分） |
| `tax_amount` | Integer | NOT NULL, default=0 | 税额（分） |
| `status` | Integer | NOT NULL, default=0 | 0=待开票 1=已开票 2=开票失败 3=已作废 |
| `pdf_url` | String(500) | nullable | 电子发票 PDF 下载地址 |
| `api_response` | Text | nullable | 第三方开票 API 原始响应 |
| `remark` | Text | nullable | 备注 |

### 38.4 业务流程

```
租户申请开票
  ├── POST /tenant/invoice/apply
  │     body: {order_id, invoice_type, title, tax_no?, bank_info?, address_info?}
  ├── 校验：订单已支付(status=1)、未开过票(order_id UNIQUE)
  ├── 专票额外校验：tax_no/bank_info/address_info 必填
  ├── 创建 platform_invoice 记录（status=0 待开票）
  └── 返回申请成功

超管审核开票
  ├── GET /platform/invoice/list（待开票列表）
  ├── PUT /platform/invoice/issue/{id}
  │     ├── 调用第三方开票 API（百望云等）
  │     ├── 成功 → 更新 status=1、pdf_url、api_response
  │     ├── 失败 → 更新 status=2、记录错误信息
  │     └── 通知租户（站内信 + 邮件，含下载链接）
  └── PUT /platform/invoice/void/{id}（发票作废，仅已开票可作废）
```

### 38.5 业务规则

| 规则 | 说明 |
|------|------|
| **一单一票** | 每个订单仅可开具一张发票（order_id UNIQUE），杜绝重复开票 |
| **开票时限** | 订单支付后 30 天内可申请，超期不再支持（税务合规） |
| **金额匹配** | 发票金额必须等于订单实付金额 |
| **专票校验** | 增值税专用发票必须填写税号+开户行+地址，缺一不可 |
| **第三方对接** | 对接百望云/票通等电子发票平台，API 调用失败时自动重试 3 次后标记失败 |
| **PDF 存储** | 电子发票 PDF 上传至文件服务（§37.2），按 `invoice/{tenant_id}/{invoice_no}.pdf` 路径存储 |
| **作废规则** | 当月开具的发票可作废，跨月发票需冲红（暂不支持，预留扩展） |

### 38.6 API 端点

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/tenant/invoice/apply` | 申请开票 | 租户管理员 |
| GET | `/tenant/invoice/list` | 我的发票列表 | 租户管理员 |
| GET | `/tenant/invoice/{id}/download` | 下载发票 PDF | 租户管理员 |
| GET | `/platform/invoice/list` | 全部发票列表（支持筛选） | 超管 |
| PUT | `/platform/invoice/issue/{id}` | 开具发票（调用第三方 API） | 超管 |
| PUT | `/platform/invoice/void/{id}` | 作废发票 | 超管 |

---

## 39. AuditLog 租户审计日志模块

### 39.1 业务描述

记录平台级和租户级的关键管理操作，形成不可篡改的审计轨迹。满足企业内部合规审查、SOC2/ISO27001 认证中的数据追溯要求。审计日志与操作日志（§14）的区别在于：操作日志面向业务操作的查询追踪，审计日志面向合规要求的不可否认性记录。

### 39.2 操作分类

| 分类 | 说明 | 示例 |
|------|------|------|
| **租户管理** | 租户生命周期操作 | 创建/启禁用/冻结/删除/变更套餐 |
| **权限变更** | 角色/菜单/授权操作 | 角色创建/删除、菜单分配/回收 |
| **套餐变更** | 套餐相关操作 | 套餐价格修改、套餐菜单变更 |
| **支付与退款** | 财务相关操作 | 订单创建、退款批准/驳回 |
| **发票管理** | 开票相关操作 | 开具发票、作废发票 |
| **用户邀请** | 团队管理操作 | 发送邀请、取消邀请 |

### 39.3 数据模型

#### platform_audit_log

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `action` | String(50) | NOT NULL | 操作类型：`tenant.create`/`tenant.package_change`/`role.delete` 等 |
| `target_type` | String(50) | NOT NULL | 操作对象类型：`tenant`/`package`/`role`/`order`/`invoice` |
| `target_id` | Integer | NOT NULL | 操作对象 ID |
| `target_name` | String(200) | nullable | 操作对象名称（冗余存储，防删除后无法追溯） |
| `tenant_id` | FK→platform_tenant.id | nullable | 关联租户（平台级操作可为 null） |
| `operator_id` | FK→sys_user.id | NOT NULL | 操作人 |
| `operator_name` | String(50) | NOT NULL | 操作人名称（冗余） |
| `detail` | JSON | NOT NULL | 操作详情（变更前/后的关键字段） |
| `ip_address` | String(45) | nullable | 操作 IP |
| `user_agent` | String(500) | nullable | 浏览器 UA |

| **设计要点** | 说明 |
|------|------|
| **不可篡改** | 无 Update/Delete API，仅支持 Insert 和 Read |
| **变更对比** | `detail` JSON 字段存储 `{"before": {...}, "after": {...}}` 格式的变更对比 |
| **冗余存储** | target_name/operator_name 冗余存储，确保删除关联数据后仍可追溯 |
| **保留策略** | 默认保留 3 年，超期归档至冷存储（S3/OSS），支持按需导出 CSV/JSON |

### 39.4 审计事件清单

| action | target_type | 触发场景 | detail 示例 |
|--------|-------------|---------|------------|
| `tenant.create` | tenant | 创建租户 | `{after: {code, name, package_id}}` |
| `tenant.status_change` | tenant | 启禁/冻结/归档 | `{before: {status}, after: {status}}` |
| `tenant.package_change` | tenant | 变更套餐 | `{before: {package_id, name}, after: {package_id, name}}` |
| `tenant.quota_change` | tenant | 调整配额 | `{before: {max_users}, after: {max_users}}` |
| `tenant.delete` | tenant | 删除租户 | `{before: {code, name, deleted_at}}` |
| `package.price_change` | package | 修改套餐价格 | `{before: {price}, after: {price}}` |
| `package.menu_change` | package | 变更套餐菜单 | `{added: [...], removed: [...]}` |
| `role.delete` | role | 删除角色 | `{before: {name, user_count}}` |
| `order.refund_approve` | order | 批准退款 | `{order_no, amount, reason}` |
| `order.refund_reject` | order | 驳回退款 | `{order_no, amount, reject_reason}` |
| `invoice.issue` | invoice | 开具发票 | `{invoice_no, amount, type}` |
| `invoice.void` | invoice | 作废发票 | `{invoice_no, reason}` |
| `invite.send` | invite | 发送邀请 | `{invitee_email, target_role}` |

### 39.5 业务规则

| 规则 | 说明 |
|------|------|
| **全量记录** | 所有审计事件在业务操作的事务中同步写入，不依赖异步任务（防止丢失） |
| **不可删除** | 审计日志无 DELETE API，管理员不可手动删除（如需清理需走冷存储归档流程） |
| **权限** | 仅超管可查阅审计日志，租户端不可见 |
| **分页与筛选** | 支持按 action/target_type/tenant_id/operator_id/时间范围 多条件筛选分页查询 |
| **保留策略** | 定时任务 `archive_audit_logs` 每月扫描，将 3 年前的日志导出至 OSS 后从主表删除 |

### 39.6 API 端点

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/platform/audit/list` | 审计日志列表（支持筛选/分页） | 超管 |
| GET | `/platform/audit/detail/{id}` | 审计日志详情 | 超管 |
| GET | `/platform/audit/export` | 导出审计日志（CSV/JSON） | 超管 |

---

## 40. Dashboard 运营大盘

### 40.1 业务描述

平台运营数据可视化看板，基于已有数据（订单/支付/API用量/租户/工单）聚合展示核心运营指标，帮助超管快速掌握平台健康状况。

### 40.2 核心指标

| 指标 | 数据源 | 说明 |
|------|--------|------|
| **租户总数** | platform_tenant | 按状态分布（active/suspended/expired） |
| **本月新增租户** | platform_tenant | 按月统计新建租户数 |
| **今日活跃租户** | platform_api_usage_daily | 当日有 API 调用的租户数 |
| **月收入（MRR）** | platform_order | status=1 订单按月汇总金额 |
| **退款率** | platform_refund | 退款金额/总收入 × 100% |
| **API 调用总量** | platform_api_usage_daily | 按天/月聚合调用次数 |
| **待处理工单数** | platform_ticket | status=0/1 的工单数量 |
| **套餐分布** | platform_tenant JOIN platform_package | 各套餐租户数量（饼图） |
| **收入趋势** | platform_order | 近 12 个月收入折线图 |

### 40.3 API 端点

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/platform/dashboard/overview` | 运营概览（总览数据） | 超管 |
| GET | `/platform/dashboard/revenue` | 收入趋势（按月） | 超管 |
| GET | `/platform/dashboard/tenants` | 租户统计 | 超管 |
| GET | `/platform/dashboard/api-usage` | API 用量趋势 | 超管 |

---