---
name: ledger-cli
description: Super simple ledger CLI tool. Pre-compiled binaries included. No build needed. Cross-platform (Windows/Linux/macOS). Agent-friendly with JSON output.
version: 0.1.0
---

# Ledger CLI - Agent-Friendly Ledger

A super simplified personal finance/ledger CLI tool designed for AI agent interaction.
Pre-compiled binaries included - no Go installation required.

## Quick Start

### For Users (Pre-compiled)

Download the skill zip, extract, and run setup:

`ash
unzip ledger-cli-*-skill.zip
cd ledger-cli
bash setup.sh
`

The setup.sh script auto-detects your platform (Linux/macOS/Windows, amd64/arm64)
and copies the correct binary to the current directory.

### For Agents (Runtime Detection)

When running from the skill directory, detect the platform and execute the correct binary:

`ash
# Agent platform detection
SKILL_DIR="<path-to-skill-directory>"
OS=""
ARCH=""
case "" in x86_64) ARCH="amd64" ;; aarch64) ARCH="arm64" ;; esac

# Linux/macOS
exec "$SKILL_DIR/bin/ledger-cli-$OS-$ARCH" "$@"

# Windows (PowerShell)
# Use: & "\bin\ledger-cli-windows-amd64.exe" <command>
`

### For Developers (Source Build)

`ash
go build -o ledger-cli .
# or on Windows: go build -o ledger-cli.exe .
`

## Usage Reference

All commands support --json (or -j) flag for JSON output.

### Transaction Management

`ash
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
`

### Monthly Summary

`ash
ledger-cli summary --year 2026 --month 6
`

### Statistics

`ash
# By category (default)
ledger-cli stats --group-by category

# By account
ledger-cli stats --group-by account

# Other dimensions: subcategory, project, member, merchant

# With date range
ledger-cli stats --group-by category --start 2026-01-01 --end 2026-06-30
`

### Expense Analysis

`ash
ledger-cli analyze --year 2026 --month 6
`

### Auto-complete Hints

`ash
ledger-cli suggest --field category --keyword "fo"
ledger-cli suggest --field account
ledger-cli suggest --field merchant
ledger-cli accounts
ledger-cli categories
`

### Tag Management

`ash
ledger-cli tag create --name food --color "#ff0000"
ledger-cli tag list
ledger-cli tag delete 1
ledger-cli tag transactions food
`

### Budget Management

`ash
# Set budget
ledger-cli budget set --year 2026 --month 6 --category food --amount 2000
ledger-cli budget set --year 2026 --month 6 --amount 10000  # total budget

# List / check budgets
ledger-cli budget list --year 2026 --month 6
ledger-cli budget check --year 2026 --month 6
`

### Budget Templates

`ash
ledger-cli budget-template create --name "monthly food" --category food --amount 2000
ledger-cli budget-template list
ledger-cli budget-template apply 1 --year 2026 --month 6
ledger-cli budget-template delete 1
`

### Record Templates

`ash
# Create template
ledger-cli template create --name "commute" --type expense --amount 5.0 --category transport --account wechat --note "subway"

# List / apply / suggest
ledger-cli template list
ledger-cli template apply 1 --date 2026-06-19
ledger-cli template suggest

# Update / delete
ledger-cli template update 1 --amount 6.0
ledger-cli template delete 1
`

### Import / Export

`ash
# Import CSV (Suishouji format)
ledger-cli import --file data.csv

# Export
ledger-cli export --output report.csv --format csv
ledger-cli export --output data.json --format json --start 2026-01-01 --end 2026-06-30
`

### System Info

`ash
ledger-cli info
`

## Data Types

- **Transaction types**: expense (spending), income (earning)
- **Date format**: YYYY-MM-DD
- **Amount**: positive decimal numbers
- **JSON output**: All commands support --json flag for structured output

## Configuration

- **Database path**: Set LEDGER_DB_PATH environment variable, default ~/.ledger-cli/ledger.db
- **No server needed**: Direct CLI, instant response
- **No web UI**: Pure agent communication

## Architecture

- Single Go binary, no runtime dependencies
- SQLite database (WAL mode, pure Go)
- Cross-platform: Windows, Linux, macOS (amd64 + arm64)
- Works with any AI agent (Reasonix, Claude, etc.)

## Agent Interaction Guide

When a user asks to record expenses/income, use the 	x add command.
When a user asks for summaries, use summary or stats.
When a user asks for budgets, use udget commands.
All commands return JSON with --json flag for easy parsing.