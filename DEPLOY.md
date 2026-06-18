# Ledger 部署指南

## 📦 部署包说明

| 包 | 说明 |
|----|------|
| `ledger-service.zip` | 核心服务（已容器化，推荐 Docker 部署） |
| `ledger-skills.zip` | AI Agent 技能（HTTP API 客户端） |

---

## 🐳 Docker 部署（推荐）

### 1. 准备

```bash
# SSH 到飞牛OS
ssh admin@nas_ip

# 创建项目目录
mkdir -p /volume1/docker/ledger/data
cd /volume1/docker/ledger
```

### 2. 上传文件

通过飞牛OS 文件管理器，把整个项目上传到 `/volume1/docker/ledger/`。

### 3. 启动

```bash
# 构建并启动
docker compose up -d

# 查看日志
docker compose logs -f

# 访问 http://飞牛OS_IP:5800
```

### 4. 配置 Skills

解压 `ledger-skills.zip` 到 Agent 可访问的位置，编辑 `.env`：

```bash
# skills/ledger/.env
LEDGER_API_URL=http://192.168.31.126:5800
```

---

## 🚀 本地测试（非 Docker）

```bash
# 1. 安装依赖
pip install flask flask-cors

# 2. 配置环境
cp .env.example .env

# 3. 导入数据（如果有 CSV）
python scripts/import_ledger.py data.csv

# 4. 启动 Web 服务
python web/run.py

# 5. 访问 http://127.0.0.1:5800
```

---

## 🔧 数据维护

### 导入 CSV

Docker 部署时，CSV 需要通过容器内执行：

```bash
# 把 CSV 放到数据目录
cp mydata.csv /volume1/docker/ledger/data/

# 在容器内导入
docker exec -it ledger python scripts/import_ledger.py /data/mydata.csv
```

### 备份数据库

```bash
# Docker 数据在宿主机的 ./data/ 目录
cp /volume1/docker/ledger/data/ledger.db /volume1/backup/ledger-$(date +%Y%m%d).db
```

### 升级

```bash
cd /volume1/docker/ledger
git pull
docker compose up -d --build
```

---

## ❓ 故障排除

### 问题：Agent 连不上 API

**检查**：
```bash
# 在 Agent 所在机器上测试
curl http://NAS_IP:5800/api/health
```

**解决**：
- 确认 Docker 容器在运行：`docker ps | grep ledger`
- 确认 `.env` 中 `LEDGER_API_URL` 指向正确的 IP 和端口
- 确认飞牛OS 防火墙未阻挡 5800 端口

### 问题：数据库不存在

**解决**：
首次启动会自行创建，或通过导入 CSV 初始化。
