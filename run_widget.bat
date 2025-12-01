@echo off
REM ============================================
REM PDBOT Widget - Quick Start
REM Government of Pakistan - Ministry of Planning
REM Version 2.4.0
REM ============================================

title PDBOT Widget v2.4.0

echo.
echo  ========================================
echo   🤖 PDBOT Widget v2.4.0
echo   Government of Pakistan
echo   Ministry of Planning, Development
echo   ^& Special Initiatives
echo  ========================================
echo.
echo  Starting Widget API + React Frontend...
echo.

REM Check Python is available
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

REM Check Node.js is available
where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js/npm not found! Please install Node.js
    pause
    exit /b 1
)

REM Start API server in background
echo [1/2] Starting Widget API Server (port 5000)...
start /B "PDBOT API" cmd /c "cd /d %~dp0 && python widget_api.py"

REM Wait for API to initialize
timeout /t 3 /nobreak >nul

REM Start React widget
echo [2/2] Starting React Widget...
echo.
echo  ========================================
echo   Widget will open at:
echo   🌐 http://localhost:3000
echo   📱 Access from phone via same network
echo  ========================================
echo.

cd /d "%~dp0frontend-widget"
call npm run dev

pause
