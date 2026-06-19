# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased] - rewrite/go

### Changed
- **Full rewrite in Go** — replaces the original Python/Flask + React stack.
  - Cobra CLI replacing `scripts/cli.py` (30+ sub-commands)
  - chi HTTP router replacing Flask `web/app.py` (30+ routes)
  - `modernc.org/sqlite` (pure Go, no CGO) replacing Python `sqlite3`
  - Viper + slog replacing Python `config.py` + `logging`
  - `embed.FS` for single-binary SPA distribution
- Response format `{success, data, error}` is preserved verbatim so the
  React frontend and existing agents require zero changes.

### Performance
- Single binary (~20 MB) replaces Python 3.10+ Flask image (~110 MB)
- Cold start: <50 ms (was ~600 ms for Python)
- `go test -race ./...` runs in <5 s

### CI / CD
- Multi-OS / multi-arch build matrix (linux/amd64, linux/arm64,
  windows/amd64, darwin/amd64, darwin/arm64)
- GoReleaser for cross-platform binaries + Docker images
- Docker images pushed to Docker Hub, ghcr.io, and Aliyun Container Registry

## [0.1.0] - 2026-06-XX — master (legacy Python)

Initial public release. Personal accounting system with Flask API,
React frontend, Docusaurus docs, and Docker multi-registry publishing.

[0.1.0]: https://github.com/kdeerfish/ledger/releases/tag/v0.1.0
