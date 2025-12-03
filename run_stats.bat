@echo off
REM ============================================
REM PDBOT Statistics Dashboard Launcher v2.5.0
REM ============================================
REM Launches the real-time statistics dashboard
REM Requires: PDBOT Widget API running on port 5000
REM ============================================

title PDBOT Statistics Dashboard
cd /d "%~dp0"

echo.
echo  ========================================
echo     PDBOT Statistics Dashboard
echo  ========================================
echo.
echo  This dashboard shows real-time stats from the PDBOT server.
echo  Make sure the server is running first (run_widget.ps1)
echo.
echo  Press any key to start...
pause > nul

REM Run the PowerShell dashboard with Watch mode for auto-refresh
powershell -ExecutionPolicy Bypass -File ".\stats_dashboard.ps1" -Watch

pause
