@echo off
REM ============================================
REM PDBot Quick Start - v0.6.0
REM One-click setup and launch
REM ============================================

echo.
echo ========================================
echo    PDBot Quick Start
echo ========================================
echo.

REM Check if this is first run
IF NOT EXIST ".venv\Scripts\activate.bat" (
  echo First-time setup detected. This will take 2-5 minutes...
  echo.
  call setup.bat
  IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Setup failed. Please check errors above.
    pause
    exit /b 1
  )
  echo.
  echo Setup complete! Launching app...
  echo.
) ELSE (
  echo Environment ready. Launching app...
  echo.
)

REM Run the app
call run.bat
