---
name: ledger
description: 个人记账工具，支持记账、查账、统计、预算管理等功能
version: 2.0.0
---

# Ledger API

## 基本信息

Content-Type: application/json

### Base URL 解析

执行任何 API 调用前，**必须先确定 `BASE_URL`**，按以下优先级：

1. **系统环境变量** `$LEDGER_API_URL`
2. **`.env` 文件** `skills/ledger/.env` 中的 `LEDGER_API_URL`
3. **Docker 容器内** 自动使用 `http://host.docker.internal:5800`
4. **默认值** `http://127.0.0.1:5800`

确定方法（在执行任何 curl 之前运行一次）：

```bash
# 1. 优先使用环境变量
BASE_URL="${LEDGER_API_URL:-}"

# 2. 检查 .env 文件
if [ -z "$BASE_URL" ] && [ -f "skills/ledger/.env" ]; then
  BASE_URL=$(grep -E '^LEDGER_API_URL=' skills/ledger/.env | cut -d= -f2-)
fi

# 3. Docker 容器内自动检测
if [ -z "$BASE_URL" ] && ([ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null); then
  BASE_URL="http://host.docker.internal:5800"
fi

# 4. 默认值
BASE_URL="${BASE_URL:-http://127.0.0.1:5800}"
```

后续所有命令中的 `$BASE_URL` 即由此解析得到。

所有响应格式：
```json
{"success": true, "data": {...}}
{"success": false, "error": "错误信息"}
```

---

## 交易管理

### 记账

```bash
curl -X POST $BASE_URL/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"支出","amount":30,"category":"食品酒水","subcategory":"早餐","account":"微信零钱","note":"包子豆浆"}'
```

必填：`amount`（正数）
可选：`type`（支出/收入，默认支出）、`category`、`subcategory`、`account`、`project`、`member`、`merchant`、`note`、`date`（格式 YYYY-MM-DD HH:MM:SS）、`force`（true 跳过重复检查）、`tag_ids`（标签ID数组）

返回：`{"success":true,"data":{"id":42}}`

### 查看记录

```bash
# 最近 20 条
curl $BASE_URL/api/transactions?limit=20

# 带筛选
curl "$BASE_URL/api/transactions?category=食品酒水&account=微信零钱&limit=10"

# 包含已删除
curl "$BASE_URL/api/transactions?include_deleted=true&limit=5"
```

筛选参数：`type`、`category`、`subcategory`、`account`、`project`、`member`、`merchant`、`keyword`、`tag_ids`、`year`、`month`、`start_date`、`end_date`、`limit`、`offset`

### 查看单条

```bash
curl $BASE_URL/api/transactions/42
```

### 搜索

```bash
curl "$BASE_URL/api/transactions/search?keyword=早餐&search_type=all&limit=20"
```

`search_type`: `all`（默认）/ `note` / `category` / `merchant`

### 修改记录

```bash
# 单字段
curl -X PUT $BASE_URL/api/transactions/42 \
  -H 'Content-Type: application/json' \
  -d '{"field":"amount","value":50}'

# 多字段
curl -X PUT $BASE_URL/api/transactions/42 \
  -H 'Content-Type: application/json' \
  -d '{"amount":50,"note":"修改备注","category":"餐饮"}'
```

可修改字段：`amount`、`category`、`subcategory`、`account`、`project`、`member`、`merchant`、`note`、`trans_date`、`type`、`tag_ids`

### 删除 / 恢复

```bash
# 软删除
curl -X DELETE $BASE_URL/api/transactions/42

# 恢复
curl -X POST $BASE_URL/api/transactions/42/restore
```

---

## 统计查询

### 收支汇总

```bash
curl "$BASE_URL/api/summary?year=2026&month=6"
```

返回：`income`、`expense`、`balance`、`daily_avg_expense`、`income_count`、`expense_count`

### 分组统计

```bash
# 按类别
curl "$BASE_URL/api/stats?group_by=category&year=2026&month=6"

# 按账户、月份、商家、成员、项目、标签、类型
curl "$BASE_URL/api/stats?group_by=account&year=2026"
```

`group_by`: `category` / `subcategory` / `account` / `merchant` / `project` / `member` / `month` / `tag` / `type`
可选：`sub_group=subcategory`（二级分组）

### 趋势

```bash
curl "$BASE_URL/api/trends?year=2026&granularity=month"
```

`granularity`: `day` / `week` / `month`

---

## 枚举查询

```bash
# 所有类别（含子类别及使用次数）
curl $BASE_URL/api/categories

# 常用子类别 TOP20
curl $BASE_URL/api/categories/quick

# 所有账户
curl $BASE_URL/api/accounts

# 所有成员
curl $BASE_URL/api/members

# 所有项目
curl $BASE_URL/api/projects

# 所有商家
curl $BASE_URL/api/merchants

# 自动建议（综合）
curl "$BASE_URL/api/suggestions?field=all&keyword=早"
```

`suggestions` 的 `field`: `all` / `categories` / `subcategories` / `accounts` / `merchants` / `projects` / `members`

---

## 预算管理

### 设置预算

```bash
curl -X POST $BASE_URL/api/budgets \
  -H 'Content-Type: application/json' \
  -d '{"category":"食品酒水","amount":2000,"year":2026,"month":6}'
```

可选：`dimension_type`（category/account/member/project/merchant）、`dimension_value`

### 查看预算执行

```bash
curl "$BASE_URL/api/budgets/check?year=2026&month=6"
```

返回每个预算的 `budget`、`spent`、`remaining`、`percentage`

### 预算列表

```bash
curl "$BASE_URL/api/budgets?year=2026&month=6"
```

---

## 模板管理

### 列表 / 创建 / 修改 / 删除

```bash
# 列表
curl $BASE_URL/api/templates

# 创建
curl -X POST $BASE_URL/api/templates \
  -H 'Content-Type: application/json' \
  -d '{"name":"早餐","template_type":"日常","type":"支出","amount":15,"category":"食品酒水","subcategory":"早餐","account":"微信零钱"}'

# 修改
curl -X PUT $BASE_URL/api/templates/1 \
  -H 'Content-Type: application/json' \
  -d '{"amount":20}'

# 删除
curl -X DELETE $BASE_URL/api/templates/1

# 使用（增加使用次数）
curl -X POST $BASE_URL/api/templates/1/use
```

---

## 标签管理

```bash
# 列表
curl $BASE_URL/api/tags

# 创建
curl -X POST $BASE_URL/api/tags \
  -H 'Content-Type: application/json' \
  -d '{"name":"报销","color":"#ef4444"}'

# 删除
curl -X DELETE $BASE_URL/api/tags/1

# 按标签查记录
curl "$BASE_URL/api/tags/1/transactions?limit=20"
```

---

## 智能导入

### 上传预览

上传 CSV 文件，自动推断列映射，返回预览数据：

```bash
curl -X POST $BASE_URL/api/import/preview \
  -F "file=@/path/to/data.csv"
```

返回：
- `detected_source`：检测到的数据来源（支付宝/微信/随手记/银行）
- `headers`：CSV 表头列表
- `mapping`：列映射建议（含置信度）
- `unmapped_columns`：未映射的列（将存入 extra_data）
- `preview_rows`：前5行转换后数据
- `total_rows`：总行数
- `suggested_tags`：建议标签
- `duplicate_estimate`：预估重复数

### 执行导入

```bash
curl -X POST $BASE_URL/api/import/execute \
  -F "file=@/path/to/data.csv" \
  -F 'mapping={"交易时间":"date","支付金额":"amount","交易对方":"merchant"}' \
  -F 'tags=["支付宝导入","2024-06"]' \
  -F "skip_duplicates=true" \
  -F "source=支付宝"
```

参数：
- `file`：CSV 文件（必填）
- `mapping`：列映射 JSON（必填，key=CSV列名，value=目标字段）
- `tags`：标签数组 JSON（可选）
- `skip_duplicates`：是否跳过重复（可选，默认 true）
- `source`：数据来源（可选，不传则自动检测）

目标字段：`type`（交易类型）、`amount`（金额）、`date`（日期）、`category`（类别）、`subcategory`（子类别）、`account`（账户）、`merchant`（商家）、`member`（成员）、`project`（项目）、`note`（备注）

返回：`imported`（成功数）、`skipped`（跳过数）、`duplicates_found`（重复数）、`batch_id`（批次ID）、`tags_applied`

### 导入批次历史

```bash
curl $BASE_URL/api/import/batches
```

### 智能映射说明

导入引擎会自动：
1. **检测编码**：UTF-8 / GBK / GB2312
2. **推断列名**：支付宝"交易对方"→merchant，微信"支付方式"→account 等
3. **标准化值**：根据数据库已有数据自动归类（如"招行"→"招商银行"）
4. **管理别名**：映射结果自动学习为别名，下次导入更准确
5. **保留未映射数据**：未匹配的列值存入 `extra_data` 字段，不丢失
6. **自动打标签**：来源标签（"微信导入"）+ 时间标签（"2024-06"）

---

## 增强导出

### 导出预览

```bash
curl "$BASE_URL/api/export/preview?start_date=2024-01-01&end_date=2024-06-30"
```

返回：`count`（记录数）、`date_range`、`income`、`expense`、`balance`

### 导出文件

```bash
# Excel（多 Sheet：明细+月度汇总+分类统计+账户统计）
curl "$BASE_URL/api/export/v2?format=excel&start_date=2024-01-01" -o export.xlsx

# CSV（与导入格式兼容，可直接重新导入）
curl "$BASE_URL/api/export/v2?format=csv" -o export.csv

# PDF（月度报告）
curl "$BASE_URL/api/export/v2?format=pdf&title=2024上半年报告" -o report.pdf

# JSON
curl "$BASE_URL/api/export/v2?format=json" -o export.json
```

筛选参数：`start_date`、`end_date`、`category`、`account`、`type`（支出/收入）、`tag_ids`（逗号分隔）

Excel/PDF 额外参数：`sheets`（逗号分隔：明细,月度汇总,分类统计,账户统计）

CSV 额外参数：`import_compatible`（true=列名与导入一致，默认 true）

---

## 其他

```bash
# 健康检查
curl $BASE_URL/api/health

# 数据库信息
curl $BASE_URL/api/info

# 消费分析报告
curl $BASE_URL/api/analyze
```

---

## 其他客户端

如果环境中没有 curl（如 Docker 容器），可使用 wget，详见 [references/wget.md](references/wget.md)。

---

## 注意事项

- 金额必须为正数
- 重复记录会被拦截，设置 `"force": true` 跳过检查
- 日期格式：`YYYY-MM-DD HH:MM:SS`，不传则使用当前时间
- 删除为软删除，可通过 `/restore` 恢复
- 导入文件大小限制：10MB
- CSV 导出默认与导入格式兼容，可直接重新导入
