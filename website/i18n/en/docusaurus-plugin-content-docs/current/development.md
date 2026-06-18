---
sidebar_position: 15
---

# 🛠 Development Guide

## Requirements

- Python 3.10+
- Git
- Docker (optional)

## Setup

```bash
git clone https://github.com/kdeerfish/ledger.git
cd ledger
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install -e ".[dev,lint]"
```

## Project Structure

```
ledger/
├── ledger_modules/          # Core modules
│   ├── __init__.py
│   ├── db.py                # SQLite init/migration
│   ├── transactions.py      # Transaction CRUD
│   ├── budgets.py           # Budget management
│   └── config.py            # Config (env loading)
├── scripts/
│   ├── cli.py               # CLI entry point
│   ├── import_ledger.py     # CSV import
│   ├── release.py           # Release script
│   └── deploy.py            # Deploy script
├── web/                     # Flask web app
│   ├── app.py               # API endpoints
│   ├── run.py               # Start script
│   ├── templates/           # HTML templates
│   └── static/              # CSS
├── tests/                   # pytest tests
└── website/                 # Docusaurus docs
```

## Running Tests

```bash
# All tests
make test

# With coverage
make coverage

# Specific test
python -m pytest tests -v -k "test_budget"
```

Current coverage: **86%** (102+ test cases)

## Make Commands

| Command | Description |
|---------|-------------|
| `make test` | Run tests |
| `make coverage` | Test + coverage report |
| `make lint` | ruff lint |
| `make lint-fix` | Auto-fix |
| `make format` | Format code |

## Database

Ledger uses SQLite with automatic schema creation and migration.

```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT, subcategory TEXT,
    account TEXT, project TEXT, member TEXT, merchant TEXT,
    note TEXT,
    trans_date TEXT NOT NULL,
    is_deleted INTEGER DEFAULT 0
);
```

## CI/CD

GitHub Actions automatically:
1. Push master → Run tests → Build Docker → Push to 3 registries
2. Push tag v* → Same as above + version tag
