# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ledger is a personal accounting system with natural language input support. Python Flask backend + React frontend + SQLite storage. The UI and documentation are in Chinese.

## Common Commands

```bash
# Testing
make test              # Run all tests
make test-quick        # Quick tests (short output)
make test-match        # Run tests matching a pattern: make test-match test_transactions
# Or directly:
.venv/Scripts/python.exe -m pytest tests -v
.venv/Scripts/python.exe -m pytest tests -v -k "test_name"

# Lint & Format
make lint              # Ruff check
make lint-fix          # Ruff auto-fix
make format            # Ruff format

# Coverage
make coverage          # Tests + coverage report (generates htmlcov/)

# Run
python web/run.py      # Start Flask web server (default port 5800)
python web/run.py --port 8080 --debug

# Install
pip install -e ".[dev,lint]"

# Frontend
cd frontend && npm run dev     # Vite dev server
cd frontend && npm run build   # Production build to frontend/dist/

# Build (Windows targets — uses PowerShell)
make build             # All builds (Windows EXE + Docker + Skills)
make build-windows     # PyInstaller desktop build → deploy/
make build-docker      # Docker context → deploy/
make build-skills      # AI skill pack → deploy/
```

## Architecture

### Backend (`ledger_modules/`)

Core business logic modules, all sharing a module-level `DB_PATH` variable:

- **`db.py`** — SQLite schema, migrations (`DB_VERSION`), tag CRUD. Schema changes require bumping `DB_VERSION` and adding migration logic in `init_db()`.
- **`transactions.py`** — CRUD for transactions, search/filter/export/statistics. Duplicate checking on add (same day+type+amount+category).
- **`budgets.py`** — Budget management (set/check/templates) + record templates.
- **`import_engine.py`** — CSV import with encoding detection, column name inference, value normalization, dedup.
- **`export_engine.py`** — CSV/JSON export.
- **`agent.py`** — LLM integration (OpenAI/Claude/DeepSeek/Ollama/Qwen/etc.) with tool-calling for transaction operations.
- **`agent_config_store.py`** — Multi-config storage for AI agent settings.
- **`config.py`** — Loads `.env` file and resolves `LEDGER_DB_PATH`. Every module calls `get_db_path()` at import time.

### Web Layer (`web/`)

- **`app.py`** — Flask API (1400+ lines). All routes, `sync_db_path()` to keep modules in sync, `MethodOverrideMiddleware` for PUT/DELETE via `?_method=` query param.
- **`agent_routes.py`** — Agent API routes, provider configuration (PROVIDERS_CONFIG with 20+ LLM providers), model listing.
- **`run.py`** — Entry point, argument parsing, starts Flask dev server.

### Frontend (`frontend/`)

React 19 + Vite 8 + Bootstrap 5. **No TypeScript — pure JSX only.** Uses React Router 7 for routing, Chart.js for stats visualizations. Pages: Dashboard, Transactions, Budgets, Categories, Stats, Import, Export, More. The `AgentChat.jsx` component provides an AI chat widget.

### Tests (`tests/`)

pytest with `temp_db` fixture (each test gets an isolated SQLite DB in a temp dir, auto-cleaned). `sample_db` fixture inserts 5 sample transactions. Tests patch `DB_PATH` on `db_module`, `tx_module`, and `budget_module` simultaneously.

### Skills (`skills/ledger/`)

MCP-compatible skill pack for AI agent integration. Contains SKILL.md, reference docs, examples, and scripts.

## Key Patterns & Gotchas

- **DB_PATH synchronization**: Every module has its own `DB_PATH` at module level. `web/app.py` calls `sync_db_path()` to keep them aligned. Tests do the same via `conftest.py`. If you add a new module that touches the DB, it needs the same pattern.
- **Soft deletes**: Transactions use `is_deleted` flag. Most queries filter `WHERE is_deleted = 0`.
- **Method override**: The Flask app wraps WSGI with `MethodOverrideMiddleware` — clients that can't send PUT/DELETE use `POST` with `?_method=PUT`.
- **Encoding**: Windows GBK encoding is handled throughout (`_safe_print()` in transactions, `PYTHONUTF8=1` env in app.py).
- **Migrations**: Schema changes go in `db.py:init_db()` with version checks against `DB_VERSION`. Always add `PRAGMA table_info` checks before `ALTER TABLE`.
- **Config**: `.env` file at project root for `LEDGER_DB_PATH`, `WEB_HOST`, `WEB_PORT`, `WEB_DEBUG`, `WEB_CORS_ORIGINS`.
- **Makefile is Windows-centric**: Uses PowerShell for build targets. `PYTHON` is set to `.venv\Scripts\python.exe`.
