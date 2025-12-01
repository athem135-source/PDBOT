# ============================================
# PDBOT Widget + API Runner (PowerShell)
# Government of Pakistan - Ministry of Planning
# ============================================

Write-Host ""
Write-Host " ========================================" -ForegroundColor Green
Write-Host "   PDBOT Widget + API Server" -ForegroundColor Green
Write-Host "   Government of Pakistan" -ForegroundColor Green
Write-Host " ========================================" -ForegroundColor Green
Write-Host ""

# Refresh PATH for Node.js
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start API server in background
Write-Host "[INFO] Starting Widget API Server (port 5000)..." -ForegroundColor Cyan
$apiProcess = Start-Process -FilePath "python" -ArgumentList "$scriptDir\widget_api.py" -PassThru -WindowStyle Normal

# Wait for API to initialize
Start-Sleep -Seconds 3

# Check if API process started successfully
if ($apiProcess -and !$apiProcess.HasExited) {
    Write-Host "[OK] API Server started (PID: $($apiProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "[WARNING] API Server may not have started correctly" -ForegroundColor Yellow
}

# Start React widget
Write-Host "[INFO] Starting React Widget (port 3000)..." -ForegroundColor Cyan
Set-Location "$scriptDir\frontend-widget"
npm run dev
