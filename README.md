<div align="center">

# 📒 Ledger — 个人记账系统

**收支管理 · 预算规划 · 标签分类 · 多维统计 · React 仪表盘 · AI Agent 集成**

[![Docker Pulls](https://img.shields.io/docker/pulls/zouzhenglu/ledger?logo=docker&label=Docker%20Hub)](https://hub.docker.com/r/zouzhenglu/ledger)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/kdeerfish/ledger/docker-publish.yml?branch=master&label=CI%2FCD&logo=github)](https://github.com/kdeerfish/ledger/actions)
[![License](https://img.shields.io/github/license/kdeerfish/ledger)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)

**🐳 [`docker`](https://hub.docker.com/r/zouzhenglu/ledger) · [📖 完整文档](https://kdeerfish.github.io/ledger)**

</div>

---

## 🚀 30 秒启动

> 已经装了 Docker？一行命令搞定。

```bash
docker run -d --name ledger -p 5800:5800 -v $(pwd)/data:/data --restart unless-stopped zouzhenglu/ledger:latest
```

浏览器打开 **http://localhost:5800** 即可使用。

国内用户把镜像换成 `crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest` 拉取更快。

---

## 📚 文档导航

> 完整文档站：👉 **https://kdeerfish.github.io/ledger**

| 你想干什么？ | 看这里 |
|-------------|--------|
| **第一次安装**，不知道选什么方式 | 👉 [快速开始 — 按你的环境选](https://kdeerfish.github.io/ledger/docs/getting-started/) |
| Docker 跑在 **Windows + WSL** | 👉 [Docker on WSL 指南](https://kdeerfish.github.io/ledger/docs/getting-started/docker-wsl/) |
| Docker 跑在 **NAS / 飞牛OS / 群晖** | 👉 [Docker on NAS 指南](https://kdeerfish.github.io/ledger/docs/getting-started/docker-nas/) |
| 不想用 Docker，**直接跑源码** | 👉 [源码运行指南](https://kdeerfish.github.io/ledger/docs/getting-started/source-code/) |
| 怎么用 **Web 界面** 记账 | 👉 [Web 界面使用手册](https://kdeerfish.github.io/ledger/docs/user-guide/web-ui/) |
| 怎么用 **命令行** 记账 | 👉 [CLI 命令参考](https://kdeerfish.github.io/ledger/docs/user-guide/cli/) |
| 想让 **AI Agent / Hermes** 接管记账 | 👉 [AI Agent 集成指南](https://kdeerfish.github.io/ledger/docs/ai-agent/) |
| 数据库在哪 / 怎么备份 / 怎么迁移 | 👉 [FAQ · 数据管理](https://kdeerfish.github.io/ledger/docs/faq/data/) |
| 出问题了 | 👉 [FAQ · 常见问题](https://kdeerfish.github.io/ledger/docs/faq/troubleshooting/) |

---

## ✨ 主要功能

| 功能 | 说明 |
|------|------|
| ✅ **收支记账** | 添加 / 编辑 / 软删除 / 恢复 / 物理删除 |
| ✅ **标签分类** | 多标签 + 颜色标记 + 多维筛选 |
| ✅ **CSV 导入** | 随手记 CSV 一键导入，自动去重 |
| ✅ **预算管理** | 按月 / 类别 / 账户，多维度预算 + 模板 + 超支预警 |
| ✅ **多维统计** | 9 种分组 × 3 种图表，点击图表跳转筛选 |
| ✅ **记账模板** | 常用交易一键记账，使用频次统计 |
| ✅ **数据导出** | CSV / JSON 一键导出 |
| ✅ **React 仪表盘** | 响应式 UI，手机 / 平板 / PC 均可用 |
| ✅ **AI Agent 集成** | 提供 JSON API + 标准技能包（SKILL.md） |

---

## 🐳 镜像仓库

| 仓库 | 拉取命令 | 适用 |
|------|----------|------|
| **Docker Hub**（主） | `docker pull zouzhenglu/ledger:latest` | 🌍 全球默认 |
| GitHub Container Registry | `docker pull ghcr.io/kdeerfish/ledger:latest` | 🌍 备选 |
| **阿里云** | `docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest` | 🇨🇳 国内最快 |

---

## 🌟 项目信息

| 项目 | 链接 |
|------|------|
| GitHub 仓库 | [kdeerfish/ledger](https://github.com/kdeerfish/ledger) |
| 完整文档站 | [kdeerfish.github.io/ledger](https://kdeerfish.github.io/ledger) |
| 问题反馈 | [Issues](https://github.com/kdeerfish/ledger/issues) |
| Docker Hub | [zouzhenglu/ledger](https://hub.docker.com/r/zouzhenglu/ledger) |
| 许可 | MIT |