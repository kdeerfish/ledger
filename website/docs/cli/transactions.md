---
sidebar_position: 5
---

# 📊 交易管理 (CLI)

`ledger tx` 子命令组提供完整的交易 CRUD 操作。

## 添加交易

```bash
ledger tx add \
  --type 支出|收入 \
  --amount 100 \
  --category 食品 \
  --subcategory 零食 \
  --account 微信 \
  --project 日常 \
  --member 本人 \
  --merchant 711 \
  --note "晚上加餐" \
  --date "2026-06-19 12:00:00" \
  --tag 日常 --tag 工作日 \
  --force
```

| Flag | 简写 | 必填 | 说明 |
|------|------|------|------|
| `--type` | `-t` | ✅ | `支出` 或 `收入` |
| `--amount` | `-a` | ✅ | 金额 (正数) |
| `--category` | `-c` | | 类别 |
| `--subcategory` | | | 子类别 |
| `--account` | `-A` | | 账户 |
| `--project` | `-p` | | 项目 |
| `--member` | `-m` | | 成员 |
| `--merchant` | | | 商家 |
| `--note` | `-n` | | 备注 |
| `--date` | `-d` | | `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`(默认 = now) |
| `--tag` | | | 标签(可多次) |
| `--force` | | | 强制添加,跳过重复检测 |

## 列出交易

```bash
ledger tx list --limit 20 --include-deleted
```

| Flag | 简写 | 默认 | 说明 |
|------|------|------|------|
| `--limit` | `-l` | 20 | 限制条数 |
| `--include-deleted` | | false | 包含已软删记录 |

## 查询单条

```bash
ledger tx get --id 1
```

## 更新单字段

白名单字段: `amount / category / subcategory / account / project / member / merchant / note / trans_date / type`

```bash
ledger tx update --id 1 --field amount --value 150
```

## 软删除

```bash
ledger tx delete --id 1
```

## 恢复软删

```bash
ledger tx restore --id 1
```

## 永久删除(危险)

```bash
ledger tx hard-delete --id 1 --confirm
```

## 重复检测

默认会拒绝同日/同金额/同类型/同类别的重复交易。绕过用 `--force`。

## 软删行为

所有查询/统计默认 `is_deleted = 0`,软删记录隐藏。如需查看传 `--include-deleted`(CLI)或 `include_deleted=true`(HTTP)。
