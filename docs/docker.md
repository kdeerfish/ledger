---
layout: default
title: Docker 部署指南
---

# 🐳 Docker 部署

## 镜像仓库

Ledger 通过 GitHub Actions CI/CD 自动构建，推送到 3 个镜像仓库：

| 仓库 | 地址 | 适合场景 |
|------|------|----------|
| **Docker Hub** | `zouzhenglu/ledger` | 全球通用 |
| **GitHub Container Registry** | `ghcr.io/kdeerfish/ledger` | 开发者、GitHub 生态 |
| **阿里云容器镜像服务** | `crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger` | 🇨🇳 国内用户（速度最快） |

---

## 📥 拉取镜像

```bash
# Docker Hub
docker pull zouzhenglu/ledger:latest

# ghcr.io（需先登录）
echo ${{ secrets.GHCR_TOKEN }} | docker login ghcr.io -u zouzhenglu --password-stdin
docker pull ghcr.io/kdeerfish/ledger:latest

# 阿里云
docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest
```

> **提示**：阿里云国内访问速度最快，推荐中国大陆用户使用。

---

## 🚀 快速启动

### 方式一：docker run

```bash
docker run -d \
  --name ledger \
  -p 5800:5800 \
  -v $(pwd)/data:/data \
  --restart unless-stopped \
  zouzhenglu/ledger:latest
```

### 方式二：docker-compose（推荐）

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

### 方式三：从源码构建

```bash
git clone https://github.com/kdeerfish/ledger.git
cd ledger
docker compose build
docker compose up -d
```

---

## 📂 数据持久化

数据库默认保存在容器的 `/data/ledger.db`，通过挂载卷持久化：

```bash
# 宿主机路径可自定义
-v /volume1/docker/ledger/data:/data
```

**备份数据库：**

```bash
cp ./data/ledger.db ./data/ledger-$(date +%Y%m%d).db
```

**导入已有数据：**

把旧的 `ledger.db` 复制到 `./data/` 目录下，重启容器即可：

```bash
docker compose restart
```

---

## 📋 运维命令

```bash
# 查看日志
docker compose logs -f

# 停止
docker compose down

# 升级（拉取最新镜像）
docker compose pull
docker compose up -d

# 从源码升级
git pull
docker compose up -d --build

# 进入容器
docker exec -it ledger bash

# 在容器内导入 CSV
docker exec -it ledger python scripts/import_ledger.py /data/mymoney_data.csv
```

---

## 🔄 CI/CD 流水线

每次 push 到 `master` 分支或打 `v*` 格式的 tag，GitHub Actions 自动：

1. ✅ 运行 pytest（102+ 测试用例）
2. ✅ 构建 Docker 镜像
3. ✅ 推送到 Docker Hub + ghcr.io + 阿里云

镜像标签规则：

| 触发方式 | 镜像标签 |
|----------|----------|
| push master | `:latest` |
| push tag `v1.5.0` | `:1.5.0` + `:latest` |
| 手动触发 | 自定义标签 + `:latest` |

---

## 🔧 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `WEB_HOST` | 监听地址 | `0.0.0.0` |
| `WEB_PORT` | 端口 | `5800` |
| `WEB_DEBUG` | 调试模式 | `false` |
| `LEDGER_DB_PATH` | 数据库路径 | `/data/ledger.db` |
| `TZ` | 时区 | `Asia/Shanghai` |

---

## 🩺 健康检查

```bash
curl http://localhost:5800/api/health
# {"success": true, "data": {"status": "ok"}}
```

Docker 内置健康检查（每 30s）确保容器自动恢复。
