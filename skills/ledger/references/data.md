# 数据命令

## 导入CSV (import)

```bash
python3 scripts/ledger_cli.py import '{"file":"path/to/data.csv"}'
```

**CSV 格式要求**（第一行必须是表头）：

| 列名 | 说明 | 必填 | 示例 |
|------|------|------|------|
| 交易类型 | 支出 或 收入 | ✅ | 支出 |
| 日期 | 格式: YYYY/MM/DD HH:MM 或 YYYY/MM/DD | ✅ | 2026/06/15 12:30 |
| 金额 | 数字 | ✅ | 25.5 |
| 类别 | 见常用类别 | ✅ | 食品酒水 |
| 子类别 | 见常用类别 | 可选 | 零食 |
| 账户 | 付款方式 | 可选 | 微信零钱 |
| 项目 | 归属项目 | 可选 | 弹性支出 |
| 成员 | 谁消费的 | 可选 | 本人 |
| 商家 | 消费场所 | 可选 | 拼多多 |
| 备注 | 补充说明 | 可选 | 买零食 |

**导入流程**：

1. 用户说"导入数据"或"导入CSV"
2. Agent 询问 CSV 文件路径（如果用户没提供）
3. 执行导入命令
4. 导入后建议用户说"学习"来分析数据

## 导出 (export)

```bash
python3 scripts/ledger_cli.py export '{"output":"report.csv","format":"csv","start_date":"2026-06-01","end_date":"2026-06-30"}'
```

参数：
- `output`: 输出文件路径 - 必填
- `format`: 格式 (csv/json) - 可选，默认csv
- `category`: 类别筛选 - 可选
- `start_date`: 开始日期 - 可选
- `end_date`: 结束日期 - 可选

## 数据分析 (analyze)

```bash
python3 scripts/ledger_cli.py analyze '{}'
```

分析用户数据，输出结构化摘要供 agent 学习。包含：
- 账户列表及使用频率
- 商家列表及使用频率
- 类别→子类别层级结构
- 成员列表
- 项目列表
- 商家→类别关联
- 账户→商家关联
- 字段使用率

## 对账指南 (reconcile)

```bash
python3 scripts/ledger_cli.py reconcile '{}'
```

