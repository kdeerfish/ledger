# 📘 CLI 命令参考

`scripts/cli.py` 是 Ledger 的统一命令行入口，所有业务逻辑委托给 `ledger_modules/` 处理。

```bash
python scripts/cli.py <action> [参数...]
```

!!! tip "查看帮助"
    ```bash
    python scripts/cli.py --help
    ```

---

## 📊 交易管理

### 添加交易

```bash
python scripts/cli.py add \
  --type 支出|收入 \
  --amount 100 \
  --category 食品 \
  --subcategory 零食 \      # (1)!
  --account 微信 \           # (2)!
  --project 日常 \
  --member 本人 \
  --merchant 711 \
  --note "零食" \
  --date "2026-06-15" \     # (3)!
  --confirm                  # (4)!
```

1.  子类别，可选
2.  账户、项目、成员、商家均为可选
3.  可选，默认当前时间
4.  跳过重复检查

### 列出交易

```bash
python scripts/cli.py list                   # 最近 20 条
python scripts/cli.py list --limit 50        # 最近 50 条
python scripts/cli.py list --include_deleted # 含已删除
```

### 修改交易

```bash
python scripts/cli.py update --id 1 --field amount --value 50
python scripts/cli.py update --id 1 --field category --value 交通
python scripts/cli.py update --id 1 --field note --value "地铁充值"
```

支持修改的字段：`amount` `category` `subcategory` `account` `project` `member` `merchant` `note` `trans_date`

### 删除与恢复

```bash
python scripts/cli.py delete --id 1                   # 软删除（可恢复）
python scripts/cli.py restore --id 1                  # 恢复
python scripts/cli.py hard_delete --id 1 --confirm    # 物理删除（不可恢复）
```

!!! warning "硬删除不可恢复"
    硬删除会从数据库中彻底清除记录，操作前请确认。

---

## 🔍 搜索与筛选

=== "搜索"

    ```bash
    python scripts/cli.py search --keyword 午餐                    # 全局搜索
    python scripts/cli.py search --keyword 午餐 --search_type note # 按备注
    python scripts/cli.py search --keyword 食品 --search_type category # 按类别
    python scripts/cli.py search --keyword 711 --search_type merchant  # 按商家
    ```

=== "筛选"

    ```bash
    python scripts/cli.py filter --category 食品
    python scripts/cli.py filter --account 微信 --start_date 2026-01-01 --end_date 2026-06-30
    python scripts/cli.py filter --member 本人 --merchant 711
    python scripts/cli.py filter --category 食品 --account 支付宝 --limit 100
    ```

搜索类型 `search_type` 可选值：

| 值 | 说明 |
|----|------|
| `all` | 全局搜索（默认） |
| `note` | 按备注搜索 |
| `category` | 按类别/子类别搜索 |
| `merchant` | 按商家搜索 |

---

## 📈 统计分析

=== "收支汇总"

    ```bash
    python scripts/cli.py summary                       # 全部汇总
    python scripts/cli.py summary --year 2026           # 2026 年
    python scripts/cli.py summary --year 2026 --month 7 # 7 月
    ```

=== "多维度统计"

    ```bash
    python scripts/cli.py stats --group_by category  # 按类别
    python scripts/cli.py stats --group_by account   # 按账户
    python scripts/cli.py stats --group_by month     # 按月
    python scripts/cli.py stats --year 2026 --month 7 --group_by account
    ```

=== "查看维度"

    ```bash
    python scripts/cli.py accounts          # 列出所有账户
    python scripts/cli.py categories        # 列出所有类别（含子类别+统计）
    python scripts/cli.py members           # 列出所有成员（含收支统计）
    python scripts/cli.py reconcile_guide   # 对账指南
    ```

---

## 💰 预算管理

=== "设置预算"

    ```bash
    # 按类别设置
    python scripts/cli.py budget_set --category 食品 --amount 1000 --year 2026 --month 7

    # 按账户维度
    python scripts/cli.py budget_set --category 餐饮 --amount 500 --dimension_type account --dimension_value 微信

    # 按成员维度
    python scripts/cli.py budget_set --category 日常 --amount 2000 --dimension_type member --dimension_value 本人
    ```

=== "检查预算"

    ```bash
    python scripts/cli.py budget_check                     # 本月
    python scripts/cli.py budget_check --year 2026 --month 7
    ```

=== "预算模板"

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

---

## 📋 记录模板（一键记账）

```bash
# 创建模板
python scripts/cli.py template_create \
  --template_name "通勤" \
  --type 支出 \
  --template_amount 6 \
  --category 交通 --subcategory 地铁 --account 微信 --note "地铁通勤"

# 列出模板
python scripts/cli.py template_list

# 应用模板（自动记账）
python scripts/cli.py template_apply --template_id 1
python scripts/cli.py template_apply --template_id 1 --template_amount 7  # 覆盖金额

# 更新 / 删除
python scripts/cli.py template_update --template_id 1 --template_name "通勤（涨价后）"
python scripts/cli.py template_delete --template_id 1

# 智能推荐
python scripts/cli.py template_suggest --template_limit 5
```

!!! tip "一键记账"
    创建模板后，`template_apply` 会自动按模板参数记账，无需每次输入完整命令。

---

## 📁 数据导入导出

=== "导入 CSV"

    ```bash
    python scripts/import_ledger.py data/sample/mymoney_data.csv
    python scripts/cli.py import_csv --file data.csv
    ```

=== "导出"

    ```bash
    python scripts/cli.py export --output report.csv                     # CSV
    python scripts/cli.py export --output report.json --format json      # JSON
    python scripts/cli.py export --output output.csv --category 食品     # 按类别
    python scripts/cli.py export --output output.csv --start_date 2026-01-01 --end_date 2026-06-30
    ```

---

## 🤖 AI Agent 集成

通过 JSON 参数调用，适合 picoclaw 等 AI Agent：

```bash
python ledger-skills/scripts/ledger_cli.py add '{"type":"支出","amount":25.5,"category":"食品","account":"微信"}'
python ledger-skills/scripts/ledger_cli.py list '{"limit":5}'
python ledger-skills/scripts/ledger_cli.py summary '{"year":2026,"month":7}'
python ledger-skills/scripts/ledger_cli.py search '{"keyword":"午餐"}'
python ledger-skills/scripts/ledger_cli.py stats '{"group_by":"category"}'
```

---

## 🛠 数据库

```bash
# 手动初始化数据库
python scripts/cli.py init

# 数据交叉分析（供 AI Agent 学习用户习惯）
python scripts/cli.py analyze
```
