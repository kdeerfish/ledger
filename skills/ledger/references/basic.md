# 基础命令

所有命令通过 HTTP API 调用，Base URL 通过环境变量 `$BASE_URL` 解析（详见主文档 [SKILL.md](../SKILL.md) 的「Base URL 解析」章节）

## 记账

```bash
curl -X POST $BASE_URL/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"支出","amount":25.5,"category":"食品酒水","subcategory":"零食","account":"微信零钱","note":"零食"}'
```

参数：
- `type`: 支出 或 收入 - 可选，默认支出
- `amount`: 金额 - 必填，正数
- `category`: 类别 - 可选
- `subcategory`: 子类别 - 可选
- `account`: 账户 - 可选
- `project`: 项目 - 可选
- `member`: 成员 - 可选
- `merchant`: 商家 - 可选
- `note`: 备注 - 可选
- `tag_ids`: 标签 ID 列表 [1, 2, 3] - 可选
- `date`: 日期 (YYYY-MM-DD HH:MM:SS) - 可选，默认当前时间
- `force`: 强制插入（跳过重复检查）- 可选，默认 false

## 查账

```bash
curl "$BASE_URL/api/transactions?limit=20"
```

参数：`limit`、`offset`、`include_deleted`、`type`、`category`、`account`、`member`、`merchant`、`keyword`、`tag_ids`、`year`、`month`、`start_date`、`end_date`

## 搜索

```bash
curl "$BASE_URL/api/transactions/search?keyword=拼多多&search_type=all&limit=50"
```

`search_type`: `all`（默认）/ `note` / `category` / `merchant`

## 汇总

```bash
curl "$BASE_URL/api/summary?year=2026&month=6"
```

参数：`year`、`month`（均可选）

## 统计

```bash
curl "$BASE_URL/api/stats?group_by=category&year=2026&month=6"
```

`group_by`: `category` / `subcategory` / `account` / `merchant` / `project` / `member` / `month` / `tag` / `type`

## 枚举查询

```bash
curl $BASE_URL/api/accounts
curl $BASE_URL/api/categories
curl $BASE_URL/api/members
curl $BASE_URL/api/projects
curl $BASE_URL/api/merchants
```
