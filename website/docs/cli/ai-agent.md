---
sidebar_position: 11
---

# 🤖 AI Agent 集成 (Go 版)

`skills/ledger/SKILL.md` 是给 LLM Agent 看的技能描述,被 Claude Code / Cursor / Continue / Cline 等 IDE Agent 自动识别。

## 安装(给 Agent 读)

把 `skills/ledger/` 目录放到以下任一位置:

```bash
# Claude Code (项目级)
mkdir -p .claude/skills
cp -r skills/ledger .claude/skills/ledger

# Cursor (项目级)
mkdir -p .cursor/skills
cp -r skills/ledger .cursor/skills/ledger
```

Agent 启动后会读 `SKILL.md` 了解 ledger 能力,自动知道怎么调用。

## 两种调用方式

### 方式 1: HTTP API(推荐给 LLM 自动化场景)

启动服务(在后台跑一次就行):

```bash
./bin/ledger serve --port 5800 &
```

Agent 用 HTTP 调用:

```bash
# 新增交易
curl -s -X POST http://localhost:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"支出","amount":25.5,"category":"食品","account":"微信"}'
# → {"success":true,"data":{"id":1,"type":"支出",...}}

# 查最近 5 笔
curl -s 'http://localhost:5800/api/transactions?limit=5'

# 月度汇总
curl -s 'http://localhost:5800/api/summary?year=2026&month=6'

# 按类别统计
curl -s 'http://localhost:5800/api/stats?group_by=category'
```

### 方式 2: CLI(脚本式)

`skills/ledger/scripts/ledger_cli.sh` 是 bash 封装,自动定位二进制:

```bash
# 任何 LLM agent 用自然语言触发的命令
./skills/ledger/scripts/ledger_cli.sh tx add --type 支出 --amount 30 --category 食品
./skills/ledger/scripts/ledger_cli.sh misc summary --year 2026 --month 6
./skills/ledger/scripts/ledger_cli.sh misc stats --group-by category
```

## 让 Agent 帮你做

告诉 Agent(自然语言):

> "我今天午餐花了 35 块,微信支付的,帮我记一下"

Agent 会读 `SKILL.md` → 调用 `tx add` → 返回成功提示。

> "上个月食品花了多少?有没有超预算?"

Agent 读 `SKILL.md` → 调用 `misc stats --group-by category --start-date ...` + `/api/budgets/check` → 回答你。

## 安全提示

- **不要让 Agent 访问生产数据库的写权限**: Agent 默认通过 `LEDGER_DB_PATH` 定位库路径,可以限制 Agent 跑在只读环境
- **二次确认危险操作**: 永久删除 (`tx hard-delete --confirm`) 仍需人工 `--confirm`,Agent 不能跳过

## 详细能力

完整命令列表见 [CLI 手册](./index)。HTTP API 详见 [API 文档](../api)。
