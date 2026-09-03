---
layout: doc
outline: "deep"
title: Deployment Guide
description: "Deployment guide: Docker Compose, production hardening, Nginx + SSL, multi-environment config."
---
# Deployment Guide

## Deployment Overview

FastApiAdmin supports:

- **Docker Compose** (recommended): Fast, portable
- **Manual deployment**: For highly customized setups
- **Cloud services**: Alibaba Cloud, Tencent Cloud, etc.

## Docker Compose Deployment (Recommended)

> See [docker/README.md](https://github.com/fastapiadmin/FastapiAdmin/blob/master/docker/README.md) for details.

### 1. Prerequisites

- Docker ≥ 20.10
- Docker Compose v2
- Ports 80 and 443 open

### 2. Install Docker

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install docker.io docker-compose -y

# CentOS / RHEL
sudo yum install docker docker-compose -y

# Start & enable
sudo systemctl start docker && sudo systemctl enable docker
```

### 3. Deploy

```bash
git clone https://github.com/fastapiadmin/FastApiAdmin.git
cd FastApiAdmin

# Configure environment
cp docker/.env.example docker/.env
# Edit docker/.env with DB passwords, Redis password, etc.

# Deploy
chmod +x deploy.sh
./deploy.sh
```

### 4. Post-Deployment

#### SSL Certificate

```bash
# Self-signed (testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/nginx/ssl/server.key \
  -out docker/nginx/ssl/server.pem \
  -subj "/CN=your-domain.com"

# Let's Encrypt (production)
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
# Copy certs to docker/nginx/ssl/
```

#### Domain

Add an A record pointing to your server IP.

### 5. Service Management

| Command | Description |
|---------|-------------|
| `./deploy.sh` | Full deployment |
| `./deploy.sh logs` | View logs |
| `./deploy.sh stop` | Stop services |
| `./deploy.sh restart` | Restart services |

### 6. Access

| Service | URL |
|---------|-----|
| Frontend | `https://domain/web` |
| API Docs | `https://domain/api/v1/docs` |

## Manual Deployment

### Backend

```bash
cd FastapiAdmin/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env/.env.example env/.env.prod     # Edit as needed

# Start with Gunicorn + Uvicorn
pip install gunicorn uvloop
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8001 --daemon
```

### Frontend

```bash
cd FastapiAdmin/frontend/web
pnpm install && pnpm run build
# Deploy dist/ to Nginx or any web server
```

### Nginx Example

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /web {
        root /path/to/FastapiAdmin/frontend/web;
        index index.html;
        try_files $uri $uri/ /web/index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Mobile Deployment

### H5

```bash
cd FastapiAdmin/frontend/app
pnpm install && pnpm run build:h5
# Deploy dist/build/h5 to Nginx
```

### Mini Program

```bash
pnpm run build:mp-weixin
# Import dist/build/mp-weixin into WeChat DevTools
# Upload and submit for review
```

## Common Deployment Issues

| Issue | Solution |
|-------|----------|
| Docker container fails to start | `cd docker && docker compose logs [service]` |
| Missing env file | `cp docker/.env.example docker/.env` |
| Database connection failure | Check `.env` credentials, MySQL container status |
| Nginx 502 Bad Gateway | Check backend is running, port is correct |
| SSL certificate error | Check certificate path and validity |
| Port conflict | Change port in `.env` |
