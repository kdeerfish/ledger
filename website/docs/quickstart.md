---
sidebar_position: 2
---

# 🚀 快速开始

## 安装

```bash
# 1. 安装开发依赖
pip install -e ".[dev,lint]"

# 2. 配置环境变量（可选，留空使用默认值）
cp .env.example .env

# 3. 导入随手记 CSV（可选）
python scripts/import_ledger.py data/sample/mymoney_data.csv

# 4. 开始记账！
python scripts/cli.py add --type 支出 --amount 100 --category 食品 --account 微信
```

## 一分钟上手

```bash
# 查看最近交易
python scripts/cli.py list

# 查看收支汇总
python scripts/cli.py summary

# 搜索交易
python scripts/cli.py search --keyword 午餐

# 按类别筛选
python scripts/cli.py filter --category 食品
```

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `python scripts/cli.py list` | 查看最近交易 |
| `python scripts/cli.py add --type 支出 --amount 100 --category 食品` | 记一笔支出 |
| `python scripts/cli.py summary` | 收支汇总 |
| `python scripts/cli.py search --keyword xxx` | 搜索交易 |
| `python scripts/cli.py stats --group_by category` | 按类别统计 |

## Web 界面

```bash
pip install flask flask-cors
python web/run.py
```

访问 [http://localhost:5800](http://localhost:5800)

详细的 CLI 命令参考请见 [CLI 命令参考](/docs/cli/transactions) 页面。
