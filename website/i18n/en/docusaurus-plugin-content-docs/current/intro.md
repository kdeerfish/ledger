---
sidebar_position: 1
---

# 📒 Ledger Documentation

**Ledger** is a personal accounting system with CLI, Web UI, AI Agent integration, and Docker deployment.

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

## 📦 Image Registries

| Registry | Pull Command | Speed |
|----------|-------------|-------|
| **Docker Hub** | `docker pull zouzhenglu/ledger:latest` | 🌍 Global |
| **ghcr.io** | `docker pull ghcr.io/kdeerfish/ledger:latest` | 🌍 Global |
| **Alibaba Cloud** | `docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest` | 🇨🇳 China fastest |

## 🌟 Project Info

| Item | Link |
|------|------|
| GitHub | [kdeerfish/ledger](https://github.com/kdeerfish/ledger) |
| Issues | [Issues](https://github.com/kdeerfish/ledger/issues) |
| Docker Hub | [zouzhenglu/ledger](https://hub.docker.com/r/zouzhenglu/ledger) |
| License | MIT |
