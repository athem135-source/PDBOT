# Utility Scripts

Helper scripts for setup, running, and maintaining PDBot.

## Windows Scripts (.bat)

- **start.bat** - One-click launcher (recommended for first-time users)
- **setup.bat** - Initial environment setup and dependency installation
- **run.bat** - Quick launcher for daily use
- **diagnose.bat** - System diagnostics and health checks
- **create_shortcut.bat** - Create desktop shortcut

## PowerShell Scripts (.ps1)

- **run.ps1** - PowerShell launcher with better error handling
- **run_updated_pndbot.ps1** - Launcher with automatic updates check
- **generate_detailed_report.ps1** - Generate diagnostic reports

## Python Scripts (.py)

- **rebuild_vectordb.py** - Rebuild Qdrant vector database from scratch

## Usage

### First Time Setup (Windows)

```cmd
# Run setup (installs dependencies, checks services)
setup.bat

# Start application
start.bat
```

### Daily Usage

```cmd
# Quick start
run.bat

# OR with PowerShell
powershell -ExecutionPolicy Bypass -File scripts\run.ps1
```

### Rebuild Vector Database

```bash
# Rebuild from current manual
python scripts/rebuild_vectordb.py
```

### Diagnostics

```cmd
# Check system health
diagnose.bat
```

## Notes

- All scripts should be run from the **project root directory**
- PowerShell scripts may require execution policy bypass
- Python scripts assume virtual environment is activated
