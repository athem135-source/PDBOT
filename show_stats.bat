@echo off
title PDBOT Statistics Dashboard
echo.
echo ============================================================
echo           PDBOT Statistics Dashboard
echo           Launching PowerShell dashboard...
echo ============================================================
echo.

REM Check if server is running first
curl -s http://localhost:5000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] PDBOT server may not be running!
    echo           Start it with: run_widget.ps1
    echo.
    pause
)

REM Launch PowerShell dashboard with watch mode
powershell -ExecutionPolicy Bypass -File "%~dp0stats_dashboard.ps1" -Watch -Interval 5

pause
