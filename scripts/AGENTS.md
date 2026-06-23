# scripts

CLI utilities and build scripts for Ledger.

## STRUCTURE

```
scripts/
├── cli.py             # Main CLI entry point
├── import_ledger.py   # CSV import CLI
├── deploy.py          # Deployment script
├── release.py         # Release packaging
├── build_entry.py     # PyInstaller entry
├── desktop_entry.py   # Desktop app entry
├── webview_api.py     # Webview API helpers
├── test_api.py        # Manual API testing
└── auto_test.py       # Auto test runner
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Add CLI command | `cli.py` | argparse-based |
| Add import source | `import_ledger.py` | CSV parsing logic |
| Modify release | `release.py` | Git tagging + packaging |

## CONVENTIONS

- CLI uses argparse (no click/typer)
- Scripts can be run standalone or via Makefile
- `cli.py` is the main entry: `make cli <command>`

## ANTI-PATTERNS

- **DO NOT** add dependencies (keep requirements.txt minimal)
- **DO NOT** hardcode paths (use `ROOT_DIR` relative)
- **ALWAYS** use `if __name__ == '__main__'` guard
