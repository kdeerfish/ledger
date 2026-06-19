# ledger-cli

Super simplified personal finance CLI tool for AI agents.

## Features

- Transaction management (add, list, update, delete, restore)
- Monthly summary and statistics
- Tag management
- Budget management and templates
- Record templates
- CSV import/export
- Duplicate detection
- Cross-platform (Windows/Linux)
- Single binary, no dependencies
- Agent-friendly (JSON output support)

## Build

```bash
go build -o ledger-cli
# or on Windows:
go build -o ledger-cli.exe
```

## Quick Start

```bash
# Add a transaction
./ledger-cli tx add --type expense --amount 25.5 --category food --account wechat

# List recent transactions
./ledger-cli tx list

# Monthly summary
./ledger-cli summary --year 2026 --month 6

# Stats by category
./ledger-cli stats --group-by category

# JSON output
./ledger-cli tx list --json -j
```

## Configuration

- `LEDGER_DB_PATH`: SQLite database path (default: `~/.ledger-cli/ledger.db`)
- No server, no web UI, no config files needed

## Transaction Types

- `expense`: Spending
- `income`: Earning

## Full Command Reference

Run `./ledger-cli --help` for all commands.
