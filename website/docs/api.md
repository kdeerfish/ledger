---
sidebar_position: 14
---

# 🔌 HTTP API 文档 (Go 版)

Ledger Go 版提供 **30+ RESTful API 端点**,响应结构与 Python 版 100% 兼容。

**Base URL**: `http://<host>:5800`

## 通用响应格式

```json
{ "success": true, "data": { ... } }
```

失败时:
```json
{ "success": false, "error": "..." }
```

带 HTTP 状态码 4xx/5xx。

## 端点分类

### 🩺 健康与元信息

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/health` | 健康检查,返回 `{status, db_path, version}` |
| GET | `/api/info` | 数据库元信息(总/活跃/软删数、日期范围、标签数) |

### 💰 交易

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/transactions` | 列表,支持 `limit/offset/include_deleted/type/category/account/project/member/merchant/keyword/tag_ids/year/month/start_date/end_date` |
| POST | `/api/transactions` | 新增(JSON body),返回 201 |
| GET | `/api/transactions/{id}` | 单条(含 tag 数组) |
| PUT | `/api/transactions/{id}` | 局部更新(白名单字段) |
| DELETE | `/api/transactions/{id}` | 软删除 |
| POST | `/api/transactions/{id}/restore` | 恢复软删 |
| GET | `/api/transactions/{id}/hard-delete?confirm=true` | 永久删除 |
| GET | `/api/transactions/search?keyword=...` | 关键词搜索 |

### 🏷 标签

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/tags` | 列表(含 `usage_count`) |
| POST | `/api/tags` | 创建 |
| DELETE | `/api/tags/{id}` | 删除(级联删关联) |
| GET | `/api/tags/{id}/transactions` | 该标签下交易 |

### 📋 模板

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/templates` | 列表 |
| POST | `/api/templates` | 创建 |
| PUT | `/api/templates/{id}` | 更新 |
| DELETE | `/api/templates/{id}` | 删除 |
| POST | `/api/templates/{id}/use` | 应用模板生成交易 |

### 💼 预算

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/budgets` | 列表(`year/month` 可选) |
| POST | `/api/budgets` | 设置(自动 upsert) |
| GET | `/api/budgets/check` | 执行情况(`spent/remaining/percentage`) |

### 📊 统计 / 报告

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/summary` | 收入/支出/结余/笔数 |
| GET | `/api/stats` | 按 `group_by` 分组(支持 `sub_group` 二级) |
| GET | `/api/suggestions` | 自动补全数据 |
| GET | `/api/accounts` / `/api/categories` / `/api/members` | distinct 值列表 |
| GET | `/api/analyze` | 交叉统计报告 |

### 📤 导出

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/export?format=csv\|json` | 导出筛选结果 |

## 详细示例

### 新增交易

```bash
curl -X POST http://localhost:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "支出",
    "amount": 25.5,
    "category": "食品",
    "subcategory": "午餐",
    "account": "微信",
    "note": "公司食堂",
    "trans_date": "2026-06-19 12:00:00",
    "tags": ["日常", "工作日"]
  }'
```

响应:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "type": "支出",
    "amount": 25.5,
    "category": "食品",
    "subcategory": "午餐",
    "account": "微信",
    "note": "公司食堂",
    "trans_date": "2026-06-19 12:00:00",
    "is_deleted": false,
    "tag_ids": [1, 2],
    "tags": ["日常", "工作日"]
  }
}
```

### 列表 + 筛选

```bash
# 最近 10 条
curl 'http://localhost:5800/api/transactions?limit=10'

# 6 月食品类支出
curl 'http://localhost:5800/api/transactions?category=食品&start_date=2026-06-01&end_date=2026-06-30'

# 按 tag 筛选
curl 'http://localhost:5800/api/transactions?tag_ids=1,2'
```

### 预算检查

```bash
curl 'http://localhost:5800/api/budgets/check?year=2026&month=6'
```

响应:
```json
{
  "success": true,
  "data": {
    "checks": [
      {
        "budget_id": 1,
        "category": "食品",
        "year": 2026,
        "month": 6,
        "dimension_type": "category",
        "dimension_value": "",
        "budget": 1000,
        "spent": 145.5,
        "remaining": 854.5,
        "percentage": 14.55
      }
    ]
  }
}
```

## 错误码

| 状态 | 含义 |
|------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 参数错误(JSON 解析失败、字段白名单) |
| 404 | 资源不存在 |
| 409 | 重复(同日/同金额/同类型/同类别) |
| 500 | 内部错误 |

## 与 Python 版兼容性

Go 版的 API 路径、参数、响应结构与 Python 版**完全一致**:
- 同一路径 (`/api/transactions`)
- 同一参数名 (`limit/offset/category/...`)
- 同一响应结构 (`{success, data, error}`)
- 同一错误码

因此原 Python 版的前端和 Agent 代码**无需修改**即可对接 Go 版。
