---
name: ledger
description: 个人记账工具，支持记账、查账、统计、预算管理等功能
version: 2.0.0
---

# Ledger API

## 基本信息

```
Base URL: http://127.0.0.1:5800
Content-Type: application/json
```

所有响应格式：
```json
{"success": true, "data": {...}}
{"success": false, "error": "错误信息"}
```

---

## 交易管理

### 记账

```bash
curl -X POST http://127.0.0.1:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"支出","amount":30,"category":"食品酒水","subcategory":"早餐","account":"微信零钱","note":"包子豆浆"}'
```

必填：`amount`（正数）
可选：`type`（支出/收入，默认支出）、`category`、`subcategory`、`account`、`project`、`member`、`merchant`、`note`、`date`（格式 YYYY-MM-DD HH:MM:SS）、`force`（true 跳过重复检查）、`tag_ids`（标签ID数组）

返回：`{"success":true,"data":{"id":42}}`

### 查看记录

```bash
# 最近 20 条
curl http://127.0.0.1:5800/api/transactions?limit=20

# 带筛选
curl "http://127.0.0.1:5800/api/transactions?category=食品酒水&account=微信零钱&limit=10"

# 包含已删除
curl "http://127.0.0.1:5800/api/transactions?include_deleted=true&limit=5"
```

筛选参数：`type`、`category`、`subcategory`、`account`、`project`、`member`、`merchant`、`keyword`、`tag_ids`、`year`、`month`、`start_date`、`end_date`、`limit`、`offset`

### 查看单条

```bash
curl http://127.0.0.1:5800/api/transactions/42
```

### 搜索

```bash
curl "http://127.0.0.1:5800/api/transactions/search?keyword=早餐&search_type=all&limit=20"
```

`search_type`: `all`（默认）/ `note` / `category` / `merchant`

### 修改记录

```bash
# 单字段
curl -X PUT http://127.0.0.1:5800/api/transactions/42 \
  -H 'Content-Type: application/json' \
  -d '{"field":"amount","value":50}'

# 多字段
curl -X PUT http://127.0.0.1:5800/api/transactions/42 \
  -H 'Content-Type: application/json' \
  -d '{"amount":50,"note":"修改备注","category":"餐饮"}'
```

可修改字段：`amount`、`category`、`subcategory`、`account`、`project`、`member`、`merchant`、`note`、`trans_date`、`type`、`tag_ids`

### 删除 / 恢复

```bash
# 软删除
curl -X DELETE http://127.0.0.1:5800/api/transactions/42

# 恢复
curl -X POST http://127.0.0.1:5800/api/transactions/42/restore
```

---

## 统计查询

### 收支汇总

```bash
curl "http://127.0.0.1:5800/api/summary?year=2026&month=6"
```

返回：`income`、`expense`、`balance`、`daily_avg_expense`、`income_count`、`expense_count`

### 分组统计

```bash
# 按类别
curl "http://127.0.0.1:5800/api/stats?group_by=category&year=2026&month=6"

# 按账户、月份、商家、成员、项目、标签、类型
curl "http://127.0.0.1:5800/api/stats?group_by=account&year=2026"
```

`group_by`: `category` / `subcategory` / `account` / `merchant` / `project` / `member` / `month` / `tag` / `type`
可选：`sub_group=subcategory`（二级分组）

### 趋势

```bash
curl "http://127.0.0.1:5800/api/trends?year=2026&granularity=month"
```

`granularity`: `day` / `week` / `month`

---

## 枚举查询

```bash
# 所有类别（含子类别及使用次数）
curl http://127.0.0.1:5800/api/categories

# 常用子类别 TOP20
curl http://127.0.0.1:5800/api/categories/quick

# 所有账户
curl http://127.0.0.1:5800/api/accounts

# 所有成员
curl http://127.0.0.1:5800/api/members

# 所有项目
curl http://127.0.0.1:5800/api/projects

# 所有商家
curl http://127.0.0.1:5800/api/merchants

# 自动建议（综合）
curl "http://127.0.0.1:5800/api/suggestions?field=all&keyword=早"
```

`suggestions` 的 `field`: `all` / `categories` / `subcategories` / `accounts` / `merchants` / `projects` / `members`

---

## 预算管理

### 设置预算

```bash
curl -X POST http://127.0.0.1:5800/api/budgets \
  -H 'Content-Type: application/json' \
  -d '{"category":"食品酒水","amount":2000,"year":2026,"month":6}'
```

可选：`dimension_type`（category/account/member/project/merchant）、`dimension_value`

### 查看预算执行

```bash
curl "http://127.0.0.1:5800/api/budgets/check?year=2026&month=6"
```

返回每个预算的 `budget`、`spent`、`remaining`、`percentage`

### 预算列表

```bash
curl "http://127.0.0.1:5800/api/budgets?year=2026&month=6"
```

---

## 模板管理

### 列表 / 创建 / 修改 / 删除

```bash
# 列表
curl http://127.0.0.1:5800/api/templates

# 创建
curl -X POST http://127.0.0.1:5800/api/templates \
  -H 'Content-Type: application/json' \
  -d '{"name":"早餐","template_type":"日常","type":"支出","amount":15,"category":"食品酒水","subcategory":"早餐","account":"微信零钱"}'

# 修改
curl -X PUT http://127.0.0.1:5800/api/templates/1 \
  -H 'Content-Type: application/json' \
  -d '{"amount":20}'

# 删除
curl -X DELETE http://127.0.0.1:5800/api/templates/1

# 使用（增加使用次数）
curl -X POST http://127.0.0.1:5800/api/templates/1/use
```

---

## 标签管理

```bash
# 列表
curl http://127.0.0.1:5800/api/tags

# 创建
curl -X POST http://127.0.0.1:5800/api/tags \
  -H 'Content-Type: application/json' \
  -d '{"name":"报销","color":"#ef4444"}'

# 删除
curl -X DELETE http://127.0.0.1:5800/api/tags/1

# 按标签查记录
curl "http://127.0.0.1:5800/api/tags/1/transactions?limit=20"
```

---

## 数据导出

```bash
# JSON 格式
curl "http://127.0.0.1:5800/api/export?format=json&category=食品酒水&start_date=2026-01-01&end_date=2026-06-30"

# CSV 格式
curl "http://127.0.0.1:5800/api/export?format=csv"
```

---

## 其他

```bash
# 健康检查
curl http://127.0.0.1:5800/api/health

# 数据库信息
curl http://127.0.0.1:5800/api/info

# 消费分析报告
curl http://127.0.0.1:5800/api/analyze
```

---

## 其他客户端

### Go CLI (ledger-cli)

单二进制，不依赖 curl/wget/python，适用于任何 Linux/Docker 环境。

```bash
# 设置 API 地址（默认 http://127.0.0.1:5800）
export LEDGER_API_URL=http://127.0.0.1:5800

# 交易管理
ledger-cli tx add --amount 30 --category 食品酒水 --note 早餐
ledger-cli tx list --limit 10
ledger-cli tx get 42
ledger-cli tx search 早餐
ledger-cli tx update 42 --amount 50
ledger-cli tx delete 42
ledger-cli tx restore 42

# 统计查询
ledger-cli stats summary --year 2026 --month 6
ledger-cli stats group --by category --year 2026 --month 6
ledger-cli stats trends --year 2026 --granularity month

# 枚举查询
ledger-cli meta categories
ledger-cli meta accounts
ledger-cli meta suggest --field all --keyword 早

# 预算管理
ledger-cli budget set --category 食品酒水 --amount 2000 --year 2026 --month 6
ledger-cli budget check --year 2026 --month 6
ledger-cli budget list --year 2026 --month 6

# 模板管理
ledger-cli template list
ledger-cli template add --name 早餐 --amount 15 --category 食品酒水
ledger-cli template update 1 --amount 20
ledger-cli template delete 1
ledger-cli template use 1

# 标签管理
ledger-cli tag list
ledger-cli tag add --name 报销 --color "#ef4444"
ledger-cli tag delete 1
ledger-cli tag tx 1

# 数据导出
ledger-cli export --format json --category 食品酒水
ledger-cli export --format csv

# 其他
ledger-cli misc health
ledger-cli misc info
ledger-cli misc analyze
```

编译：`go build -o bin/ledger-cli ./cmd/ledger-cli`
交叉编译：`GOOS=linux GOARCH=arm64 go build -o bin/ledger-cli-linux-arm64 ./cmd/ledger-cli`

### wget

如果环境没有 curl，可使用 wget，详见 [references/wget.md](references/wget.md)。

---

## 注意事项

- 金额必须为正数
- 重复记录会被拦截，设置 `"force": true` 跳过检查
- 日期格式：`YYYY-MM-DD HH:MM:SS`，不传则使用当前时间
- 删除为软删除，可通过 `/restore` 恢复

