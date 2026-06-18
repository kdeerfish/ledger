---
sidebar_position: 14
---

# 🔌 API 文档

Ledger Web 服务提供 RESTful API，所有端点返回 JSON 格式。

**Base URL:** `http://<host>:5800`

## 通用响应格式

```json
{
  "success": true,
  "data": { ... }
}
```

失败时：

```json
{
  "success": false,
  "error": "错误描述"
}
```

## 端点一览

### 🩺 系统

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/info` | 系统信息 |

### 📊 交易

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/transactions` | 交易列表 |
| POST | `/api/transactions` | 新增交易 |
| GET | `/api/transactions/<id>` | 获取单条交易 |
| PUT | `/api/transactions/<id>` | 更新交易 |
| DELETE | `/api/transactions/<id>` | 软删除 |
| POST | `/api/transactions/<id>/restore` | 恢复 |
| DELETE | `/api/transactions/<id>/hard` | 物理删除 |
| GET | `/api/transactions/search` | 搜索 |
| GET | `/api/transactions/filter` | 筛选 |

### 📈 统计

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/summary` | 收支汇总 |
| GET | `/api/stats` | 多维度统计 |

### 💰 预算

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/budgets` | 预算列表 |
| POST | `/api/budgets` | 设置预算 |
| GET | `/api/budgets/check` | 预算执行检查 |

### 🏷 辅助

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/categories` | 类别列表 |
| GET | `/api/accounts` | 账户列表 |

## 示例

### 获取交易列表

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

### 新增交易

```bash
curl -X POST http://localhost:5800/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"type":"支出","amount":100,"category":"食品","account":"微信","note":"午餐"}'
```

### 收支汇总

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

## 错误码

| HTTP 状态码 | 说明 |
|-------------|------|
| `200` | 成功 |
| `400` | 请求参数错误 |
| `404` | 资源不存在 |
| `500` | 服务器内部错误 |
