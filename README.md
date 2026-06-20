# 📒 Ledger — 个人记账系统 (Go 版)

**收支管理 · 预算规划 · 标签分类 · 多维统计 · React 仪表盘 · AI Agent 集成**

[![CI](https://img.shields.io/github/actions/workflow/status/kdeerfish/ledger/ci.yml?branch=rewrite/go&label=CI%2FCD&logo=github)](https://github.com/kdeerfish/ledger/actions)
[![Tests](https://img.shields.io/github/actions/workflow/status/kdeerfish/ledger/ci.yml?branch=rewrite/go&label=Tests&logo=vitest)](https://github.com/kdeerfish/ledger/actions)
[![License](https://img.shields.io/github/license/kdeerfish/ledger)](LICENSE)
[![License](https://img.shields.io/github/license/kdeerfish/ledger)](LICENSE)
[![Go](https://img.shields.io/badge/Go-1.23%2B-00ADD8?logo=go)](https://go.dev/)
[![Go Coverage](https://img.shields.io/codecov/c/github/kdeerfish/ledger?branch=rewrite/go&label=Go%20Coverage&logo=codecov)](https://codecov.io/gh/kdeerfish/ledger)
[![Frontend Coverage](https://img.shields.io/codecov/c/github/kdeerfish/ledger?branch=rewrite/go&label=Frontend%20Coverage&logo=codecov&flag=frontend)](https://codecov.io/gh/kdeerfish/ledger)

> **Go 重写版本** — 体积更小(单二进制 ~20MB),启动更快(无 Python/Node 运行时),性能更好(原生并发),API 100% 兼容原 Python 版本。
> 旧 Python 版仍在 `master` 分支保留,供回退使用。

---

## 🐳 一分钟启动

### 方式 1: Docker(推荐)
```bash
# Go 版发布到独立仓库 ledger-go,与 Python 版 (zouzhenglu/ledger) 并行不冲突
docker pull zouzhenglu/ledger-go
docker run -d \
  --name ledger-go \
  -p 5800:5800 \
  -v $(pwd)/data:/data \
  --restart unless-stopped \
  zouzhenglu/ledger-go
open http://localhost:5800
```

### 方式 2: docker-compose(从 rewrite/go 分支)
```bash
wget https://raw.githubusercontent.com/kdeerfish/ledger/rewrite/go/docker-compose.yml
docker compose up -d
```

### 方式 3: 单二进制
```bash
# 从 release 下载
wget https://github.com/kdeerfish/ledger/releases/latest/download/ledger-linux-amd64.tar.gz
tar xzf ledger-linux-amd64.tar.gz
./ledger serve --port 5800
```

### 备选镜像仓库(Go 版 `ledger-go` 命名空间)

| 仓库 | 拉取命令 | 适用场景 |
|------|----------|----------|
| **Docker Hub**(主) | `docker pull zouzhenglu/ledger-go` | 🌍 全球默认 |
| GitHub Container Registry | `docker pull ghcr.io/kdeerfish/ledger-go` | 🌍 开发者备选 |
| 阿里云容器镜像服务 | `docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger-go` | 🇨🇳 国内最快 |

> 📦 旧 Python 版镜像仍在 `zouzhenglu/ledger`,**与 Go 版并行不冲突**,你可以按需拉取任意版本。

---

## ✨ 功能总览

| 功能 | 说明 |
|------|------|
| ✅ **收支记账** | 添加 / 编辑 / 软删除 / 恢复 / 物理删除 |
| ✅ **标签分类** | 多标签创建 / 关联 / 筛选 / 统计,颜色标记 |
| ✅ **CSV 导入** | 随手记 CSV 一键导入,自动去重 |
| ✅ **搜索筛选** | 关键词 + 类别 / 账户 / 商家 / 标签 / 日期等多维筛选 |
| ✅ **统计分析** | 按 9 种维度分组统计 |
| ✅ **预算管理** | 按月 / 类别 / 维度设置预算,进度跟踪 |
| ✅ **预算模板** | 创建模板、一键应用、智能推荐 |
| ✅ **记账模板** | 常用交易模板,一键记账,使用频次统计 |
| ✅ **数据导出** | CSV / JSON 格式导出 |
| ✅ **React 仪表盘** | 响应式 UI,手机 / 平板 / PC 均可用 |
| ✅ **AI Agent 集成** | `skills/ledger/SKILL.md` 供 LLM Agent 调用 |
| ✅ **Docker 多架构** | linux/amd64, linux/arm64, windows/amd64, darwin/amd64, darwin/arm64 |

---

## 📖 CLI 命令速查

```bash
# 交易管理
ledger tx add    --type 支出 --amount 100 --category 食品 --account 微信
ledger tx list
ledger tx get    --id 1
ledger tx update --id 1 --field amount --value 120
ledger tx delete --id 1              # 软删除
ledger tx restore --id 1
ledger tx hard-delete --id 1 --confirm

# 预算
ledger budget set   --category 食品 --amount 1000 --year 2026 --month 6
ledger budget check --year 2026 --month 6
ledger budget template-create --name 月度餐饮 --category 食品 --amount 1500
ledger budget template-apply  --id 1

# 记账模板
ledger template create --name 早餐 --type 支出 --amount 8 --category 食品
ledger template apply  --id 1
ledger template suggest

# 搜索 / 过滤 / 统计
ledger misc search  --keyword 午餐
ledger misc filter  --category 食品 --start-date 2026-01-01
ledger misc summary --year 2026 --month 6
ledger misc stats   --group-by category
ledger misc analyze

# 数据导入导出
ledger misc import --file data.csv
ledger misc export --output report.csv --format csv
```

---

## 🌐 Web 管理界面

启动后访问 `http://localhost:5800`:

| 页面 | 功能 |
|------|------|
| **概览** | 收支卡片 + 月度柱状图 + 累计折线图 + 类别环形图 |
| **交易** | 多维筛选表格 + 分页 + 编辑 / 删除 |
| **记一笔** | 模板选择 + 字段自动建议 + 子类别 + 标签选择器 |
| **预算** | 总览卡片 + 类别进度条 + 执行明细表 |
| **类别+标签** | 类别层级统计 + 标签创建 / 颜色管理 |
| **统计** | 9 种分组 × 3 种图表 |

---

## 🤖 AI Agent 集成

`skills/ledger/SKILL.md` 是给 LLM Agent 看的技能说明,支持:
- Claude Code / Cursor / Continue / Cline 等 IDE Agent
- 通过 HTTP API 自动化记账
- 通过 CLI 在 shell 里调用

参见 [`skills/ledger/SKILL.md`](skills/ledger/SKILL.md) 详细文档。

---

## 🛠 开发

### 环境要求

- Go 1.23+
- Node.js 20+(仅前端开发时需要)
- Docker(可选,用于容器化)

### 快速搭建

```bash
# 克隆
git clone https://github.com/kdeerfish/ledger.git
cd ledger
git checkout rewrite/go

# 拉依赖
go mod download

# 编译 + 测试
make build
make test

# 跑起来
./bin/ledger serve --port 5800

# 访问 http://localhost:5800
```

### 开发模式(前后端热更新)

```bash
# 终端 1:Go 后端(默认 :5800,带 SPA)
./bin/ledger serve --port 5800

# 终端 2:Vite 前端 HMR
cd frontend && npm install && npm run dev  # :5173, 代理 /api → 5800

# 访问 http://localhost:5173
```

### 项目结构

```
ledger/
├── cmd/ledger/                 # Go 入口
├── internal/
│   ├── config/                 # viper 配置
│   ├── logger/                 # slog
│   ├── db/                     # modernc/sqlite + 迁移
│   ├── domain/                 # 数据模型
│   ├── repo/                   # 数据访问层
│   ├── service/                # 业务层
│   ├── httpapi/                # chi HTTP 路由
│   ├── cli/                    # cobra CLI
│   ├── webui/                  # embed.FS 前端
│   └── version/                # ldflags 注入
├── frontend/                   # React + Vite
├── skills/ledger/              # AI Agent 技能包
├── website/                    # Docusaurus 文档站
├── .github/workflows/          # CI / Release
├── Dockerfile                  # 多阶段构建
├── docker-compose.yml
├── Makefile
├── go.mod / go.sum
├── .goreleaser.yml
└── README.md
```

### 常用命令

| 命令 | 说明 |
|------|------|
| `make build` | 编译单二进制 (`bin/ledger`) |
| `make test` | 跑所有测试 |
| `make test-race` | `-race` 检测器 |
| `make coverage` | 覆盖率报告 |
| `make fmt` | `gofmt -s -w .` |
| `make vet` | `go vet ./...` |
| `make lint` | golangci-lint(需安装) |
| `make clean` | 清理产物 |
| `make docker` | 构建容器镜像 |
| `make snapshot` | goreleaser snapshot |

---

## 🏗 技术栈

| 层 | 选型 | 理由 |
|----|------|------|
| CLI | spf13/cobra | Go CLI 事实标准 |
| Web | net/http + chi | 轻量、中间件丰富 |
| 数据库 | modernc.org/sqlite | 纯 Go,无 CGO,跨平台编译 |
| 配置 | spf13/viper | .env / 环境变量 / 默认值 |
| 日志 | log/slog | 标准库 |
| 测试 | stretchr/testify | 行业标准 |
| 静态资源 | embed.FS | 单二进制部署 |
| CI | GitHub Actions | 多 OS 矩阵测试 + 多架构构建 |
| 发布 | GoReleaser | 自动生成 SBOM / checksums / 多仓库 Docker 推送 |

---

## 📦 版本

- **rewrite/go**:v0.2.0-dev(开发中,Go 重写版本)
- **master**:v0.1.0(稳定,Python 旧版)

---

## 📜 License

[MIT](LICENSE)
