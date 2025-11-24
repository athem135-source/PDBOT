# ============================================
# PDBot Run Script - v1.4.0 (PowerShell)
# Phase 2: Reliability & Behavior Engineering
# Quick launch with automatic setup if needed
# ============================================

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   PDBot - Launching Chatbot" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if setup is needed
$venvActivate = Join-Path ".venv" "Scripts\Activate.ps1"
if (-not (Test-Path $venvActivate)) {
    Write-Host "[!] Virtual environment not found." -ForegroundColor Yellow
    Write-Host "[!] Running setup first...`n" -ForegroundColor Yellow
    
    # Run setup.bat
    $setupScript = Join-Path $PSScriptRoot "setup.bat"
    if (Test-Path $setupScript) {
        & cmd /c $setupScript
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n[ERROR] Setup failed. Please fix errors above." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[ERROR] setup.bat not found. Please run setup manually." -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

# Activate environment
Write-Host "[1/3] Activating virtual environment..." -ForegroundColor Gray
try {
    . $venvActivate
    Write-Host "[OK] Environment activated`n" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to activate virtual environment: $_" -ForegroundColor Red
    exit 1
}

# Quick service check
Write-Host "[2/3] Checking services..." -ForegroundColor Gray
$servicesOk = $true

# Check Ollama
try {
    $null = & ollama --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Ollama ready" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Ollama not detected - install from https://ollama.com/" -ForegroundColor Yellow
        $servicesOk = $false
    }
} catch {
    Write-Host "[WARN] Ollama not detected - install from https://ollama.com/" -ForegroundColor Yellow
    $servicesOk = $false
}

# Check Qdrant (default port 6338 as per app.py)
try {
    $response = Invoke-WebRequest -Uri "http://localhost:6338/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] Qdrant ready`n" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Qdrant not responding - start with: docker run -d -p 6338:6333 qdrant/qdrant`n" -ForegroundColor Yellow
        $servicesOk = $false
    }
} catch {
    Write-Host "[WARN] Qdrant not responding - start with: docker run -d -p 6338:6333 qdrant/qdrant`n" -ForegroundColor Yellow
    $servicesOk = $false
}

if (-not $servicesOk) {
    Write-Host "[INFO] Some services are offline. App will run in limited mode." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to cancel, or wait 5 seconds to continue..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    Write-Host ""
}

# Launch app
Write-Host "[3/3] Starting Streamlit app...`n" -ForegroundColor Gray

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   App URL: http://localhost:8501" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Gray

streamlit run src/app.py
