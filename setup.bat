@echo off
setlocal

REM Setup venv, install deps, and run the Streamlit app.

IF NOT EXIST ".venv\Scripts\activate.bat" (
  echo [+] Creating Python virtual environment...
  py -m venv .venv
  IF %ERRORLEVEL% NEQ 0 (
    echo [!] Failed to create virtual environment. Ensure Python is installed and in PATH.
    goto :end
  )
)

call ".venv\Scripts\activate"
python -m pip install --upgrade pip
IF EXIST requirements.txt (
  echo [+] Installing dependencies from requirements.txt...
  pip install -r requirements.txt
) ELSE (
  echo [!] requirements.txt not found. Aborting.
  goto :end
)

echo.
echo [i] Checking Ollama installation (optional)...
ollama --version >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo [!] Ollama not detected in PATH. Install from https://ollama.com/ and pull a model, e.g. ^"ollama pull tinyllama^".
) ELSE (
  echo [+] Ollama detected. Ensure the model is pulled: ollama pull tinyllama
)

echo.
echo [+] Launching app...
streamlit run src\app.py

:end
endlocal
