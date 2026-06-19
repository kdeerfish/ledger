---
name: ledger
description: 个人记账工具 (Go 重写版),支持记账、查账、统计、预算管理、数据导入导出、AI Agent 集成等功能
version: 2.0.0
---

# Ledger - 个人记账系统 (Go)

## 概述

Ledger 是一个基于 HTTP API 和 CLI 的个人记账系统,Go 重写版本。
后端用 Go (chi + cobra + modernc/sqlite),前端用 React 19 + Vite,
单二进制部署,无 Python / Node 运行时依赖(除开发前端构建外)。

## 调用方式

### 方式一: CLI (推荐给 agent 写脚本)

```bash
# 二进制路径: ./bin/ledger  或  $PATH 里的 ledger
./bin/ledger tx add --type 支出 --amount 25.5 --category 食品 --account 微信
./bin/ledger tx list --limit 10
./bin/ledger misc summary --year 2026 --month 6
./bin/ledger misc stats --group-by category
./bin/ledger misc export --output report.csv --format csv
```

### 方式二: HTTP API (推荐给 web / 脚本语言)

启动服务:`./bin/ledger serve --port 5800`

```bash
# 列出最近交易
curl -s http://localhost:5800/api/transactions?limit=20

# 新增交易
curl -s -X POST http://localhost:5800/api/transactions \
     -H 'Content-Type: application/json' \
     -d '{"type":"支出","amount":25.5,"category":"食品","account":"微信"}'

# 预算检查
curl -s "http://localhost:5800/api/budgets/check?year=2026&month=6"

# 导出
curl -s "http://localhost:5800/api/export?format=json&start_date=2026-01-01" -o data.json
```

所有响应统一为:
```json
{ "success": true, "data": { ... } }
```
失败: `{ "success": false, "error": "..." }` + HTTP 4xx/5xx。

## 核心功能

### 交易管理
- `tx add` / `tx list` / `tx get` / `tx update` / `tx delete` / `tx restore` / `tx hard-delete`
- 软删除 + 恢复机制
- 重复检测(同日/同金额/同类型/同类别)

### 标签管理
- `tag list` / `tag create` / `tag delete`
- 多对多关联,带使用次数统计

### 预算管理
- `budget set` / `budget list` / `budget check`
- 按 (year, month, category, dimension_type, dimension_value) 唯一
- 预算模板: `budget template-create/list/update/delete/apply/suggest`

### 记账模板
- `template create` / `template list` / `template update` / `template delete` / `template apply` / `template suggest`
- 模板应用自动累加 `usage_count`

### 统计 / 报告
- `misc summary` 月度汇总
- `misc stats --group-by category|account|project|member|merchant|month` 9 种分组
- `misc analyze` 交叉统计报告
- `misc suggest` 自动补全

### 导入 / 导出
- `misc import --file data.csv` 支持随手记 CSV
- `misc export --output report.{csv,json}` 两种格式

## 配置文件

环境变量(或 `.env`):
- `LEDGER_DB_PATH`: SQLite 文件路径 (默认 `data/ledger.db`)
- `WEB_HOST` / `WEB_PORT`: HTTP 监听 (默认 `0.0.0.0:5800`)
- `WEB_CORS_ORIGINS`: 允许的跨域来源
- `WEB_DEBUG`: 调试模式
- `LOG_LEVEL` / `LOG_FORMAT`: 日志 (debug/info/warn/error, json/text)

## 部署

### 单二进制
```bash
make build       # 输出 bin/ledger
./bin/ledger serve --port 5800
```

### Docker
```bash
docker pull zouzhenglu/ledger
docker run -d -p 5800:5800 -v $(pwd)/data:/data zouzhenglu/ledger
```

### docker-compose
```bash
wget https://raw.githubusercontent.com/kdeerfish/ledger/master/docker-compose.yml
docker compose up -d
```

## 详细参考

- `references/basic.md` - 基础交易操作
- `references/budget.md` - 预算管理
- `references/data.md` - 数据导入导出
- `references/field-guide.md` - 字段参考
- `references/modify.md` - 修改 / 删除 / 恢复
- `references/template.md` - 模板使用

## 示例

- `examples/basic-examples.md`
- `examples/budget-examples.md`
- `examples/template-examples.md`
- `examples/import-workflow.md`
- `examples/data-examples.md`
- `examples/modify-examples.md`
- `examples/field-guide-examples.md`
- `examples/learn-workflow.md`
