---
name: Ledger (记账系统)
description: Use when the user wants to "记账", "记一笔", "查账", "查记录", "查支出", "查收入", "搜索账单", "统计", "预算", "导出账单", "对账", "转账", "数据矫正", "记一笔支出", "记一笔收入", "查看账户", "查看余额", "本月花了多少", "上个月支出", or any personal finance/accounting tasks. Provides complete CLI tools for managing personal finances via bash commands.
version: 1.0.0
---

# Ledger - 个人记账系统

## 快速开始

所有命令通过 `python3 scripts/ledger_cli.py <command> '<json_args>'` 调用。

## 命令列表

### 记账 (add)

```bash
python3 scripts/ledger_cli.py add '{"type":"expense","amount":25.5,"category":"食品酒水","subcategory":"零食","account":"微信零钱","note":"零食"}'
```

参数：
- `type`: expense(支出) 或 income(收入) - 必填
- `amount`: 金额 - 必填
- `category`: 类别 - 必填
- `subcategory`: 子类别 - 可选
- `account`: 账户 - 可选
- `project`: 项目 - 可选
- `member`: 成员 - 可选
- `merchant`: 商家 - 可选
- `note`: 备注 - 可选
- `date`: 日期 (YYYY-MM-DD HH:MM:SS) - 可选，默认当前时间

### 查账 (list)

```bash
python3 scripts/ledger_cli.py list '{"limit":20}'
```

参数：
- `limit`: 显示条数 - 可选，默认20
- `include_deleted`: 包含已删除 - 可选，默认false

### 搜索 (search)

```bash
python3 scripts/ledger_cli.py search '{"keyword":"拼多多","search_type":"all","limit":50}'
```

参数：
- `keyword`: 搜索关键词 - 必填
- `search_type`: all/note/category/merchant - 可选，默认all
- `limit`: 返回条数 - 可选，默认50

### 筛选 (filter)

```bash
python3 scripts/ledger_cli.py filter '{"category":"食品酒水","start_date":"2026-06-01","end_date":"2026-06-30"}'
```

参数：
- `category`: 类别筛选
- `account`: 账户筛选
- `member`: 成员筛选
- `merchant`: 商家筛选
- `project`: 项目筛选
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)
- `limit`: 返回条数 - 可选，默认50

### 汇总 (summary)

```bash
python3 scripts/ledger_cli.py summary '{"year":2026,"month":6}'
```

参数：
- `year`: 年份 - 可选
- `month`: 月份 - 可选

### 统计 (stats)

```bash
python3 scripts/ledger_cli.py stats '{"year":2026,"month":6,"group_by":"category"}'
```

参数：
- `year`: 年份
- `month`: 月份
- `group_by`: category/account/month

### 修改 (update)

```bash
python3 scripts/ledger_cli.py update '{"id":123,"field":"amount","value":50.0}'
```

参数：
- `id`: 记录ID - 必填
- `field`: 修改字段 (amount/category/subcategory/account/project/member/merchant/note/trans_date) - 必填
- `value`: 新值 - 必填

### 删除 (delete)

```bash
python3 scripts/ledger_cli.py delete '{"id":123}'
```

软删除，可恢复。

### 恢复 (restore)

```bash
python3 scripts/ledger_cli.py restore '{"id":123}'
```

### 预算 (budget_set/budget_check)

```bash
# 设置预算
python3 scripts/ledger_cli.py budget_set '{"category":"食品酒水","amount":1000,"year":2026,"month":6}'

# 按账户维度设置预算
python3 scripts/ledger_cli.py budget_set '{"category":"餐饮","amount":500,"dimension_type":"account","dimension_value":"xxx信用卡","year":2026,"month":6}'

# 查看预算
python3 scripts/ledger_cli.py budget_check '{"year":2026,"month":6}'
```

### 预算模板 (budget_template_create/list/update/delete/apply/suggest)

```bash
python3 scripts/ledger_cli.py budget_template_create '{"name":"吃饭模板","description":"日常吃饭","category":"餐饮","amount":400,"dimension_type":"account","dimension_value":"xxx信用卡"}'
python3 scripts/ledger_cli.py budget_template_list '{}'
python3 scripts/ledger_cli.py budget_template_apply '{"id":1,"year":2026,"month":6}'
python3 scripts/ledger_cli.py budget_template_suggest '{"limit":3}'
```

### 导出 (export)

```bash
python3 scripts/ledger_cli.py export '{"output":"report.csv","format":"csv","start_date":"2026-06-01","end_date":"2026-06-30"}'
```

### 列表查询

```bash
python3 scripts/ledger_cli.py accounts   # 列出所有账户
python3 scripts/ledger_cli.py categories  # 列出所有类别
python3 scripts/ledger_cli.py members     # 列出所有成员
```

### 导入CSV (import)

```bash
python3 scripts/ledger_cli.py import '{"file":"path/to/data.csv"}'
```

### 对账指南 (reconcile)

```bash
python3 scripts/ledger_cli.py reconcile '{}'
```

## 常用场景示例

### 用户说"今天花了30块钱买零食"
```bash
python3 scripts/ledger_cli.py add '{"type":"expense","amount":30,"category":"食品酒水","subcategory":"零食","account":"微信零钱","note":"零食"}'
```

### 用户说"帮我看看这个月花了多少"
```bash
python3 scripts/ledger_cli.py summary '{"year":2026,"month":6}'
```

### 用户说"上个月在拼多多买了多少东西"
```bash
python3 scripts/ledger_cli.py search '{"keyword":"拼多多","search_type":"merchant"}'
python3 scripts/ledger_cli.py filter '{"merchant":"拼多多","start_date":"2026-05-01","end_date":"2026-05-31"}'
```

### 用户说"把刚才那笔记错了，改成50"
```bash
python3 scripts/ledger_cli.py update '{"id":123,"field":"amount","value":50}'
```

### 用户说"设个预算，食品酒水每月1000块"
```bash
python3 scripts/ledger_cli.py budget_set '{"category":"食品酒水","amount":1000}'
```

### 用户说"给我看看这个月的支出统计"
```bash
python3 scripts/ledger_cli.py stats '{"year":2026,"month":6,"group_by":"category"}'
```

### 用户说"我有哪些银行卡"
```bash
python3 scripts/ledger_cli.py accounts
```

### 用户说"记一笔收入，工资5000"
```bash
python3 scripts/ledger_cli.py add '{"type":"income","amount":5000,"category":"职业收入","account":"招商银行","note":"工资"}'
```

## 成员说明

- `本人` - 用户本人
- `fish` - 用户的伴侣
- `妈妈` - 用户的母亲
- `家庭公用` - 家庭共同支出

## 常用类别

### 支出
- 食品酒水 (零食/早午晚餐/水果/饮料/甜品/牛奶/烟酒茶)
- 居家物业 (日常用品/房租水电/维修保养/柴米油盐/家电家私)
- 行车交通 (打车租车/公共交通/高铁长途)
- 衣服饰品 (衣服裤子/鞋帽包包/居家穿着)
- 医疗保健 (药品费)
- 休闲娱乐 (数码3C/运动装备)
- 交流通讯 (网费/手机费)
- 学习进修 (学无止境)
- 人情往来 (礼尚往来/网络红包)
- 其他杂项
- 金融保险 (保险)
- 自由职业 (大模型费用)
- 外贸电商 (设备/运费/进货)
- 项目投入 (批发矿泉水/生意投入)

### 收入
- 职业收入 (卖水收入)
- 其他收入 (意外来钱/薅羊毛)

## 输出格式

所有命令返回JSON格式：
```json
{
  "success": true,
  "data": "命令输出内容",
  "error": null
}
```

## 脚本位置

脚本路径通过环境变量 `LEDGER_PATH` 配置，未设置时自动检测当前目录。

```bash
# 设置环境变量（可选）
export LEDGER_PATH=/path/to/ledger
```
