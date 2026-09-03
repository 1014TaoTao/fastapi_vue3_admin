---
layout: doc
outline: "deep"
title: Quick Start
description: "Spin up a working MVP in 15-30 minutes: prerequisites, source, Docker Compose, first run."
---

## Demo Environment

- Website: [https://service.fastapiadmin.com](https://service.fastapiadmin.com)
- Web: [https://service.fastapiadmin.com/web](https://service.fastapiadmin.com/web)
- Mobile: [https://service.fastapiadmin.com/app](https://service.fastapiadmin.com/app)
- Demo account: `admin` / `123456` (**for the official demo site only — do not use in production**; change the default password immediately after first deployment)

## Prerequisites

| Type | Technology | Version |
|------|------------|---------|
| Backend | Python | ≥ 3.10 (3.12 recommended) |
| Backend | FastAPI | 0.109+ |
| Frontend | Node.js | ≥ 20.0 |
| Frontend | pnpm | ≥ 9.0 |
| Web UI | Element Plus | 2.10+ |
| Mobile | UniApp | 3.0+ |
| App UI | Wot Design Uni | 1.9+ |
| Database | MySQL | 8.0+ / PostgreSQL 13+ / SQLite |
| Middleware | Redis | 7.0+ |

## Get the Code

```bash
git clone https://github.com/fastapiadmin/FastApiAdmin.git
# or via Gitee
git clone https://gitee.com/fastapiadmin/FastApiAdmin.git
```

## Backend Setup

### 1. Configure Environment

```bash
cd FastapiAdmin/backend
cp env/.env.example env/.env.dev
# Edit env/.env.dev with your database, Redis, JWT secret, etc.
```

### 2. Install & Start

```bash
# Recommended: use uv (matches pyproject.toml)
uv sync
uv run main.py run --env=dev

# Or traditional pip/venv
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py run --env=dev
```

**First start auto-initializes database schema & seed data** — no manual migration needed.

### 3. Database Migrations (when changing models)

```bash
python main.py revision --env=dev
python main.py upgrade --env=dev
# or: uv run main.py revision/upgrade --env=dev
```

## Frontend Setup

```bash
# Web Frontend (Vue3)
cd FastapiAdmin/frontend/web
pnpm install
pnpm run dev

# Mobile (UniApp)
cd FastapiAdmin/frontend/app
pnpm install
pnpm run dev:h5

# Documentation Site (VitePress)
cd FastapiAdmin/frontend/docs
pnpm install
pnpm run dev
```

## Local Access URLs

| Service | URL |
|---------|-----|
| Web Frontend | `http://127.0.0.1:5173` |
| Mobile H5 | `http://127.0.0.1:8080` |
| Documentation | `http://127.0.0.1:5174` |
| Backend API | `http://127.0.0.1:8001` |
| Swagger | `http://127.0.0.1:8001/docs` |

## Docker Deployment

See [Deployment Guide](./deployment), quick commands:

```bash
chmod +x deploy.sh
./deploy.sh              # Full deployment
./deploy.sh logs         # View logs
./deploy.sh stop         # Stop services
./deploy.sh restart      # Restart services
```

## FAQ

| Question | Answer |
|----------|--------|
| Backend fails with DB connection error | Ensure empty DB created, `.env.dev` credentials correct |
| Frontend CORS errors | Confirm backend running, `VITE_API_BASE_URL` correct |
| Do I need migrations before first start? | **No** — auto-initialized on first start |
| Node.js version mismatch | Use nvm: `nvm install 20` |
