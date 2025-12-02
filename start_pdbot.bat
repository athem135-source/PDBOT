@echo off
REM ============================================
REM PDBOT Unified Launcher v2.4.8
REM Developer: M. Hassan Arif Afridi
REM ============================================

setlocal enabledelayedexpansion

REM Get script directory
cd /d "%~dp0"

:menu
cls
echo.
echo  ========================================
echo      PDBOT v2.4.8 - Unified Launcher
echo      Developer: M. Hassan Arif Afridi
echo      Planning ^& Development Assistant
echo  ========================================
echo.
echo   Select an option:
echo.
echo   [1] React Widget (Recommended)
echo       - Modern floating chat widget
echo       - Admin Panel (type "nufc")
echo.
echo   [2] Streamlit App (Legacy Dashboard)
echo       - Admin panel, file upload
echo.
echo   [3] Start Qdrant Only
echo       - Vector database server
echo.
echo   [0] Exit
echo.
echo  ========================================
echo.

set /p choice="Enter your choice (0-3): "

if "%choice%"=="1" goto widget
if "%choice%"=="2" goto streamlit
if "%choice%"=="3" goto qdrant
if "%choice%"=="0" goto end

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

:qdrant
cls
echo.
echo  ========================================
echo   Starting Qdrant Vector Database...
echo  ========================================
echo.

where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo   [ERROR] Docker not found!
    echo   Please install Docker Desktop from https://docker.com
    pause
    goto menu
)

echo   Checking Qdrant container...
docker ps -q --filter "name=pndbot-qdrant" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    for /f %%i in ('docker ps -q --filter "name=pndbot-qdrant"') do set RUNNING=%%i
    if defined RUNNING (
        echo   Qdrant already running at http://localhost:6338
    ) else (
        echo   Starting existing container...
        docker start pndbot-qdrant
    )
) else (
    echo   Creating new Qdrant container...
    docker run -d -p 6338:6333 -p 6334:6334 --name pndbot-qdrant qdrant/qdrant
)

echo.
echo   Qdrant running at: http://localhost:6338
echo.
pause
goto menu

:widget
cls
echo.
echo  ========================================
echo   Starting PDBOT React Widget v2.4.8
echo  ========================================
echo.

REM Step 1: Start Qdrant
echo [1/4] Starting Qdrant...
where docker >nul 2>nul
if %ERRORLEVEL% equ 0 (
    docker ps -q --filter "name=pndbot-qdrant" | findstr . >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        docker start pndbot-qdrant >nul 2>nul
        if %ERRORLEVEL% neq 0 (
            docker run -d -p 6338:6333 -p 6334:6334 --name pndbot-qdrant qdrant/qdrant >nul 2>nul
        )
        timeout /t 3 /nobreak >nul
    )
    echo       Qdrant running on port 6338
) else (
    echo       [WARN] Docker not found - Qdrant may not work
)

REM Step 2: Check Ollama
echo [2/4] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo       Ollama running on port 11434
) else (
    echo       [WARN] Ollama not responding - please start it
)

REM Step 3: Start Flask API
echo [3/4] Starting Widget API (port 5000)...
echo       Ensuring critical packages...
pip install qdrant-client waitress sentence-transformers --quiet >nul 2>nul
start "PDBOT Widget API" /min cmd /c "cd /d %~dp0 && python widget_api.py"
timeout /t 10 /nobreak >nul
echo       API started

REM Step 4: Start React Widget
echo [4/4] Starting React Widget...
echo.
echo  ========================================
echo   Widget running at:
echo   Local:   http://localhost:3000
echo   Network: http://192.168.0.101:3000
echo  ========================================
echo.
echo  Press Ctrl+C to stop
echo.

cd /d "%~dp0frontend-widget"
call npx vite --host

goto end

:streamlit
cls
echo.
echo  ========================================
echo   Starting PDBOT Streamlit (Legacy)
echo  ========================================
echo.

REM Step 1: Start Qdrant
echo [1/2] Starting Qdrant...
where docker >nul 2>nul
if %ERRORLEVEL% equ 0 (
    docker ps -q --filter "name=pndbot-qdrant" | findstr . >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        docker start pndbot-qdrant >nul 2>nul
        if %ERRORLEVEL% neq 0 (
            docker run -d -p 6338:6333 -p 6334:6334 --name pndbot-qdrant qdrant/qdrant >nul 2>nul
        )
        timeout /t 3 /nobreak >nul
    )
    echo       Qdrant running on port 6338
) else (
    echo       [WARN] Docker not found - Qdrant may not work
)

REM Step 2: Start Streamlit
echo [2/2] Starting Streamlit App (port 8501)...
echo.
echo  ========================================
echo   Streamlit running at:
echo   Local:   http://localhost:8501
echo  ========================================
echo.

cd /d "%~dp0"
start "" http://localhost:8501
streamlit run src_streamlit_legacy\app.py

goto end

:end
echo.
echo  Goodbye!
echo.
endlocal
