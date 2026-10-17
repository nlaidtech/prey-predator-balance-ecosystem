@echo off
cd /d "%~dp0"
echo Starting Predator-Prey Wildlife Ecosystem...
"C:\Users\kurtr\AppData\Local\Programs\Python\Python312\python.exe" src/main.py
if errorlevel 1 (
    echo.
    echo Simulation encountered an issue.
    pause
)
