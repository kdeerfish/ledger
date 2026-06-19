---
name: ledger
description: 个人记账工具，支持记账、查账、统计、预算管理、数据导入导出等功能
version: 2.0.0
---

# Ledger - 个人记账系统

## 概述

Ledger 是一个基于 HTTP API 的个人记账系统，通过 Docker 容器部署，提供完整的财务记录和分析功能。

## 调用方式

```bash
python3 scripts/ledger_cli.py <command> '<json_args>'
```

所有命令返回统一的 JSON 格式：
```json
{
  "success": true,
  "data": "..."
}
```

## 核心功能

### 交易管理

| 功能 | 命令 | 说明 |
|------|------|------|
| 记账 | `add` | 添加收入或支出记录 |
| 查账 | `list` | 查看最近记录 |
| 搜索 | `search` | 按关键词搜索记录 |
| 筛选 | `filter` | 按条件筛选记录 |
| 汇总 | `summary` | 按月汇总收支 |
| 统计 | `stats` | 按类别/账户/月份统计 |
| 修改 | `update` | 修改已有记录 |
| 删除 | `delete` | 删除记录 |
| 恢复 | `restore` | 恢复已删除记录 |

### 预算管理

| 功能 | 命令 | 说明 |
|------|------|------|
| 设置预算 | `budget_set` | 为类别设置预算限额 |
| 查看预算 | `budget_check` | 查看预算执行情况 |
| 预算模板 | `budget_template_*` | 预算模板的增删改查、应用、推荐 |

### 通用记录模板

| 功能 | 命令 | 说明 |
|------|------|------|
| 模板管理 | `template_*` | 记录模板的增删改查、应用、推荐 |

### 数据与查询

| 功能 | 命令 | 说明 |
|------|------|------|
| 导出 | `export` | 导出数据 (支持 JSON/CSV) |
| 分析 | `analyze` | 分析消费习惯 |
| 账户列表 | `accounts` | 查看所有账户 |
| 类别列表 | `categories` | 查看所有类别 |
| 成员列表 | `members` | 查看所有成员 |

### 系统

| 功能 | 命令 | 说明 |
|------|------|------|
| 健康检查 | `health` | 检查 API 连接状态 |

## 快速开始

### 记一笔账
```bash
python3 scripts/ledger_cli.py add '{"type":"支出","amount":30,"category":"食品酒水","account":"微信零钱"}'
```

### 查看最近记录
```bash
python3 scripts/ledger_cli.py list '{"limit":10}'
```

### 查看月度统计
```bash
python3 scripts/ledger_cli.py summary '{"year":2026,"month":6}'
```

### 检查连接
```bash
python3 scripts/ledger_cli.py health '{}'
```

## 文档索引

详细命令参数请查阅 `references/` 目录：

| 文档 | 内容 |
|------|------|
| `references/basic.md` | 基础命令 (add/list/search/filter/summary/stats) |
| `references/modify.md` | 修改命令 (update/delete/restore) |
| `references/budget.md` | 预算命令 (budget_set/budget_check) |
| `references/template.md` | 通用记录模板 (template_*) |
| `references/data.md` | 数据命令 (export/analyze) |
| `references/field-guide.md` | 字段用途说明、场景示例 |

日常操作示例见 `examples/` 目录。

## 配置

在 `skills/ledger/.env` 中配置 API 地址（如需连接远程服务）：
```bash
LEDGER_API_URL=http://127.0.0.1:5800
```

## 注意事项

- 添加记录时自动检查重复，如需跳过请设置 `"force": true`
- 所有日期格式为 `YYYY-MM-DD HH:MM:SS`，不传则使用当前时间
- 预算模板支持按类别、账户、项目、成员等维度设置
- 通用模板可快速创建常用记录，支持推荐功能
