# 🚀 Quick Start Guide - PDBot

## One-Command Launch

### Windows (Easiest)
```cmd
start.bat
```
This will automatically:
- ✅ Check if setup is needed
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Fix Keras compatibility issues
- ✅ Validate Ollama & Qdrant services
- ✅ Launch the chatbot at http://localhost:8501

### Alternative Methods

#### PowerShell
```powershell
.\run.ps1
```

#### Command Prompt
```cmd
run.bat
```

Both will auto-run `setup.bat` if this is your first time.

---

## First-Time Setup Only

If you prefer manual setup before running:

```cmd
setup.bat
```

This will:
1. ✅ Verify Python 3.10+ is installed
2. ✅ Create `.venv` virtual environment
3. ✅ Upgrade pip
4. ✅ Install all dependencies from `requirements.txt`
5. ✅ Fix Keras 3 compatibility (uninstall keras if present)
6. ✅ Check Ollama installation and TinyLlama model
7. ✅ Verify Qdrant is running on port 6333

---

## Prerequisites

### Required
- **Python 3.10+** - [Download](https://www.python.org/downloads/)

### Optional (for full RAG features)
- **Ollama** - [Download](https://ollama.com/)
  ```cmd
  ollama pull tinyllama
  ```
  
- **Qdrant** (via Docker)
  ```cmd
  docker run -d -p 6333:6333 qdrant/qdrant
  ```

---

## Service Status

When you run the app, it will check:

| Service | Status | Required? | Fix |
|---------|--------|-----------|-----|
| **Python** | Must be installed | ✅ Yes | [python.org](https://www.python.org/) |
| **Ollama** | Optional | ⚠️ Recommended | [ollama.com](https://ollama.com/) |
| **Qdrant** | Optional | ⚠️ Recommended | `docker run -p 6333:6333 qdrant/qdrant` |

**Note:** The app will run in **limited mode** if Ollama/Qdrant are offline (Exact Mode only).

---

## Troubleshooting

### "Python not found"
Install Python 3.10+ from https://www.python.org/ and make sure to check "Add Python to PATH" during installation.

### "Ollama not detected"
1. Install from https://ollama.com/
2. Run: `ollama pull tinyllama`
3. Verify: `ollama list` should show tinyllama

### "Qdrant not responding"
**Option 1 - Docker (Recommended):**
```cmd
docker run -d -p 6333:6333 qdrant/qdrant
```

**Option 2 - Manual Install:**
Follow instructions at https://qdrant.tech/documentation/quick-start/

### "Keras compatibility warning"
This is automatically fixed by `setup.bat`. If you see this warning, run:
```cmd
pip uninstall -y keras
```

### Port already in use
If port 8501 is busy, Streamlit will auto-select 8502, 8503, etc.

---

## What Happens on First Run?

1. **Virtual Environment** - Creates `.venv` folder (~500MB after deps)
2. **Dependencies** - Downloads 12 packages (~2-5 minutes)
3. **Models** - Downloads sentence-transformers model (~100MB, one-time)
4. **NLTK Data** - Downloads punkt tokenizer (~1MB, one-time)

**Total first-run time:** 3-7 minutes depending on internet speed

---

## Daily Usage

After first setup, just run:
```cmd
start.bat
```

The app will:
- ✅ Launch in ~5-10 seconds
- ✅ Open your browser automatically
- ✅ Be ready at http://localhost:8501

---

## Stopping the App

Press **Ctrl+C** in the terminal, or just close the terminal window.

---

## File Structure

```
PND BOT MINI DEMO/
├── start.bat       ← ONE-CLICK LAUNCH (use this!)
├── run.bat         ← Launch only (auto-setup if needed)
├── run.ps1         ← PowerShell version
├── setup.bat       ← First-time setup only
└── src/
    └── app.py      ← Main application
```

---

## Need Help?

- 📖 **Full Documentation:** See `README.md`
- 🐛 **Issues:** https://github.com/athem135-source/PDBOT/issues
- 💬 **Discussions:** https://github.com/athem135-source/PDBOT/discussions

---

**Version:** 0.6.0  
**Last Updated:** November 17, 2025
