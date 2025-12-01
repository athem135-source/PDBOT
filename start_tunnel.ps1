# ============================================
# PDBOT Cloudflare Tunnel - External Access
# Version 2.4.9
# ============================================

$Host.UI.RawUI.WindowTitle = "PDBOT Cloudflare Tunnel"

Write-Host ""
Write-Host " ========================================"
Write-Host "   🌐 PDBOT External Access via Cloudflare"
Write-Host "   Government of Pakistan"
Write-Host " ========================================"
Write-Host ""

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Check if API is running
Write-Host "[1/2] Checking if Widget API is running..." -ForegroundColor Cyan
try {
    $null = Invoke-RestMethod -Uri "http://localhost:5000/health" -TimeoutSec 3
    Write-Host "      ✅ Widget API is running on port 5000" -ForegroundColor Green
} catch {
    Write-Host "      ❌ Widget API not running!" -ForegroundColor Red
    Write-Host "      Please start PDBOT first using: .\run_widget.ps1" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Start Cloudflare Tunnel
Write-Host "[2/2] Starting Cloudflare Tunnel..." -ForegroundColor Cyan
Write-Host ""
Write-Host " ========================================"
Write-Host "   📱 EXTERNAL ACCESS ENABLED"
Write-Host "   Share the URL below with any device!"
Write-Host " ========================================"
Write-Host ""
Write-Host "   Starting tunnel to localhost:5000..."
Write-Host "   (Look for the https://*.trycloudflare.com URL)"
Write-Host ""
Write-Host " ========================================"
Write-Host ""

# Run cloudflared tunnel (this will output the public URL)
cloudflared tunnel --url http://localhost:5000

