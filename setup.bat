@echo off
setlocal EnableDelayedExpansion

REM ============================================
REM PDBot Setup Script - v1.5.0
REM Phase 3 & 4: Behavior Engineering + Query Classification
REM Creates venv, installs dependencies, validates services
REM ============================================

echo.
echo ========================================
echo    PDBot Setup - Complete Installation
echo ========================================
echo.

REM Check Python installation
echo [1/6] Checking Python installation...
py --version >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo [ERROR] Python not found. Install Python 3.10+ from https://www.python.org/
  goto :end
)
for /f "tokens=2" %%i in ('py --version 2^>^&1') do set PYVER=%%i
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

REM Activate and upgrade pip
echo [3/6] Activating environment and upgrading pip...
call ".venv\Scripts\activate"
python -m pip install --upgrade pip --quiet
echo [OK] Pip upgraded
echo.

REM Install dependencies
echo [4/6] Installing Python dependencies...
IF EXIST requirements.txt (
  echo This may take 2-5 minutes on first run...
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

REM Fix Keras 3 compatibility issue
echo [5/6] Fixing Keras compatibility for sentence-transformers...
pip uninstall -y keras >NUL 2>&1
echo [OK] Keras compatibility fixed
echo.

REM Validate services
echo [6/6] Validating external services...
echo.
echo   Checking Ollama (LLM backend)...
ollama --version >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo   [WARN] Ollama not detected.
  echo   Install from: https://ollama.com/
  echo   After installation, this script will auto-install TinyLlama
  echo.
  echo   Manual installation:
  echo     1. Download Ollama: https://ollama.com/download
  echo     2. Run: ollama pull tinyllama
  echo     3. Verify: ollama list
) ELSE (
  for /f "tokens=*" %%i in ('ollama --version 2^>^&1') do set OLLAMA_VER=%%i
  echo   [OK] Ollama detected: !OLLAMA_VER!
  echo   Checking TinyLlama model...
  ollama list 2^>^&1 | findstr /i "tinyllama" >NUL
  IF %ERRORLEVEL% NEQ 0 (
    echo   [INFO] TinyLlama model not found. Installing now...
    echo   This will download ~637MB - may take 2-5 minutes...
    ollama pull tinyllama
    IF %ERRORLEVEL% EQU 0 (
      echo   [OK] TinyLlama installed successfully
    ) ELSE (
      echo   [ERROR] Failed to install TinyLlama
      echo   Try manually: ollama pull tinyllama
    )
  ) ELSE (
    echo   [OK] TinyLlama model ready
  )
)
echo.
echo   Checking Qdrant (Vector DB)...
curl --silent --max-time 2 http://localhost:6333/health >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo   [WARN] Qdrant not responding on port 6333
  echo   Install: https://qdrant.tech/documentation/quick-start/
  echo   Or run: docker run -p 6333:6333 qdrant/qdrant
) ELSE (
  echo   [OK] Qdrant service is running
)
echo.

echo ========================================
echo    Setup Complete!
echo ========================================
echo.
echo [NOTE] First run will auto-download models (~100MB):
echo   - all-MiniLM-L6-v2 (embedding model)
echo   - cross-encoder/ms-marco-MiniLM-L-6-v2 (reranker)
echo.
echo To run the chatbot:
echo   run.bat          (Windows CMD)
echo   .\run.ps1        (PowerShell)
echo.
echo The app will open at http://localhost:8501
echo.

:end
endlocal
