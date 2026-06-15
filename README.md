# Ledger - 个人记账系统

## 项目结构

```
ledger/
├── import_ledger.py      # CSV导入脚本
├── ledger_api.py         # CLI API
├── scripts/
│   └── ledger_cli.py     # picoclaw调用入口
└── tests/
    └── test_full.py      # 全面测试
```

## 目录说明

| 目录 | 用途 |
|------|------|
| `E:\sync\agentscode\ledger\` | 开发环境 |
| `E:\sync\agentscode\ledger-deploy\` | 部署包 |
| `E:\sync\agentscode\docker-ledger\` | 生产环境配置 |
| `D:\kezhe\.picoclaw\workspace\skills\ledger\` | 测试环境 |

## 快速开始

```bash
# 安装依赖（无第三方依赖，仅标准库）

# 导入CSV
python import_ledger.py your_data.csv

# 使用API
python ledger_api.py list
python ledger_api.py add --type expense --amount 100 --category 食品

# 设置多维度预算
python ledger_api.py budget_set --category 餐饮 --amount 500 --year 2026 --month 6 --dimension_type account --dimension_value xxx信用卡

# 创建预算模板
python ledger_api.py budget_template_create --template_name 吃饭模板 --category 餐饮 --template_amount 400 --dimension_type account --dimension_value xxx信用卡 --member 本人 --account xxx信用卡

# 查看模板并套用
python ledger_api.py budget_template_list
python ledger_api.py budget_template_apply --template_id 1 --year 2026 --month 6
```

## 说明

- 预算现在支持按分类、账户、成员、项目、商家等维度设置。
- 支持创建预算模板，后续相似场景可直接套用，避免重复输入。
- 系统也会根据你历史交易自动给出模板建议，用户确认后即可生成模板。

## 开发

```bash
# 运行测试
python test_full.py

# 检查覆盖率
python -m coverage run --source=ledger_api,import_ledger test_full.py
python -m coverage report
```
