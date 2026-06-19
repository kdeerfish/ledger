# 📦 发布指南

Ledger Go 版支持**本地手动发布**和 **GitHub Actions 自动发布**两种方式。

---

## 方式 1: GitHub Actions 自动发布 (推荐)

### 流程

```
git tag v0.2.0
git push origin v0.2.0
  ↓ 自动触发 .github/workflows/release.yml
  ↓ GoReleaser: 跨平台构建 (5 OS/arch)
  ↓ Docker 多架构镜像 → Docker Hub / ghcr.io / 阿里云
  ↓ 创建 GitHub Release
```

### 前置条件

1. GitHub 仓库 Settings → Secrets 设置:
   - `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`: Docker Hub 凭据
   - `ALIYUN_USERNAME` / `ALIYUN_TOKEN`: 阿里云镜像服务凭据
   - `GITHUB_TOKEN`: 自动提供,无需手动配置

2. 确保 `.goreleaser.yml` 里的镜像名正确:
   ```yaml
   images:
     - docker.io/zouzhenglu/ledger-go
     - ghcr.io/kdeerfish/ledger-go
     - crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger-go
   ```

### 执行

```bash
# 1. 确保所有测试通过
make check

# 2. 更新 CHANGELOG.md
vim CHANGELOG.md

# 3. 提交
git add -A && git commit -m "chore: prepare v0.2.0 release"

# 4. 打 tag 并推送
git tag v0.2.0
git push origin rewrite/go
git push origin v0.2.0

# 5. 等待 GitHub Actions 完成 (约 5-10 分钟)
#    https://github.com/kdeerfish/ledger/actions
```

---

## 方式 2: 本地手动发布

### 前置条件

```bash
# Go 1.23+
go version

# GoReleaser (可选,只在本地打包时需要)
go install github.com/goreleaser/goreleaser@latest
```

### 本地 snapshot (dry-run,不推远端)

```bash
# 用 VSCode Task: 📦 Release: Snapshot (local)
# 或命令行:
make snapshot
```

产物在 `dist/` 目录,可本地测试二进制:

```bash
dist/ledger_windows_amd64_v1/ledger.exe version
dist/ledger_linux_amd64_v1/ledger version
```

### 本地打包二进制 (不通过 GoReleaser)

```bash
# Windows
go build -trimpath -ldflags "-s -w -X github.com/kdeerfish/ledger/internal/version.Version=v0.2.0" -o bin/ledger.exe ./cmd/ledger

# Linux
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags "-s -w" -o bin/ledger-linux-amd64 ./cmd/ledger

# macOS
GOOS=darwin GOARCH=arm64 CGO_ENABLED=0 go build -trimpath -ldflags "-s -w" -o bin/ledger-darwin-arm64 ./cmd/ledger
```

### Docker 本地构建

```bash
# 用 VSCode Task: 🐳 Docker: Build
# 或命令行:
make docker

# 测试
docker run --rm -p 5800:5800 -v $(pwd)/data:/data ledger:dev
```

---

## 发布清单

发布前检查:

- [ ] `make check` 全绿 (fmt + vet + test)
- [ ] `make test-all` 全绿 (unit + integration + e2e)
- [ ] CHANGELOG.md 已更新
- [ ] README.md 版本号正确
- [ ] `internal/version/version.go` 的 Version 已更新 (或留 `0.2.0-dev`,打 tag 时 GoReleaser 注入)
- [ ] `.goreleaser.yml` 镜像名正确
- [ ] `.github/workflows/release.yml` 触发条件正确 (`tags: v*`)

---

## 版本号规则

遵循 [Semantic Versioning](https://semver.org/):

- `v0.x.y` — 开发阶段 (Go 版)
- `v1.0.0` — 首个稳定版 (功能完整,API 稳定)
- `v1.x.y` — 向后兼容的功能新增
- `v2.0.0` — 重大变更 (破坏性 API 变更)

---

## 与 Python 版的关系

| 维度 | Python 版 | Go 版 |
|------|-----------|-------|
| 分支 | `master` | `rewrite/go` |
| 版本 | `v0.1.0` (停止更新) | `v0.2.0+` (活跃) |
| Docker | `zouzhenglu/ledger` | `zouzhenglu/ledger-go` |
| GitHub Release | 在 master 上 | 在 rewrite/go 上 |

两个版本**完全独立**,可以同时存在,用户按需选择。
