@echo off
REM ============================================
REM PDBOT Unified Launcher
REM Government of Pakistan - Ministry of Planning
REM ============================================

setlocal enabledelayedexpansion

:menu
cls
echo.
echo  ========================================
echo      PDBOT - Unified Launcher
echo      Government of Pakistan
echo      Ministry of Planning, Development
echo      ^& Special Initiatives
echo  ========================================
echo.
echo   Select an option:
echo.
echo   [1] React Widget (Modern UI)
echo       - Floating chat widget
echo       - Requires: Qdrant + Flask API
echo.
echo   [2] Streamlit App (Full Dashboard)
echo       - Admin panel, file upload
echo       - Requires: Qdrant
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
echo   Qdrant will run on http://localhost:6338
echo.

REM Check if Docker is available
where docker >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo   Using Docker...
    docker run -d -p 6338:6333 -p 6334:6334 --name pndbot-qdrant qdrant/qdrant
    if %ERRORLEVEL% equ 0 (
        echo   Qdrant started successfully!
    ) else (
        echo   [INFO] Container might already exist, trying to start...
        docker start pndbot-qdrant
    )
) else (
    echo   [ERROR] Docker not found!
    echo   Please install Docker Desktop from https://docker.com
    echo   Or run Qdrant manually.
)

echo.
pause
goto menu

:widget
cls
echo.
echo  ========================================
echo   Starting PDBOT React Widget
echo  ========================================
echo.
echo   This will start:
echo   - Qdrant (if Docker available)
echo   - Flask Widget API (port 5000)
echo   - React Widget (port 3000)
echo.

REM Try to start Qdrant with Docker
where docker >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Starting Qdrant...
    docker start pndbot-qdrant 2>nul || docker run -d -p 6338:6333 -p 6334:6334 --name pndbot-qdrant qdrant/qdrant
    timeout /t 3 /nobreak >nul
)

REM Start Flask API in new window
echo [INFO] Starting Widget API Server (port 5000)...
start "PDBOT Widget API" cmd /k "cd /d %~dp0 && python widget_api.py"

REM Wait for API to start
timeout /t 5 /nobreak >nul

REM Refresh PATH for Node.js
set "PATH=%PATH%;C:\Program Files\nodejs;%LOCALAPPDATA%\Programs\nodejs"

REM Start React Widget
echo [INFO] Starting React Widget (port 3000)...
cd /d "%~dp0frontend-widget"
start "" http://localhost:3000
call npm run dev

goto end

:streamlit
cls
echo.
echo  ========================================
echo   Starting PDBOT Streamlit App
echo  ========================================
echo.
echo   This will start:
echo   - Qdrant (if Docker available)
echo   - Streamlit App (port 8501)
echo.

REM Try to start Qdrant with Docker
where docker >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Starting Qdrant...
    docker start pndbot-qdrant 2>nul || docker run -d -p 6338:6333 -p 6334:6334 --name pndbot-qdrant qdrant/qdrant
    timeout /t 3 /nobreak >nul
)

REM Start Streamlit
echo [INFO] Starting Streamlit App (port 8501)...
cd /d "%~dp0"
start "" http://localhost:8501
streamlit run src\app.py

goto end

:end
echo.
echo  Goodbye!
echo.
endlocal
