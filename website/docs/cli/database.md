---
sidebar_position: 12
---

# 🛠 数据库 (CLI)

## 初始化

数据库会在首次启动时自动初始化(任何 CLI 命令触发),无需手动调用。提供 `init` 命令仅作显式触发:

```bash
ledger init
# → ✅ 数据库已就绪: data/ledger.db
```

## 存储位置

- 默认: `./data/ledger.db`
- 可通过 `LEDGER_DB_PATH` 环境变量覆盖
- 父目录不存在时自动创建

## Schema 版本

| 版本 | 内容 |
|------|------|
| v1 | 7 张表(transactions / budgets / budget_templates / record_templates / tags / transaction_tags / meta) |
| v2 | 新增 `transactions.is_deleted` 列 + 3 个索引 + `record_templates.tags` 列 |

`meta` 表记录当前版本,启动时自动迁移(`internal/db/migrations.go`)。

## 直接查询(高级)

```bash
# 装 sqlite3 CLI
sqlite3 data/ledger.db

sqlite> .tables
sqlite> .schema transactions
sqlite> SELECT id, type, amount, category FROM transactions WHERE is_deleted = 0 ORDER BY trans_date DESC LIMIT 5;
```

## 备份 / 还原

```bash
# 备份(关闭 ledger 进程后)
sqlite3 data/ledger.db ".backup 'backup-2026-06-19.db'"

# 或直接复制
cp data/ledger.db backup/

# 还原
cp backup/ledger-2026-06-19.db data/ledger.db
```

## 维护

```bash
# WAL checkpoint(减小 WAL 文件)
sqlite3 data/ledger.db "PRAGMA wal_checkpoint(TRUNCATE);"

# 重新整理(重建索引)
sqlite3 data/ledger.db "REINDEX;"
```

## 跨版本兼容

Go 版 schema 与 Python 版 v2 兼容 — 表结构、字段、约束完全一致。
但 **Go 版从空库开始**(默认路径 `data/ledger-go.db`),**不读取 Python 版的 `data/ledger.db`**。
如需迁移,用 `misc export` 导出 Python 库为 CSV,再用 `misc import` 导入 Go 库。
