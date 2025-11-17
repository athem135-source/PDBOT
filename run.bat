@echo off
setlocal EnableDelayedExpansion

REM ============================================
REM PDBot Run Script - v0.6.0
REM Quick launch with automatic setup if needed
REM ============================================

echo.
echo ========================================
echo    PDBot - Launching Chatbot
echo ========================================
echo.

REM Check if setup is needed
IF NOT EXIST ".venv\Scripts\activate.bat" (
  echo [!] Virtual environment not found.
  echo [!] Running setup.bat first...
  echo.
  call setup.bat
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

curl --silent --max-time 2 http://localhost:6333/health >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo [WARN] Qdrant not running - start with: docker run -p 6333:6333 qdrant/qdrant
  set SERVICES_OK=0
) ELSE (
  echo [OK] Qdrant ready
)
echo.

IF !SERVICES_OK! EQU 0 (
  echo [INFO] Some services are offline. App will run in limited mode.
  echo Press Ctrl+C to cancel, or wait 5 seconds to continue...
  timeout /t 5 >NUL
  echo.
)

REM Launch app
echo [3/3] Starting Streamlit app...
echo.
echo ========================================
echo    App URL: http://localhost:8501
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

streamlit run src\app.py

:end
endlocal
