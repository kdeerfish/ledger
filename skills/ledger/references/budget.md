# 预算命令

## 设置预算

```bash
# 设置类别预算
curl -X POST http://127.0.0.1:5800/api/budgets \
  -H 'Content-Type: application/json' \
  -d '{"category":"食品酒水","amount":1000,"year":2026,"month":6}'

# 按账户维度设置预算
curl -X POST http://127.0.0.1:5800/api/budgets \
  -H 'Content-Type: application/json' \
  -d '{"category":"餐饮","amount":500,"dimension_type":"account","dimension_value":"信用卡","year":2026,"month":6}'
```

参数：
- `category`: 类别 - 必填
- `amount`: 预算金额 - 必填
- `year`: 年份 - 可选，默认当年
- `month`: 月份 - 可选，默认当月
- `dimension_type`: 维度类型 (category/account/member/project/merchant) - 可选
- `dimension_value`: 维度值 - 可选

## 查看预算执行

```bash
curl "http://127.0.0.1:5800/api/budgets/check?year=2026&month=6"
```

返回每个预算的 `budget`、`spent`、`remaining`、`percentage`

## 预算列表

```bash
curl "http://127.0.0.1:5800/api/budgets?year=2026&month=6"
```
