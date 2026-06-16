#!/usr/bin/env bash
# Run the GUI on macOS
set -e
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Run ./setup_mac.sh first"
    exit 1
fi

source venv/bin/activate
exec python src/main.py "$@"
