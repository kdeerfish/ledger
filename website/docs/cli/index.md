---
sidebar_position: 4
---

# 📘 CLI 命令参考 (Go 版)

`ledger` 是 Go 版的统一命令行入口,所有业务逻辑通过 cobra 子命令暴露。

```bash
ledger <command> [flags...]
```

:::tip 查看帮助
```bash
ledger --help                # 所有顶层命令
ledger tx --help             # tx 子命令组的所有子命令
ledger tx add --help         # 特定命令的所有 flag
```
:::

## 命令分组

| 分组 | 用途 | 子命令 |
|------|------|--------|
| [`tx`](./transactions) | 交易 CRUD | add, list, get, update, delete, restore, hard-delete |
| [`budget`](./budgets) | 预算管理 | set, list, check, template-create/list/update/delete/apply/suggest |
| [`template`](./templates) | 记账模板 | create, list, update, delete, apply, suggest |
| `tag` | 标签 CRUD | list, create, delete |
| [`misc`](./search) | 查询/统计/导入导出 | search, filter, summary, stats, import, export, analyze, reconcile, accounts, categories, members |
| `serve` | 启动 Web 服务 | `--host`, `--port`, `--debug` |
| `version` | 打印版本 | — |
| `init` | 初始化数据库(自动) | — |

## 输出格式

所有 CLI 输出是中文 + emoji 风格,与 Python 版一致:

```
✅ 已添加交易 #1 (¥25.50)
❌ 添加失败: amount must be > 0
```

需要 JSON 输出时,使用 HTTP API (`curl http://localhost:5800/api/...`)。

## 全局环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `LEDGER_DB_PATH` | `data/ledger.db` | SQLite 文件路径 |
| `WEB_PORT` | `5800` | `serve` 命令的默认端口 |
| `LOG_LEVEL` | `info` | debug / info / warn / error |
| `LOG_FORMAT` | `json` (生产) / `text` (开发) | 日志格式 |

## 子页面

- [交易 (tx)](./transactions)
- [预算 (budget)](./budgets)
- [记账模板 (template)](./templates)
- [搜索 / 过滤 / 统计 (misc)](./search)
- [数据导入导出 (misc import/export)](./import-export)
- [数据库相关 (misc summary/analyze)](./database)
- [统计 (misc stats)](./statistics)
- [AI Agent 集成 (SKILL.md)](./ai-agent)
