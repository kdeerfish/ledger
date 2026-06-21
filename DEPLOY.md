# Ledger 部署指南

## 📦 我该下载什么？

| 你的环境 | 下载 | 说明 |
|---------|------|------|
| **Windows 电脑** | `Ledger.zip` | 桌面端 EXE，解压即用 |
| **NAS / 服务器** | 直接拉 Docker 镜像 | 一行命令启动 |
| **开发者** | 源码运行 | 本地开发调试 |
| **AI Agent** | `ledger-skills.zip` | 接入 AI 记账 |

> 所有包均可在 [GitHub Releases](https://github.com/kdeerfish/ledger/releases) 下载。

---

## 🖥️ Windows 桌面端

**适合**：个人电脑用户，不想装 Docker，双击就用。

### 安装步骤

1. 下载 `Ledger.zip`
2. 解压到任意目录
3. 双击 `ledger.exe`
4. 浏览器自动打开 http://localhost:5800

### 特点

- ✅ 免安装，解压即用
- ✅ 自带 Flask 后端 + React 前端
- ✅ 系统托盘图标，可最小化到托盘
- ✅ 自动打开浏览器

### 命令行参数

```bash
ledger.exe                       # 默认启动（端口 5800）
ledger.exe --port 8080           # 指定端口
ledger.exe --width 1400 --height 900  # 指定窗口大小
```

---

## 🐳 Docker 部署（推荐）

**适合**：NAS、服务器、群晖、飞牛OS 等长期运行的环境。

### 一行启动

```bash
docker run -d --name ledger -p 5800:5800 \
  -v $(pwd)/data:/data \
  --restart unless-stopped \
  zouzhenglu/ledger:latest
```

然后访问 http://你的IP:5800

### 国内镜像（拉取更快）

```bash
docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest
```

### Docker Compose 部署

1. 创建目录：
   ```bash
   mkdir -p /volume1/docker/ledger/data
   cd /volume1/docker/ledger
   ```

2. 创建 `docker-compose.yml`：
   ```yaml
   version: "3.8"
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
         - TZ=Asia/Shanghai
   ```

3. 启动：
   ```bash
   docker compose up -d
   ```

### 飞牛OS / 群晖

1. 打开 Docker 套件 → 项目 → 新建
2. 选择目录，上传 `docker-compose.yml`
3. 点击部署

---

## 🚀 开发者（源码运行）

**适合**：想修改代码、调试功能、贡献代码。

### 前置要求

- Python 3.10+
- Node.js 18+
- Git

### 步骤

```bash
# 1. 克隆仓库
git clone https://github.com/kdeerfish/ledger.git
cd ledger

# 2. 安装 Python 依赖
pip install -e ".[dev,lint]"

# 3. 安装前端依赖
cd frontend && npm install && cd ..

# 4. 构建前端
cd frontend && npm run build && cd ..

# 5. 启动
python web/run.py
```

访问 http://localhost:5800

### 开发模式（热更新）

```bash
# 终端1：启动后端（调试模式）
WEB_DEBUG=true python web/run.py

# 终端2：启动前端开发服务器
cd frontend && npm run dev
```

访问 http://localhost:5173（前端热更新）

---

## 🤖 AI Agent 集成

**适合**：想用 AI 助手记账（如 Claude、GPT 等）。

### 步骤

1. 下载 `ledger-skills.zip`
2. 解压后配置 `.env`：
   ```bash
   LEDGER_API_URL=http://你的服务器IP:5800
   ```
3. 将 `scripts/` 目录提供给 AI Agent

### 技能说明

| 技能 | 功能 |
|------|------|
| `add_transaction` | 添加收支记录 |
| `list_transactions` | 查询交易列表 |
| `get_summary` | 获取统计摘要 |
| `manage_budget` | 管理预算 |

---

## 🔧 数据维护

### 导入 CSV

**Docker 环境**：
```bash
# 把 CSV 放到数据目录
cp mydata.csv /volume1/docker/ledger/data/

# 在容器内导入
docker exec -it ledger python scripts/import_ledger.py /data/mydata.csv
```

**本地环境**：
```bash
python scripts/import_ledger.py data/mydata.csv
```

### 备份数据库

```bash
# Docker
cp /volume1/docker/ledger/data/ledger.db /backup/ledger-$(date +%Y%m%d).db

# 本地
cp ledger.db /backup/ledger-$(date +%Y%m%d).db
```

### 升级

**Docker**：
```bash
docker pull zouzhenglu/ledger:latest
docker compose up -d
```

**本地**：
```bash
git pull
pip install -e ".[dev,lint]"
cd frontend && npm install && npm run build && cd ..
python web/run.py
```

---

## ❓ 故障排除

### 前端空白 / 404

- **Docker**：镜像已内置前端，无需额外操作
- **本地**：确认执行过 `cd frontend && npm run build`

### Agent 连不上 API

```bash
# 测试 API 是否正常
curl http://你的IP:5800/api/health
```

检查项：
- 服务是否启动：`docker ps | grep ledger` 或查看进程
- 端口是否开放：防火墙 / NAS 安全设置
- `.env` 中 `LEDGER_API_URL` 是否正确

### 数据库不存在

首次启动会自动创建，无需手动初始化。

---

## 📋 镜像仓库

| 仓库 | 拉取命令 | 适用 |
|------|----------|------|
| **Docker Hub** | `docker pull zouzhenglu/ledger:latest` | 🌍 全球默认 |
| GitHub Container Registry | `docker pull ghcr.io/kdeerfish/ledger:latest` | 🌍 备选 |
| **阿里云** | `docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest` | 🇨🇳 国内最快 |
