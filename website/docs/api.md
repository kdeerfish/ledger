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
| GET | `/api/transactions` | 交易列表（支持多维筛选：type/category/subcategory/account/project/member/merchant/tag_ids/keyword/start_date/end_date） |
| POST | `/api/transactions` | 新增交易（支持 tag_ids） |
| GET | `/api/transactions/<id>` | 获取单条交易（含 tags） |
| PUT | `/api/transactions/<id>` | 更新交易（支持 tag_ids） |
| DELETE | `/api/transactions/<id>` | 软删除 |
| POST | `/api/transactions/<id>/restore` | 恢复 |

### 🏷 标签

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/tags` | 标签列表（含 usage_count） |
| POST | `/api/tags` | 创建标签 `{"name":"xxx","color":"#6366f1"}` |
| DELETE | `/api/tags/<id>` | 删除标签 |
| GET | `/api/tags/<id>/transactions` | 某标签下的交易 |

### 📋 记账模板

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/templates` | 模板列表（按使用频次排序） |
| POST | `/api/templates` | 创建模板（支持 tag_names） |
| PUT | `/api/templates/<id>` | 更新模板 |
| DELETE | `/api/templates/<id>` | 删除模板 |
| POST | `/api/templates/<id>/use` | 使用模板（递增计数） |

### 💡 自动建议

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/suggestions?field=all` | 全部字段建议（categories/subcategories/accounts/merchants/projects/members + frequent） |
| GET | `/api/suggestions?field=accounts&keyword=微` | 带关键词筛选 |
| GET | `/api/categories/quick` | 常用子类别快速选择 |

### 📈 统计

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/summary?year=2026&month=6` | 收支汇总（含日均支出） |
| GET | `/api/stats?year=2026&group_by=category` | 多维度统计（支持 group_by: category/subcategory/account/merchant/project/member/month/tag/type） |
| GET | `/api/trends?year=2026&granularity=month` | 趋势数据（含累计趋势，granularity: day/week/month） |

### 💰 预算

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/budgets?year=2026&month=6` | 预算列表 |
| POST | `/api/budgets` | 设置预算 |
| GET | `/api/budgets/check` | 预算执行检查（含百分比） |

### 🏷 辅助数据

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/categories` | 类别/子类别层级列表 |
| GET | `/api/accounts` | 账户列表 |
| GET | `/api/members` | 成员列表 |
| GET | `/api/projects` | 项目列表 |
| GET | `/api/merchants` | 商家列表 |

## 示例

### 获取交易列表（含标签筛选）

```bash
curl "http://localhost:5800/api/transactions?limit=5&type=支出&tag_ids=1,2"
```

```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": 1,
        "date": "2026-06-15 10:00:00",
        "type": "支出",
        "amount": 100.0,
        "category": "食品",
        "subcategory": "零食",
        "account": "微信",
        "tags": [{"id": 1, "name": "餐饮", "color": "#ef4444"}]
      }
    ],
    "total": 1
  }
}
```

### 新增交易（含标签）

```bash
curl -X POST http://localhost:5800/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"type":"支出","amount":100,"category":"食品","account":"微信","note":"午餐","tag_ids":[1,2],"force":true}'
```

### 创建标签

```bash
curl -X POST http://localhost:5800/api/tags \
  -H "Content-Type: application/json" \
  -d '{"name":"餐饮","color":"#ef4444"}'
```

### 多维度统计

```bash
# 按标签统计
curl "http://localhost:5800/api/stats?year=2026&group_by=tag"

# 按商家统计
curl "http://localhost:5800/api/stats?year=2026&group_by=merchant"

# 按月趋势
curl "http://localhost:5800/api/trends?year=2026&granularity=month"
```

### 自动建议

```bash
curl "http://localhost:5800/api/suggestions?field=all"
```

## 错误码

| HTTP 状态码 | 说明 |
|-------------|------|
| `200` | 成功 |
| `400` | 请求参数错误 |
| `404` | 资源不存在 |
| `500` | 服务器内部错误 |
