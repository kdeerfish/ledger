---
sidebar_position: 9
---

# 📋 记录模板(一键记账) (CLI)

`ledger template` 子命令组管理"记账模板",应用后自动按模板参数生成交易。

## 创建模板

```bash
ledger template create \
  --name "早餐" \
  --type-mode 支出 \
  --type 支出 \
  --amount 8 \
  --category 食品 \
  --subcategory 早餐 \
  --account 微信 \
  --tag 日常
```

| Flag | 必填 | 默认 | 说明 |
|------|------|------|------|
| `--name` | ✅ | | 模板名 |
| `--type-mode` | | `通用` | 模板类型: 通用 / 支出 / 收入 |
| `--type` | | | 交易类型(支出/收入) |
| `--amount` | | 0 | 金额 |
| `--category` | | | 类别 |
| `--subcategory` | | | 子类别 |
| `--account` | | | 账户 |
| `--project` | | | 项目 |
| `--member` | | | 成员 |
| `--merchant` | | | 商家 |
| `--note` | | | 备注 |
| `--tag` | | | 标签(可多次) |

## 列出模板

```bash
ledger template list
ledger template list --type-mode 支出
```

## 更新模板

```bash
ledger template update --id 1 --set amount=10 --set category=餐饮
```

`--set` 接受 `key=value` 形式,可多次。

## 删除模板

```bash
ledger template delete --id 1
```

## 应用模板(生成一笔交易)

```bash
# 用模板默认金额
ledger template apply --id 1

# 覆盖金额(比如今天买贵了)
ledger template apply --id 1 --amount 12
```

应用后:
1. 生成一笔交易(自动跳过重复检测,因为是模板应用)
2. 模板的 `usage_count` +1,`last_used_at` 更新

## 智能推荐(按使用频次)

```bash
ledger template suggest --limit 3
# 早餐 (使用 25 次)
# 午餐 (使用 18 次)
# 通勤 (使用 12 次)
```
