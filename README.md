# 📒 Ledger - 个人记账系统

支持收支管理、预算规划、多维度统计的 CLI 记账工具。

## 目录结构

```
ledger/
├── ledger_modules/          # 核心模块包
│   ├── __init__.py          # 统一导出
│   ├── db.py                # 数据库初始化/迁移
│   ├── transactions.py      # 交易 CRUD / 搜索 / 筛选 / 导出 / 统计
│   └── budgets.py           # 预算 / 多维度预算 / 模板
├── scripts/                 # 命令行入口
│   ├── cli.py               # 统一的 CLI 入口（委托 ledger_modules）
│   └── import_ledger.py     # CSV 导入脚本
├── tests/                   # 自动化测试（pytest）
│   ├── conftest.py          # 共享 fixture（自动管理临时 DB）
│   ├── test_db.py           # 数据库表结构测试
│   ├── test_transactions.py # 交易 CRUD / 搜索 / 筛选 / 导出 / 统计
│   ├── test_budgets.py      # 预算 / 多维度 / 模板 CRUD
│   └── test_integration.py  # 端到端工作流 + CSV 导入
├── data/
│   └── sample/              # 示例数据（随手记 CSV 导出）
├── ledger-skills/           # Claude Code 自定义技能
├── pyproject.toml            # 项目配置 / pytest / coverage / ruff
├── Makefile                  # 常用命令快捷入口
├── .gitignore
├── .vscode/
│   └── settings.json
└── ledger.db                 # SQLite 数据库（运行时生成）
```

## 快速开始

```bash
# 1. 安装开发依赖
pip install -e ".[dev,lint]"

# 2. 导入随手记 CSV
python scripts/import_ledger.py data/sample/mymoney_data_20260614203414.csv

# 3. 查看最近交易
python scripts/cli.py list

# 4. 添加一笔支出
python scripts/cli.py add --type expense --amount 100 --category 食品 --account 微信

# 5. 查看本月收支汇总
python scripts/cli.py summary --year 2026 --month 6

# 6. 设置预算
python scripts/cli.py budget_set --category 食品 --amount 1000 --year 2026 --month 6

# 7. 按账户维度设置预算
python scripts/cli.py budget_set --category 餐饮 --amount 500 --dimension_type account --dimension_value xxx信用卡
```

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `python scripts/cli.py add ...` | 记一笔 |
| `python scripts/cli.py list` | 查看最近交易 |
| `python scripts/cli.py summary` | 收支汇总 |
| `python scripts/cli.py search --keyword xxx` | 搜索 |
| `python scripts/cli.py filter --category 食品` | 筛选 |
| `python scripts/cli.py update --id 1 --field amount --value 50` | 修改 |
| `python scripts/cli.py delete --id 1` | 软删除 |
| `python scripts/cli.py restore --id 1` | 恢复 |
| `python scripts/cli.py budget_set ...` | 设置预算 |
| `python scripts/cli.py budget_check` | 检查预算 |
| `python scripts/cli.py budget_template_create ...` | 创建预算模板 |
| `python scripts/cli.py export --output report.csv` | 导出 |
| `python scripts/cli.py stats` | 统计分析 |

## 测试

```bash
# 运行所有测试
make test

# 运行特定测试
python -m pytest tests -v -k "test_budget"

# 查看覆盖率
make coverage

# 打开 HTML 覆盖率报告
make coverage-view
```

## 开发

```bash
# 代码检查
make lint

# 自动修复
make lint-fix

# 格式检查
make format

# 清理缓存
make clean
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LEDGER_DB_PATH` | 数据库路径 | `./ledger.db` |

## 技术栈

- Python 3.10+（仅标准库，零第三方依赖）
- SQLite 持久化
- pytest / pytest-cov 测试
- ruff 代码检查
