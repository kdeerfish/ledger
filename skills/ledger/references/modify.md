# 修改命令

## 修改 (update)

```bash
python3 scripts/ledger_cli.py update '{"id":123,"field":"amount","value":50.0}'
```

参数：
- `id`: 记录ID - 必填
- `field`: 修改字段 (amount/category/subcategory/account/project/member/merchant/note/trans_date) - 必填
- `value`: 新值 - 必填

## 删除 (delete)

```bash
python3 scripts/ledger_cli.py delete '{"id":123}'
```

软删除，可恢复。

## 恢复 (restore)

```bash
python3 scripts/ledger_cli.py restore '{"id":123}'
```

