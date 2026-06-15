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
```

## 开发

```bash
# 运行测试
python test_full.py

# 检查覆盖率
python -m coverage run --source=ledger_api,import_ledger test_full.py
python -m coverage report
```
