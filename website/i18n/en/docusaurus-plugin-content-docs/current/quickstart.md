---
sidebar_position: 2
---

# 🚀 Quick Start

## Installation

```bash
# Install dev dependencies
pip install -e ".[dev,lint]"

# Configure env (optional)
cp .env.example .env
```

## First Commands

```bash
# Add an expense
python scripts/cli.py add --type expense --amount 100 --category 食品 --account 微信

# List recent transactions
python scripts/cli.py list

# View summary
python scripts/cli.py summary

# Search transactions
python scripts/cli.py search --keyword 午餐
```

## Web UI

```bash
pip install flask flask-cors
python web/run.py
```

Open [http://localhost:5800](http://localhost:5800)
