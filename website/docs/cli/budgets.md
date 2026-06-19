---
sidebar_position: 8
---

# 💰 预算管理 (CLI)

`ledger budget` 子命令组管理预算与预算模板。

## 设置预算

```bash
ledger budget set \
  --category 食品 \
  --amount 1000 \
  --year 2026 \
  --month 6 \
  --dimension-type category
```

| Flag | 简写 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--category` | `-c` | ✅ | | 类别名 |
| `--amount` | `-a` | ✅ | | 金额 (正数) |
| `--year` | `-y` | | 今年 | 年份 |
| `--month` | `-M` | | 本月 | 月份 |
| `--dimension-type` | | | `category` | category / account / member / project / merchant |
| `--dimension-value` | | | | 维度对应的值 |

**upsert 行为**: 同一 (year, month, category, dimension_type, dimension_value) 第二次 set 会更新金额。

## 列出预算

```bash
ledger budget list --year 2026 --month 6
```

## 检查预算执行

```bash
ledger budget check --year 2026 --month 6
```

输出示例:
```
食品           预算 ¥1000.00  已花 ¥145.50  剩余 ¥854.50  进度 14.6%
交通           预算 ¥300.00   已花 ¥80.00   剩余 ¥220.00   进度 26.7%
```

> **注意**: `spent` 只统计 `type='支出'` 的交易。收入不影响预算。

## 预算模板

### 创建

```bash
ledger budget template-create \
  --name "月度餐饮" \
  --category 食品 \
  --amount 1500 \
  --description "每月餐饮预算"
```

### 列出 / 更新 / 删除

```bash
ledger budget template-list
ledger budget template-update --id 1 --set amount=2000
ledger budget template-delete --id 1
```

### 应用模板(生成一笔预算)

```bash
ledger budget template-apply --id 1
# → 已应用模板: 食品 ¥1500.00
```

### 智能推荐

```bash
ledger budget template-suggest --limit 3
```
