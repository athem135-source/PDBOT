# Streamlit Legacy Frontend

⚠️ **DEPRECATED** - This folder contains the legacy Streamlit frontend.

## Status
- **No longer maintained** - The React Widget is now the primary frontend
- **Not recommended** - Use the Widget API at `widget_api.py` instead

## Files
- `app.py` - Main Streamlit application (legacy)
- `.streamlit/` - Streamlit configuration
- `answer.py`, `callbacks.py`, `runtime.py`, `state.py` - Streamlit helpers

## To Run (Legacy Only)
```bash
streamlit run src_streamlit_legacy/app.py
```

## Migration
The new React Widget frontend provides:
- ✅ Mobile-friendly design
- ✅ Modern UI with floating widget
- ✅ Same RAG capabilities via REST API
- ✅ Classification and guardrails
- ✅ Session memory

Use `run_widget.bat` or `run_widget.ps1` to start the new widget.
