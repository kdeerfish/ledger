---
layout: default
title: API 文档
---

# 🔌 API 文档

Ledger Web 服务提供 RESTful API，所有端点返回 JSON 格式。

**Base URL:** `http://<host>:5800`

---

## 通用响应格式

**成功：**
```json
{"success": true, "data": {...}}
```

**失败：**
```json
{"success": false, "error": "错误描述"}
```

---

## 🩺 健康检查

### `GET /api/health`

```bash
curl http://localhost:5800/api/health
```

```json
{"success": true, "data": {"status": "ok"}}
```

### `GET /api/info`

```bash
curl http://localhost:5800/api/info
```

```json
{"success": true, "data": {"web_host": "0.0.0.0", "web_port": "5800", "db_path": "/data/ledger.db"}}
```

---

## 📊 交易管理

### `GET /api/transactions`

获取交易列表。

**参数：** `limit` (默认 20), `include_deleted` (可选)

```bash
curl "http://localhost:5800/api/transactions?limit=5"
```

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "trans_date": "2026-06-15",
      "type": "支出",
      "amount": 100.0,
      "category": "食品",
      "subcategory": "零食",
      "account": "微信",
      "note": "零食",
      "is_deleted": false
    }
  ]
}
```

### `POST /api/transactions`

新增交易。

```bash
curl -X POST http://localhost:5800/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"type":"支出","amount":100,"category":"食品","account":"微信","note":"午餐"}'
```

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | `支出` 或 `收入` |
| `amount` | number | 是 | 金额 |
| `category` | string | 否 | 类别 |
| `subcategory` | string | 否 | 子类别 |
| `account` | string | 否 | 账户 |
| `project` | string | 否 | 项目 |
| `member` | string | 否 | 成员 |
| `merchant` | string | 否 | 商家 |
| `note` | string | 否 | 备注 |
| `trans_date` | string | 否 | 日期，默认当前时间 |

### `PUT /api/transactions/<id>`

更新交易。

```bash
curl -X PUT http://localhost:5800/api/transactions/1 \
  -H "Content-Type: application/json" \
  -d '{"field":"amount","value":50}'
```

### `DELETE /api/transactions/<id>`

软删除交易。

```bash
curl -X DELETE http://localhost:5800/api/transactions/1
```

### `POST /api/transactions/<id>/restore`

恢复已删除交易。

```bash
curl -X POST http://localhost:5800/api/transactions/1/restore
```

### `DELETE /api/transactions/<id>/hard`

物理删除（不可恢复）。

```bash
curl -X DELETE "http://localhost:5800/api/transactions/1/hard?confirm=true"
```

---

## 🔍 搜索与筛选

### `GET /api/transactions/search`

```bash
curl "http://localhost:5800/api/transactions/search?keyword=午餐&type=note&limit=10"
```

**参数：** `keyword` (必填), `type` (all/note/category/merchant), `limit`

### `GET /api/transactions/filter`

```bash
curl "http://localhost:5800/api/transactions/filter?category=食品&account=微信&start_date=2026-01-01&end_date=2026-06-30"
```

---

## 📈 统计

### `GET /api/summary`

```bash
curl "http://localhost:5800/api/summary?year=2026&month=7"
```

```json
{
  "success": true,
  "data": {
    "income": 5000.0,
    "expense": 3200.0,
    "balance": 1800.0,
    "period": "2026-7"
  }
}
```

### `GET /api/statistics`

```bash
curl "http://localhost:5800/api/statistics?year=2026&group_by=category"
```

**参数：** `year`, `month`, `group_by` (category/account/month)

---

## 💰 预算

### `GET /api/budgets`

获取某月预算列表。

```bash
curl "http://localhost:5800/api/budgets?year=2026&month=7"
```

### `POST /api/budgets`

设置预算。

```bash
curl -X POST http://localhost:5800/api/budgets \
  -H "Content-Type: application/json" \
  -d '{"category":"食品","amount":1000,"year":2026,"month":7}'
```

---

## 🏷 辅助接口

### `GET /api/categories`

```bash
curl http://localhost:5800/api/categories
```

### `GET /api/accounts`

```bash
curl http://localhost:5800/api/accounts
```

---

## 错误码

| HTTP 状态码 | 说明 |
|-------------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
