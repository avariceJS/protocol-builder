#!/usr/bin/env bash
# Build macOS .app bundle
# Requires: ./setup_mac.sh to have been run first
set -e
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Run ./setup_mac.sh first"
    exit 1
fi

source venv/bin/activate

echo "=== Building macOS .app ==="
pip install pyinstaller -q

rm -rf dist/ПротоколСборщик.app dist/ПротоколСборщик build/ПротоколСборщик
pyinstaller build.spec --clean --noconfirm

echo ""
echo "=== Done ==="
echo "App: dist/ПротоколСборщик.app"
echo "Run: open dist/ПротоколСборщик.app"
