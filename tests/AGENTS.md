# tests

pytest test suite for Ledger.

## STRUCTURE

```
tests/
├── conftest.py        # Shared fixtures (temp_db, sample_db)
├── test_api_integration.py  # API endpoint tests (501 lines)
├── test_transactions.py     # Transaction CRUD tests
├── test_budgets.py          # Budget feature tests
├── test_import_engine.py    # CSV import tests
├── test_export_engine.py    # Export tests
├── test_db.py               # Database tests
├── test_config.py           # Config tests
└── test_*.py                # Other test files
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Add API test | `test_api_integration.py` | Use Flask test client |
| Add transaction test | `test_transactions.py` | Unit tests for CRUD |
| Add fixture | `conftest.py` | `temp_db` creates fresh DB |

## CONVENTIONS

- Every test gets fresh DB via `temp_db` fixture
- Use `sample_db` for tests needing sample data
- Test files named `test_*.py`
- Functions named `test_*`
- Use `get_rows()` helper for DB assertions

## ANTI-PATTERNS

- **DO NOT** share DB between tests (use `temp_db`)
- **DO NOT** modify `ledger.db` (tests use temp directory)
- **DO NOT** skip cleanup (handled by `temp_db` fixture)
- **ALWAYS** use `sample_db` fixture when testing with data
