---
sidebar_position: 9
---

# 📋 记录模板（一键记账）

创建模板后，`template_apply` 会自动按模板参数记账，无需每次输入完整命令。

```bash
# 创建模板
python scripts/cli.py template_create \
  --template_name "通勤" \
  --type 支出 \
  --template_amount 6 \
  --category 交通 --subcategory 地铁 --account 微信 --note "地铁通勤"

# 列出模板
python scripts/cli.py template_list

# 应用模板（自动记账）
python scripts/cli.py template_apply --template_id 1
python scripts/cli.py template_apply --template_id 1 --template_amount 7  # 覆盖金额

# 更新 / 删除
python scripts/cli.py template_update --template_id 1 --template_name "通勤（涨价后）"
python scripts/cli.py template_delete --template_id 1

# 智能推荐
python scripts/cli.py template_suggest --template_limit 5
```
