---
layout: doc
title: Why Choose FastApiAdmin?
description: Why FastApiAdmin? Comparison with other admin frameworks — async backend, full-stack fusion.
outline: "deep"
---

If you're evaluating a rapid development platform for admin/dashboard systems, here's how FastApiAdmin compares.

## How We Compare

| Dimension | FastApiAdmin | Django Admin / Flask-Admin | Frontend-only Templates |
|-----------|-------------|---------------------------|------------------------|
| **Backend** | FastAPI async, Pydantic type-safe | Django/Flask sync-first | None, build yourself |
| **Frontend** | Vue3 + TypeScript + Element Plus, ready-to-use | Jinja templates | Vue3 + Element Plus |
| **Mobile** | UniApp multi-platform (H5/Mini Program/App) | None | None |
| **Code Generator** | Built-in, DB table → full CRUD | Extra plugins needed | None |
| **Deployment** | Docker Compose one-click, Nginx + SSL included | Manual setup | Manual setup |
| **Architecture** | Vertical slice by domain, auto plugin registration | Layer-first | Layer-first |
| **Database** | MySQL / PostgreSQL / SQLite, Alembic migrations | Django ORM migrations | None |

## Technology Rationale

### Why FastAPI over Django/Flask?

| Feature | FastAPI | Django | Flask |
|---------|---------|--------|-------|
| Async native | ✅ Built-in async/await | ⚠️ 3.1+ partial | ❌ Extensions needed |
| Auto API docs | ✅ Swagger + Redoc auto-generated | ❌ drf-spectacular needed | ❌ Plugins needed |
| Type safety | ✅ Pydantic request/response validation | ❌ Runtime only | ❌ No built-in |
| Performance | ~30k req/s | ~10k req/s | ~15k req/s |
| Learning curve | Moderate | Steep | Gentle |

FastAPI's **auto type validation + auto docs + async performance** is a combo advantage — you don't trade speed for developer experience.

### Why Vue3 over React?

| Feature | Vue3 | React |
|---------|------|-------|
| Learning curve | Low (templates + Composition API) | Medium (JSX + Hooks mental model) |
| Official ecosystem | Router, Pinia, Vite unified | Third-party fragmentation |
| TypeScript | Composition API first-class | Good support |
| Chinese community | Very active | Active |

For admin/dashboard scenarios, Vue3 + Element Plus provides superior developer efficiency and component completeness.

### Why Vertical Slice by Domain?

```
# Vertical slice (this project)
modules/system/user/            # All user code in one directory
├── controller.py
├── service.py
├── crud.py
├── model.py
└── schema.py

# Layer-first (common approach)
models/user.py                  # User model here
schemas/user.py                 # User schema elsewhere
services/user.py                # User logic yet elsewhere
```

| Scenario | Vertical Slice (ours) | Layer-First |
|----------|----------------------|-------------|
| Parallel dev (different modules/people) | ✅ Independent dirs, zero conflicts | ❌ Same model.py file |
| Extract to sub-repo/service | ✅ Move whole directory | ❌ Pull from multiple dirs |
| Browse all models at once | ❌ Use IDE search | ✅ One models/ dir |

We chose vertical slicing to **prioritize team parallelism and decoupling**. For schema overview, use IDE, Alembic, or DB tools.

## What You Get Out of the Box

Features FastApiAdmin provides that raw frameworks or frontend-only templates **don't**:

| Feature | FastApiAdmin | Django Admin | Frontend Template |
|---------|:-----------:|:-----------:|:-----------------:|
| RBAC (menu/button/data level) | ✅ | ⚠️ Basic | ❌ |
| Code generator (table → CRUD) | ✅ | ❌ | ❌ |
| Server + cache monitoring | ✅ | ❌ | ❌ |
| Operation log auditing | ✅ | ✅ | ❌ |
| Scheduled task management | ✅ | ❌ | ❌ |
| WebSocket real-time push | ✅ | ❌ | ❌ |
| Mobile (H5/Mini Program) | ✅ | ❌ | ❌ |

## Summary

FastApiAdmin is the **best fit** if you need:
- ✅ Python stack, want FastAPI's async performance
- ✅ Vue3 frontend team, need production-ready admin template
- ✅ Mobile support (H5/Mini Program)
- ✅ Don't want to build RBAC, logging, monitoring from scratch
- ✅ Multi-developer, need low coupling between modules

## Next Steps

If you've decided to give it a try, follow this path:

| Order | Doc | Time | Goal |
|:-----:|-----|:----:|------|
| 1 | [Quick Start](/en/guide/start) | 10 min | Run locally, see the login page and dashboard |
| 2 | [Backend Guide](/en/guide/backend) | 15 min | Add your first business module |
| 3 | [Frontend Guide](/en/guide/frontend) | 15 min | Add your first page |
| 4 | [Deployment Guide](/en/guide/deployment) | 20 min | Push from local to production |

Or just [clone the repo](https://github.com/fastapiadmin/FastApiAdmin) and explore the code alongside the docs.

::: tip Stuck somewhere?
[Common Issues](/en/guide/why#common-issues)  ·  [GitHub Issues](https://github.com/fastapiadmin/FastApiAdmin/issues)  ·  [Gitee Issues](https://gitee.com/fastapiadmin/FastapiAdmin/issues)
:::
