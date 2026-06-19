---
sidebar_position: 6
---

# ⌨️ CLI 命令参考

喜欢命令行？Ledger 提供完整 CLI，无需启动 Web 服务就能记账、查账、做统计。

---

## 快速上手

```bash
# 记一笔
python scripts/cli.py add --type 支出 --amount 25.5 --category 食品 --account 微信

# 查看最近 20 条
python scripts/cli.py list

# 看本月汇总
python scripts/cli.py summary

# 搜索关键词
python scripts/cli.py search --keyword 午餐

# 按类别筛选
python scripts/cli.py filter --category 食品
```

> 完整 CLI 在容器里也可以用：`docker exec ledger python scripts/cli.py add ...`

---

## 📋 命令总览

| 命令 | 说明 |
|------|------|
| `init` | 初始化数据库 |
| `add` | 添加一笔交易 |
| `list` | 查看交易列表 |
| `update` | 修改某笔交易 |
| `delete` | 软删除 |
| `restore` | 恢复已删除 |
| `hard_delete` | 永久删除 |
| `search` | 关键词搜索 |
| `filter` | 多条件筛选 |
| `summary` | 按月汇总 |
| `stats` | 按维度统计 |
| `budget_set` | 设置预算 |
| `budget_check` | 预算执行检查 |
| `budget_template_*` | 预算模板（增/删/查/应用/推荐） |
| `template_*` | 记账模板 |
| `import_csv` | 导入 CSV |
| `export` | 导出 CSV / JSON |

---

## 1. 交易管理

### 添加 `add`

```bash
python scripts/cli.py add \
  --type 支出 \
  --amount 100 \
  --category 食品 \
  --subcategory 午餐 \
  --account 微信 \
  --project 公司 \
  --member 我 \
  --merchant 麦当劳 \
  --note 同事请客 \
  --date "2026-06-19 12:30:00"
```

所有参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `--type` | ✅ | 支出 / 收入 |
| `--amount` | ✅ | 金额（数字） |
| `--category` | ❌ | 一级类别（如「食品」） |
| `--subcategory` | ❌ | 子类别 |
| `--account` | ❌ | 账户（微信 / 支付宝 等） |
| `--project` | ❌ | 项目 |
| `--member` | ❌ | 家庭成员 |
| `--merchant` ❌ | 商家 |
| `--note` | ❌ | 备注 |
| `--date` | ❌ | 日期，不传默认当前时间 |
| `--confirm` | ❌ | 跳过重复检查直接保存 |

### 列表 `list`

```bash
python scripts/cli.py list --limit 50
python scripts/cli.py list --include-deleted   # 含已删除的
```

### 修改 `update`

```bash
python scripts/cli.py update --id 123 --field amount --value 99.9
python scripts/cli.py update --id 123 --field category --value 餐饮
```

可改字段：`type / amount / category / subcategory / account / project / member / merchant / note / date`

### 删除 / 恢复

```bash
python scripts/cli.py delete --id 123           # 软删除
python scripts/cli.py restore --id 123          # 恢复
python scripts/cli.py hard_delete --id 123      # 永久删除
python scripts/cli.py hard_delete --id 123 --confirm  # 跳过确认
```

---

## 2. 搜索与筛选

### 关键词搜索 `search`

```bash
python scripts/cli.py search --keyword 午餐
python scripts/cli.py search --keyword 麦当劳 --limit 20
```

### 多维筛选 `filter`

```bash
python scripts/cli.py filter --category 食品 --start_date 2026-06-01 --end_date 2026-06-30
python scripts/cli.py filter --account 微信 --type 支出
python scripts/cli.py filter --merchant 麦当劳 --limit 100
```

支持参数：`--type / --category / --subcategory / --account / --project / --member / --merchant / --start_date / --end_date / --limit`

---

## 3. 汇总与统计

### 月度汇总 `summary`

```bash
python scripts/cli.py summary                 # 当月
python scripts/cli.py summary --year 2026 --month 6
```

输出示例：

```
========== 2026 年 6 月汇总 ==========
  收入:   ¥8,500.00
  支出:   ¥3,200.00
  结余:   ¥5,300.00
  日均:   ¥106.67
===================================
```

### 多维统计 `stats`

```bash
python scripts/cli.py stats --group_by category
python scripts/cli.py stats --group_by account --year 2026
python scripts/cli.py stats --group_by merchant --type 支出
python scripts/cli.py stats --group_by tag
```

可选 `--group_by`：

| 值 | 说明 |
|----|------|
| `category` | 类别（最常用） |
| `subcategory` | 子类别 |
| `account` | 账户 |
| `merchant` | 商家 |
| `project` | 项目 |
| `member` | 成员 |
| `month` | 月份趋势 |
| `tag` | 标签 |
| `type` | 类型 |

---

## 4. 预算管理

### 设置 `budget_set`

```bash
python scripts/cli.py budget_set --category 食品 --amount 1000 --year 2026 --month 6
python scripts/cli.py budget_set --account 微信 --amount 2000 --year 2026 --month 6
```

### 检查 `budget_check`

```bash
python scripts/cli.py budget_check
python scripts/cli.py budget_check --year 2026 --month 6
```

### 预算模板

```bash
# 创建模板
python scripts/cli.py budget_template_create --name 日常预算

# 列出模板
python scripts/cli.py budget_template_list

# 应用模板到指定月份
python scripts/cli.py budget_template_apply --template_id 1 --year 2026 --month 7

# 智能推荐（基于历史消费）
python scripts/cli.py budget_template_suggest
```

---

## 5. 记账模板

把常用交易存成模板，下次一键记账：

```bash
# 创建
python scripts/cli.py template_create \
  --template_name 通勤地铁 \
  --type 支出 \
  --amount 6 \
  --category 交通 \
  --subcategory 地铁 \
  --account 微信

# 列出（按使用频次排序）
python scripts/cli.py template_list

# 使用（创建一笔交易，usage_count +1）
python scripts/cli.py template_apply --template_id 1

# 更新 / 删除
python scripts/cli.py template_update --id 1 --amount 7
python scripts/cli.py template_delete --id 1
```

---

## 6. 导入 / 导出

### 导入 CSV

```bash
python scripts/cli.py import_csv --file data/sample/mymoney_data.csv
```

支持的格式：随手记（MyMoney）CSV。自动去重。

### 导出

```bash
python scripts/cli.py export --output report.csv          # CSV
python scripts/cli.py export --output report.json --format json   # JSON
```

---

## 7. 数据库管理

```bash
# 初始化（首次运行会自动建表）
python scripts/cli.py init

# 查看帮助
python scripts/cli.py --help
python scripts/cli.py add --help
```

---

## 8. 在 Docker 容器里用 CLI

```bash
docker exec -it ledger python scripts/cli.py add \
  --type 支出 --amount 25.5 --category 食品 --account 微信

docker exec ledger python scripts/cli.py summary

docker exec ledger python scripts/cli.py list --limit 10
```

（`-it` 可选，加上能用中文输入；不带也能跑）