---
sidebar_position: 6
---

# 🔍 搜索与筛选 (CLI)

## 关键词搜索

```bash
ledger misc search --keyword 午餐                     # 全局(默认搜索备注+类别+商家+子类别)
ledger misc search --keyword 711 --search-type merchant  # 仅商家
ledger misc search --keyword 早餐 --search-type note
ledger misc search --keyword 食品 --search-type category
```

| Flag | 简写 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--keyword` | `-k` | ✅ | | 关键词 |
| `--search-type` | | | `all` | all / note / category / merchant |
| `--limit` | `-l` | | 50 | 限制条数 |

## 多维过滤

```bash
ledger misc filter \
  --category 食品 \
  --account 微信 \
  --start-date 2026-01-01 \
  --end-date 2026-06-30 \
  --limit 100
```

可用过滤字段:
- `--category`
- `--subcategory`
- `--account`
- `--project`
- `--member`
- `--merchant`
- `--start-date` / `--end-date` (格式 `YYYY-MM-DD`)

## 搜索 vs 过滤

| 维度 | `search` | `filter` |
|------|----------|----------|
| 输入 | 关键词 + search_type | 多个等值过滤 |
| 适用 | 模糊查找(包含子串) | 精确匹配 |
| 性能 | LIKE 扫描 | 索引命中 |
