@echo off
setlocal EnableDelayedExpansion

REM ============================================
REM PDBot Troubleshooting & Diagnostics - v2.0.1
REM Checks Python, venv, key packages, Ollama, Qdrant, ports, disk
REM Default Qdrant port: 6333 (override via .env QDRANT_PORT or PNDBOT_QDRANT_URL)
REM ============================================

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%\.." >NUL

REM Resolve Qdrant URL
set "QDRANT_PORT=6333"
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
echo    PDBot System Diagnostics (v2.0.1)
echo ========================================
echo.

echo [1] Checking Python installation...
py --version >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo [ERROR] Python not found in PATH
  echo Install from: https://www.python.org/downloads/
) ELSE (
  for /f "tokens=2" %%i in ('py --version 2^>^&1') do echo [OK] Python %%i
)
echo.

echo [2] Checking virtual environment...
IF EXIST ".venv\Scripts\activate.bat" (
  echo [OK] Virtual environment exists
  call ".venv\Scripts\activate"
  python --version
) ELSE (
  echo [ERROR] Virtual environment not found
  echo Run: scripts\setup.bat
)
echo.

echo [3] Checking Python packages...
IF EXIST ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate"
  echo Checking critical packages...
  python -c "import streamlit; print('[OK] streamlit v' + streamlit.__version__)" 2>NUL || echo [ERROR] streamlit not installed
  python -c "import transformers; print('[OK] transformers v' + transformers.__version__)" 2>NUL || echo [ERROR] transformers not installed
  python -c "import sentence_transformers; print('[OK] sentence-transformers v' + sentence_transformers.__version__)" 2>NUL || echo [ERROR] sentence-transformers not installed
  python -c "import qdrant_client; print('[OK] qdrant-client v' + qdrant_client.__version__)" 2>NUL || echo [ERROR] qdrant-client not installed
  python -c "import langchain; print('[OK] langchain v' + langchain.__version__)" 2>NUL || echo [ERROR] langchain not installed
)
echo.

echo [4] Checking Ollama (LLM Backend)...
ollama --version >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo [ERROR] Ollama not installed
  echo Install: https://ollama.com/
) ELSE (
  for /f "tokens=*" %%i in ('ollama --version 2^>^&1') do echo [OK] %%i
  echo   Tip: verify your model with `ollama list` (default expected: mistral:latest)
)
echo.

echo [5] Checking Qdrant (Vector Database) at %QDRANT_URL%...
curl --silent --max-time 2 "%QDRANT_URL%/health" >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo [ERROR] Qdrant not responding at %QDRANT_URL%
  echo Start: docker run -d -p %QDRANT_PORT%:6333 -v %%cd%%\qdrant_storage:/qdrant/storage --name qdrant qdrant/qdrant
) ELSE (
  echo [OK] Qdrant is running
  curl --silent "%QDRANT_URL%/collections" 2>NUL
)
echo.

echo [6] Checking network ports...
netstat -an | findstr "8501" >NUL
IF %ERRORLEVEL% EQU 0 (
  echo [WARN] Port 8501 is in use (Streamlit may use 8502)
) ELSE (
  echo [OK] Port 8501 is available
)
echo.

echo [7] Checking disk space...
for /f "tokens=3" %%a in ('dir /-c ^| find "bytes free"') do echo [OK] Free space: %%a bytes
echo.

echo ========================================
echo    Diagnostic Summary
echo ========================================
echo.
echo If you see [ERROR] above, fix those issues first.
echo Then run: scripts\start.bat
echo.
echo Need more help? Check QUICKSTART.md
echo.

pause

popd >NUL
endlocal
