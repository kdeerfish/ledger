---
sidebar_position: 14
---

# 🔌 API Reference

**Base URL:** `http://<host>:5800`

## Response Format

```json
{
  "success": true,
  "data": { ... }
}

// Error:
{
  "success": false,
  "error": "Error message"
}
```

## Endpoints

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/info` | System info |

### Transactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/transactions` | List |
| POST | `/api/transactions` | Create |
| PUT | `/api/transactions/<id>` | Update |
| DELETE | `/api/transactions/<id>` | Soft delete |
| GET | `/api/transactions/search` | Search |
| GET | `/api/transactions/filter` | Filter |

### Statistics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/summary` | Income/Expense summary |
| GET | `/api/stats` | Grouped statistics |

### Budgets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/budgets` | List budgets |
| POST | `/api/budgets` | Set budget |

### Utilities

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/categories` | Categories list |
| GET | `/api/accounts` | Accounts list |

## Examples

### List transactions

```bash
curl "http://localhost:5800/api/transactions?limit=5"
```

### Add transaction

```bash
curl -X POST http://localhost:5800/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"type":"expense","amount":100,"category":"食品","account":"微信","note":"lunch"}'
```

### Summary

```bash
curl "http://localhost:5800/api/summary?year=2026&month=7"
```

## HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad request |
| `404` | Not found |
| `500` | Internal error |
