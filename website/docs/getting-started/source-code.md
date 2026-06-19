---
sidebar_position: 4
---

# 🛠 源码运行（不用 Docker）

> 适合：Linux 服务器、个人电脑、想二次开发的用户、需要完全控制运行环境的场景。

---

## 0. 前置环境

| 工具 | 最低版本 | 检查命令 |
|------|---------|---------|
| Python | 3.10+ | `python3 --version` |
| pip | 最新 | `pip --version` |
| Git | 任意 | `git --version` |
| Node.js（仅前端构建时需要） | 20+ | `node --version` |

:::tip 只想跑 CLI 命令行？
**不需要 Node.js**，Python 装好就行。
:::

---

## 1. 克隆项目

```bash
git clone https://github.com/kdeerfish/ledger.git
cd ledger
```

---

## 2. 创建虚拟环境（推荐）

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1

# Windows CMD
python -m venv .venv
.venv\Scripts\activate.bat
```

激活后命令行会有 `(.venv)` 前缀。

---

## 3. 安装依赖

### 最小依赖（仅 CLI）

```bash
pip install -e .
```

### 完整开发依赖（含 Web、测试、代码检查）

```bash
pip install -e ".[dev,lint]"
```

---

## 4. 配置（可选）

复制示例配置文件：

```bash
cp .env.example .env
```

`.env` 文件里能改的配置（**留空就用默认值**）：

```bash
# 数据库文件路径（默认：./ledger.db）
LEDGER_DB_PATH=./ledger.db

# Web 服务监听地址 / 端口
WEB_HOST=0.0.0.0
WEB_PORT=5800
WEB_DEBUG=false

# CORS 跨域（如需从其他域名访问 API）
# WEB_CORS_ORIGINS=https://myapp.example.com
```

---

## 5A. 仅用 CLI（最快）

不用启动 Web 服务，直接命令行记账：

```bash
# 初始化数据库（首次会自动建，也可以不跑）
python scripts/cli.py init

# 记一笔
python scripts/cli.py add --type 支出 --amount 100 --category 食品 --account 微信

# 查看最近
python scripts/cli.py list

# 看月度汇总
python scripts/cli.py summary
```

完整命令列表见 [CLI 命令参考](../user-guide/cli.md)。

---

## 5B. 启动 Web 服务

### 生产模式（一个端口搞定）

需要先把前端构建好：

```bash
# 1. 构建前端
cd frontend
npm install
npm run build
cd ..

# 2. 启动 Web
python web/run.py
```

访问 `http://localhost:5800` 。

### 开发模式（带热更新）

```bash
# 终端 1：Flask 后端（会自动代理前端请求到 Vite）
WEB_DEBUG=true python web/run.py

# 终端 2：Vite 前端开发服务器
cd frontend && npm run dev
```

访问 `http://localhost:5800` ，改代码自动刷新。

或者用 VS Code 的 **"Full Stack Dev"** compound 配置一键启动。

---

## 6. 让 Web 服务后台运行

### Linux / macOS

```bash
# 方式 1：nohup
nohup python web/run.py > ledger-web.log 2>&1 &

# 方式 2：screen（可重连）
screen -dmS ledger python web/run.py
# 重连：screen -r ledger

# 方式 3：tmux
tmux new -d -s ledger 'python web/run.py'
# 重连：tmux attach -t ledger

# 方式 4：systemd 服务（生产推荐）
```

### 用 systemd 做成服务（Linux 推荐）

创建 `/etc/systemd/system/ledger.service`：

```ini
[Unit]
Description=Ledger Personal Accounting
After=network.target

[Service]
Type=simple
User=你的用户名
WorkingDirectory=/home/你的用户名/ledger
Environment=PATH=/home/你的用户名/ledger/.venv/bin
ExecStart=/home/你的用户名/ledger/.venv/bin/python web/run.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ledger
sudo systemctl status ledger
```

### Windows 后台运行

用 [NSSM](https://nssm.cc/) 把 `python web/run.py` 注册成 Windows 服务，最稳。

或者用 [PM2](https://pm2.keymetrics.io/)（需要 Node）：

```bash
npm install -g pm2
pm2 start "python web/run.py" --name ledger
pm2 save
pm2 startup
```

---

## 7. 数据在哪？

| 模式 | 数据库路径 |
|------|----------|
| 默认 | 项目根目录 `./ledger.db` |
| 自定义 | `.env` 里 `LEDGER_DB_PATH` 指定 |

### 备份

直接复制 `.db` 文件即可：

```bash
cp ./ledger.db ./ledger-$(date +%Y%m%d).db
```

---

## 8. 升级

```bash
cd ledger
git pull
pip install -e ".[dev,lint]"   # 拉新依赖
cd frontend && npm install && npm run build && cd ..
# 重启 Web 服务
```

数据库格式向后兼容，**升级不丢数据**。

---

## 9. 故障排除

### `ModuleNotFoundError: No module named 'flask'`

依赖没装全：`pip install -e .` 或 `pip install -e ".[dev,lint]"`

### 端口被占用

```bash
# 找占用进程
# Linux/macOS
sudo lsof -i :5800
# Windows
netstat -ano | findstr :5800

# 换成别的端口
WEB_PORT=8800 python web/run.py
```

### 中文乱码（Windows）

源码已做兼容处理。如果还是乱码：

```powershell
# PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
python web/run.py
```

---

更多问题见 [FAQ · 故障排除](../faq/troubleshooting.md)。