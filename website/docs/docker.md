---
sidebar_position: 3
---

# 🐳 Docker 部署 (Go 版)

## 镜像仓库

Go 版发布到独立的 `ledger-go` 命名空间(与 Python 版 `zouzhenglu/ledger` 并存):

| 仓库 | 拉取命令 | 速度 |
|------|----------|------|
| **Docker Hub**(主) | `docker pull zouzhenglu/ledger-go:latest` | 🌍 全球默认 |
| **GitHub Container Registry** | `docker pull ghcr.io/kdeerfish/ledger-go:latest` | 🌍 备选 |
| **阿里云容器镜像服务** | `docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger-go:latest` | 🇨🇳 国内最快 |

## 多架构支持

每个仓库同时提供:
- `linux/amd64` — 普通 PC / 服务器
- `linux/arm64` — 树莓派 / Mac M1 / ARM 服务器

Docker 自动选择匹配的架构。

## 快速启动

```bash
docker run -d \
  --name ledger \
  -p 5800:5800 \
  -v $(pwd)/data:/data \
  --restart unless-stopped \
  zouzhenglu/ledger-go:latest
```

启动后访问 http://localhost:5800。

## docker-compose

```yaml
services:
  ledger:
    image: zouzhenglu/ledger-go:latest
    container_name: ledger
    restart: unless-stopped
    ports:
      - "5800:5800"
    volumes:
      - ./data:/data
    environment:
      WEB_HOST: "0.0.0.0"
      WEB_PORT: "5800"
      LEDGER_DB_PATH: "/data/ledger.db"
      LOG_LEVEL: "info"
```

```bash
wget https://raw.githubusercontent.com/kdeerfish/ledger/rewrite/go/docker-compose.yml
docker compose up -d
```

## 数据持久化

数据库保存在容器 `/data/ledger.db`,通过 `-v $(pwd)/data:/data` 映射到宿主机。
删除容器不会丢数据,反之亦然(只要不删宿主机目录)。

## 多实例并存

Go 版与 Python 版可以同时跑(用不同端口):

```bash
# Python 版: :5800 (旧数据)
docker run -d --name ledger-py -p 5800:5800 -v $(pwd)/data-py:/data zouzhenglu/ledger

# Go 版: :5801 (新数据)
docker run -d --name ledger-go -p 5801:5800 -v $(pwd)/data-go:/data zouzhenglu/ledger-go
```

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `WEB_HOST` | `0.0.0.0` | HTTP 监听地址 |
| `WEB_PORT` | `5800` | HTTP 端口 |
| `WEB_DEBUG` | `false` | 调试模式 (verbose 日志) |
| `WEB_CORS_ORIGINS` | `*` | CORS 允许的来源 (逗号分隔) |
| `LEDGER_DB_PATH` | `/data/ledger.db` | SQLite 文件路径 |
| `LOG_LEVEL` | `info` | debug / info / warn / error |
| `LOG_FORMAT` | `json` | json / text (debug 模式默认 text) |

## 健康检查

镜像内置 `HEALTHCHECK`(基于 `ledger version` 命令),Docker 自动监控容器健康状态:

```bash
docker inspect --format='{{.State.Health.Status}}' ledger
# 输出: healthy / unhealthy / starting
```

## 升级

```bash
# 1. 拉取新版
docker pull zouzhenglu/ledger-go:latest

# 2. 停掉旧容器
docker stop ledger && docker rm ledger

# 3. 启动新容器(数据卷保持不动)
docker run -d --name ledger -p 5800:5800 -v $(pwd)/data:/data zouzhenglu/ledger-go:latest
```

## 镜像体积对比

| 版本 | 基础镜像 | 压缩后 | 解压后 |
|------|----------|--------|--------|
| Python 0.1.0 | `python:3.11-alpine` + node | ~30 MB | ~110 MB |
| **Go 0.2.0** | `distroless/static:nonroot` | ~8 MB | **~20 MB** |
