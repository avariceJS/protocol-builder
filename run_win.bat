@echo off
cd /d "%~dp0"

if not exist "venv\" (
    echo Run setup_win.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python src\main.py
