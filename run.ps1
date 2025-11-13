# Activate venv and run the app (PowerShell)
$venvActivate = Join-Path ".venv" "Scripts\Activate.ps1"
if (-not (Test-Path $venvActivate)) {
  Write-Host "Virtual environment not found. Creating one (requires Python)..."
  py -m venv .venv
}

if (Test-Path $venvActivate) {
  . $venvActivate
} else {
  Write-Error "Failed to create/locate venv. Ensure Python is installed (py --version)."
  exit 1
}

python -m pip install --upgrade pip
if (Test-Path "requirements.txt") {
  pip install -r requirements.txt
} else {
  Write-Error "requirements.txt not found. Aborting."
  exit 1
}

# Optional: check Ollama
try {
  $ov = (& ollama --version) 2>$null
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "Ollama not detected. Install from https://ollama.com/ and run 'ollama pull tinyllama'"
  } else {
    Write-Host "Ollama detected: $ov"
  }
} catch {
  Write-Warning "Ollama not detected. Install from https://ollama.com/ and run 'ollama pull tinyllama'"
}

streamlit run src/app.py
