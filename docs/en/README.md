---
layout: default
title: Ledger Documentation
---

# 📒 Ledger — Personal Accounting System

**Income & Expense Management · Budget Planning · Multi-dimensional Statistics · Web UI · AI Agent Integration**

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| ✅ **Transaction Management** | Add / Edit / Soft-delete / Restore / Hard-delete |
| ✅ **CSV Import** | One-click import from随手记 (SuiShouJi) format |
| ✅ **Search & Filter** | By keyword, category, account, merchant, date range |
| ✅ **Statistics** | Group by category/account/month, cross-analysis |
| ✅ **Budget Management** | Monthly budget by category, real-time tracking |
| ✅ **Budget Templates** | Create, apply, smart recommendation |
| ✅ **Record Templates** | One-click recurring transactions |
| ✅ **Export** | CSV / JSON format |
| ✅ **Web UI** | Flask + Bootstrap 5, responsive design |
| ✅ **AI Agent** | JSON API for picoclaw and other agents |
| ✅ **Docker** | Multi-registry: Docker Hub / ghcr.io / Alibaba Cloud |

---

## 🚀 Quick Start

```bash
# Install
pip install -e ".[dev,lint]"

# Add an expense
python scripts/cli.py add --type expense --amount 100 --category 食品 --account 微信

# List transactions
python scripts/cli.py list

# Summary
python scripts/cli.py summary
```

## 🐳 Docker

```bash
docker pull zouzhenglu/ledger:latest
docker run -d --name ledger -p 5800:5800 -v ./data:/data --restart unless-stopped zouzhenglu/ledger:latest
```

---

## 📚 Documentation

- [CLI Reference](../cli.md)
- [Web UI Guide](../web.md)
- [Docker Deployment](../docker.md)
- [API Reference](../api.md)
- [Development Guide](../development.md)

---

<div align="center">

[GitHub](https://github.com/kdeerfish/ledger) · [Issues](https://github.com/kdeerfish/ledger/issues)

</div>
