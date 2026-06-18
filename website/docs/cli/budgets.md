---
sidebar_position: 8
---

# 💰 预算管理

## 设置预算

```bash
# 按类别设置
python scripts/cli.py budget_set --category 食品 --amount 1000 --year 2026 --month 7

# 按账户维度
python scripts/cli.py budget_set --category 餐饮 --amount 500 --dimension_type account --dimension_value 微信

# 按成员维度
python scripts/cli.py budget_set --category 日常 --amount 2000 --dimension_type member --dimension_value 本人
```

## 检查预算

```bash
python scripts/cli.py budget_check                     # 本月
python scripts/cli.py budget_check --year 2026 --month 7
```

## 预算模板

```bash
# 创建
python scripts/cli.py budget_template_create --template_name "月度餐饮" --category 食品 --template_amount 1500

# 列出
python scripts/cli.py budget_template_list

# 应用
python scripts/cli.py budget_template_apply --template_id 1 --year 2026 --month 8

# 更新 / 删除
python scripts/cli.py budget_template_update --template_id 1 --template_name "新名称"
python scripts/cli.py budget_template_delete --template_id 1

# 智能推荐
python scripts/cli.py budget_template_suggest --template_limit 5
```
