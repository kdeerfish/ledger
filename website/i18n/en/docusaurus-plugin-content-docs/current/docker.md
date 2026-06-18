---
sidebar_position: 3
---

# 🐳 Docker Deployment

## Image Registries

| Registry | Pull Command | Speed |
|----------|-------------|-------|
| **Docker Hub** | `docker pull zouzhenglu/ledger:latest` | 🌍 Global |
| **ghcr.io** | `docker pull ghcr.io/kdeerfish/ledger:latest` | 🌍 Global |
| **Alibaba Cloud** | `docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest` | 🇨🇳 China |

## Quick Start

### docker run

```bash
docker run -d \
  --name ledger \
  -p 5800:5800 \
  -v $(pwd)/data:/data \
  --restart unless-stopped \
  zouzhenglu/ledger:latest
```

### docker-compose

```yaml
services:
  ledger:
    image: zouzhenglu/ledger:latest
    container_name: ledger
    restart: unless-stopped
    ports:
      - "5800:5800"
    volumes:
      - ./data:/data
    environment:
      - WEB_HOST=0.0.0.0
      - WEB_PORT=5800
      - TZ=Asia/Shanghai
```

### Build from source

```bash
git clone https://github.com/kdeerfish/ledger.git
cd ledger
docker compose build
docker compose up -d
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WEB_HOST` | Bind address | `0.0.0.0` |
| `WEB_PORT` | Port | `5800` |
| `WEB_DEBUG` | Debug mode | `false` |
| `LEDGER_DB_PATH` | Database path | `/data/ledger.db` |
| `TZ` | Timezone | `Asia/Shanghai` |

## Health Check

```bash
curl http://localhost:5800/api/health
```

```json
{"success": true, "data": {"status": "ok"}}
```
