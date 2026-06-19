---
name: ledger-cli
description: Super simple ledger CLI tool. Install once, use directly with agent. No web UI, no extra config. Cross-platform (Windows/Linux).
version: 0.1.0
---

# Ledger CLI - Agent-Friendly Ledger

A super simplified personal finance/ledger CLI tool designed for AI agent interaction.

## Quick Start

### 1. Build (one-time)

```bash
cd <skill-directory>
go build -o ledger-cli
```

On Windows the binary is `ledger-cli.exe`. On Linux it's `ledger-cli`.

### 2. Add to PATH or use absolute path

```bash
# Option A: Add to PATH
export PATH="$PATH:<skill-directory>"

# Option B: Use absolute path
<skill-directory>/ledger-cli <command>
```

## Usage Reference

All commands support `--json` (or `-j`) flag for JSON output.

### Transaction Management

```bash
# Add transaction
ledger-cli tx add --type expense --amount 25.5 --category food --account wechat --date 2026-06-19 --note "lunch"
ledger-cli tx add --type income --amount 5000 --category salary --account bank --date 2026-06-01

# List recent transactions
ledger-cli tx list --limit 20

# List with filters
ledger-cli tx list --category food --account wechat --start 2026-06-01 --end 2026-06-30
ledger-cli tx list --type expense --keyword "coffee"
ledger-cli tx list --type income

# Get single transaction
ledger-cli tx get 123

# Update transaction
ledger-cli tx update 123 --amount 30.0 --note "dinner"

# Soft delete / restore / permanent delete
ledger-cli tx delete 123
ledger-cli tx restore 123
ledger-cli tx hard-delete 123
```

### Monthly Summary

```bash
ledger-cli summary --year 2026 --month 6
```

### Statistics

```bash
# By category (default)
ledger-cli stats --group-by category

# By account
ledger-cli stats --group-by account

# Other dimensions: subcategory, project, member, merchant

# With date range
ledger-cli stats --group-by category --start 2026-01-01 --end 2026-06-30
```

### Expense Analysis

```bash
ledger-cli analyze --year 2026 --month 6
```

### Auto-complete Hints

```bash
ledger-cli suggest --field category --keyword "fo"
ledger-cli suggest --field account
ledger-cli suggest --field merchant
ledger-cli accounts
ledger-cli categories
```

### Tag Management

```bash
ledger-cli tag create --name food --color "#ff0000"
ledger-cli tag list
ledger-cli tag delete 1
ledger-cli tag transactions food
```

### Budget Management

```bash
# Set budget
ledger-cli budget set --year 2026 --month 6 --category food --amount 2000
ledger-cli budget set --year 2026 --month 6 --amount 10000  # total budget

# List / check budgets
ledger-cli budget list --year 2026 --month 6
ledger-cli budget check --year 2026 --month 6
```

### Budget Templates

```bash
ledger-cli budget-template create --name "monthly food" --category food --amount 2000
ledger-cli budget-template list
ledger-cli budget-template apply 1 --year 2026 --month 6
ledger-cli budget-template delete 1
```

### Record Templates

```bash
# Create template
ledger-cli template create --name "commute" --type expense --amount 5.0 --category transport --account wechat --note "subway"

# List / apply / suggest
ledger-cli template list
ledger-cli template apply 1 --date 2026-06-19
ledger-cli template suggest

# Update / delete
ledger-cli template update 1 --amount 6.0
ledger-cli template delete 1
```

### Import / Export

```bash
# Import CSV (Suishouji format)
ledger-cli import --file data.csv

# Export
ledger-cli export --output report.csv --format csv
ledger-cli export --output data.json --format json --start 2026-01-01 --end 2026-06-30
```

### System Info

```bash
ledger-cli info
```

## Data Types

- **Transaction types**: `expense` (spending), `income` (earning)
- **Date format**: `YYYY-MM-DD`
- **Amount**: positive decimal numbers
- **JSON output**: All commands support `--json` flag for structured output

## Configuration

- **Database path**: Set `LEDGER_DB_PATH` environment variable, default `~/.ledger-cli/ledger.db`
- **No server needed**: Direct CLI, instant response
- **No web UI**: Pure agent communication

## Architecture

- Single Go binary, no runtime dependencies
- SQLite database (WAL mode, pure Go)
- Cross-platform: Windows, Linux, macOS
- Works with any AI agent (Reasonix, Claude, etc.)

## Agent Interaction Guide

When a user asks to record expenses/income, use the `tx add` command.
When a user asks for summaries, use `summary` or `stats`.
When a user asks for budgets, use `budget` commands.
All commands return JSON with `--json` flag for easy parsing.
