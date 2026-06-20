#!/usr/bin/env bash
# setup.sh - Auto-detect platform and activate the correct binary
# Run this once after extracting the skill package
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== ledger-cli setup ==="

# Detect OS
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
case "$OS" in
  linux*)  OS="linux" ;;
  darwin*) OS="darwin" ;;
  msys*|mingw*|cygwin*|windowsnt*)
    OS="windows"
    echo "Windows detected. Copying ledger-cli.exe..."
    if [ -f bin/ledger-cli-windows-amd64.exe ]; then
      cp bin/ledger-cli-windows-amd64.exe ledger-cli.exe
      echo "Done! Use: ledger-cli.exe <command>"
    else
      echo "ERROR: bin/ledger-cli-windows-amd64.exe not found"
      exit 1
    fi
    exit 0
    ;;
  *)
    echo "ERROR: Unsupported OS: $OS"
    exit 1
    ;;
esac

# Detect architecture
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64)   ARCH="amd64" ;;
  aarch64|arm64)   ARCH="arm64" ;;
  *)
    echo "ERROR: Unsupported architecture: $ARCH"
    exit 1
    ;;
esac

BINARY="bin/ledger-cli-${OS}-${ARCH}"
if [ ! -f "$BINARY" ]; then
  echo "ERROR: Binary not found: $BINARY"
  echo "Available binaries:"
  ls bin/ledger-cli-* 2>/dev/null || echo "  (none)"
  exit 1
fi

# Make executable and create symlink/copy
chmod +x "$BINARY"
cp "$BINARY" ledger-cli

echo "Platform: ${OS}/${ARCH}"
echo "Binary:   ${BINARY}"
echo "Setup:    ledger-cli (ready to use)"
echo ""
echo "Usage: ./ledger-cli <command>"
echo "Example: ./ledger-cli tx add --type expense --amount 25 --category food"