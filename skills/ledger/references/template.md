# 模板管理

## 创建模板

```bash
# 创建支出模板
curl -X POST $BASE_URL/api/templates \
  -H 'Content-Type: application/json' \
  -d '{"name":"零食模板","template_type":"支出","type":"支出","amount":30,"category":"食品酒水","subcategory":"零食","account":"微信零钱","merchant":"拼多多"}'

# 创建收入模板
curl -X POST $BASE_URL/api/templates \
  -H 'Content-Type: application/json' \
  -d '{"name":"工资模板","template_type":"收入","type":"收入","amount":5000,"category":"职业收入","account":"招商银行"}'
```

参数：
- `name`: 模板名称 - 必填
- `template_type`: 模板类型 - 可选，默认"通用"
- `type`: 交易类型 (支出/收入) - 可选
- `amount`: 金额 - 可选
- `category`、`subcategory`、`account`、`project`、`member`、`merchant`、`note` - 可选
- `tag_names`: 标签名称列表 - 可选
- `description`: 描述 - 可选

## 列出模板

```bash
curl $BASE_URL/api/templates
```

## 修改模板

```bash
curl -X PUT $BASE_URL/api/templates/1 \
  -H 'Content-Type: application/json' \
  -d '{"amount":40}'
```

## 删除模板

```bash
curl -X DELETE $BASE_URL/api/templates/1
```

## 使用模板（增加使用次数）

```bash
curl -X POST $BASE_URL/api/templates/1/use
```
