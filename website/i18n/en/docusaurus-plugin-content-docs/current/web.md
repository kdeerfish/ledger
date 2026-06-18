---
sidebar_position: 13
---

# 🌐 Web UI

Ledger provides a web-based UI built with Flask + Bootstrap 5.

## Start

```bash
pip install flask flask-cors
python web/run.py
```

Open [http://localhost:5800](http://localhost:5800)

### Docker

```bash
docker run -d --name ledger -p 5800:5800 -v ./data:/data --restart unless-stopped zouzhenglu/ledger:latest
```

## Pages

- **Dashboard**: Summary cards, trend chart, recent transactions
- **Transactions**: Full table with search, filter, CRUD
- **Budgets**: Budget list with progress bars and alerts
- **Categories**: Category hierarchy with stats
- **Stats**: Charts grouped by category/account/month

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `WEB_HOST` | Bind address | `0.0.0.0` |
| `WEB_PORT` | Port | `5800` |
| `WEB_DEBUG` | Debug mode | `false` |
| `LEDGER_DB_PATH` | Database path | `./ledger.db` |
