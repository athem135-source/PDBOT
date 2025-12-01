@echo off
REM ============================================
REM PDBOT Cloudflare Tunnel - External Access
REM Version 2.4.9
REM ============================================

title PDBOT Cloudflare Tunnel

echo.
echo  ========================================
echo    PDBOT External Access via Cloudflare
echo    Government of Pakistan
echo  ========================================
echo.

cd /d "%~dp0"

REM Check if API is running
echo [1/2] Checking if Widget API is running...
curl -s http://localhost:5000/health >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo       [ERROR] Widget API not running!
    echo       Please start PDBOT first using: start_pdbot.bat
    echo.
    pause
    exit /b 1
)
echo       Widget API is running on port 5000

REM Start Cloudflare Tunnel
echo [2/2] Starting Cloudflare Tunnel...
echo.
echo  ========================================
echo    EXTERNAL ACCESS ENABLED
echo    Share the URL below with any device!
echo  ========================================
echo.
echo    Starting tunnel to localhost:5000...
echo    (Look for the https://*.trycloudflare.com URL)
echo.
echo  ========================================
echo.

cloudflared tunnel --url http://localhost:5000

pause
