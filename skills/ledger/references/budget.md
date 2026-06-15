# 预算命令

## 设置预算 (budget_set)

```bash
# 设置预算
python3 scripts/ledger_cli.py budget_set '{"category":"食品酒水","amount":1000,"year":2026,"month":6}'

# 按账户维度设置预算
python3 scripts/ledger_cli.py budget_set '{"category":"餐饮","amount":500,"dimension_type":"account","dimension_value":"xxx信用卡","year":2026,"month":6}'
```

参数：
- `category`: 类别 - 必填
- `amount`: 预算金额 - 必填
- `year`: 年份 - 可选，默认当年
- `month`: 月份 - 可选，默认当月
- `dimension_type`: 维度类型 (category/account/member/project/merchant) - 可选
- `dimension_value`: 维度值 - 可选

## 查看预算 (budget_check)

```bash
python3 scripts/ledger_cli.py budget_check '{"year":2026,"month":6}'
```

## 预算模板 (budget_template_*)

```bash
# 创建模板
python3 scripts/ledger_cli.py budget_template_create '{"name":"吃饭模板","description":"日常吃饭","category":"餐饮","amount":400,"dimension_type":"account","dimension_value":"xxx信用卡"}'

# 列出模板
python3 scripts/ledger_cli.py budget_template_list '{}'

# 应用模板
python3 scripts/ledger_cli.py budget_template_apply '{"id":1,"year":2026,"month":6}'

# 推荐模板
python3 scripts/ledger_cli.py budget_template_suggest '{"limit":3}'

# 更新模板
python3 scripts/ledger_cli.py budget_template_update '{"id":1,"amount":500}'

# 删除模板
python3 scripts/ledger_cli.py budget_template_delete '{"id":1}'
```


