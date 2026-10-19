@echo off
title Push to GitHub
cd /d "%~dp0"
echo ========================================================
echo   Pushing Wildlife Ecosystem to GitHub (nlaidtech)
echo ========================================================
echo.
echo Running: git push -u origin main --force
echo.
git push -u origin main --force > push.log 2>&1
type push.log
echo.
if %ERRORLEVEL% equ 0 (
    echo ========================================================
    echo   [SUCCESS] Pushed cleanly to GitHub!
    echo   https://github.com/nlaidtech/prey-predator-balance-ecosystem
    echo ========================================================
) else (
    echo ========================================================
    echo   [NOTICE] If a browser sign-in prompt appeared,
    echo   please click "Sign in with your browser" to authorize.
    echo ========================================================
)
echo.
pause
