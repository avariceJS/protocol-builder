@echo off
:: Setup for Windows: creates venv and installs all dependencies
cd /d "%~dp0"

echo === Protocol Builder: Setup (Windows) ===

:: Check Python 3.11+
python --version 2>nul | findstr /R "3\.[1-9][1-9]" >nul
if errorlevel 1 (
    echo ERROR: Python 3.11+ required.
    echo Download: https://python.org/downloads/
    pause
    exit /b 1
)

:: Create venv
if not exist "venv\" (
    python -m venv venv
    echo Created venv\
)

call venv\Scripts\activate.bat

:: Install dependencies
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo.
echo === Setup complete ===
echo Run: run_win.bat
pause
