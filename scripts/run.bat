@echo off
setlocal EnableDelayedExpansion

REM ============================================
REM PDBot Run Script - v2.0.0
REM Quick launch with automatic setup if needed
REM Default Qdrant port: 6338 (override via .env QDRANT_PORT or PNDBOT_QDRANT_URL)
REM ============================================

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%\.." >NUL

REM Derive Qdrant URL
set "QDRANT_PORT=6338"
if exist ".env" (
  for /f "tokens=2 delims==" %%i in ('findstr /r "^QDRANT_PORT=" ".env"') do set "QDRANT_PORT=%%i"
)
if defined PNDBOT_QDRANT_URL (
  set "QDRANT_URL=%PNDBOT_QDRANT_URL%"
) else if defined QDRANT_URL (
  set "QDRANT_URL=%QDRANT_URL%"
) else (
  set "QDRANT_URL=http://localhost:%QDRANT_PORT%"
)

echo.
echo ========================================
echo    PDBot - Launching Chatbot (v2.0.0)
echo ========================================
echo.

REM Check if setup is needed
IF NOT EXIST ".venv\Scripts\activate.bat" (
  echo [!] Virtual environment not found.
  echo [!] Running setup.bat first...
  echo.
  call "%SCRIPT_DIR%setup.bat"
  IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Setup failed. Please fix errors above.
    goto :end
  )
  echo.
)

REM Activate environment
echo [1/3] Activating virtual environment...
call ".venv\Scripts\activate"
IF %ERRORLEVEL% NEQ 0 (
  echo [ERROR] Failed to activate virtual environment.
  goto :end
)
echo [OK] Environment activated
echo.

REM Quick service check
echo [2/3] Checking services...
set SERVICES_OK=1

ollama --version >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo [WARN] Ollama not detected - install from https://ollama.com/
  set SERVICES_OK=0
) ELSE (
  echo [OK] Ollama ready
)

curl --silent --max-time 2 "%QDRANT_URL%/health" >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo [WARN] Qdrant not running - start with: docker run -d -p %QDRANT_PORT%:6333 -v %%cd%%\qdrant_storage:/qdrant/storage --name qdrant qdrant/qdrant
  set SERVICES_OK=0
) ELSE (
  echo [OK] Qdrant ready at %QDRANT_URL%
)
echo.

IF !SERVICES_OK! EQU 0 (
  echo [INFO] Some services are offline. App will run in limited mode.
  echo Press Ctrl+C to cancel, or wait 5 seconds to continue...
  timeout /t 5 >NUL
  echo.
)

REM Launch app
set "PNDBOT_QDRANT_URL=%QDRANT_URL%"
echo [3/3] Starting Streamlit app...
echo.
echo ========================================
echo    App URL: http://localhost:8501
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

streamlit run "src\app.py" --server.port 8501

:end
popd >NUL
endlocal
