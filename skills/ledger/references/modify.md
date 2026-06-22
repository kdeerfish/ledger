# 修改命令

## 修改记录

```bash
# 单字段修改
curl -X PUT $BASE_URL/api/transactions/123 \
  -H 'Content-Type: application/json' \
  -d '{"field":"amount","value":50.0}'

# 多字段修改
curl -X PUT $BASE_URL/api/transactions/123 \
  -H 'Content-Type: application/json' \
  -d '{"amount":50,"category":"餐饮","note":"修改备注"}'
```

可修改字段：`amount`、`category`、`subcategory`、`account`、`project`、`member`、`merchant`、`note`、`trans_date`、`type`、`tag_ids`

## 删除记录

```bash
curl -X DELETE $BASE_URL/api/transactions/123
```

软删除，可恢复。

## 恢复记录

```bash
curl -X POST $BASE_URL/api/transactions/123/restore
```
