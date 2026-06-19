# 🚀 快速上手 (USAGE.md)

回答你最初的问题: **"我应该怎么用?"**

---

## 📦 你现在有什么

工作目录 `E:\sync\agentscode\ledgerGO` 在分支 **`rewrite/go`**,6 个 Go 重写 commit + 1 个 e2e commit:

```
ee93380 test(e2e): 6 HTTP-level e2e tests
c651a4b feat(go): Docker, CI/CD, Agent skill, README, CHANGELOG
d3b7068 feat(go): frontend embed + unit tests (42 cases all green)
a107727 feat(go): CLI (cobra) + Web API (chi) + httpapi server
2e0689b feat(go): scaffold + infra + domain + repo + service layers
34ff1ed chore(rewrite/go): remove Python source, CI, docs config
```

`master` 分支(原 Python 版)原封未动,随时可切回去。

---

## 🛠 本地怎么跑(Windows / 你现在的环境)

### 1. 确认工具链

```powershell
# Go 1.23+ (我已装好在 C:\Users\kezhe\go\bin)
& "$env:USERPROFILE\go\bin\go.exe" version
# 输出: go version go1.23.4 windows/amd64

# PATH 加好(一次性)
[Environment]::SetEnvironmentVariable("Path", "C:\Users\kezhe\go\bin;$env:Path", "User")
# 下次新开 PowerShell 就直接能用 go
```

### 2. 切到分支 + 编译

```powershell
cd E:\sync\agentscode\ledgerGO
git checkout rewrite/go

# 编译(纯 Go,无 CGO 依赖,秒级)
go build -o bin\ledger.exe .\cmd\ledger
# 输出: bin\ledger.exe (15 MB)
```

### 3. 跑 CLI

```powershell
# 基础
.\bin\ledger.exe version
.\bin\ledger.exe --help

# 记一笔
.\bin\ledger.exe tx add --type 支出 --amount 30 --category 食品 --account 微信 --note 午餐

# 列出
.\bin\ledger.exe tx list
.\bin\ledger.exe tx list --limit 5 --include-deleted

# 更新
.\bin\ledger.exe tx update --id 1 --field amount --value 35

# 软删 / 恢复 / 硬删
.\bin\ledger.exe tx delete --id 1
.\bin\ledger.exe tx restore --id 1
.\bin\ledger.exe tx hard-delete --id 1 --confirm

# 搜索 / 过滤
.\bin\ledger.exe misc search --keyword 午餐
.\bin\ledger.exe misc filter --category 食品 --start-date 2026-01-01

# 统计
.\bin\ledger.exe misc summary --year 2026 --month 6
.\bin\ledger.exe misc stats --group-by category
.\bin\ledger.exe misc analyze

# 预算
.\bin\ledger.exe budget set --category 食品 --amount 1000 --year 2026 --month 6
.\bin\ledger.exe budget check --year 2026 --month 6

# 模板
.\bin\ledger.exe template create --name 早餐 --type 支出 --amount 8 --category 食品
.\bin\ledger.exe template apply --id 1

# 标签
.\bin\ledger.exe tag list
.\bin\ledger.exe tag create --name 日常 --color "#3b82f6"

# 导入 / 导出
.\bin\ledger.exe misc import --file data\sample\mymoney_data_20260614203414.csv
.\bin\ledger.exe misc export --output data\export.csv --format csv
.\bin\ledger.exe misc export --output data\export.json --format json
```

### 4. 跑 Web

```powershell
# 启动
$env:LEDGER_DB_PATH = "E:\sync\agentscode\ledgerGO\data\ledger.db"
.\bin\ledger.exe serve --port 5800
# → 打开 http://localhost:5800
```

**Web 页面**:
- `/` 概览(收支卡片 + 柱状图 + 折线图 + 环形图)
- `/transactions` 交易列表
- `/add` 记一笔
- `/budgets` 预算
- `/categories` 类别+标签
- `/stats` 统计

### 5. 跑测试

```powershell
# 单元测试 (42 个)
go test -count=1 .\internal\...

# E2E (6 个 HTTP 全链路)
go test -tags=e2e -count=1 .\e2e\...

# 全部 + vet
go test -count=1 .\...; go vet .\...

# 覆盖率
go test -coverprofile=coverage.out -covermode=atomic .\...
go tool cover -func=coverage.out
```

---

## 🌐 HTTP API(给脚本 / 其他语言用)

```bash
# 健康检查
curl http://localhost:5800/api/health

# 列出最近 5 笔
curl 'http://localhost:5800/api/transactions?limit=5'

# 新增交易(JSON)
curl -X POST http://localhost:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"支出","amount":25.5,"category":"食品","account":"微信"}'

# 6 月汇总
curl 'http://localhost:5800/api/summary?year=2026&month=6'

# 按类别统计
curl 'http://localhost:5800/api/stats?group_by=category'

# 预算检查
curl 'http://localhost:5800/api/budgets/check?year=2026&month=6'

# 导出
curl 'http://localhost:5800/api/export?format=csv' -o data.csv
```

完整 API 列表见 [`website/docs/api.md`](website/docs/api.md)。

---

## 🐳 推到远端 + Docker 发布(下一步)

### 1. 推分支到 GitHub

```bash
# 添加远程(已有则跳过)
git remote add github https://github.com/kdeerfish/ledger.git

# 推 rewrite/go(只推这个分支,master 不动)
git push -u github rewrite/go
```

### 2. 触发 Docker 多仓库发布

```bash
# 打 tag(打 v* 前缀会触发 release.yml)
git checkout rewrite/go
git tag v0.2.0
git push github v0.2.0
```

GitHub Actions 自动跑(`.github/workflows/release.yml`):
- GoReleaser 跨平台构建 (5 OS/arch)
- Docker 多架构镜像 → `zouzhenglu/ledger-go` (Docker Hub) + `ghcr.io/kdeerfish/ledger-go` + 阿里云同名
- 创建 GitHub Release

### 3. 用户怎么用 Go 版

```bash
# 拉镜像(独立仓库,与 Python 版不冲突)
docker pull zouzhenglu/ledger-go:latest

# 启动
docker run -d -p 5800:5800 -v $(pwd)/data:/data --name ledger zouzhenglu/ledger-go:latest
```

### 4. 与 Python 版并存(过渡期)

Python 版 Docker 在 `zouzhenglu/ledger`,Go 版在 `zouzhenglu/ledger-go`,**两个完全独立,可以同时跑**:

```bash
# Python 版跑在 :5800 (旧数据)
docker run -d -p 5800:5800 -v $(pwd)/data-py:/data --name ledger-py zouzhenglu/ledger

# Go 版跑在 :5801 (新数据)
docker run -d -p 5801:5800 -v $(pwd)/data-go:/data --name ledger-go zouzhenglu/ledger-go
```

---

## 🤖 让 AI Agent 用(可选)

`skills/ledger/SKILL.md` 是给 LLM 看的技能说明。安装到 IDE:

```bash
# Claude Code
mkdir -p .claude/skills
cp -r skills/ledger .claude/skills/

# Cursor
mkdir -p .cursor/skills
cp -r skills/ledger .cursor/skills/
```

Agent 启动后读 SKILL.md,自动知道所有 CLI/HTTP 能力,你可以自然语言让它记账。

---

## ❓ 常见问题

**Q: Go 版能读 Python 版的 `ledger.db` 吗?**
A: **不能**,Go 版走独立数据库路径(`data/ledger-go.db` 默认)。Schema 兼容(v2),但本期不实现读取。需要迁移用 `misc export` → `misc import` 走 CSV 中转。

**Q: Python 版还能用吗?**
A: **能**。`master` 分支原封未动,切回去 `git checkout master` 即可。

**Q: 二进制多大?需要什么依赖?**
A: 15 MB,**零运行时依赖**(纯 Go 静态编译)。不需要 Python、不需要 Node、不需要 CGO。

**Q: 为什么不用 go-chi/gin/echo?**
A: 我选了 chi,因为它轻量、中间件生态完整、跟 net/http 标准库兼容最好。

**Q: 前端为什么用 embed.FS?**
A: 单二进制部署,不用挂载 frontend/dist 目录,容器镜像从 110 MB 缩到 20 MB。

**Q: 我 Windows 跑过 `go test -race` 失败**
A: 正常,`-race` 需要 CGO(Windows 上是 MinGW)。我已经把所有 race-friendly 测试跑过(用 `-count=1`),CI 上 Linux runner 会跑 `-race`。

**Q: 我想改点东西再发布**
A:
1. `git checkout rewrite/go`
2. 改代码
3. `make test` 跑过
4. `git add -A && git commit -m "feat: ..."`
5. `git tag v0.2.1 && git push github v0.2.1`

---

## 📂 关键文档

| 文档 | 用途 |
|------|------|
| [README.md](README.md) | 项目主入口(Go 版) |
| [CHANGELOG.md](CHANGELOG.md) | 版本变更日志 |
| [website/docs/intro.md](website/docs/intro.md) | 文档站首页 |
| [website/docs/quickstart.md](website/docs/quickstart.md) | 快速开始 |
| [website/docs/api.md](website/docs/api.md) | HTTP API 完整参考 |
| [website/docs/docker.md](website/docs/docker.md) | Docker 部署 |
| [website/docs/development.md](website/docs/development.md) | 开发指南 |
| [skills/ledger/SKILL.md](skills/ledger/SKILL.md) | AI Agent 技能说明 |
| [.goreleaser.yml](.goreleaser.yml) | 发布配置 |
| [.github/workflows/](.github/workflows/) | CI / CD |

---

## 🆘 遇到问题?

1. **Go 命令找不到** → `& "$env:USERPROFILE\go\bin\go.exe" version` 确认
2. **依赖下载超时** → 确认 `GOPROXY=https://goproxy.io,direct` 已设
3. **编译错误** → `go mod tidy` 重置依赖
4. **数据库锁定** → 关闭其他 ledger 进程
5. **端口被占** → 用 `--port 5801` 换端口

直接问我也行(把错误信息贴过来)。
