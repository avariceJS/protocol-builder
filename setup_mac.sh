#!/usr/bin/env bash
# Setup for macOS: creates venv and installs all dependencies
set -e

cd "$(dirname "$0")"

echo "=== Protocol Builder: Setup (macOS) ==="

# Find a working Python (Homebrew 3.12+ on some macOS builds breaks pyexpat/pip)
PYTHON=""
for cmd in python3.13 python3.12 python3.11 /usr/bin/python3 python3; do
    if command -v "$cmd" &>/dev/null; then
        if "$cmd" -c "from xml.parsers import expat" 2>/dev/null; then
            ver=$("$cmd" -c "import sys; print(sys.version_info[:2])" 2>/dev/null)
            if [[ "$ver" > "(3, 8)" ]]; then
                PYTHON="$cmd"
                break
            fi
        else
            echo "Skip $cmd: pyexpat broken (common with brew python on macOS)"
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: No working Python found."
    echo "Try: brew install python@3.12 && brew install expat"
    echo "Or use system Python: /usr/bin/python3 -m venv venv"
    exit 1
fi

echo "Using: $PYTHON ($($PYTHON --version))"

# Create venv if not exists
if [ ! -d "venv" ]; then
    "$PYTHON" -m venv venv
    echo "Created venv/"
fi

source venv/bin/activate

# Upgrade pip silently
pip install --upgrade pip -q

# Install dependencies
pip install -r requirements.txt -q
echo ""
echo "=== Setup complete ==="
echo "Run:  ./run_mac.sh"
