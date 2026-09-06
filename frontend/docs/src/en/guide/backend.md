---
layout: doc
title: Backend Development Guide
description: "Backend development guide: FastAPI routing, SQLAlchemy models, Pydantic schemas, service layer patterns."
outline: "deep"
---
# Backend Development Guide

> For detailed directory structure, migration commands, and date serialization conventions, see [backend/README.md](https://github.com/fastapiadmin/FastapiAdmin/blob/master/backend/README.md).

## Technology Stack

| Technology | Description |
|------------|-------------|
| FastAPI 0.115+ | Modern async web framework |
| SQLAlchemy 2.0 | ORM framework |
| Alembic 1.15+ | Database migration tool |
| Pydantic 2.x | Data validation & serialization |
| APScheduler 3.11+ | Scheduled task scheduling |
| Redis | Cache & session storage |
| Uvicorn | ASGI server |

## Project Structure

```
backend/app/
├── api/v1/              # Route manifests (aggregation only, no business logic)
│   ├── system.py        #   System routes
│   ├── monitor.py       #   Monitoring routes
│   └── ...
├── modules/             # Business layer (vertical slices by domain)
│   ├── system/          #   System management domain (users, roles, menus, etc.)
│   ├── monitor/         #   Monitoring domain
│   ├── ai/              #   AI features domain
│   ├── task/            #   Task domain (scheduled jobs)
│   ├── workflow/        #   Workflow domain
│   ├── generator/       #   Code generator domain
│   └── common/          #   Common domain (files, health check)
├── common/              # Shared components (constants, enums, response)
├── config/              # Project configuration
├── core/                # Core modules (database, security, auth, middleware)
├── plugin/              # Plugin directory (extension development)
└── utils/               # Utilities
```

## Module Layering

Each business module follows a uniform layered structure (vertical slice):

```
modules/<module>/<domain>/
├── controller.py    # HTTP request handling
├── service.py       # Business logic
├── crud.py          # Database operations
├── model.py         # ORM model
├── schema.py        # Pydantic validation
└── param.py         # Request parameters
```

## Quick Start

```bash
cd backend

# Recommended: use uv
uv sync
uv run main.py run --env=dev

# Or traditional
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py run --env=dev
```

**First start auto-initializes database schema & seed data.**

## Database Migrations

Only use when you've modified ORM models:

```bash
python main.py revision --env=dev
python main.py upgrade --env=dev
# or: uv run main.py revision/upgrade --env=dev
```

## Plugin Development

The project uses a **plugin-based architecture**. Develop under `backend/app/plugin/`:

### Auto Route Registration

1. Controller file must be named `controller.py`
2. Routes auto-map: `module_xxx` → `/xxx`
3. System auto-scans `plugin/` for all `controller.py` files

### Steps

1. Create `module_yourfeature/` under `backend/app/plugin/`
2. Write `model.py` → `schema.py` → `crud.py` → `service.py` → `controller.py`
3. Routes auto-register — no manual configuration

### Controller Example

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
    tags=["Your Feature"],
)

@YourFeatureRouter.get("/detail/{id}", summary="Get Detail")
async def get_detail(
    id: int = Path(..., description="Feature ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_yourfeature:yourcontroller:detail"])),
) -> JSONResponse:
    result = await YourFeatureService.detail_service(id=id, auth=auth)
    return SuccessResponse(data=result)
```

## Code Generator

Built-in code generator auto-generates CRUD code from database schema. Access via "Code Generation" module after login.

## Conventions

- **Date serialization**: Use Pydantic `PlainSerializer(..., when_used='json')`, ORM with `mode='python'`, JSON/Redis with `mode='json'`
- **Unified response**: Use `SuccessResponse` and `jsonable_encoder`
- **Permission control**: All APIs require `AuthPermission`
- **Logging**: Critical operations use `OperationLogRoute`

## Code Style

```bash
ruff check              # Check
ruff check --fix        # Auto-fix
# or: uv run ruff check / --fix
```
