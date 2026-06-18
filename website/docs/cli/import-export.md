---
sidebar_position: 10
---

# 📁 数据导入导出

## 导入 CSV

```bash
python scripts/import_ledger.py data/sample/mymoney_data.csv
python scripts/cli.py import_csv --file data.csv
```

## 导出

```bash
python scripts/cli.py export --output report.csv                     # CSV
python scripts/cli.py export --output report.json --format json      # JSON
python scripts/cli.py export --output output.csv --category 食品     # 按类别
python scripts/cli.py export --output output.csv --start_date 2026-01-01 --end_date 2026-06-30
```
