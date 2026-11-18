@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title IMMY - сборка exe
cd /d "%~dp0"

echo ============================================
echo   IMMY v8.0 - сборка игры в exe
echo ============================================
echo.

where git >nul 2>nul
if %errorlevel%==0 (
    echo [1/3] Проверка обновлений репозитория...
    git fetch origin
    for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set "BRANCH=%%b"
    git pull --ff-only origin !BRANCH!
    if errorlevel 1 (
        echo [!] Не удалось обновить репозиторий - собираю текущие файлы.
    ) else (
        echo [+] Репозиторий обновлён.
    )
) else (
    echo [1/3] git не найден - пропускаю проверку обновлений.
)
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [!] Python не найден. Установи Python 3.10+ и добавь его в PATH.
    pause
    exit /b 1
)

echo [2/3] Проверка PyInstaller...
python -c "import PyInstaller" >nul 2>nul
if errorlevel 1 (
    echo     Установка PyInstaller...
    python -m pip install --quiet pyinstaller
)

echo [3/3] Сборка exe...
python -m PyInstaller --onefile --noconsole --name IMMY ^
    --icon "%~dp0assets\icon.ico" ^
    --hidden-import tkinter --hidden-import winsound ^
    main.py
if errorlevel 1 (
    echo [!] Ошибка сборки.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Готово: dist\IMMY.exe
echo   Исходные файлы остаются в папке -
echo   код можно править и пересобрать снова
echo   запуском build.bat
echo ============================================
pause
