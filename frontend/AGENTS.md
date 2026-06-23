# frontend

React + Vite frontend for Ledger.

## STRUCTURE

```
frontend/src/
├── App.jsx            # Router setup
├── main.jsx           # Entry point
├── api/index.js       # API client functions
├── components/        # Reusable UI components
│   ├── Layout.jsx     # App shell with nav
│   ├── TransactionForm.jsx
│   └── TagSelector.jsx
└── pages/             # Route pages
    ├── Dashboard.jsx
    ├── Transactions.jsx
    ├── Budgets.jsx
    ├── Categories.jsx
    ├── Stats.jsx
    ├── Import.jsx
    ├── Export.jsx
    └── More.jsx
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new page | `src/pages/` + update `App.jsx` router |
| Add API call | `src/api/index.js` | Centralized API client |
| Add shared component | `src/components/` | Layout, forms, selectors |
| Modify charts | `Stats.jsx`, `Dashboard.jsx` | Chart.js via react-chartjs-2 |

## CONVENTIONS

- Pure JSX (no TypeScript)
- Bootstrap 5 for styling (CDN or npm)
- React Router v7 for routing
- Chart.js for data visualization
- API calls via `src/api/index.js`

## ANTI-PATTERNS

- **DO NOT** add TypeScript files
- **DO NOT** use CSS modules (use Bootstrap classes)
- **DO NOT** add Redux/state management (use React state)
- **ALWAYS** use `api/index.js` for backend calls
