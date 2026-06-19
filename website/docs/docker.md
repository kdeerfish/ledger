---
sidebar_position: 3
---

# 🐳 Docker 部署

## 镜像仓库

Ledger 通过 GitHub Actions CI/CD 自动构建，推送到 **3 个镜像仓库**：

| 仓库 | 拉取命令 | 速度 |
|------|----------|------|
| **Docker Hub**（主） | `docker pull zouzhenglu/ledger:latest` | 🌍 全球默认 |
| **GitHub Container Registry** | `docker pull ghcr.io/kdeerfish/ledger:latest` | 🌍 备选 |
| **阿里云容器镜像服务** | `docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest` | 🇨🇳 国内最快 |

:::tip 国内用户推荐
阿里云镜像无需代理，拉取速度最快
:::

## 🚀 快速启动

### docker run

```bash
docker run -d \
  --name ledger \
  -p 5800:5800 \
  -v $(pwd)/data:/data \
  --restart unless-stopped \
  zouzhenglu/ledger:latest
```

### docker-compose（推荐）

创建 `docker-compose.yml`：

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

启动：

```bash
docker compose up -d
docker compose logs -f
```

### 从源码构建

```bash
git clone https://github.com/kdeerfish/ledger.git
cd ledger
docker compose build
docker compose up -d
```

启动后访问 [http://localhost:5800](http://localhost:5800)

## 📂 数据持久化

数据库默认保存在容器的 `/data/ledger.db`，通过挂载卷持久化：

```bash
-v /volume1/docker/ledger/data:/data
```

### 备份数据库

```bash
cp ./data/ledger.db ./data/ledger-$(date +%Y%m%d).db
```

### 导入已有数据

把旧的 `ledger.db` 复制到 `./data/` 目录下，重启容器即可：

```bash
docker compose restart
```

## 📋 运维命令

| 命令 | 说明 |
|------|------|
| `docker compose logs -f` | 查看实时日志 |
| `docker compose down` | 停止容器 |
| `docker compose pull` | 拉取最新镜像 |
| `docker compose up -d` | 重启 |
| `git pull && docker compose up -d --build` | 从源码升级 |
| `docker exec -it ledger bash` | 进入容器 |
| `docker exec -it ledger python scripts/import_ledger.py /data/file.csv` | 容器内导入 CSV |

## 🔄 CI/CD 流水线

每次 push 到 `master` 分支或打 `v*` tag，GitHub Actions 自动执行：

```mermaid
graph LR
    A[Push master/tag] --> B[Run Tests (252)]
    B --> C[Build Frontend]
    C --> D[Build Docker]
    D --> E[Docker Hub]
    D --> F[ghcr.io]
    D --> G[阿里云]
```

### 镜像标签规则

| 触发方式 | 构建标签 |
|----------|----------|
| push `master` | `:latest` |
| push tag `v0.1.0` | `:0.1.0` + `:latest` |
| 手动触发 | 自定义标签 + `:latest` |

## 🔧 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `WEB_HOST` | 监听地址 | `0.0.0.0` |
| `WEB_PORT` | 端口 | `5800` |
| `WEB_DEBUG` | 调试模式 | `false` |
| `LEDGER_DB_PATH` | 数据库路径 | `/data/ledger.db` |
| `TZ` | 时区 | `Asia/Shanghai` |

## 🩺 健康检查

```bash
curl http://localhost:5800/api/health
```

```json
{"success": true, "data": {"status": "ok"}}
```

Docker 内置 HEALTHCHECK（每 30s 检测一次），容器异常自动重启。
