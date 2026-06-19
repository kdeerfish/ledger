---
sidebar_position: 10
---

# 📁 数据导入导出 (CLI)

## 导入 CSV

支持"随手记"格式的 CSV,中文表头:

```bash
ledger misc import --file data.csv
```

**预期列名** (首行):
```
交易类型,金额,日期,类别,子类别,账户,项目,成员,商家,备注
```

| 交易类型值 | 行为 |
|-----------|------|
| `支出` / `收入` | 正常导入 |
| 其他 | 跳过(不报错) |
| 金额 = 0 或非数字 | 跳过 |
| 日期无法解析 | 跳过 |

**日期格式**:
- `2026/06/19 12:00` ✅
- `2026/06/19` ✅
- 其他格式 ❌(跳过)

**去重策略**: 导入时按 (date, type, amount, category) 检测,重复行被自动拒绝(不报错)。

**排序**: 导入时按日期升序排列再 INSERT,保证 ID 顺序 = 时间顺序。

## 导出

```bash
# CSV (默认)
ledger misc export --output report.csv

# JSON
ledger misc export --output report.json --format json

# 加筛选
ledger misc export --output 2026-food.csv \
  --start-date 2026-01-01 --end-date 2026-12-31 \
  --category 食品
```

| Flag | 简写 | 默认 | 说明 |
|------|------|------|------|
| `--output` | `-o` | ✅ | 输出文件路径 |
| `--format` | `-f` | csv | csv / json |
| `--start-date` | | | 起始 YYYY-MM-DD |
| `--end-date` | | | 结束 YYYY-MM-DD |
| `--category` | | | 按类别过滤 |

## HTTP 端点(脚本友好)

```bash
# 浏览器/前端
curl 'http://localhost:5800/api/export?format=csv&start_date=2026-01-01' -o report.csv

# JSON
curl 'http://localhost:5800/api/export?format=json' -o report.json
```

## 完整数据备份

```bash
# 备份当前数据库
cp data/ledger.db backup/ledger-$(date +%F).db

# 完整导出所有数据(无筛选)
ledger misc export --output backup/all.csv
```
