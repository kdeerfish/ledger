---
sidebar_position: 15
---

# 🛠 开发指南 (Go 版)

## 环境要求

- **Go 1.23+** ([下载](https://go.dev/dl/))
- **Node.js 20+**(仅前端开发时需要)
- **Git**
- **Docker**(可选,用于容器化部署与 e2e 测试)
- **GCC / MinGW**(可选,只在使用 `go test -race` 时需要)

## 搭建开发环境

```bash
# 克隆项目
git clone https://github.com/kdeerfish/ledger.git
cd ledger
git checkout rewrite/go  # Go 版代码

# 拉 Go 依赖
go mod download

# 安装前端依赖(仅改前端时需要)
cd frontend && npm install && cd ..

# 编译
make build    # 输出 bin/ledger (或 bin/ledger.exe on Windows)

# 跑测试
make test     # 42 个单元测试
make test -tags=e2e  # + 6 个 e2e 测试

# 跑起来
./bin/ledger serve --port 5800
```

## 项目结构

```
ledger/
├── cmd/ledger/             # Go 入口
│   └── main.go
├── internal/
│   ├── config/             # viper 配置加载
│   ├── logger/             # slog 封装
│   ├── db/                 # modernc/sqlite + 迁移
│   ├── domain/             # 纯数据模型 + sentinel errors
│   ├── repo/               # 数据访问层 (纯 SQL)
│   ├── service/            # 业务层 (35+ 方法 1:1 复刻 Python)
│   ├── httpapi/            # chi HTTP 路由
│   ├── cli/                # cobra CLI 命令树
│   ├── webui/              # embed.FS 前端
│   ├── version/            # ldflags 注入
│   └── testutil/           # 测试 fixture
├── e2e/                    # e2e 测试 (-tags=e2e)
├── frontend/               # React 19 + Vite 8
├── skills/ledger/          # AI Agent 技能包
├── website/                # Docusaurus 文档站
├── .github/workflows/      # CI + Release
├── Dockerfile              # 多阶段构建
├── docker-compose.yml
├── .goreleaser.yml         # GoReleaser 配置
├── Makefile
├── go.mod / go.sum
├── .golangci.yml           # golangci-lint 配置
└── README.md
```

## 4 层架构

```
httpapi/cli        ← 输入层:HTTP 请求 / CLI 参数
     ↓
service            ← 业务层:验证、去重、关联、衍生计算
     ↓
repo               ← 数据层:纯 SQL,无业务
     ↓
db / domain        ← 基础设施:连接池、schema、迁移
```

**规则**:
- `service` 不 import `httpapi/cli`(避免循环)
- `repo` 只用 `domain` 类型 + `db.DB` 接口
- `domain` 不 import 任何业务包(纯结构体)

## 常用命令

| 命令 | 说明 |
|------|------|
| `make build` | 编译单二进制 (`bin/ledger`) |
| `make test` | 跑所有单元测试 |
| `make test-race` | `-race` 检测器(需要 CGO/GCC) |
| `make coverage` | 覆盖率报告 |
| `make fmt` | `gofmt -s -w .` |
| `make vet` | `go vet ./...` |
| `make lint` | golangci-lint(需先 `go install`) |
| `make check` | fmt + vet + test 一把梭 |
| `make clean` | 清理产物 |
| `make docker` | 构建容器镜像 |
| `make snapshot` | goreleaser snapshot(本地测试发布) |

## 开发模式(前后端热更新)

```bash
# 终端 1:Go 后端 + 静态 SPA(已嵌入二进制)
./bin/ledger serve --port 5800

# 终端 2:Vite 前端 HMR(改了 React 代码立刻生效)
cd frontend && npm run dev
# 访问 http://localhost:5173 (Vite dev server)
# /api 请求通过 vite.config.js 代理到 :5800
```

## 添加新功能的标准流程

1. **domain**: 在 `internal/domain/` 加结构体 / sentinel error
2. **repo**: 在 `internal/repo/` 加 `xxx_repo.go`,提供 `Create/Get/List/Update/Delete`
3. **service**: 在 `internal/service/` 加 `xxx_service.go`,组合 repo + 业务规则
4. **httpapi**: 在 `internal/httpapi/server.go` 加路由
5. **cli**: 在 `internal/cli/` 加 cobra 子命令
6. **测试**: 在 `internal/<layer>/xxx_test.go` 加单元测试,e2e 必要时加

## 数据库迁移

Schema 版本由 `internal/db/db.go` 的 `CurrentVersion` 常量控制。

加新迁移:
1. 在 `migrations.go` 加 `applyV2(d)` 等函数(幂等)
2. 在 `Migrate()` 加 `if current < 3 { applyV2(d) }` 分支
3. 把 `CurrentVersion` 改成 3
4. 加测试覆盖新 schema

## 调试技巧

```bash
# 详细日志
./bin/ledger serve --port 5800
LOG_LEVEL=debug LOG_FORMAT=text ./bin/ledger serve

# SQLite 调试
sqlite3 data/ledger.db ".tables"
sqlite3 data/ledger.db "SELECT * FROM transactions LIMIT 5"

# 打印 SQL
LOG_LEVEL=debug ./bin/ledger tx list
```

## 发布新版本

```bash
# 1. 确保所有测试通过
make check

# 2. 提交并推分支
git add -A
git commit -m "feat: ..."
git push origin rewrite/go

# 3. 打 tag(只打 v 前缀的,触发 release.yml)
git tag v0.2.0
git push origin v0.2.0

# 4. GitHub Actions 自动跑:
#    - GoReleaser 跨平台构建 (5 OS/arch)
#    - Docker 多架构镜像推到 zouzhenglu/ledger-go (3 个 registry)
#    - 创建 GitHub Release
```

## CI/CD

- **ci.yml**: 每次 push / PR 跑 `lint + test + build matrix`
- **release.yml**: 打 `v*` tag 触发 GoReleaser + Docker 多仓库推送

## 与 Python 版的关系

| 维度 | Python 版 | Go 版 |
|------|-----------|-------|
| 分支 | `master` | `rewrite/go` |
| 仓库 | `kdeerfish/ledger` (master) | `kdeerfish/ledger` (rewrite/go) |
| Docker | `zouzhenglu/ledger` | `zouzhenglu/ledger-go` |
| 文档站 | https://kdeerfish.github.io/ledger | 同源(子路径) |
| 状态 | 停止更新,仅 bugfix | **活跃开发** |
