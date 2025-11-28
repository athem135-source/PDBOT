@echo off
setlocal

REM ============================================
REM PDBot Quick Start - v2.0.0
REM One-click setup and launch from repo root
REM ============================================

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%\.." >NUL

echo.
echo ========================================
echo    PDBot Quick Start (v2.0.0)
echo ========================================
echo.

REM Check if this is first run
IF NOT EXIST ".venv\Scripts\activate.bat" (
  echo First-time setup detected. This may take a few minutes...
  echo.
  call "%SCRIPT_DIR%setup.bat"
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
call "%SCRIPT_DIR%run.bat"

popd >NUL
endlocal
