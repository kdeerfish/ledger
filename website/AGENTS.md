# website

Docusaurus documentation site for Ledger.

## STRUCTURE

```
website/
├── docusaurus.config.ts  # Main config
├── sidebars.ts           # Sidebar navigation
├── docs/                 # Documentation pages
│   ├── getting-started/
│   ├── user-guide/
│   ├── cli/
│   ├── faq/
│   └── ai-agent/
├── src/
│   ├── pages/            # Custom pages
│   └── css/              # Custom styles
└── static/               # Static assets (images)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add doc page | `docs/` | Create `.md` file |
| Modify sidebar | `sidebars.ts` | Navigation structure |
| Change site config | `docusaurus.config.ts` | Title, URL, theme |
| Add custom page | `src/pages/` | React components |

## CONVENTIONS

- Docs in Markdown format
- Frontmatter for metadata (title, sidebar_position)
- Use Docusaurus admonitions (`:::note`, `:::warning`)
- Deploy to GitHub Pages via CI/CD

## ANTI-PATTERNS

- **DO NOT** commit `build/` directory
- **DO NOT** modify `docusaurus.config.ts` without testing
- **ALWAYS** use relative links for internal docs
- **ALWAYS** add frontmatter to new doc pages
