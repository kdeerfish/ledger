# skills

AI agent skill packs for Ledger integration.

## STRUCTURE

```
skills/ledger/
├── SKILL.md            # Skill documentation
├── .env.example        # Environment template
├── examples/           # Usage examples
└── references/         # API references
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Update skill docs | `SKILL.md` | Main documentation |
| Add example | `examples/` | Code snippets |
| Add API reference | `references/` | Endpoint docs |

## CONVENTIONS

- Skill pack is self-contained in `skills/ledger/`
- `.env.example` shows required environment variables
- References document the REST API endpoints
- Examples show integration patterns

## ANTI-PATTERNS

- **DO NOT** include real API keys in examples
- **DO NOT** hardcode URLs (use environment variables)
- **ALWAYS** update SKILL.md when adding features
- **ALWAYS** provide working examples
