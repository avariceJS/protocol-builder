@echo off
REM Режим разработки: автоперезапуск GUI при сохранении файлов
cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo Сначала запустите setup_win.bat
    exit /b 1
)

call venv\Scripts\activate.bat

python -c "import watchdog" 2>nul
if errorlevel 1 (
    echo Устанавливаю dev-зависимости…
    pip install -r requirements-dev.txt -q
)

python scripts\dev_watch.py %*
