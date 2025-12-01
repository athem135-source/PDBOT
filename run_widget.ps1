# ============================================
# PDBOT Widget - Quick Start (PowerShell)
# Government of Pakistan - Ministry of Planning
# Version 2.4.0
# ============================================

$Host.UI.RawUI.WindowTitle = "PDBOT Widget v2.4.0"

Write-Host ""
Write-Host " ========================================"
Write-Host "   🤖 PDBOT Widget v2.4.0"
Write-Host "   Government of Pakistan"
Write-Host "   Ministry of Planning, Development"
Write-Host "   & Special Initiatives"
Write-Host " ========================================"
Write-Host ""
Write-Host " Starting Widget API + React Frontend..."
Write-Host ""

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

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

# Start API server in background
Write-Host "[1/2] Starting Widget API Server (port 5000)..." -ForegroundColor Cyan
Start-Process -FilePath "python" -ArgumentList "widget_api.py" -NoNewWindow -PassThru | Out-Null

# Wait for API
Start-Sleep -Seconds 3

# Start React widget
Write-Host "[2/2] Starting React Widget..." -ForegroundColor Cyan
Write-Host ""
Write-Host " ========================================"
Write-Host "   Widget will open at:"
Write-Host "   🌐 http://localhost:3000"
Write-Host "   📱 Access from phone via same network"
Write-Host " ========================================"
Write-Host ""

Set-Location "$scriptDir\frontend-widget"
npm run dev

Read-Host "Press Enter to exit"
