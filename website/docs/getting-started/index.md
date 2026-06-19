---
sidebar_position: 1
---

# 🚀 快速开始

选择最符合你环境的安装方式，每种方式都给了 **完整的步骤 + 数据持久化方案**。

## 🧭 选一个适合你的方式

| 你的情况 | 推荐方式 | 文档 |
|----------|---------|------|
| **Windows 用户**，Docker 装在 WSL2 里 | Docker on WSL | 👉 [docker-wsl.md](./docker-wsl.md) |
| Docker 装在 **群晖 / 飞牛OS / unRAID** 等 NAS | Docker on NAS | 👉 [docker-nas.md](./docker-nas.md) |
| **Linux 服务器** / 不想用 Docker | 源码运行 | 👉 [source-code.md](./source-code.md) |
| 只想快速体验 | 上面任选一种，30 秒跑起来即可 | 👉 看本页底部 |

:::tip 不确定选哪个？
**99% 的个人用户选 Docker on WSL 或 Docker on NAS**。Docker 一行命令搞定，自带健康检查、自动重启、数据持久化，几乎零维护。
:::

---

## ⏱️ 三种方式对比

| | Docker（WSL/NAS） | 源码运行 |
|---|---|---|
| 安装难度 | ⭐ 极简 | ⭐⭐⭐ 中等 |
| 一键启动 | ✅ | ❌（需自己配 Python/Node） |
| 数据持久化 | 自动（卷挂载） | 手动 |
| 自动重启 | ✅ `--restart unless-stopped` | ❌ |
| 升级 | `docker pull` 一行命令 | `git pull` + 重新安装 |
| 适合谁 | 个人日常使用 | 开发者 / 想二次定制 |

---

## 🏃 想 30 秒先跑起来？

不管什么平台，先复制这一行（**默认假设 Docker 已装好**）：

```bash
docker run -d --name ledger -p 5800:5800 -v $(pwd)/data:/data --restart unless-stopped zouzhenglu/ledger:latest
```

- ✅ 启动成功：浏览器打开 **http://localhost:5800**
- ❌ 启动失败 / 想搞明白每一步：去上面表格里选你的环境，对应文档会讲清楚细节。

---

## 📂 安装后你会在哪里看到数据？

| 部署方式 | 数据库位置 |
|----------|----------|
| Docker（WSL/NAS） | 你挂载的卷，默认 `./data/ledger.db`（容器内 `/data/ledger.db`） |
| 源码运行 | 项目根目录的 `./ledger.db`，或 `.env` 里的 `LEDGER_DB_PATH` |

备份 = 复制这个文件。详见 [FAQ · 数据管理](../faq/data.md)。

---

## 🤔 下一步看什么？

- 不知道怎么用 Web 界面？ 👉 [Web 界面使用手册](../user-guide/web-ui.md)
- 喜欢命令行？ 👉 [CLI 命令参考](../user-guide/cli.md)
- 想让 AI 自动记账？ 👉 [AI Agent 集成](../ai-agent/index.md)
- 出问题了？ 👉 [FAQ · 故障排除](../faq/troubleshooting.md)