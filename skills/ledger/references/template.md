# 通用记录模板

## 创建模板 (template_create)

```bash
# 创建支出模板
python3 scripts/ledger_cli.py template_create '{"name":"零食模板","template_type":"支出","type":"支出","amount":30,"category":"食品酒水","subcategory":"零食","account":"微信零钱","merchant":"拼多多"}'

# 创建收入模板
python3 scripts/ledger_cli.py template_create '{"name":"工资模板","template_type":"收入","type":"收入","amount":5000,"category":"职业收入","account":"招商银行"}'
```

参数：
- `name`: 模板名称 - 必填
- `template_type`: 模板类型 (支出/收入/预算/通用) - 可选，默认"通用"
- `type`: 交易类型 (支出/收入) - 可选
- `amount`: 金额 - 可选
- `category`: 类别 - 可选
- `subcategory`: 子类别 - 可选
- `account`: 账户 - 可选
- `project`: 项目 - 可选
- `member`: 成员 - 可选
- `merchant`: 商家 - 可选
- `note`: 备注 - 可选
- `description`: 描述 - 可选

## 列出模板 (template_list)

```bash
# 列出所有模板
python3 scripts/ledger_cli.py template_list '{}'

# 按类型列出模板
python3 scripts/ledger_cli.py template_list '{"template_type":"支出"}'
```

## 应用模板 (template_apply)

```bash
# 应用模板（快速记账）
python3 scripts/ledger_cli.py template_apply '{"id":1}'

# 应用模板并覆盖金额
python3 scripts/ledger_cli.py template_apply '{"id":1,"amount":50}'
```

## 推荐模板 (template_suggest)

```bash
python3 scripts/ledger_cli.py template_suggest '{"limit":5}'
```

## 更新模板 (template_update)

```bash
python3 scripts/ledger_cli.py template_update '{"id":1,"amount":40}'
```

## 删除模板 (template_delete)

```bash
python3 scripts/ledger_cli.py template_delete '{"id":1}'
```

