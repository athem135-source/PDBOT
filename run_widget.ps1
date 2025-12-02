# ============================================
# PDBOT Widget - Quick Start (PowerShell)
# Government of Pakistan - Ministry of Planning
# Version 2.4.9
# ============================================

$Host.UI.RawUI.WindowTitle = "PDBOT Widget v2.4.9"

Write-Host ""
Write-Host " ========================================"
Write-Host "   🤖 PDBOT Widget v2.4.9"
Write-Host "   Government of Pakistan"
Write-Host "   Ministry of Planning, Development"
Write-Host "   & Special Initiatives"
Write-Host " ========================================"
Write-Host ""

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Activate virtual environment if it exists
$venvPath = Join-Path $scriptDir ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "[VENV] Activating virtual environment..." -ForegroundColor Green
    & $venvPath
} else {
    Write-Host "[WARN] Virtual environment not found at .venv" -ForegroundColor Yellow
    Write-Host "      Run: python -m venv .venv" -ForegroundColor Yellow
}

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python not found! Please install Python 3.8+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check npm
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Node.js/npm not found! Please install Node.js" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Docker and start Qdrant
Write-Host "[1/4] Checking Qdrant vector database..." -ForegroundColor Cyan
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $qdrantRunning = docker ps --filter "name=pndbot-qdrant" --format "{{.Names}}" 2>$null
    if (-not $qdrantRunning) {
        Write-Host "      Starting Qdrant container..." -ForegroundColor Yellow
        docker start pndbot-qdrant 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "      Creating new Qdrant container..." -ForegroundColor Yellow
            docker run -d -p 6338:6333 -p 6334:6334 --name pndbot-qdrant qdrant/qdrant 2>$null
        }
        Start-Sleep -Seconds 3
        Write-Host "      Qdrant started on port 6338" -ForegroundColor Green
    } else {
        Write-Host "      Qdrant already running" -ForegroundColor Green
    }
} else {
    Write-Host "      [WARN] Docker not found - Qdrant may not work" -ForegroundColor Yellow
}

# Check Ollama
Write-Host "[2/4] Checking Ollama LLM..." -ForegroundColor Cyan
try {
    $null = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
    Write-Host "      Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "      [WARN] Ollama not responding at localhost:11434" -ForegroundColor Yellow
    Write-Host "      Please start Ollama with: ollama serve" -ForegroundColor Yellow
}

# Start API server in background
Write-Host "[3/4] Starting Widget API Server (port 5000)..." -ForegroundColor Cyan

Start-Process -FilePath "python" -ArgumentList "widget_api.py" -NoNewWindow -PassThru | Out-Null

# Wait for API (longer to allow embedding model to load)
Start-Sleep -Seconds 10

# Start React widget
Write-Host "[4/4] Starting React Widget..." -ForegroundColor Cyan
Write-Host ""
Write-Host " ========================================"
Write-Host "   Widget will open at:"
Write-Host "   🌐 http://localhost:3000"
Write-Host "   📱 Network: http://192.168.0.101:3000"
Write-Host " ========================================"
Write-Host ""
Write-Host " Press Ctrl+C to stop the widget"
Write-Host ""

Set-Location "$scriptDir\frontend-widget"
npx vite --host

Read-Host "Press Enter to exit"
