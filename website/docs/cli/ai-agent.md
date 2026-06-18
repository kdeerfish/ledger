---
sidebar_position: 11
---

# 🤖 AI Agent 集成

通过 JSON 参数调用，适合 picoclaw 等 AI Agent：

```bash
python ledger-skills/scripts/ledger_cli.py add '{"type":"支出","amount":25.5,"category":"食品","account":"微信"}'
python ledger-skills/scripts/ledger_cli.py list '{"limit":5}'
python ledger-skills/scripts/ledger_cli.py summary '{"year":2026,"month":7}'
python ledger-skills/scripts/ledger_cli.py search '{"keyword":"午餐"}'
python ledger-skills/scripts/ledger_cli.py stats '{"group_by":"category"}'
```
