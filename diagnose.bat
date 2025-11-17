@echo off
REM ============================================
REM PDBot Troubleshooting & Diagnostics
REM ============================================

echo.
echo ========================================
echo    PDBot System Diagnostics
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
  echo Run: setup.bat
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
  echo.
  echo Checking models...
  ollama list
)
echo.

echo [5] Checking Qdrant (Vector Database)...
curl --silent --max-time 2 http://localhost:6333/health >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo [ERROR] Qdrant not responding on port 6333
  echo Start: docker run -d -p 6333:6333 qdrant/qdrant
) ELSE (
  echo [OK] Qdrant is running
  curl --silent http://localhost:6333/collections 2>NUL
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
echo Then run: start.bat
echo.
echo Need more help? Check QUICKSTART.md
echo.

pause
