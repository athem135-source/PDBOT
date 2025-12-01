@echo off
REM ============================================
REM PDBOT Widget Build Script
REM Government of Pakistan - Ministry of Planning
REM ============================================

echo.
echo  ========================================
echo   Building PDBOT Widget for Production
echo  ========================================
echo.

call npm run build

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo  ========================================
echo   Build Complete!
echo  ========================================
echo.
echo   Output files are in the 'dist' folder:
echo   - pdbot-widget.js
echo   - pdbot-widget.css
echo.
echo   To embed in a website, add:
echo   ^<script src="pdbot-widget.js"^>^</script^>
echo.
pause
