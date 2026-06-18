---
name: ledger
description: 记账、查账、统计、预算、导入导出、学习用户习惯等个人财务管理工具（HTTP API 版）
version: 2.0.0
---

# Ledger - 个人记账系统

## 系统架构

```
AI Agent ──HTTP──→ Docker 容器
    │                   │
    │   ledger_cli.py   │  Web UI (Flask)
    │   (API 客户端)    │  REST API
    │                   │  SQLite Database
    └───────────────────┘
```

- Agent **不再直接读写 SQLite**，全部通过 HTTP API 操作
- Ledger 运行在 Docker 容器中，数据持久化在宿主机
- Agent 可运行在**任何位置**（同机、远端、另一台 NAS）

## 配置

在 `skills/ledger/.env` 中配置 API 地址：

```bash
# 编辑 .env 文件
LEDGER_API_URL=http://192.168.31.126:5800
```

如果 Agent 和 Docker 在同一台机器上，可以用 `http://127.0.0.1:5800`。

## 核心概念

通过 `python3 scripts/ledger_cli.py <command> '<json_args>'` 调用，所有命令返回 JSON 格式。

### 常用命令

```bash
# 记账
python3 scripts/ledger_cli.py add '{"type":"支出","amount":30,"category":"食品酒水","account":"微信零钱"}'

# 查账
python3 scripts/ledger_cli.py list '{"limit":10}'

# 统计
python3 scripts/ledger_cli.py summary '{"year":2026,"month":6}'

# 分析数据
python3 scripts/ledger_cli.py analyze '{}'

# 检查 API 连接
python3 scripts/ledger_cli.py health '{}'
```

## 文档索引

详细文档位于 `references/` 目录：

| 文档 | 内容 | 何时读取 |
|------|------|----------|
| `references/basic.md` | 基础命令 (add/list/search/filter/summary/stats) | 记账、查账、搜索时 |
| `references/modify.md` | 修改命令 (update/delete/restore) | 修改、删除记录时 |
| `references/budget.md` | 预算命令 (budget_set/budget_check) | 设置、查看预算时 |
| `references/template.md` | 通用记录模板 (template_*) | 使用模板快速记账时 |
| `references/data.md` | 数据命令 (export/analyze) | 导出、分析数据时 |
| `references/field-guide.md` | 字段用途说明、场景示例 | 不确定字段怎么填时 |

> 每个参考文档都有对应的日常操作示例，见 `examples/` 目录。

## 工作流程

### 流程 1：首次使用 / 学习习惯

当用户说"学习"、"学习我的习惯"、"分析我的数据"时：

1. **调用 analyze 命令**：
   ```bash
   python3 scripts/ledger_cli.py analyze '{}'
   ```

2. **阅读分析报告**，重点关注：
   - 【账户】列表（付款方式/资金来源）
   - 【商家】列表（消费场所/平台）
   - 【类别→子类别】（消费分类习惯）
   - 【成员】列表（家庭成员）
   - 【项目】列表（长期项目）

3. **用 remember 工具保存关键模式**到记忆

### 流程 2：日常记账

```
用户："今天花了30块买零食"
→ 根据 field-guide 正确填写字段
→ 执行 add 命令
```

## 重要规则

### 去重检查

添加记录时自动检查相似记录。发现重复时需设置 `"force": true` 跳过检查。

### 输出格式

所有命令统一返回：
```json
{
  "success": true,
  "data": "..."
}
```

## 快速参考

### 预算管理

```bash
# 设置预算
python3 scripts/ledger_cli.py budget_set '{"category":"食品酒水","amount":2000}'

# 检查预算
python3 scripts/ledger_cli.py budget_check '{}'
```

### 数据统计

```bash
# 按类别统计
python3 scripts/ledger_cli.py stats '{"group_by":"category"}'

# 按账户统计
python3 scripts/ledger_cli.py stats '{"group_by":"account"}'

# 按月统计
python3 scripts/ledger_cli.py stats '{"group_by":"month"}'
```
