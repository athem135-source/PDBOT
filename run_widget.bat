@echo off
REM ============================================
REM PDBOT Widget - Quick Start
REM Government of Pakistan - Ministry of Planning
REM Version 2.4.3
REM ============================================

title PDBOT Widget v2.4.3

echo.
echo  ========================================
echo   🤖 PDBOT Widget v2.4.3
echo   Government of Pakistan
echo   Ministry of Planning, Development
echo   ^& Special Initiatives
echo  ========================================
echo.

REM Check Python is available
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

REM Check Node.js is available
where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js/npm not found! Please install Node.js
    pause
    exit /b 1
)

REM Check Docker for Qdrant
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARN] Docker not found - Qdrant may not work
    goto :skip_qdrant
)

REM Start/Check Qdrant container
echo [1/4] Checking Qdrant vector database...
docker ps --filter "name=pndbot-qdrant" --format "{{.Names}}" | findstr /i "pndbot-qdrant" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo      Starting Qdrant container...
    docker start pndbot-qdrant >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo      Creating new Qdrant container...
        docker run -d -p 6338:6333 -p 6334:6334 --name pndbot-qdrant qdrant/qdrant >nul 2>&1
    )
    timeout /t 3 /nobreak >nul
    echo      Qdrant started on port 6338
) else (
    echo      Qdrant already running
)

:skip_qdrant

REM Check Ollama for LLM
echo [2/4] Checking Ollama LLM...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo      [WARN] Ollama not responding at localhost:11434
    echo      Please start Ollama with: ollama serve
) else (
    echo      Ollama is running
)

REM Start API server in background
echo [3/4] Starting Widget API Server (port 5000)...
cd /d "%~dp0"
start /B "PDBOT API" cmd /c "python widget_api.py"

REM Wait for API to initialize
timeout /t 4 /nobreak >nul

REM Start React widget
echo [4/4] Starting React Widget...
echo.
echo  ========================================
echo   Widget will open at:
echo   🌐 http://localhost:3000
echo   📱 Network: http://192.168.0.101:3000
echo  ========================================
echo.
echo  Press Ctrl+C to stop the widget
echo.

cd /d "%~dp0frontend-widget"
call npx vite --host

pause
