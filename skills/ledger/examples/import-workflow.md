# 导入工作流示例

## 场景

用户有 CSV 格式的记账数据，需要导入到系统中。

## 完整流程

### 步骤 1：用户发起导入

**用户说**：
> 导入数据

**Agent 回复**：
> 请把 CSV 文件放到 NAS 上，然后提供文件所在的路径。

### 步骤 2：用户提供文件路径

**用户说**：
> /volume1/docker/ledger/data/mymoney_export.csv

### 步骤 3：执行导入

**Agent 回复**：
> 请在 NAS 终端执行以下命令在 Docker 容器中导入：

```bash
# 确认文件已放在数据目录
ls -la /volume1/docker/ledger/data/mymoney_export.csv
# 在容器内执行导入
docker exec -it ledger python scripts/import_ledger.py /data/mymoney_export.csv
```

### 步骤 4：建议学习

**Agent 回复**：
> 导入完成！建议说"学习记账"来分析你的数据，这样我就能记住你的账户、商家、类别等习惯。

### 步骤 5：用户学习

**用户说**：
> 学习

**Agent 执行**：
```bash
curl http://127.0.0.1:5800/api/analyze
```

**Agent 用 remember 保存关键模式**

## CSV 格式要求

| 列名 | 必填 | 说明 |
|------|------|------|
| 交易类型 | ✅ | 支出/收入 |
| 日期 | ✅ | YYYY/MM/DD HH:MM |
| 金额 | ✅ | 数字 |
| 类别 | ✅ | 食品酒水、交通等 |
| 子类别 | 可选 | 零食、早午餐等 |
| 账户 | 可选 | 微信零钱、招商银行 |
| 商家 | 可选 | 京东、拼多多 |

## 注意事项

1. 确保 CSV 文件编码为 UTF-8
2. 第一行必须是表头
3. 导入后建议执行"学习记账"分析数据
