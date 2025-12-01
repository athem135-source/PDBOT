@echo off
REM ============================================
REM PDBOT Widget + API Runner
REM Government of Pakistan - Ministry of Planning
REM ============================================

echo.
echo  ========================================
echo   PDBOT Widget + API Server
echo   Government of Pakistan
echo  ========================================
echo.

REM Start the API server in a new window
echo [INFO] Starting Widget API Server (port 5000)...
start "PDBOT Widget API" cmd /c "cd /d %~dp0 && python widget_api.py"

REM Wait for API to start
timeout /t 3 /nobreak >nul

REM Start the React widget
echo [INFO] Starting React Widget (port 3000)...
cd /d "%~dp0frontend-widget"
call npm run dev

pause
