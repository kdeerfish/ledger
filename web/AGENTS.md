# web

Flask API server for Ledger.

## STRUCTURE

```
web/
├── app.py             # Main Flask app, all routes (1421 lines)
├── run.py             # Entry point
├── agent_routes.py    # AI agent API endpoints
├── __init__.py        # Package init
├── static/            # Static assets
└── templates/         # Legacy HTML templates
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add API route | `app.py` | Use `@app.route('/api/...')` |
| Add page route | `app.py` | Catch-all serves React SPA |
| Modify agent API | `agent_routes.py` | AI integration endpoints |

## CONVENTIONS

- All API routes return `api_success()` or `api_error()`
- PUT/DELETE via `?_method=PUT` (MethodOverrideMiddleware)
- Use `require_json` decorator for POST/PUT with JSON body
- Call `sync_db_path()` at start of each route handler
- CORS configured via `WEB_CORS_ORIGINS` env var

## ANTI-PATTERNS

- **DO NOT** add routes without `sync_db_path()` call
- **DO NOT** use `request.json` directly - use `@require_json` decorator
- **ALWAYS** return `api_success()` or `api_error()` (not raw jsonify)
- **ALWAYS** handle exceptions and return `api_error()` with message
