@echo off
:: Build Windows installer (Setup.exe)
:: Requires: setup_win.bat, Inno Setup 6 — https://jrsoftware.org/isinfo.php
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
if errorlevel 1 (
    echo PyInstaller build failed
    pause
    exit /b 1
)

set "ISCC="
for %%I in (
    "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    "%ProgramFiles%\Inno Setup 6\ISCC.exe"
) do (
    if exist %%I set "ISCC=%%~I"
)

if not defined ISCC (
    echo Inno Setup 6 not found. Install from https://jrsoftware.org/isinfo.php
    echo Portable .exe is ready: dist\ПротоколСборщик.exe
    pause
    exit /b 1
)

echo === Building installer ===
if not exist installer_output mkdir installer_output
"%ISCC%" installer\ProtocolBuilder.iss
if errorlevel 1 (
    echo Installer build failed
    pause
    exit /b 1
)

echo.
echo === Done ===
echo Portable:  dist\ПротоколСборщик.exe
echo Installer: installer_output\ПротоколСборщик_Setup.exe
pause
