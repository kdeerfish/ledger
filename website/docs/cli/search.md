---
sidebar_position: 6
---

# 🔍 搜索与筛选

## 搜索

```bash
python scripts/cli.py search --keyword 午餐                    # 全局搜索
python scripts/cli.py search --keyword 午餐 --search_type note # 按备注
python scripts/cli.py search --keyword 食品 --search_type category # 按类别
python scripts/cli.py search --keyword 711 --search_type merchant  # 按商家
```

搜索类型 `search_type` 可选值：

| 值 | 说明 |
|----|------|
| `all` | 全局搜索（默认） |
| `note` | 按备注搜索 |
| `category` | 按类别/子类别搜索 |
| `merchant` | 按商家搜索 |

## 筛选

```bash
python scripts/cli.py filter --category 食品
python scripts/cli.py filter --account 微信 --start_date 2026-01-01 --end_date 2026-06-30
python scripts/cli.py filter --member 本人 --merchant 711
python scripts/cli.py filter --category 食品 --account 支付宝 --limit 100
```
