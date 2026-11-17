@echo off
setlocal enabledelayedexpansion
title IMMY - sborka exe
cd /d "%~dp0"

echo ============================================
echo   IMMY - sborka igry v exe
echo ============================================
echo.

where git >nul 2>nul
if %errorlevel%==0 (
    echo [1/3] Proverka obnovleniy repozitoriya...
    git fetch origin
    for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set "BRANCH=%%b"
    git pull --ff-only origin !BRANCH!
    if errorlevel 1 (
        echo [!] Ne udalos obnovit repozitoriy - sobirayu tekushchie faily.
    ) else (
        echo [+] Repozitoriy obnovlen.
    )
) else (
    echo [1/3] git ne nayden - propuskayu proverku obnovleniy.
)
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [!] Python ne nayden. Ustanovi Python 3.10+ i dobav' v PATH.
    pause
    exit /b 1
)

echo [2/3] Proverka PyInstaller...
python -c "import PyInstaller" >nul 2>nul
if errorlevel 1 (
    echo     Ustanovka PyInstaller...
    python -m pip install --quiet pyinstaller
)

echo [3/3] Sborka exe...
python -m PyInstaller --onefile --noconsole --name IMMY ^
    --hidden-import tkinter --hidden-import winsound ^
    main.py
if errorlevel 1 (
    echo [!] Oshibka sborki.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Gotovo: dist\IMMY.exe
echo   Ishodnye faily ostayutsya v papke -
echo   kod mozhno pravit i peresobrat snova
echo   zapuskom build.bat
echo ============================================
pause
