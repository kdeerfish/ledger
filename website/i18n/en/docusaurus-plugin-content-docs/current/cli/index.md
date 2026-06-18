---
sidebar_position: 4
---

# 📘 CLI Reference

`scripts/cli.py` is the unified CLI entry point.

```bash
python scripts/cli.py <action> [arguments...]
```

## Transactions

```bash
# Add
python scripts/cli.py add --type expense --amount 100 --category 食品 --account 微信

# List
python scripts/cli.py list
python scripts/cli.py list --limit 50

# Update
python scripts/cli.py update --id 1 --field amount --value 50

# Delete / Restore
python scripts/cli.py delete --id 1
python scripts/cli.py restore --id 1
python scripts/cli.py hard_delete --id 1 --confirm
```

## Search & Filter

```bash
python scripts/cli.py search --keyword lunch
python scripts/cli.py filter --category 食品 --account 微信
```

## Statistics

```bash
python scripts/cli.py summary
python scripts/cli.py stats --group_by category
```

## Budget

```bash
python scripts/cli.py budget_set --category 食品 --amount 1000 --year 2026 --month 7
python scripts/cli.py budget_check
```

## AI Agent

```bash
python ledger-skills/scripts/ledger_cli.py add '{"type":"expense","amount":25.5,"category":"食品"}'
```
