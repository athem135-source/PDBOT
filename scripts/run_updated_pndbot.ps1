<#
 Run the updated PnD Bot (Streamlit) using the project's virtual environment
 and proactively stop any OLD Streamlit instances that are running a different app,
 without affecting this updated one.
#>

$ErrorActionPreference = "Stop"

# Path to the project's virtual environment Python
$py = "D:\PLANNING WORK\Chatbot\chatbot-project\.venv\Scripts\python.exe"
# Path to the updated app (the one we want to keep)
$app = "D:\PLANNING WORK\Chatbot\PND BOT MINI DEMO\src\app.py"
$appFull = [System.IO.Path]::GetFullPath($app)

if (-Not (Test-Path $py)) { throw "Python interpreter not found at $py. Ensure the virtual environment exists and try again." }
if (-Not (Test-Path $app)) { throw "App not found at $app" }

# 1) Stop any other Streamlit instances not pointing at our target app
try {
  $procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'streamlit') -and ($_.CommandLine -match ' run ') }
  foreach ($p in $procs) {
    $cl = $p.CommandLine
    $m = [regex]::Match($cl, 'streamlit\s+run\s+"([^"]+)"|streamlit\s+run\s+([^\s]+)')
    $cmdApp = $null
    if ($m.Success) {
      $cmdApp = if ($m.Groups[1].Value) { $m.Groups[1].Value } else { $m.Groups[2].Value }
    }
    if ($cmdApp) {
      try { $cmdApp = [System.IO.Path]::GetFullPath($cmdApp) } catch {}
      if ($cmdApp -and ($cmdApp -ne $appFull)) {
        # Different app -> stop it
        try {
          Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
          Write-Host "Stopped old Streamlit instance (PID $($p.ProcessId)) for: $cmdApp"
        } catch {}
      }
    }
  }
} catch {
  Write-Host "Skipping cleanup of old Streamlit instances: $($_.Exception.Message)"
}

# 2) Launch our updated Streamlit app
& $py -m streamlit run $app --server.port 8501