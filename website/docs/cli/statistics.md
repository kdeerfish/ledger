---
sidebar_position: 7
---

# 📈 统计分析

## 收支汇总

```bash
python scripts/cli.py summary                       # 全部汇总
python scripts/cli.py summary --year 2026           # 2026 年
python scripts/cli.py summary --year 2026 --month 7 # 7 月
```

## 多维度统计

```bash
python scripts/cli.py stats --group_by category  # 按类别
python scripts/cli.py stats --group_by account   # 按账户
python scripts/cli.py stats --group_by month     # 按月
python scripts/cli.py stats --year 2026 --month 7 --group_by account
```

## 查看维度

```bash
python scripts/cli.py accounts          # 列出所有账户
python scripts/cli.py categories        # 列出所有类别（含子类别+统计）
python scripts/cli.py members           # 列出所有成员（含收支统计）
python scripts/cli.py reconcile_guide   # 对账指南
```
