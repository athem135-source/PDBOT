@echo off
setlocal EnableDelayedExpansion

REM ============================================
REM PDBot Setup Script - v2.0.0
REM Creates venv, installs dependencies, validates services
REM Default Qdrant port: 6338 (falls back to .env QDRANT_PORT if set)
REM ============================================

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%\.." >NUL

REM Resolve Qdrant port from .env if provided
set "QDRANT_PORT=6338"
if exist ".env" (
  for /f "tokens=2 delims==" %%i in ('findstr /r "^QDRANT_PORT=" ".env"') do set "QDRANT_PORT=%%i"
)
set "QDRANT_URL=http://localhost:%QDRANT_PORT%"

echo.
echo ========================================
echo    PDBot Setup - v2.0.0
echo ========================================
echo.

REM Check Python installation
echo [1/6] Checking Python installation...
py --version >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo [ERROR] Python not found. Install Python 3.10+ from https://www.python.org/
  goto :end
)
for /f "tokens=2" %%i in ('py --version 2^>^&1') do set "PYVER=%%i"
echo [OK] Python !PYVER! detected
echo.

REM Create virtual environment
echo [2/6] Setting up virtual environment...
IF NOT EXIST ".venv\Scripts\activate.bat" (
  echo Creating .venv...
  py -m venv .venv
  IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to create virtual environment.
    goto :end
  )
  echo [OK] Virtual environment created
) ELSE (
  echo [OK] Virtual environment already exists
)
echo.

REM Activate and upgrade pip/setuptools/wheel
echo [3/6] Activating environment and upgrading pip...
call ".venv\Scripts\activate"
python -m pip install --upgrade pip setuptools wheel --quiet
echo [OK] Pip toolchain upgraded
echo.

REM Install dependencies
echo [4/6] Installing Python dependencies...
IF EXIST requirements.txt (
  echo This may take a few minutes on first run...
  pip install -r requirements.txt --quiet
  IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Dependency installation failed. Check your internet connection.
    goto :end
  )
  echo [OK] All dependencies installed
) ELSE (
  echo [ERROR] requirements.txt not found.
  goto :end
)
echo.

REM Optional: ensure NLTK punkt for sentence tokenization (silent if already present)
echo [5/6] Ensuring NLTK punkt tokenizer...
python - <<PY
try:
    import nltk
    nltk.data.find("tokenizers/punkt")
    print("[OK] NLTK punkt already available")
except LookupError:
    import nltk
    nltk.download("punkt", quiet=True)
    print("[OK] NLTK punkt downloaded")
except Exception as e:
    print(f"[WARN] Could not verify/download NLTK punkt: {e}")
PY
echo.

REM Validate services
echo [6/6] Validating external services...
echo.
echo   Checking Ollama (LLM backend)...
ollama --version >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo   [WARN] Ollama not detected.
  echo   Install from: https://ollama.com/
) ELSE (
  for /f "tokens=*" %%i in ('ollama --version 2^>^&1') do set "OLLAMA_VER=%%i"
  echo   [OK] Ollama detected: !OLLAMA_VER!
  echo   Tip: set OLLAMA_MODEL in .env (default: mistral:latest)
)
echo.
echo   Checking Qdrant (Vector DB) at %QDRANT_URL%...
curl --silent --max-time 2 "%QDRANT_URL%/health" >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo   [WARN] Qdrant not responding at %QDRANT_URL%
  echo   Install: https://qdrant.tech/documentation/quick-start/
  echo   Or run (with persistent storage):
  echo     docker run -d -p %QDRANT_PORT%:6333 -v %%cd%%\qdrant_storage:/qdrant/storage --name qdrant qdrant/qdrant
) ELSE (
  echo   [OK] Qdrant service is running
)
echo.

echo ========================================
echo    Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1) run.bat          (Windows CMD)
echo   2) .\run.ps1        (PowerShell)
echo.
echo The app will open at http://localhost:8501
echo.

:end
popd >NUL
endlocal
