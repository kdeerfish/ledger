# 数据命令

## 导入 CSV

Ledger 运行在 Docker 中，CSV 导入方式：

```bash
# 1. 把 CSV 文件放到宿主机的数据目录
cp mymoney.csv /volume1/docker/ledger/data/

# 2. 进入容器执行导入
docker exec -it ledger python scripts/import_ledger.py /data/mymoney.csv
```

**CSV 格式要求**（第一行必须是表头）：

| 列名 | 说明 | 必填 | 示例 |
|------|------|------|------|
| 交易类型 | 支出 或 收入 | ✅ | 支出 |
| 日期 | YYYY/MM/DD HH:MM 或 YYYY/MM/DD | ✅ | 2026/06/15 12:30 |
| 金额 | 数字 | ✅ | 25.5 |
| 类别 | 见常用类别 | ✅ | 食品酒水 |
| 子类别 | 见常用类别 | 可选 | 零食 |
| 账户 | 付款方式 | 可选 | 微信零钱 |
| 项目 | 归属项目 | 可选 | 弹性支出 |
| 成员 | 谁消费的 | 可选 | 本人 |
| 商家 | 消费场所 | 可选 | 拼多多 |
| 备注 | 补充说明 | 可选 | 买零食 |

## 导出数据

```bash
# JSON 格式
curl "http://127.0.0.1:5800/api/export?format=json&start_date=2026-06-01&end_date=2026-06-30"

# CSV 格式
curl "http://127.0.0.1:5800/api/export?format=csv&category=食品酒水"
```

参数：`format`（json/csv）、`category`、`start_date`、`end_date`

## 数据分析

```bash
curl http://127.0.0.1:5800/api/analyze
```

输出结构化摘要：账户列表、商家列表、类别层级、成员列表、项目列表、字段使用率等。

## 健康检查

```bash
curl http://127.0.0.1:5800/api/health
```

返回数据库状态、记录数、版本号。

## 数据库信息

```bash
curl http://127.0.0.1:5800/api/info
```
