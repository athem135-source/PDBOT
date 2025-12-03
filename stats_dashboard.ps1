# ============================================================================
# PDBOT Statistics Dashboard v2.5.0-patch2
# ============================================================================
# Displays real-time statistics about the PDBOT server
# Run: .\stats_dashboard.ps1
# Run with watch mode: .\stats_dashboard.ps1 -Watch
# ============================================================================

param(
    [string]$ApiUrl = "http://localhost:5000",
    [switch]$Watch,
    [int]$Interval = 5
)

$Host.UI.RawUI.WindowTitle = "PDBOT Statistics Dashboard"

function Show-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "  +============================================================+" -ForegroundColor Green
    Write-Host "  |        PDBOT Statistics Dashboard v2.5.0-patch2            |" -ForegroundColor Green
    Write-Host "  |        Planning & Development Bot Monitor                  |" -ForegroundColor Green
    Write-Host "  +============================================================+" -ForegroundColor Green
    Write-Host ""
}

function Get-Stats {
    try {
        # Get admin statistics
        $statsResponse = Invoke-RestMethod -Uri "$ApiUrl/admin/statistics" -Method Get -TimeoutSec 5
        # Get admin status for services
        $statusResponse = Invoke-RestMethod -Uri "$ApiUrl/admin/status" -Method Get -TimeoutSec 5
        
        return @{
            Stats = $statsResponse
            Status = $statusResponse
            Success = $true
        }
    } catch {
        return @{
            Error = $_.Exception.Message
            Success = $false
        }
    }
}

function Format-StatusColor {
    param([string]$Status)
    
    if ($Status -eq "connected" -or $Status -eq $true -or $Status -eq "ok") {
        return "Green"
    } elseif ($Status -like "*error*" -or $Status -eq $false) {
        return "Red"
    } else {
        return "Yellow"
    }
}

function Show-Stats {
    param($Data)
    
    Show-Banner
    
    if (-not $Data.Success) {
        Write-Host "  [ERROR] Cannot connect to PDBOT API" -ForegroundColor Red
        Write-Host "     URL: $ApiUrl" -ForegroundColor Gray
        Write-Host "     Error: $($Data.Error)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  Make sure the PDBOT server is running:" -ForegroundColor Yellow
        Write-Host "     .\run_widget.ps1" -ForegroundColor Cyan
        return
    }
    
    $stats = $Data.Stats
    $status = $Data.Status
    
    # Server Info
    Write-Host "  +-----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host "  |                    SERVER INFO                            |" -ForegroundColor Cyan
    Write-Host "  +-----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "    Version:        " -NoNewline; Write-Host $status.version -ForegroundColor Yellow
    Write-Host "    PID:            " -NoNewline; Write-Host $stats.system.pid -ForegroundColor Yellow
    Write-Host "    Memory:         " -NoNewline; Write-Host "$($stats.system.memory_mb) MB" -ForegroundColor Yellow
    Write-Host "    CPU:            " -NoNewline; Write-Host "$($stats.system.cpu_percent)%" -ForegroundColor Yellow
    Write-Host "    Timestamp:      " -NoNewline; Write-Host $stats.timestamp -ForegroundColor Gray
    Write-Host ""
    
    # Services Status
    Write-Host "  +-----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host "  |                   SERVICES STATUS                         |" -ForegroundColor Cyan
    Write-Host "  +-----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host ""
    
    $qdrantColor = Format-StatusColor $status.qdrant_status
    $ollamaColor = Format-StatusColor $status.ollama_status
    $modelColor = Format-StatusColor $stats.services.model_loaded
    $classifierColor = Format-StatusColor $stats.services.classifier_loaded
    $groqColor = Format-StatusColor $stats.services.groq_available
    
    Write-Host "    Qdrant:         " -NoNewline; Write-Host $status.qdrant_status -ForegroundColor $qdrantColor
    Write-Host "    Ollama:         " -NoNewline; Write-Host $status.ollama_status -ForegroundColor $ollamaColor
    Write-Host "    Model:          " -NoNewline; Write-Host $(if($stats.services.model_loaded){"Loaded"}else{"Not Loaded"}) -ForegroundColor $modelColor
    Write-Host "    Classifier:     " -NoNewline; Write-Host $(if($stats.services.classifier_loaded){"Loaded"}else{"Not Loaded"}) -ForegroundColor $classifierColor
    Write-Host "    Groq API:       " -NoNewline; Write-Host $(if($stats.services.groq_available){"Available"}else{"Not Available"}) -ForegroundColor $groqColor
    Write-Host ""
    
    # Sessions
    Write-Host "  +-----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host "  |                    ACTIVE SESSIONS                        |" -ForegroundColor Cyan
    Write-Host "  +-----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "    Active Sessions:  " -NoNewline; Write-Host $stats.sessions.active_count -ForegroundColor Green
    Write-Host "    Total Messages:   " -NoNewline; Write-Host $stats.sessions.total_messages -ForegroundColor Yellow
    Write-Host "    Max/Session:      " -NoNewline; Write-Host $stats.sessions.max_per_session -ForegroundColor Gray
    Write-Host ""
    
    if ($stats.sessions.details -and $stats.sessions.details.Count -gt 0) {
        Write-Host "    Session Details:" -ForegroundColor Gray
        foreach ($session in $stats.sessions.details) {
            Write-Host "      * $($session.session_id) - $($session.message_count) msgs - $($session.last_activity)" -ForegroundColor DarkGray
        }
        Write-Host ""
    }
    
    # Feedback
    Write-Host "  +-----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host "  |                    FEEDBACK STATS                         |" -ForegroundColor Cyan
    Write-Host "  +-----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host ""
    
    $totalFeedback = 0
    if ($stats.feedback) {
        foreach ($key in @("5_star", "4_star", "3_star", "2_star", "1_star")) {
            $count = $stats.feedback.$key
            $totalFeedback += $count
            $stars = [int]$key.Split("_")[0]
            $starStr = "*" * $stars
            $barLength = [Math]::Min($count, 20)
            $bar = "#" * $barLength
            Write-Host "    $starStr : " -NoNewline
            Write-Host $bar -NoNewline -ForegroundColor Yellow
            Write-Host " ($count)" -ForegroundColor Gray
        }
    }
    Write-Host ""
    Write-Host "    Total Feedback:   " -NoNewline; Write-Host $totalFeedback -ForegroundColor Green
    Write-Host ""
    
    # Footer
    Write-Host "  -----------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "    Press Ctrl+C to exit" -ForegroundColor DarkGray
    if ($Watch) {
        Write-Host "    Auto-refreshing every $Interval seconds..." -ForegroundColor DarkGray
    }
    Write-Host ""
}

# Main execution
if ($Watch) {
    while ($true) {
        $data = Get-Stats
        Show-Stats -Data $data
        Start-Sleep -Seconds $Interval
    }
} else {
    $data = Get-Stats
    Show-Stats -Data $data
}
