@echo off
title Predator-Prey Balance Ecosystem
cd /d "%~dp0"

echo ============================================================
echo   Launching Wildlife Ecosystem Simulation...
echo ============================================================

set "PY_EXE="

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :RUN
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_EXE=python"
    goto :RUN
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_EXE=py"
    goto :RUN
)

:RUN
if defined PY_EXE (
    "%PY_EXE%" main.py
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Simulation exited with error code %errorlevel%.
        pause
    )
) else (
    echo.
    echo [ERROR] Python was not found on your system.
    echo Please ensure Python 3.10+ is installed.
    pause
)
