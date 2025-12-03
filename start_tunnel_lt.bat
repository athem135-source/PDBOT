@echo off
REM PDBOT localtunnel - Fixed URL
REM Permanent URL: https://pdbot-gop.loca.lt
title PDBOT localtunnel
cd /d "%~dp0"

echo.
echo  ========================================
echo    PDBOT External Access (localtunnel)
echo    URL: https://pdbot-gop.loca.lt
echo  ========================================
echo.

where lt >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo   [ERROR] localtunnel not installed!
    echo   Install: npm install -g localtunnel
    pause
    exit /b 1
)

echo [1/2] Checking Widget API...
curl -s http://localhost:5000/health >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo       Starting API...
    start "PDBOT API" /min cmd /c "cd /d %~dp0 && .venv\Scripts\python.exe widget_api.py"
    timeout /t 15 /nobreak >nul
)
echo       [OK] API running

echo [2/2] Starting localtunnel...
echo.
echo  Opening: https://pdbot-gop.loca.lt
start "" "https://pdbot-gop.loca.lt"
echo.

lt --port 5000 --subdomain pdbot-gop
pause
