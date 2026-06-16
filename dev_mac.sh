#!/usr/bin/env bash
# Режим разработки: автоперезапуск GUI при сохранении файлов
set -e
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Сначала запустите ./setup_mac.sh"
    exit 1
fi

source venv/bin/activate

if ! python -c "import watchdog" 2>/dev/null; then
    echo "Устанавливаю dev-зависимости…"
    pip install -r requirements-dev.txt -q
fi

exec python scripts/dev_watch.py "$@"
