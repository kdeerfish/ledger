# Ledger 部署指南

## 📦 部署包说明

| 包 | 说明 |
|----|------|
| `Ledger.zip` | Windows 桌面端（EXE，解压即用） |
| `ledger-service.zip` | 核心服务（已容器化，推荐 Docker 部署） |
| `ledger-skills.zip` | AI Agent 技能（HTTP API 客户端） |

---

## 🖥️ Windows 桌面端

从 GitHub Release 下载 `Ledger.zip`，解压后双击 `ledger.exe` 即可运行，无需安装 Python 或其他依赖。

### 特点
- 自带 Flask 后端 + React 前端，解压即用
- 系统托盘图标，支持最小化到托盘
- 默认端口 5800，访问 http://localhost:5800

### 命令行参数
```bash
ledger.exe --port 8080          # 指定端口
ledger.exe --width 1400 --height 900  # 指定窗口大小
```

---

## 🐳 Docker 部署（推荐）

Docker 镜像使用多阶段构建，自动编译 React 前端 + Python 后端，一个镜像搞定。

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
# 构建（自动编译前端 + 打包 Python 后端）并启动
docker compose up -d --build

# 查看日志
docker compose logs -f

# 访问 http://飞牛OS_IP:5800
```

构建过程：
1. 第一阶段：用 Node.js 20 编译 React 前端到 `dist/`
2. 第二阶段：用 Python 3.11 运行 Flask 后端，直接服务编译好的前端
3. 最终镜像只包含运行所需文件，不含 Node.js

### 4. 配置 Skills

```bash
# skills/ledger/.env
LEDGER_API_URL=http://192.168.31.126:5800
```

---

## 🚀 本地运行

### 生产模式（直接服务构建好的前端）

```bash
# 1. 构建前端
cd frontend && npm install && npm run build && cd ..

# 2. 安装 Python 依赖
pip install flask flask-cors

# 3. 启动（自动服务 frontend/dist/ 里的前端文件）
python web/run.py

# 4. 访问 http://127.0.0.1:5800
```

### 开发模式（有热更新）

```bash
# 终端1：启动 Flask 后端（调试模式，代理前端请求到 Vite）
WEB_DEBUG=true python web/run.py

# 终端2：启动 Vite 开发服务器
cd frontend && npm run dev

# 访问 http://127.0.0.1:5173（或 :5800 自动代理到 Vite）
```

或直接用 VS Code launch.json 里的 **"Full Stack Dev"** compound 配置。

---

## 🔧 数据维护

### 导入 CSV

```bash
# 把 CSV 放到数据目录
cp mydata.csv /volume1/docker/ledger/data/

# 在容器内导入
docker exec -it ledger python scripts/import_ledger.py /data/mydata.csv
```

### 备份数据库

```bash
cp /volume1/docker/ledger/data/ledger.db /volume1/backup/ledger-$(date +%Y%m%d).db
```

### 升级

```bash
cd /volume1/docker/ledger
git pull
# 重新构建（含前端编译）+ 启动
docker compose up -d --build
```

---

## ❓ 故障排除

### 前端空白 / 404

**生产环境**：确认 `frontend/dist/` 存在且包含 `index.html`。Docker 部署时多阶段构建会自动生成。

**本地生产模式**：
```bash
cd frontend && npm run build
```

### Agent 连不上 API

```bash
curl http://NAS_IP:5800/api/health
```

- 确认容器运行：`docker ps | grep ledger`
- 确认 `.env` 中 `LEDGER_API_URL` 指向正确 IP 和端口
- 确认防火墙未阻挡 5800 端口

### 数据库不存在

首次启动会自动创建，或通过导入 CSV 初始化。
