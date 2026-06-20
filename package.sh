#!/usr/bin/env bash
# package.sh - Cross-compile and package the skill for distribution
# Usage: bash package.sh
set -euo pipefail

# Extract version from main.go
VERSION=$(grep -oP 'const version = "\K[^"]+' main.go 2>/dev/null || echo "0.1.0")
echo "=== Packaging ledger-cli v${VERSION} ==="

# Clean previous builds
rm -rf bin dist

# Target platforms
TARGETS=(
  "linux/amd64"
  "linux/arm64"
  "darwin/amd64"
  "darwin/arm64"
  "windows/amd64"
)

# Build all targets
for target in "${TARGETS[@]}"; do
  GOOS="${target%/*}"
  GOARCH="${target#*/}"
  EXT=""
  if [ "$GOOS" = "windows" ]; then EXT=".exe"; fi
  OUT="bin/ledger-cli-${GOOS}-${GOARCH}${EXT}"
  echo "  Building ${GOOS}/${GOARCH} -> ${OUT}"
  CGO_ENABLED=0 GOOS=$GOOS GOARCH=$GOARCH \
    go build -trimpath -ldflags "-s -w" -o "$OUT" .
done

# Create dist directory
mkdir -p dist

# Package skill zip (contains everything a user needs)
SKILL_DIR="dist/ledger-cli"
rm -rf "$SKILL_DIR"
mkdir -p "$SKILL_DIR/bin"

cp SKILL.md README.md main.go "$SKILL_DIR/"
cp bin/ledger-cli-* "$SKILL_DIR/bin/"
cp setup.sh "$SKILL_DIR/"
chmod +x "$SKILL_DIR/setup.sh" "$SKILL_DIR/bin/ledger-cli-"*

# Create zip
cd dist
ZIP_NAME="ledger-cli-${VERSION}-skill.zip"
rm -f "$ZIP_NAME"
if command -v zip &>/dev/null; then
  zip -r "$ZIP_NAME" ledger-cli/
elif command -v powershell &>/dev/null; then
  powershell -Command "Compress-Archive -Path 'ledger-cli' -DestinationPath '$ZIP_NAME'"
else
  echo "ERROR: Neither zip nor powershell found. Cannot create zip."
  exit 1
fi
rm -rf ledger-cli
cd ..

echo ""
echo "=== Done! ==="
echo "Binaries:   bin/"
echo "Skill zip:  dist/${ZIP_NAME}"
echo ""
echo "Upload dist/${ZIP_NAME} to Reasonix Skills or GitHub Release."