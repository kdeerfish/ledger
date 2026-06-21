# 字段用途说明

## 字段含义（重要！）

记账时必须正确区分每个字段的含义：

| 字段 | 含义 | 判断标准 | 常见错误 |
|------|------|----------|----------|
| `account` | 账户 = 付款方式/资金来源 | 钱从哪里扣/收到哪里 → 微信零钱、支付宝、银行卡 | ❌ 把"京东"当账户 |
| `merchant` | 商家 = 消费场所/平台 | 在哪里花的钱 → 京东、拼多多、美团、滴滴 | ❌ 把"微信"当商家 |
| `category` | 类别 = 花在什么类型的东西上 | 消费的类型 → 食品酒水、交通、服饰 | ❌ 把"零食"当类别 |
| `subcategory` | 子类别 = 具体花在什么上 | 类别下的细分 → 零食、早午餐、水果 | ❌ 把"食品酒水"当子类别 |
| `project` | 项目 = 归属的长期项目/生意 | 不是商家！是你的项目 → 电商、AI、外贸 | ❌ 把"拼多多"当项目 |
| `member` | 成员 = 谁花了这笔钱 | 谁的消费 → 本人、fish、妈妈 | |
| `tag` | 标签 = 自定义分类 | 跨类别的标记 → 餐饮、出差、必须要花的 | ❌ 把类别当标签 |

## 不确定时怎么办？

1. **查记忆**：参考之前"学习"保存的用户习惯
2. **查数据**：运行 analyze 查看用户的实际数据分布
3. **问用户**：不确定就问"这个应该填在哪里？"

## 场景示例

| 用户说 | merchant | category | subcategory | account | note |
|--------|----------|----------|-------------|---------|------|
| "京东买了200块零食" | 京东 | 食品酒水 | 零食 | (用户习惯) | |
| "微信支付打车30块" | 滴滴 | 行车交通 | 打车租车 | 微信零钱 | |
| "招商银行工资到账5000" | | 职业收入 | 工资收入 | 招商银行 | 工资 |
| "拼多多买了日用品" | 拼多多 | 居家物业 | 日常用品 | (用户习惯) | |
| "美团外卖35块" | 美团 | 食品酒水 | 早午晚餐 | (用户习惯) | |

## 常用场景

### 用户说"导入数据"或"导入CSV"

**Agent 应回复**：Ledger 运行在 Docker 中，请把 CSV 文件放到 NAS 上，然后我来帮你导入。

```bash
# 1. 用户把 CSV 放到数据目录
# 2. 执行容器内导入
docker exec -it ledger python scripts/import_ledger.py /data/your-file.csv
```

导入完成后建议：
> 导入完成！建议说"学习"来分析你的数据，这样我就能记住你的账户、商家、类别等习惯。

### 用户说"学习"或"分析我的数据"

```bash
curl http://127.0.0.1:5800/api/analyze
```

然后用 `remember` 保存关键模式到记忆。

### 用户说"今天花了30块钱买零食"

```bash
curl -X POST http://127.0.0.1:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"支出","amount":30,"category":"食品酒水","subcategory":"零食","account":"微信零钱","note":"零食"}'
```

### 用户说"帮我看看这个月花了多少"

```bash
curl "http://127.0.0.1:5800/api/summary?year=2026&month=6"
```

### 用户说"上个月在拼多多买了多少东西"

```bash
curl "http://127.0.0.1:5800/api/transactions/search?keyword=拼多多&search_type=merchant"
curl "http://127.0.0.1:5800/api/transactions?merchant=拼多多&start_date=2026-05-01&end_date=2026-05-31"
```

### 用户说"把刚才那笔记错了，改成50"

```bash
curl -X PUT http://127.0.0.1:5800/api/transactions/123 \
  -H 'Content-Type: application/json' \
  -d '{"field":"amount","value":50}'
```

### 用户说"设个预算，食品酒水每月1000块"

```bash
curl -X POST http://127.0.0.1:5800/api/budgets \
  -H 'Content-Type: application/json' \
  -d '{"category":"食品酒水","amount":1000}'
```

### 用户说"给我看看这个月的支出统计"

```bash
curl "http://127.0.0.1:5800/api/stats?group_by=category&year=2026&month=6"
```

### 用户说"我有哪些银行卡"

```bash
curl http://127.0.0.1:5800/api/accounts
```

### 用户说"记一笔收入，工资5000"

```bash
curl -X POST http://127.0.0.1:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"收入","amount":5000,"category":"职业收入","account":"招商银行","note":"工资"}'
```

### 用户说"用模板记一笔零食"

```bash
# 先查看模板列表
curl http://127.0.0.1:5800/api/templates
# 然后使用模板
curl -X POST http://127.0.0.1:5800/api/templates/1/use
```

### 用户说"帮我看看有哪些模板"

```bash
curl http://127.0.0.1:5800/api/templates
```
