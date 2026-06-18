# 数据命令

## 导入CSV

Ledger 运行在 Docker 中，CSV 导入方式变了：

**方式一：通过 Docker 数据卷**

```bash
# 1. 把 CSV 文件放到宿主机的数据目录
cp mymoney.csv /volume1/docker/ledger/data/

# 2. 进入容器执行导入
docker exec -it ledger python scripts/import_ledger.py /data/mymoney.csv
```

**方式二：宿主机直接运行（临时）**

```bash
# 停止容器，把 ledger.db 复制到项目目录
cp /volume1/docker/ledger/data/ledger.db .
pip install flask flask-cors
python scripts/import_ledger.py data.csv
# 导入完成后再把 ledger.db 复制回去
cp ledger.db /volume1/docker/ledger/data/
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

## 导出 (export)

```bash
python3 scripts/ledger_cli.py export '{"format":"csv","start_date":"2026-06-01","end_date":"2026-06-30"}'
```

参数：
- `format`: 格式 (csv/json) - 可选，默认json
- `category`: 类别筛选 - 可选
- `start_date`: 开始日期 - 可选
- `end_date`: 结束日期 - 可选

> 注意：导出数据通过 API 返回，不会写入文件。需手动保存到文件。

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

## 连接检查 (health)

```bash
python3 scripts/ledger_cli.py health '{}'
```

检查 API 连接是否正常，返回数据库状态和记录数。
