---
sidebar_position: 5
---

# 📊 交易管理

`scripts/cli.py` 支持完整的交易 CRUD 操作。

## 添加交易

```bash
python scripts/cli.py add \
  --type 支出|收入 \
  --amount 100 \
  --category 食品 \
  --subcategory 零食 \      # 可选
  --account 微信 \           # 可选
  --project 日常 \
  --member 本人 \
  --merchant 711 \
  --note "零食" \
  --date "2026-06-15" \     # 可选，默认当前时间
  --confirm                  # 跳过重复检查
```

## 列出交易

```bash
python scripts/cli.py list                   # 最近 20 条
python scripts/cli.py list --limit 50        # 最近 50 条
python scripts/cli.py list --include_deleted # 含已删除
```

## 修改交易

```bash
python scripts/cli.py update --id 1 --field amount --value 50
python scripts/cli.py update --id 1 --field category --value 交通
python scripts/cli.py update --id 1 --field note --value "地铁充值"
```

支持修改的字段：`amount` `category` `subcategory` `account` `project` `member` `merchant` `note` `trans_date`

## 删除与恢复

```bash
python scripts/cli.py delete --id 1                   # 软删除（可恢复）
python scripts/cli.py restore --id 1                  # 恢复
python scripts/cli.py hard_delete --id 1 --confirm    # 物理删除（不可恢复）
```

:::warning 硬删除不可恢复
硬删除会从数据库中彻底清除记录，操作前请确认。
:::
