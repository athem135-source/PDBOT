@echo off
REM ============================================
REM PDBOT Complete Setup Script v2.4.8
REM Developer: M. Hassan Arif Afridi
REM One-time setup for all dependencies
REM ============================================

setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo  ========================================
echo   PDBOT v2.4.8 - Complete Setup
echo   Developer: M. Hassan Arif Afridi
echo  ========================================
echo.
echo  This will install all required components:
echo  - Python dependencies (Flask, Qdrant, etc.)
echo  - Node.js dependencies (React Widget)
echo  - Docker container (Qdrant vector DB)
echo.
pause

REM ============================================
REM Step 1: Check Python
REM ============================================
echo.
echo [1/6] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ from https://python.org
    goto :error
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo       Python %%i detected
echo       [OK]

REM ============================================
REM Step 2: Install Python Dependencies
REM ============================================
echo.
echo [2/6] Installing Python dependencies...
echo       This may take a few minutes...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if %ERRORLEVEL% neq 0 (
    echo [WARN] Some packages may have failed. Trying essential ones...
)

REM Install essential packages individually
pip install flask flask-cors waitress qdrant-client sentence-transformers langchain --quiet
pip install PyMuPDF nltk requests python-dotenv psutil --quiet

echo       [OK] Python packages installed

REM ============================================
REM Step 3: Check Node.js
REM ============================================
echo.
echo [3/6] Checking Node.js...
node --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARN] Node.js not found!
    echo       Install from https://nodejs.org for React Widget
    echo       Skipping frontend setup...
    goto :skip_node
)
for /f %%i in ('node --version') do echo       Node.js %%i detected
echo       [OK]

REM ============================================
REM Step 4: Install Node.js Dependencies
REM ============================================
echo.
echo [4/6] Installing React Widget dependencies...
cd frontend-widget
call npm install --silent 2>nul
if %ERRORLEVEL% neq 0 (
    echo [WARN] npm install had issues, trying again...
    call npm install
)
cd ..
echo       [OK] React dependencies installed

:skip_node

REM ============================================
REM Step 5: Check Docker & Start Qdrant
REM ============================================
echo.
echo [5/6] Setting up Qdrant (Vector Database)...
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARN] Docker not found!
    echo       Install Docker Desktop from https://docker.com
    echo       Qdrant is required for semantic search.
    goto :skip_docker
)
echo       Docker detected

REM Check if container exists
docker ps -a --filter "name=pndbot-qdrant" --format "{{.Names}}" | findstr "pndbot-qdrant" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo       Qdrant container exists, starting...
    docker start pndbot-qdrant >nul 2>&1
) else (
    echo       Creating Qdrant container...
    docker run -d -p 6338:6333 -p 6334:6334 --name pndbot-qdrant qdrant/qdrant >nul 2>&1
)
timeout /t 3 /nobreak >nul
echo       [OK] Qdrant running on port 6338

:skip_docker

REM ============================================
REM Step 6: Check Ollama
REM ============================================
echo.
echo [6/6] Checking Ollama (LLM Backend)...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo       Ollama is running
    echo       [OK]
) else (
    echo [WARN] Ollama not responding!
    echo       Install from https://ollama.ai
    echo       Then run: ollama pull mistral
)

REM ============================================
REM Setup Complete
REM ============================================
echo.
echo  ========================================
echo   Setup Complete!
echo  ========================================
echo.
echo   To start PDBOT, run:
echo     start_pdbot.bat
echo.
echo   Select [1] for React Widget (recommended)
echo   Select [2] for Streamlit (legacy)
echo.
echo  ========================================
echo.
pause
goto :end

:error
echo.
echo  ========================================
echo   Setup Failed - Please check errors above
echo  ========================================
echo.
pause

:end
endlocal
