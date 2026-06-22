# 数据命令

## 智能导入

### Web 端导入（推荐）

访问 `/import` 页面，4 步完成：
1. 上传 CSV 文件
2. 确认列映射（自动推断，可手动调整）
3. 设置标签和导入选项
4. 确认导入

### API 导入

```bash
# 1. 预览（上传文件，获取映射建议）
curl -X POST $BASE_URL/api/import/preview \
  -F "file=@/path/to/data.csv"

# 2. 执行导入（确认映射后）
curl -X POST $BASE_URL/api/import/execute \
  -F "file=@/path/to/data.csv" \
  -F 'mapping={"交易时间":"date","支付金额":"amount","交易对方":"merchant"}' \
  -F 'tags=["支付宝导入","2024-06"]' \
  -F "skip_duplicates=true"

# 3. 查看导入批次历史
curl $BASE_URL/api/import/batches
```

### CLI 导入

Docker 环境：
```bash
# 把 CSV 文件放到宿主机数据目录
cp mymoney.csv /volume1/docker/ledger/data/
# 在容器内执行
docker exec -it ledger python scripts/import_ledger.py /data/mymoney.csv
```

### 智能映射

导入引擎自动处理：
- **编码检测**：UTF-8 / GBK / GB2312
- **列名推断**：支付宝、微信、随手记、银行等常见格式自动识别
- **值标准化**：根据已有数据自动归类（如"招行"→"招商银行"）
- **别名学习**：映射结果自动保存为别名，下次导入更准确
- **数据保留**：未映射列的值存入 `extra_data` 字段，不丢失

### CSV 格式

导入引擎支持多种列名，以下为标准格式：

| 列名 | 说明 | 必填 | 示例 |
|------|------|------|------|
| 交易类型 | 支出 或 收入 | ✅ | 支出 |
| 日期 | 多种格式自动识别 | ✅ | 2026/06/15 12:30 |
| 金额 | 数字 | ✅ | 25.5 |
| 类别 | 自动匹配已有类别 | ✅ | 食品酒水 |
| 子类别 | 自动匹配 | 可选 | 零食 |
| 账户 | 自动匹配已有账户 | 可选 | 微信零钱 |
| 项目 | 归属项目 | 可选 | 弹性支出 |
| 成员 | 谁消费的 | 可选 | 本人 |
| 商家 | 消费场所 | 可选 | 拼多多 |
| 备注 | 补充说明 | 可选 | 买零食 |

也支持支付宝（交易对方/支付金额）、微信（交易单号/支付方式）等平台特有列名。

## 增强导出

### Web 端导出

访问 `/export` 页面，选择格式、筛选条件、一键下载。

### API 导出

```bash
# 导出预览（查看记录数和金额）
curl "$BASE_URL/api/export/preview?start_date=2024-01-01&end_date=2024-06-30"

# Excel（多 Sheet：明细+月度汇总+分类统计+账户统计）
curl "$BASE_URL/api/export/v2?format=excel" -o export.xlsx

# CSV（与导入格式兼容，可直接重新导入）
curl "$BASE_URL/api/export/v2?format=csv" -o export.csv

# PDF（月度报告）
curl "$BASE_URL/api/export/v2?format=pdf&title=2024上半年报告" -o report.pdf

# JSON（含标签信息）
curl "$BASE_URL/api/export/v2?format=json" -o export.json
```

筛选参数：`start_date`、`end_date`、`category`、`account`、`type`、`tag_ids`

Excel/PDF 额外参数：`sheets=明细,月度汇总,分类统计,账户统计`

### 旧版导出（兼容）

```bash
# JSON 格式
curl "$BASE_URL/api/export?format=json&start_date=2026-06-01&end_date=2026-06-30"

# CSV 格式
curl "$BASE_URL/api/export?format=csv&category=食品酒水"
```

## 数据分析

```bash
curl $BASE_URL/api/analyze
```

输出结构化摘要：账户列表、商家列表、类别层级、成员列表、项目列表、字段使用率等。

## 健康检查

```bash
curl $BASE_URL/api/health
```

返回数据库状态、记录数、版本号。

## 数据库信息

```bash
curl $BASE_URL/api/info
```
