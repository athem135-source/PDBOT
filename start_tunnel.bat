@echo off
REM PDBOT Cloudflare Tunnel v2.5.0-patch2
title PDBOT Tunnel
cd /d "%~dp0"

echo.
echo  ========================================
echo    PDBOT External Access via Cloudflare
echo  ========================================
echo.

where cloudflared >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo   [ERROR] cloudflared not found!
    echo   Install: winget install Cloudflare.cloudflared
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

echo [2/2] Starting Cloudflare Tunnel...
echo.
echo  ========================================
echo    TUNNEL STARTING - Watch for URL
echo    Share the https URL with anyone!
echo  ========================================
echo.

cloudflared tunnel --url http://localhost:5000
pause
