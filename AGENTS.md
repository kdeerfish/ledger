# PROJECT KNOWLEDGE BASE

**Generated:** 2026-06-23
**Commit:** 7451fa4
**Branch:** feat/agent-chat

## OVERVIEW

Ledger is a personal accounting system with natural language input support. Python Flask backend + React frontend + Docusaurus documentation. Uses SQLite for storage.

## STRUCTURE

```
ledger-agent-chat/
├── ledger_modules/    # Core business logic (Python)
├── web/               # Flask API server
├── frontend/          # React + Vite UI
├── tests/             # pytest test suite
├── scripts/           # CLI utilities
├── website/           # Docusaurus documentation
├── skills/            # AI agent skill packs
└── docs/              # Markdown documentation
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add API endpoint | `web/app.py` | Flask routes, 1400+ lines |
| Modify business logic | `ledger_modules/` | transactions, budgets, import/export |
| Add React page | `frontend/src/pages/` | Bootstrap 5 + Chart.js |
| Write test | `tests/` | pytest, fixtures in conftest.py |
| Add CLI command | `scripts/cli.py` | Entry point for CLI |
| Update docs | `website/docs/` | Docusaurus markdown |
| AI integration | `skills/ledger/` | MCP skill pack |

## CONVENTIONS

- **Python**: Flask, SQLite, ruff linter, 120 char line length
- **Frontend**: React 19, Vite 8, Bootstrap 5, no TypeScript
- **Tests**: pytest with temp_db fixture, each test gets fresh DB
- **Build**: Makefile targets, PowerShell on Windows
- **CI/CD**: GitHub Actions (docker-publish, docs, release)

## ANTI-PATTERNS (THIS PROJECT)

- **DO NOT** use TypeScript in frontend (pure JSX)
- **DO NOT** modify DB schema without updating `DB_VERSION` in `db.py`
- **DO NOT** commit `ledger.db` (local dev database)
- **ALWAYS** use `sync_db_path()` before DB operations in `web/app.py`

## COMMANDS

```bash
# Development
make test              # Run all tests
make test-quick        # Quick tests
make lint              # Lint Python code
make format            # Format Python code

# Build
make build             # All builds (Windows + Docker + Skills)
make build-windows     # Windows desktop only
make build-docker      # Docker server only

# Run
make cli               # CLI entry
python web/run.py      # Start web server
```

## NOTES

- Flask app uses `MethodOverrideMiddleware` for PUT/DELETE via `?_method=`
- Frontend proxies to Vite dev server in debug mode (`WEB_DEBUG=true`)
- Database auto-migrates on startup (version tracked in `meta` table)
- Tags system supports "排除统计" tag to exclude transactions from stats
