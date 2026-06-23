# ledger_modules

Core business logic for Ledger accounting system.

## STRUCTURE

```
ledger_modules/
├── db.py              # Database schema, migrations, tag helpers
├── transactions.py    # CRUD, search, import, statistics (525 lines)
├── budgets.py         # Budget management, templates
├── import_engine.py   # CSV import with mapping (681 lines)
├── export_engine.py   # CSV/JSON export (527 lines)
├── config.py          # Environment config, DB path
└── desktop_config.py  # Windows desktop settings
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Add DB column | `db.py` | Update `DB_VERSION` + migration logic |
| Modify transaction CRUD | `transactions.py` | Uses global `DB_PATH` |
| Add budget feature | `budgets.py` | Dimension-based budgets |
| Change import format | `import_engine.py` | Column mapping system |
| Add export format | `export_engine.py` | Template-based |

## CONVENTIONS

- All modules use `DB_PATH` global (set via `sync_db_path()` from web/app.py)
- Database version tracked in `meta` table, auto-migrates on startup
- Soft delete via `is_deleted` column (not physical delete)
- Tags many-to-many via `transaction_tags` junction table

## ANTI-PATTERNS

- **DO NOT** hardcode DB path - always use `DB_PATH` global
- **DO NOT** skip migration version check in `db.py`
- **ALWAYS** close SQLite connections (no connection pooling)
- **ALWAYS** use parameterized queries (no string formatting for SQL)
