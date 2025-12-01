@echo off
REM ============================================
REM PDBOT Widget Setup Script
REM Government of Pakistan - Ministry of Planning
REM ============================================

echo.
echo  ========================================
echo   PDBOT React Widget Setup
echo   Government of Pakistan
echo  ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [INFO] Node.js version:
node --version

echo.
echo [INFO] Installing dependencies...
call npm install

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo  ========================================
echo   Setup Complete!
echo  ========================================
echo.
echo   Run 'run-widget.bat' to start the widget
echo.
pause
