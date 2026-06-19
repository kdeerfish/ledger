---
sidebar_position: 2
---

# 🚀 快速开始 (Go 版)

## 🐳 Docker 部署(推荐)

```bash
# Go 版独立仓库,与 Python 版 (zouzhenglu/ledger) 不冲突
docker pull zouzhenglu/ledger-go
docker run -d --name ledger -p 5800:5800 -v $(pwd)/data:/data --restart unless-stopped zouzhenglu/ledger-go

# 查看日志
docker logs -f ledger

# 打开 http://localhost:5800
```

> 无需安装 Python 或 Node.js,有 Docker 就能用。

## 📦 单二进制部署

下载适合你系统的二进制:

```bash
# Linux
wget https://github.com/kdeerfish/ledger/releases/latest/download/ledger-linux-amd64.tar.gz
tar xzf ledger-linux-amd64.tar.gz
./ledger serve --port 5800

# Windows (PowerShell)
Invoke-WebRequest -Uri "https://github.com/kdeerfish/ledger/releases/latest/download/ledger-windows-amd64.zip" -OutFile "ledger.zip"
Expand-Archive ledger.zip
.\ledger.exe serve --port 5800

# macOS
curl -L -o ledger.tar.gz https://github.com/kdeerfish/ledger/releases/latest/download/ledger-darwin-arm64.tar.gz
tar xzf ledger.tar.gz
./ledger serve --port 5800
```

## 💻 CLI 使用

下载后可以直接在命令行使用:

```bash
./ledger version
./ledger tx add --type 支出 --amount 25.5 --category 食品 --account 微信
./ledger tx list --limit 10
./ledger misc summary --year 2026 --month 6
./ledger misc stats --group-by category
./ledger misc export --output report.csv --format csv
```

完整命令列表见 [CLI 手册](./cli/index)。

## 🌐 HTTP API

启动服务后,所有功能也可通过 HTTP 调用:

```bash
# 健康检查
curl http://localhost:5800/api/health

# 列出最近交易
curl http://localhost:5800/api/transactions

# 新增一笔
curl -X POST http://localhost:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"支出","amount":25.5,"category":"食品","account":"微信"}'
```

完整接口见 [HTTP API 文档](./api)。

## 🔄 从 Python 版升级

**Go 版与 Python 版数据不互通**, 因为:
- Go 版使用同一个 SQLite schema(v2),但**走全新空库**(`./data/ledger-go.db`)
- Python 用户的原 `ledger.db` 保留不动,不被 Go 版读取或修改

升级路径:

```bash
# 1. Python 版继续跑在 master 分支(旧数据 ./data/ledger.db)
cd ledger && git checkout master
python web/run.py  # 旧服务跑在 :5800

# 2. Go 版跑在 rewrite/go 分支(新数据 ./data/ledger-go.db)
git checkout rewrite/go
go build -o bin/ledger ./cmd/ledger
./bin/ledger serve --port 5801  # 用不同端口避免冲突

# 3. 用 Go 版 CLI 导出 Python 库,再导入 Go 库
# Python 库导出
python -c "import sqlite3; c=sqlite3.connect('data/ledger.db').cursor(); c.execute('SELECT * FROM transactions'); ..."
# 导入 Go 库(用 misc import --file)
./bin/ledger misc import --file migrated.csv
```

(详细迁移脚本后续 PR 跟进。)

## 🛠 本地开发

```bash
git clone https://github.com/kdeerfish/ledger.git
cd ledger
git checkout rewrite/go

# 安装依赖
go mod download

# 编译
make build

# 跑测试
make test

# 跑服务
./bin/ledger serve --port 5800
```

详细开发指南见 [开发文档](./development)。
