---
sidebar_position: 7
---

# 🤖 AI Agent 集成

Ledger 设计之初就考虑了 AI Agent 场景——**所有能力都通过 HTTP API 暴露**，并提供标准化的 **技能包（Skill）**。

任何能调用 Python 的 Agent（Hermes、picoclaw、AutoGPT、LangGraph Agent…）都能接管记账。

---

## 🧭 几种 Agent 接入方式

| 接入方式 | 难度 | 适合 |
|---------|------|------|
| **方式 1：HTTP REST API 直调** | ⭐ | 自己写脚本、自动化任务 |
| **方式 2：ledger_cli.py 包装** | ⭐⭐ | LLM Agent（最常用） |
| **方式 3：Skills 包（SKILL.md）** | ⭐⭐ | 支持 Skills 协议的 Agent（Hermes / picoclaw） |
| **方式 4：MCP Server（未来）** | ⭐⭐⭐ | 完整 Agent 框架 |

---

## 方式 1：HTTP REST API 直调

所有 API 见 [API 文档](../api.md)。几个最常用的：

```bash
# 健康检查
curl http://localhost:5800/api/health

# 最近 5 笔
curl "http://localhost:5800/api/transactions?limit=5"

# 记一笔支出
curl -X POST http://localhost:5800/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"type":"支出","amount":25.5,"category":"食品","account":"微信","note":"午餐"}'

# 按月统计
curl "http://localhost:5800/api/summary?year=2026&month=6"
```

返回统一 JSON 格式：

```json
{"success": true, "data": {...}}
{"success": false, "error": "..."}
```

---

## 方式 2：ledger_cli.py 包装

`ledger_cli.py` 是给 Agent 用的**统一 CLI**，所有命令接收 JSON 参数、返回 JSON 结果。

### 安装到 Agent 环境

技能包在项目的 `skills/ledger/` 目录下。把它复制到 Agent 能访问的位置：

```bash
# 项目里就有，打包版本在 deploy/ledger-skills.zip
unzip deploy/ledger-skills.zip -d ~/.local/share/ledger-skills
```

### 配置 API 地址

编辑 `skills/ledger/.env`（或复制 `.env.example` 为 `.env`）：

```bash
LEDGER_API_URL=http://192.168.1.100:5800
```

> Docker 默认在本机就跑，填 `http://localhost:5800`；如果是远程 NAS，改成 NAS IP。

### 调用示例

```bash
python3 skills/ledger/scripts/ledger_cli.py add \
  '{"type":"支出","amount":30,"category":"食品","account":"微信"}'

python3 skills/ledger/scripts/ledger_cli.py list '{"limit":5}'

python3 skills/ledger/scripts/ledger_cli.py summary '{"year":2026,"month":6}'

python3 skills/ledger/scripts/ledger_cli.py search '{"keyword":"午餐"}'

python3 skills/ledger/scripts/ledger_cli.py stats '{"group_by":"category"}'

python3 skills/ledger/scripts/ledger_cli.py health '{}'
```

返回示例：

```json
{"success": true, "data": "已添加交易，ID=123"}
```

### 全部命令

| 命令 | 说明 | 必填参数 |
|------|------|---------|
| `health` | 检查 API | 无 |
| `add` | 记一笔 | `type, amount` |
| `list` | 查最近 | `limit`（可选） |
| `search` | 关键词搜索 | `keyword` |
| `filter` | 多维筛选 | 可选多个 |
| `summary` | 月汇总 | `year, month` |
| `stats` | 多维统计 | `group_by` |
| `update` | 改交易 | `id, field, value` |
| `delete` | 软删除 | `id` |
| `restore` | 恢复 | `id` |
| `budget_set` | 设预算 | `amount` |
| `budget_check` | 查预算 | 无 |
| `template_*` | 记账模板 | 视命令而定 |
| `export` | 导出 | `output` |
| `analyze` | 分析习惯 | 无 |
| `accounts` | 账户列表 | 无 |
| `categories` | 类别列表 | 无 |
| `members` | 成员列表 | 无 |

---

## 方式 3：Skills 包（SKILL.md 标准协议）

项目里的 `skills/ledger/SKILL.md` 是按 [Skills 协议](https://github.com/zouzhenglu/picoclaw) 写的，Agent 加载后会自动识别能力：

```yaml
---
name: ledger
description: 个人记账工具，支持记账、查账、统计、预算管理、数据导入导出
version: 2.0.0
---
```

### Hermes / picoclaw Agent 怎么用

把 skills 目录复制到 Agent 的 skills 路径：

```bash
# 假设 picoclaw/Hermes 装在 ~/.picoclaw
cp -r skills/ledger ~/.picoclaw/skills/

# 配置 Agent 的 env（指向你的 Ledger API）
echo "LEDGER_API_URL=http://192.168.1.100:5800" >> ~/.picoclaw/.env
```

然后告诉 Agent：

> "今天中午吃麦当劳花了 35 块"

Agent 就会自动调 `add` 命令记账。Agent 内部走的就是 `ledger_cli.py`。

### Skills 包结构

```
skills/ledger/
├── SKILL.md                 # 主文档（Agent 读这个认识能力）
├── .env.example             # API 地址配置示例
├── scripts/
│   └── ledger_cli.py        # CLI 客户端
├── references/              # 详细文档（Agent 按需查）
│   ├── basic.md             # 基础命令
│   ├── modify.md            # 修改命令
│   ├── budget.md            # 预算命令
│   ├── template.md          # 模板命令
│   ├── data.md              # 数据导出/分析
│   └── field-guide.md       # 字段含义
└── examples/                # 使用示例
```

---

## 方式 4：MCP Server（路线图）

完整 Model Context Protocol Server 在计划中。届时 Claude Desktop / Cursor 等能直接以 MCP 工具方式调用。

---

## 🛠 实战场景示例

### 场景 1：让 Agent 定期记今天的消费

> Agent 每天晚上问："今天买了啥？"

Agent 会自动：
1. 调 `accounts` / `categories` 获取可选值
2. 调 `analyze` 看历史习惯做字段建议
3. 你确认后调 `add` 写入

### 场景 2：让 Agent 给你月度账单

> "我 6 月花了多少？哪些类目超预算了？"

Agent 会自动：
1. `summary '{"year":2026,"month":6}'`
2. `budget_check '{"year":2026,"month":6}'`
3. 整理成自然语言报告

### 场景 3：从邮件/消息自动记账

Agent 读到"已通过微信支付 28.50 元于麦当劳"，自动：

```bash
python3 ledger_cli.py add '{"type":"支出","amount":28.5,"category":"食品","account":"微信","merchant":"麦当劳","date":"2026-06-19 12:30:00"}'
```

---

## ⚙️ Agent 安全注意事项

| 风险 | 缓解 |
|------|------|
| Agent 写错数据 | `add` 自动检查重复，错了用 `delete` 软删（可恢复） |
| Agent 误调用 | API 默认只允许同源；如要远程访问加 CORS 白名单 `WEB_CORS_ORIGINS` |
| API 暴露公网 | **强烈不推荐**直暴公网。用 VPN / Tailscale / 反向代理 + 鉴权 |
| 数据泄露 | Ledger 不上传任何数据，所有数据都在你本地 |

---

## 📦 给 Agent 作者

如果你想给某个 Agent 框架写一个 Ledger 集成：

1. **优先用 `ledger_cli.py`**，最简单稳定
2. **不要绕过 HTTP API** 直接读 SQLite，并发写会冲突
3. 让 Agent 优先用 `analyze` 命令学习用户习惯，再让用户确认关键参数

---

更多技术细节见：
- [API 完整文档](../api.md)
- [Skills 包源码](https://github.com/kdeerfish/ledger/tree/master/skills/ledger)