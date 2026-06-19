---
sidebar_position: 1
---

# 📒 Ledger 文档站 (Go 版)

**Ledger** 是一个个人记账系统,Go 重写版本。支持 CLI 命令行、React Web 界面、AI Agent 集成,可通过 Docker 一键部署。

**当前版本:v0.2.0** (rewrite/go 分支,2026 年发布)

## 🎯 选 Go 版的理由

| 维度 | Python 版 (v0.1.0) | Go 版 (v0.2.0) |
|------|---------------------|-----------------|
| 镜像体积 | ~110 MB | **~20 MB** |
| 启动时间 | ~600 ms | **<50 ms** |
| 运行时依赖 | Python 3.10+ + Flask | **零依赖**(单二进制) |
| API 兼容性 | — | **100% 兼容 Python 版响应结构** |
| 数据迁移 | — | 独立新库(详见 [升级路径](./quickstart#从-python-版升级)) |

## 🚀 一分钟上手

```bash
docker pull zouzhenglu/ledger-go
docker run -d --name ledger -p 5800:5800 -v $(pwd)/data:/data zouzhenglu/ledger-go
open http://localhost:5800
```

详细说明见 [快速开始](./quickstart)。

## 📚 文档导航

- [快速开始](./quickstart) — 安装与运行
- [Docker 部署](./docker) — 生产环境部署
- [Web 界面](./web) — 浏览器使用手册
- [CLI 命令](./cli/index) — 命令行手册
- [HTTP API](./api) — 开发者 API
- [AI Agent 集成](./cli/ai-agent) — LLM Agent 技能包
- [开发指南](./development) — 本地开发与构建

## 🏗 技术栈

- **后端**: Go 1.23 + chi (HTTP) + cobra (CLI) + modernc.org/sqlite (纯 Go 无 CGO)
- **前端**: React 19 + Vite 8 + Bootstrap 5 + Chart.js
- **打包**: embed.FS (前端内嵌到二进制)
- **CI/CD**: GitHub Actions + GoReleaser

## 📦 版本与仓库

| 仓库 | 命名空间 | 内容 |
|------|----------|------|
| Docker Hub | `zouzhenglu/ledger` | **Python 版 (v0.1.0,停止更新)** |
| Docker Hub | `zouzhenglu/ledger-go` | **Go 版 (v0.2.0+,活跃维护)** |
| GitHub | `kdeerfish/ledger` (master) | Python 源码 |
| GitHub | `kdeerfish/ledger` (rewrite/go) | Go 源码 |
