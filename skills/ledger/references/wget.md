# wget 兼容

环境没有 curl 时（如 Docker 容器），可用 wget 调用本 API。

Base URL 通过环境变量 `$BASE_URL` 解析（详见主文档「Base URL 解析」章节）

## GET 请求

```bash
wget -qO- $BASE_URL/api/transactions?limit=5
```

## POST 请求

```bash
wget --post-data '{"amount":30,"category":"食品酒水"}' \
     --header='Content-Type: application/json' \
     -qO- $BASE_URL/api/transactions
```

## PUT 请求（通过 _method）

wget 不支持 PUT，通过 `?_method=PUT` 模拟：

```bash
# 修改交易
wget --post-data '{"amount":50}' \
     --header='Content-Type: application/json' \
     -qO- "$BASE_URL/api/transactions/42?_method=PUT"

# 修改模板
wget --post-data '{"amount":20}' \
     --header='Content-Type: application/json' \
     -qO- "$BASE_URL/api/templates/1?_method=PUT"
```

## DELETE 请求（通过 _method）

```bash
# 删除交易
wget --post-data='' \
     -qO- "$BASE_URL/api/transactions/42?_method=DELETE"

# 删除模板
wget --post-data='' \
     -qO- "$BASE_URL/api/templates/1?_method=DELETE"

# 删除标签
wget --post-data='' \
     -qO- "$BASE_URL/api/tags/1?_method=DELETE"
```

## 恢复删除

```bash
wget --post-data='' \
     --header='Content-Type: application/json' \
     -qO- $BASE_URL/api/transactions/42/restore
```

## 注意事项

- `?_method` 仅在 POST 请求上生效，且必须放在 URL 查询参数中
- `_method` 参数不会传入业务逻辑，自动剥离
- 大小写不敏感：`PUT`、`put`、`Put` 均可
