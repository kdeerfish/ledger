#!/usr/bin/env bash
# Ledger AI Agent skill entrypoint.
#
# The skill is a thin shim around the `ledger` binary. By default it calls
# the locally-built binary (`./bin/ledger` from the repo root). Override via
# the LEDGER_BIN environment variable.
#
# All HTTP operations go through the JSON API; the CLI is used for shell
# ergonomics only. See ./references for the full capability list.

set -euo pipefail

# Locate the ledger binary. Search order:
#   1. $LEDGER_BIN (explicit)
#   2. ./bin/ledger.exe (Windows dev build)
#   3. ./bin/ledger   (Unix dev build)
#   4. ledger in PATH  (installed via `go install` or Homebrew)
LEDGER_BIN="${LEDGER_BIN:-}"
if [[ -z "$LEDGER_BIN" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
  if [[ -x "$REPO_ROOT/bin/ledger.exe" ]]; then
    LEDGER_BIN="$REPO_ROOT/bin/ledger.exe"
  elif [[ -x "$REPO_ROOT/bin/ledger" ]]; then
    LEDGER_BIN="$REPO_ROOT/bin/ledger"
  elif command -v ledger >/dev/null 2>&1; then
    LEDGER_BIN="$(command -v ledger)"
  else
    echo "❌ ledger binary not found. Build with 'make build' or set LEDGER_BIN." >&2
    exit 1
  fi
fi

exec "$LEDGER_BIN" "$@"
