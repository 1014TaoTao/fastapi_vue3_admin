---
layout: doc
outline: "deep"
title: Project Overview
description: "Project overview: what is FastApiAdmin, full-stack architecture, multi-end delivery."
---

<div style="text-align: center;">
  <div align="center">
     <img src="/logo.svg" width="150" height="150" alt="logo" />
  </div>
  <h1>FastApiAdmin <sup style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.4em; vertical-align: super; margin-left: 5px;">v3.1.0</sup></h1>
  <h3>Modern, Open Source, Full-Stack Rapid Development Platform</h3>
  <p>If you like this project, please give it a ⭐️!</p>
</div>

## Project Introduction

**FastApiAdmin** is a **completely open-source, highly modular, and technologically advanced modern rapid development platform** designed to help developers efficiently build high-quality enterprise-level systems. It adopts a **frontend-backend separation architecture**, integrating the Python backend framework `FastAPI` and the frontend framework `Vue3` for multi-platform unified development.

> **Design Philosophy**: With modularity and loose coupling at its core, pursuing rich functionality, clean APIs, comprehensive documentation, and easy maintenance.

## Engineering Structure

```sh
FastapiAdmin/
├─ backend/               # Backend (FastAPI + Python)
├─ frontend/              # Frontend projects
│   ├── web/              # Web frontend (Vue3 + Element Plus)
│   ├── app/              # Mobile (UniApp)
│   └── docs/             # Documentation site (VitePress)
├─ docker/                # Docker deployment config
│   ├── backend/          # Backend Dockerfile
│   ├── nginx/            # Nginx config + static files
│   ├── mysql/            # MySQL data directory
│   └── redis/            # Redis data directory
├─ deploy.sh              # Deployment script
├─ deploy.bat             # Windows startup script
├─ LICENSE                # MIT License
└─ README.md              # Project docs
```

> Detailed directory structures: [Frontend](./frontend), [Backend](./backend), [Mobile](./miniprogram), [Deployment](./deployment).

## Core Highlights

| Feature | Description |
|---------|-------------|
| 🌐 Full-Stack | Frontend-backend separation, Python (FastAPI) + Vue3 |
| 🧱 Modular | Highly decoupled, plug-in architecture, auto route discovery |
| ⚡️ High Performance | Async framework + Redis caching |
| 🔒 Security | JWT OAuth2, RBAC permission control |
| 🚀 Deployment | Docker Compose one-click deployment |
| 📖 Developer Friendly | Complete documentation + Chinese UI + visual toolchain |
| 📱 Mobile Support | UniApp-based FastApp, multi-platform (H5, Mini Program, App) |
| 🛠️ Code Generator | Built-in code generation tools |

## Technology Stack

| Type | Technology |
|------|------------|
| Backend Framework | FastAPI / Uvicorn / Pydantic 2.0 / Alembic |
| ORM | SQLAlchemy 2.0 |
| Scheduled Tasks | APScheduler |
| Auth | PyJWT |
| Frontend Framework | Vue3 / Vite / Pinia / TypeScript |
| Web UI | Element Plus |
| Mobile | UniApp / Wot Design Uni |
| Database | MySQL / PostgreSQL / SQLite |
| Cache | Redis |
| Deployment | Docker / Nginx / Docker Compose |

## Built-in Modules

| Module | Features | Description |
|--------|----------|-------------|
| Dashboard | Workbench, Analysis | System overview and data analysis |
| System Management | Users, Roles, Menus, Departments, Positions, Dictionaries, Config, Notices | Core system management |
| Monitoring | Online users, Server, Cache | System health monitoring |
| Task Management | Scheduled tasks | Async task scheduling |
| Log Management | Operation logs | User behavior auditing |
| Development Tools | Code generation, Form builder, API docs | Developer productivity tools |
| File Management | File storage | Unified file management |

## Package Architecture: Domain Vertical Slice vs Layer-First

This is about **source directory organization**, separate from the MVC/Controller-Service-CRUD **logical layering** which still exists.

| Approach | Organization | Typical Structure |
|----------|-------------|-------------------|
| **Layer-First** | Group by technical layer | Top-level `models/`, `schemas/`, `services/`, `controllers/` |
| **Vertical Slice** (this project) | Group by business domain | `modules/*/` packages with `controller.py`, `service.py`, `crud.py`, `model.py`, `schema.py` (route manifests in `app/api/v1/`) |

**This project uses vertical slice by domain.**

**Rationale**:

- **Domain boundaries as units**: Modules like system management and monitoring each have independent directories. Parallel development avoids conflicts.
- **Future-proof extraction**: To split a module into its own service/repo, move one directory. Layer-first requires pulling from multiple top-level dirs.
- **Layering still exists**: Controller → Service → CRUD → Model **logical layers** are **nested inside** each domain package, rather than being the primary organizational axis.
