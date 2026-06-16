@echo off
:: Build Windows .exe
:: Requires: setup_win.bat to have been run first
cd /d "%~dp0"

if not exist "venv\" (
    echo Run setup_win.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo === Building Windows .exe ===
pip install pyinstaller -q

if exist dist\ПротоколСборщик.exe del dist\ПротоколСборщик.exe
pyinstaller build.spec --clean --noconfirm

echo.
echo === Done ===
echo File: dist\ПротоколСборщик.exe
pause
