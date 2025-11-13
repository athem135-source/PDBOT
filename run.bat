@echo off
setlocal

REM Activate virtual environment and run the app. Ensure you have run setup steps in README first.
IF NOT EXIST ".venv\Scripts\activate.bat" (
  echo Virtual environment not found. Please create it first: py -m venv .venv
  goto :end
)

call ".venv\Scripts\activate"
streamlit run src\app.py

:end
endlocal
