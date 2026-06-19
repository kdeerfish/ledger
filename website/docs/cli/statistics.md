---
sidebar_position: 7
---

# 📈 统计分析 (CLI)

## 月度汇总

```bash
ledger misc summary                    # 默认当月
ledger misc summary --year 2026 --month 6
```

输出:
```
收入 ¥8000.00  支出 ¥1234.50  结余 ¥6765.50  笔数 28
```

## 按维度统计

```bash
ledger misc stats --group-by category
ledger misc stats --group-by account
ledger misc stats --group-by project
ledger misc stats --group-by member
ledger misc stats --group-by merchant
ledger misc stats --group-by month --year 2026
```

支持 `group_by` 值:
- `category` (默认)
- `account`
- `project`
- `member`
- `merchant`
- `month` (按 `YYYY-MM` 聚合)

输出示例 (`--group-by category`):
```
食品          收 0.00    支 1450.50  笔 18
交通          收 0.00    支 320.00   笔 12
工资          收 8000.00 支 0.00     笔 1
娱乐          收 0.00    支 600.00   笔 5
```

## 二级分组

```bash
ledger misc stats --group-by category --sub-group account --year 2026
```

输出会按类别展示,每个类别下再按账户细分。

## 交叉统计报告

```bash
ledger misc analyze
```

输出多段报告(类别 / 月度 / 账户 三个维度的合计),供人工阅读。

## 限定时间范围

所有 stats / summary 命令都支持:
```bash
--start-date 2026-01-01
--end-date 2026-12-31
```

## 自动补全数据

```bash
# 获取所有类别、账户、商家、成员等的去重列表
curl 'http://localhost:5800/api/suggestions?field=category&keyword=食'
```

返回结构化数据供前端自动补全。详见 [HTTP API 文档](../api#-统计--报告)。
