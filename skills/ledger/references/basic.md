# 基础命令

所有命令通过 `python3 scripts/ledger_cli.py <command> '<json_args>'` 调用。

## 记账 (add)

```bash
python3 scripts/ledger_cli.py add '{"type":"支出","amount":25.5,"category":"食品酒水","subcategory":"零食","account":"微信零钱","note":"零食"}'
```

参数：
- `type`: 支出 或 收入 - 必填
- `amount`: 金额 - 必填
- `category`: 类别 - 必填
- `subcategory`: 子类别 - 可选
- `account`: 账户 - 可选
- `project`: 项目 - 可选
- `member`: 成员 - 可选
- `merchant`: 商家 - 可选
- `note`: 备注 - 可选
- `tag_ids`: 标签 ID 列表 [1, 2, 3] - 可选（需先创建标签获取 ID）
- `date`: 日期 (YYYY-MM-DD HH:MM:SS) - 可选，默认当前时间
- `force`: 强制插入（跳过重复检查）- 可选，默认false

## 查账 (list)

```bash
python3 scripts/ledger_cli.py list '{"limit":20}'
```

参数：
- `limit`: 显示条数 - 可选，默认20
- `include_deleted`: 包含已删除 - 可选，默认false

## 搜索 (search)

```bash
python3 scripts/ledger_cli.py search '{"keyword":"拼多多","search_type":"all","limit":50}'
```

参数：
- `keyword`: 搜索关键词 - 必填
- `search_type`: all/note/category/merchant - 可选，默认all
- `limit`: 返回条数 - 可选，默认50

## 筛选 (filter)

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

## 汇总 (summary)

```bash
python3 scripts/ledger_cli.py summary '{"year":2026,"month":6}'
```

参数：
- `year`: 年份 - 可选
- `month`: 月份 - 可选

## 统计 (stats)

```bash
python3 scripts/ledger_cli.py stats '{"year":2026,"month":6,"group_by":"category"}'
```

参数：
- `year`: 年份
- `month`: 月份
- `group_by`: category/account/month

## 列表查询

```bash
python3 scripts/ledger_cli.py accounts   # 列出所有账户
python3 scripts/ledger_cli.py categories  # 列出所有类别
python3 scripts/ledger_cli.py members     # 列出所有成员
```

