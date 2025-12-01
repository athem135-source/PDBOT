import os
import time
import io
import sys
import base64
import logging
from logging.handlers import RotatingFileHandler
import traceback
import warnings

# Suppress TensorFlow and other warnings early
warnings.filterwarnings("ignore", category=Warning)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

# Get absolute path for avatar image
_ROOT = os.path.dirname(os.path.abspath(__file__))
_AVATAR_PATH = os.path.join(_ROOT, "assets", "pakistan_emblem.png")

# Debug mode from environment variable
DEBUG_MODE = os.getenv("PNDBOT_DEBUG", "").lower() == "true"

import streamlit as st
import re
from typing import Any, TYPE_CHECKING, cast
nltk: Any = None
try:
    import nltk  # type: ignore
    _NLTK_PRESENT = True
except Exception:
    _NLTK_PRESENT = False
    nltk = None  # type: ignore

# Persist helpers (module-level): use project helper if available; fallback to local JSON
try:
    from src.utils.persist import load_chat_history, save_chat_history, clear_chat_history  # type: ignore
    _HAS_PERSIST = True
except Exception:
    _HAS_PERSIST = False
    import json as _json
    def load_chat_history():
        try:
            path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chat_single.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return _json.load(f)
        except Exception:
            return []
        return []
    def save_chat_history(items):
        try:
            folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, "chat_single.json")
            with open(path, "w", encoding="utf-8") as f:
                _json.dump(items, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    def clear_chat_history():
        try:
            folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            path = os.path.join(folder, "chat_single.json")
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

# --- Page and global CSS (professional palette) ---
st.set_page_config(page_title="PDBOT", page_icon=":robot_face:", layout="wide", initial_sidebar_state="collapsed")

_THEME_LIGHT = """
:root{
    --brand:#003366; --accent:#0A84FF;
    --bg:#FFFFFF; --panel:#F2F4F7; --text:#0B0F14; --muted:#475569; --border:#E5E7EB;
    --radius:14px; --shadow:0 10px 30px rgba(0,0,0,.06);
}
html,body { font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
a { color: var(--brand) !important; }
.hero,.card,.chat-card{
    background: var(--panel) !important; color: var(--text) !important;
    border: 1px solid var(--border) !important; border-radius: var(--radius) !important; box-shadow: var(--shadow) !important;
}
.hero{ display:flex; align-items:center; justify-content:center; text-align:center; min-height:220px; padding:24px; }
.hero .title{ font-weight:700; font-size:2.2rem; letter-spacing:.2px; color:var(--brand); }
.hero .subtitle{ color: var(--muted); margin-top:8px; }
.message{ line-height:1.55; font-size:15.5px; }
.logo svg, .logo path { fill: currentColor !important; color: var(--brand) !important; }
div.stTextInput>div>div>input { background:#fff; border:1px solid var(--border); color:#0B0F14; border-radius:12px; padding:.55rem .8rem; }
div.stTextInput>div>div>input::placeholder { color:#6B7280; }
section[data-testid="stTabs"] button { color:#0B0F14 !important; }
section[data-testid="stTabs"] button[aria-selected="true"] { border-bottom:2px solid var(--brand) !important; }
/* Chat/messages and answer cards slightly darker for better contrast */
div.stChatMessage, .stChatMessage { background:#F6F8FC !important; color:#0B0F14 !important; border:1px solid #D8E2F0 !important; border-radius:12px !important; }
/* Answer cards */
.card.success{ background:#F7FAFF !important; border:1px solid #D7DFEA !important; color:#0B0F14 !important; }
.card.warn{ background:#FFF8E1 !important; border:1px solid #F2D48B !important; color:#4A3B00 !important; }
div.stChatMessage .stMarkdown p { color:#0B0F14 !important; }
div.stButton>button {
    font-weight:600; border-radius:12px; padding:.55rem 1rem; border:1px solid transparent;
    background: var(--brand); color:#fff; transition: background .2s ease;
}
div.stButton>button:hover { background:#0A4A8A; }
"""

_THEME_DARK = """
:root{
    --brand:#86B7FF; --accent:#4BA3FF;
    --bg:#0B0F14; --panel:#11161D; --text:#E6E9EE; --muted:#94A3B8; --border:#1F2937;
    --radius:14px; --shadow:0 10px 30px rgba(0,0,0,.15);
}
html,body { font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background: var(--bg); color: var(--text); }
a { color: var(--brand) !important; }
.hero,.card,.chat-card{
    background: var(--panel) !important; color: var(--text) !important;
    border: 1px solid var(--border) !important; border-radius: var(--radius) !important; box-shadow: var(--shadow) !important;
}
.hero{ display:flex; align-items:center; justify-content:center; text-align:center; min-height:220px; padding:24px; }
.hero .title{ font-weight:700; font-size:2.2rem; letter-spacing:.2px; color:var(--brand); }
.hero .subtitle{ color: var(--muted); margin-top:8px; }
.message{ line-height:1.55; font-size:15.5px; }
.logo svg, .logo path { fill: currentColor !important; color: var(--brand) !important; }
div.stTextInput>div>div>input { background:#0F141A; border:1px solid var(--border); color: var(--text); border-radius:12px; padding:.55rem .8rem; }
div.stButton>button {
    font-weight:600; border-radius:12px; padding:.55rem 1rem; border:1px solid var(--border);
    background: #142033; color:#E6E9EE; transition: background .2s ease;
}
div.stButton>button:hover { background:#1A2A44; }
"""

def inject_theme():
    css = _THEME_DARK if st.session_state.get("_force_dark") else _THEME_LIGHT
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

if st.session_state.get("_use_new_theme", False):
    inject_theme()

# ---- Remove duplicate top-left title/caption; keep only the centered brand header below ----
if False:  # previously: st.title + caption (duplicate of centered hero)
    st.title("PDBOT")
    with st.container():
        c1 = st.columns([1])[0]
        with c1:
            st.caption("Ask questions grounded in your official planning manuals — secure, local, and intelligent.")

# Typography & hero CSS for light/dark legibility
st.markdown(
        """
<style>
h1, h2, h3, .stMarkdown {
    font-family: ui-sans-serif, -apple-system, Segoe UI, Roboto, Inter, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans", system-ui, sans-serif;
}
.pdbrand { font-weight: 800; letter-spacing: .5px; }
.block-container { padding-top: 1.5rem; }
.pdbot-hero {
    border-radius: 16px; padding: 28px 24px;
    background: linear-gradient(180deg, rgba(12,60,120,0.06) 0%, rgba(12,60,120,0.02) 100%);
    border: 1px solid rgba(12,60,120,0.12);
}
.pdbot-hero h1, .pdbot-hero h2, .pdbot-hero h3 { letter-spacing: .2px; }
.pdbot-logo img, .pdbot-logo svg { filter: brightness(0) saturate(100%); }
@media (prefers-color-scheme: dark) {
    .pdbot-hero { background: rgba(255,255,255,0.03); border-color: rgba(255,255,255,0.08); }
    .pdbot-logo img, .pdbot-logo svg { filter: invert(1) brightness(0.95) contrast(1.05); }
}
.chat-card { padding:14px 18px; border-radius:14px; background:#fff; border:1px solid #E6EAF2; }
.chat-card + .chat-card { margin-top:10px; }
</style>
""",
        unsafe_allow_html=True,
)

# Optional name prompt only when requested (after Clear/New)
def _get_query_params():
    try:
        return st.query_params  # Streamlit >= 1.33
    except Exception:
        try:
            return st.experimental_get_query_params()  # type: ignore
        except Exception:
            return {}

_qp = _get_query_params()
_ask_name = False
try:
    _ask_name = bool(_qp.get("ask_name"))
except Exception:
    _ask_name = False
if False:
    pass

# (Removed duplicate simple hero to avoid double header; detailed brand header renders below)

# Quiet Transformers logs and telemetry to avoid noisy console messages
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("TQDM_DISABLE", "1")

# ---- One-time session defaults (set before any UI) ----
_defaults = {
    "messages": [],
    "busy": False,
    "active_request_id": None,
    "_finalize": None,
    "__pending_result": None,
    "__name_input": "",
    "__name_error": "",
    "show_name_modal": False,
    # Force new dark theme by default
    "_use_new_theme": True,
    "_force_dark": True,
    "app_exit": False,
    "manual_action": None,
    "ui_notice": None,
    "_last_rerun_ts": 0.0,
}
try:
    for _k, _v in _defaults.items():
        if _k not in st.session_state:
            st.session_state[_k] = _v
except Exception:
    pass

# Default model/control knobs (overridden later by UI controls if present)
model_name: str = os.getenv("OLLAMA_MODEL", "mistral:latest")
top_k: int = 6
max_tokens: int = 768
temperature: float = 0.2

# App logging (file + console) for crash forensics
try:
    _LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(_LOG_DIR, exist_ok=True)
    _LOG_PATH = os.path.join(_LOG_DIR, "app.log")
    _root_logger = logging.getLogger()
    _root_logger.setLevel(logging.INFO)

    # Rotate at ~1MB, keep 3 backups
    _handler = RotatingFileHandler(_LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    _handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    # Avoid duplicate handlers on re-run
    if not any(isinstance(h, RotatingFileHandler) for h in _root_logger.handlers):
        _root_logger.addHandler(_handler)
    # App logger for ask events
    log = logging.getLogger("pdbot")
except Exception:
    pass

# Quiet noisy splitter logs and deprecation warnings to keep UI responsive
try:
    logging.getLogger("langchain.text_splitter").setLevel(logging.ERROR)
    logging.getLogger("langchain_text_splitters").setLevel(logging.ERROR)
    # Suppress Streamlit thread warnings from background executors
    logging.getLogger("streamlit.runtime.scriptrunner.script_thread").setLevel(logging.ERROR)
    logging.getLogger("streamlit").setLevel(logging.ERROR)

except Exception:
    pass
try:
    warnings.filterwarnings("ignore", message=r".*HuggingFaceEmbeddings.*deprecated.*")
    warnings.filterwarnings("ignore", message=r".*missing ScriptRunContext.*")
except Exception:
    pass

# --- Safety harness: throttled reruns to avoid loops/fragment warnings ---
def safe_rerun(throttle_ms: int = 300) -> None:
    """Request a rerun safely.
    - Throttles rapid repeats within 200ms
    - Falls back to a one-shot flag when called from within callbacks
    """
    try:
        now = time.time()
        last = float(st.session_state.get("_last_rerun_ts") or 0)
        if (now - last) < (throttle_ms / 1000.0):
            # Too soon; defer a single rerun
            st.session_state["_pending_rerun"] = True
            return
        st.session_state["_last_rerun_ts"] = now
        try:
            # Prefer new API when available
            if hasattr(st, "rerun"):
                st.rerun()
            else:  # pragma: no cover - legacy fallback
                st.experimental_rerun()  # type: ignore
        except Exception:
            # Likely called inside a widget callback; set a one-shot flag
            st.session_state["_pending_rerun"] = True
    except Exception:
        # Best-effort: set flag to attempt a rerun on next safe point
        try:
            st.session_state["_pending_rerun"] = True
        except Exception:
            pass

# ---- PRIORITY CONSUMER: render any deferred answer immediately ----
_pending = st.session_state.pop("__pending_result", None)
if _pending:
    try:
        st.markdown(_pending.get("rendered", ""), unsafe_allow_html=True)
    finally:
        st.session_state["busy"] = False
        st.session_state.pop("_finalize", None)
        st.session_state["active_request_id"] = None

if _NLTK_PRESENT:
    # Ensure NLTK tokenizers are available (nltk>=3.9 may require 'punkt_tab')

    # Use a local nltk_data folder inside the project to avoid permission issues.
    try:
        _APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _NLTK_DIR = os.path.join(_APP_ROOT, "nltk_data")
        os.makedirs(_NLTK_DIR, exist_ok=True)
        if _NLTK_DIR not in nltk.data.path:
            nltk.data.path.append(_NLTK_DIR)
        os.environ.setdefault("NLTK_DATA", _NLTK_DIR)

        # punkt (classic) and punkt_tab (new tables) – download on demand
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt", download_dir=_NLTK_DIR, quiet=True)
        try:
            nltk.data.find("tokenizers/punkt_tab")
        except LookupError:
            # Available in newer NLTK; ignore if not present
            try:
                nltk.download("punkt_tab", download_dir=_NLTK_DIR, quiet=True)
            except Exception:
                pass
    except Exception:
        # If anything above fails, fall back to best effort download of punkt
        try:
            nltk.download("punkt", quiet=True)
        except Exception:
            pass
else:
    st.sidebar.warning("NLTK is not installed. Please install the 'nltk' package in your environment to enable PDF processing.")



# ChatGPT dark theme CSS additions for contrast and controls
st.markdown(
    """
<style>
.block-container { padding-top: 1.25rem; }

.sidebar .stSlider > div > div, .sidebar label, .sidebar p {
    color: #E6E8EC !important;
}
.stSlider [role="slider"] { background-color: #10A37F !important; }
.stSlider .st-b6, .stSlider .css-1dp5vir { color: #E6E8EC !important; }

.stButton>button {
    background: linear-gradient(90deg,#0E9768,#10A37F);
    color: #fff; border: 0; border-radius: 8px; padding: 0.55rem 1rem;
}
.stButton>button:hover { filter: brightness(1.05); }

[data-baseweb="tab"] { color:#E6E8EC; }
h1, h2, h3 { color:#E6E8EC; }

.chat-user { background:#101418; border:1px solid #2A2F36; border-radius:12px; padding:10px; }
.chat-bot  { background:#131821; border:1px solid #273140; border-radius:12px; padding:10px; }

/* Ensure all markdown text is visible in both themes */
.markdown-text-container, .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown code, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
    color: inherit !important;
}
</style>
""",
        unsafe_allow_html=True,
)

# Ensure project root is on sys.path so `from src...` imports work even when running from src/
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_THIS_DIR)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Quiet TensorFlow logs and oneDNN noise to avoid leaking into answers/terminal spam
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # 0=all,1=warn,2=error,3=fatal
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

# Qdrant URL resolver: prefer app-specific PNDBOT var, then standard, then unique default port
def _qdrant_url() -> str:
    return os.getenv("PNDBOT_QDRANT_URL") or os.getenv("QDRANT_URL") or "http://localhost:6338"

from src.models.local_model import LocalModel
from typing import Any as _Any

# v2.0.5: Removed pretrained model support (Qwen) - using Ollama only

try:
    # Suppress TensorFlow/Keras warnings during import
    import warnings
    warnings.filterwarnings("ignore", message=".*Keras.*")
    warnings.filterwarnings("ignore", message=".*keras.*")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
    
    # FIXED: RAG auto-initialization - import and verify components at startup
    from src.rag_langchain import ingest_pdf_sentence_level as ingest_pdf
    from src.rag_langchain import search_sentences as search
    from src.rag_langchain import mmr_rerank, dedup_chunks, build_context
    from src.rag_langchain import COLLECTION as RAG_COLLECTION
    from src.rag_langchain import RetrievalBackendError, EmbeddingModelError
    _RAG_OK = True
    _RAG_IMPORT_ERR = None
    if os.getenv("PNDBOT_DEBUG", "").lower() == "true":
        print("[DEBUG] RAG imports successful - _RAG_OK = True")
    
    # Optional: New modular answer composition (set PDBOT_USE_MODULAR_ANSWERING=1 to enable)
    try:
        from src.core.answering import (
            compose_answer_with_context_check,
            AnswerResult,
            check_context_quality as check_context_quality_v2,
            format_citations as format_citations_v2,
        )
        _MODULAR_ANSWERING_AVAILABLE = True
    except ImportError:
        _MODULAR_ANSWERING_AVAILABLE = False
except Exception as _e:
    # FIXED: Show warning instead of silent failure; provide fallbacks
    _RAG_OK = False
    _RAG_IMPORT_ERR = _e
    if os.getenv("PNDBOT_DEBUG", "").lower() == "true":
        import traceback
        print(f"[DEBUG] RAG import failed: {_e}")
        traceback.print_exc()
    ingest_pdf = None  # type: ignore
    search = None      # type: ignore
    RAG_COLLECTION = "pnd_manual_sentences"  # default
    # Provide safe fallbacks for RAG helpers so downstream code can still run
    def dedup_chunks(candidates):  # type: ignore
        return list(candidates or [])
    def mmr_rerank(candidates, top_k: int = 6, lambda_mult: float = 0.5):  # type: ignore
        try:
            k = int(top_k)
        except Exception:
            k = 6
        return list(candidates or [])[:max(0, k)]
    def build_context(hits, token_budget: int = 2400):  # type: ignore
        items = []
        cits = []
        for i, h in enumerate(list(hits or [])):
            txt = str((h.get("text") if isinstance(h, dict) else "") or "").strip()
            items.append(f"[{i+1}] {txt}")
            try:
                cits.append({"n": i+1, "page": (h.get("page") if isinstance(h, dict) else None)})
            except Exception:
                cits.append({"n": i+1, "page": None})
        return {"context": "\n\n".join(items).strip(), "citations": cits}
from src.utils.text_utils import clean_text, chunk_text, chunk_text_sentences, select_relevant_chunks, highlight_matches, extract_exact_quotes, extract_factual_items, find_exact_locations, render_citations
try:
    from src.utils.text_utils import normalize_markdown  # type: ignore[attr-defined]  # optional normalizer
except Exception:
    def normalize_markdown(text: str, enforce_bullets: bool = True, max_line_len: int = 110) -> str:  # type: ignore
        return text or ""
# Robust PDF loader: prefer LangChain's PyPDFLoader, but fall back to pypdf if unavailable
try:
    from langchain_community.document_loaders import PyPDFLoader  # type: ignore
except Exception:
    class PyPDFLoader:  # type: ignore
        def __init__(self, file_path: str):
            self.file_path = file_path
        def load(self):
            try:
                import pypdf  # type: ignore
                reader = pypdf.PdfReader(self.file_path)
                docs = []
                for i, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text() or ""
                    except Exception:
                        text = ""
                    # Minimal object with attributes similar to LangChain Document
                    docs.append(type("Doc", (), {"page_content": text, "metadata": {"page": i+1}}))
                return docs
            except Exception as e:
                raise ImportError(f"No PDF loader available. Install langchain-community or pypdf. Underlying error: {e}")

# --- Manual path resolution and loader: fixed absolute path specified by user ---
MANUAL_ABSOLUTE_PATH = r"D:\\PLANNING WORK\\Manual-for-Development-Project-2024.pdf"

def _default_manual_path() -> str:
    """Return the single fixed manual path used by the app."""
    return MANUAL_ABSOLUTE_PATH

def _load_builtin_manual(force: bool = False):
    """Load the built-in manual pages always; index into Qdrant when deps are available.
    This keeps Exact mode working even if LangChain/Qdrant aren't installed or running.
    """
    manual_path = _default_manual_path()
    if not os.path.isfile(manual_path):
        st.warning(f"Built-in manual not found: {manual_path}. Set DEFAULT_MANUAL_PATH or place a PDF at data/default/manual.pdf.")
        return

    # Skip rework if same manual already loaded (pages loaded or indexed) and not forced
    same_manual = st.session_state.get("current_manual_path") == manual_path
    already_have_pages = bool(st.session_state.get("raw_pages"))
    already_indexed = bool(int(st.session_state.get("last_index_count") or 0) > 0)
    if not force and same_manual and (already_have_pages or already_indexed):
        # Update count from Qdrant if available (in case collection was rebuilt externally)
        try:
            if _RAG_OK:
                from qdrant_client import QdrantClient
                client = QdrantClient(url=_qdrant_url())
                collection = client.get_collection(RAG_COLLECTION)
                updated_count = collection.points_count
                st.session_state["last_index_count"] = updated_count
                
                # Show updated status message
                src_name = os.path.basename(manual_path)
                if updated_count and updated_count > 0:
                    st.success(f"Loaded built-in manual: {src_name} • Pages: {st.session_state.get('raw_page_count')} • Indexed {updated_count} chunks.")
        except Exception:
            pass  # Keep existing cached count
        return

    # Always load raw pages for Exact mode and basic grounding
    pages_loaded = False
    try:
        loader = PyPDFLoader(manual_path)
        with st.spinner("Reading pages…"):
            docs = loader.load()
        st.session_state["raw_pages"] = [getattr(d, "page_content", "") for d in docs]
        st.session_state["raw_page_count"] = len(docs)
        pages_loaded = True
    except Exception as _e_pages:
        # Leave a compact message but don't crash; user can still attempt indexing
        st.warning(f"Unable to read PDF pages: {_e_pages}")
        st.session_state["raw_pages"] = []
        st.session_state["raw_page_count"] = None

    # Update file metadata regardless
    st.session_state["current_manual_path"] = manual_path
    st.session_state["source_file"] = os.path.basename(manual_path)

    # Try to index if RAG is available; otherwise keep graceful fallback
    n_indexed = 0
    try:
        if _RAG_OK and ingest_pdf is not None:  # type: ignore
            with st.spinner("Indexing built-in manual…"):
                n_indexed = ingest_pdf(
                    manual_path,
                    qdrant_url=_qdrant_url(),
                )  # type: ignore
            st.session_state["indexed_ok"] = n_indexed > 0
            st.session_state["last_index_count"] = n_indexed
            st.session_state["builtin_indexed"] = n_indexed > 0
        else:
            # Keep explicit but non-blocking notice; Exact mode remains available
            st.info("Retrieval indexing skipped (dependencies missing). Exact mode will still work.")
            st.session_state["indexed_ok"] = False
            st.session_state["last_index_count"] = 0
            st.session_state["builtin_indexed"] = False
    except Exception as e:
        error_msg = str(e)
        if "Embedding model not available" in error_msg or "sentence-transformers" in error_msg:
            st.error(f"Failed to index into Qdrant: {error_msg}")
            st.warning("**Troubleshooting:** Try reinstalling dependencies with: `pip install --force-reinstall sentence-transformers torch`")
        else:
            st.error(f"Failed to index into Qdrant: {e}")
        st.session_state["indexed_ok"] = False
        st.session_state["last_index_count"] = 0
        st.session_state["builtin_indexed"] = False

    # Final status message
    src_name = os.path.basename(manual_path)
    if pages_loaded and n_indexed > 0:
        st.success(f"Loaded built-in manual: {src_name} • Pages: {st.session_state.get('raw_page_count')} • Indexed {n_indexed} chunks.")
    elif pages_loaded:
        st.success(f"Loaded built-in manual pages: {src_name} • Pages: {st.session_state.get('raw_page_count')}. Indexing not available.")
    else:
        st.error("Manual could not be read. Install 'langchain-community' or 'pypdf' to enable PDF reading.")

_HEADER = "<h1 style='margin-bottom:0; font-weight:800;'>PDBOT</h1><p style='opacity:.5;margin-top:0px;font-size:0.9em;'>v2.1.0</p><p style='opacity:.8;margin-top:4px'>Ask questions grounded in your official planning manuals — secure, local, and intelligent.</p>"
# Single, hardcoded default logo path: place your logo at this location and it will be used automatically
# Prefer explicit light-theme logo filename for white theme
HARDCODED_LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "branding_logo-black.png")

def _find_logo_path() -> str | None:
    """Return the first existing Planning & Development logo path, if present.
    Looks under src/assets and project-level assets.
    """
    try:
        # -1) Hardcoded preferred path (no upload needed across runs)
        if os.path.isfile(HARDCODED_LOGO_PATH):
            return HARDCODED_LOGO_PATH
        # 0) Session override (when set via admin UI this run)
        try:
            override = st.session_state.get("brand_logo_path_override")
            if override and os.path.isfile(override):
                return override
        except Exception:
            pass

        # 1) Persisted config path (written by admin UI)
        try:
            cfg_dir = os.path.join(_ROOT, "config")
            cfg_path = os.path.join(cfg_dir, "brand_logo_path.txt")
            if os.path.isfile(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    saved = f.read().strip().strip('"')
                if saved and os.path.isfile(saved):
                    return saved
        except Exception:
            pass

        # 2) Common asset locations inside src/ and project root
        candidates = [
            os.path.join(_THIS_DIR, "assets", "planning_and_development.png"),
            os.path.join(_THIS_DIR, "assets", "planning_and_development.jpg"),
            os.path.join(_THIS_DIR, "assets", "planning_and_development.svg"),
            os.path.join(_THIS_DIR, "assets", "branding_logo.png"),
            os.path.join(_THIS_DIR, "assets", "logo.png"),
            os.path.join(_ROOT, "assets", "planning_and_development.png"),
            os.path.join(_ROOT, "assets", "planning_and_development.jpg"),
            os.path.join(_ROOT, "assets", "planning_and_development.svg"),
            os.path.join(_ROOT, "assets", "branding_logo.png"),
            os.path.join(_ROOT, "assets", "logo.png"),
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p
    except Exception:
        pass
    return None

def render_brand_header():
    """Render top header with centered Planning & Development logo and title underneath."""
    # Lightweight CSS for centered brand header (improved light-theme contrast and professional font)
    st.markdown(
        """
        <style>
        .brand-header{ display:flex; flex-direction:column; align-items:center; justify-content:center; margin: 6px 0 10px 0; }
                /* Light theme: white card with dark text */
                .brand-card{
                    display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center;
                    padding: 22px 28px; border-radius: 16px;
                    border: 1px solid #E5E7EB; background:#FFFFFF; color:#0B0F14;
                    box-shadow: 0 12px 34px rgba(0,0,0,0.08), 0 6px 14px rgba(0,0,0,0.06);
                }
        .brand-header .brand-logo{ margin: 6px auto 8px auto; }
        .brand-header .brand-title{
          text-align:center; margin: 6px 0 0 0;
          font-weight:800; font-size: 56px; line-height:1.06;
                    color:#0B0F14;
          font-family: Inter, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
          letter-spacing: .5px;
        }
        .brand-header .brand-sub{ text-align:center; opacity:.85; margin-top:10px; }
        /* Dark mode: show logo with an invert/brightness filter for visibility */
    @media (prefers-color-scheme: dark){
            .brand-card{ background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.14); box-shadow: 0 12px 34px rgba(0,0,0,0.32), 0 4px 10px rgba(0,0,0,0.22); color:#E5E7EB; }
            .brand-header .brand-title{ color:#E5E7EB; }
            .brand-header .brand-logo{ filter: invert(1) brightness(0.96) contrast(1.05); }
    }
        @media (max-width: 768px){ .brand-header .brand-title{ font-size: 38px; } }
        </style>
        """,
        unsafe_allow_html=True,
    )
    logo_path = _find_logo_path()
    # Build a fully centered HTML block so the logo is exactly centered regardless of columns
    def _img_mime_from_path(p: str) -> str:
        ext = os.path.splitext(p)[1].lower()
        if ext in (".jpg", ".jpeg"): return "image/jpeg"
        if ext == ".png": return "image/png"
        if ext == ".svg": return "image/svg+xml"
        return "image/png"
    html = ["<div class='brand-header'>"]
    html.append("<div class='brand-card hero'>")
    # Always show the logo (dark mode handled via CSS filter)
    _show_logo = True
    if _show_logo and logo_path and os.path.isfile(logo_path):
        try:
            ext = os.path.splitext(logo_path)[1].lower()
            if ext == ".svg":
                try:
                    import re as _re_svg
                    svg_txt = open(logo_path, "r", encoding="utf-8", errors="ignore").read()
                    # Force theme-adaptive color
                    svg_txt = _re_svg.sub(r"fill=\"[^\"]*\"", "fill=\"currentColor\"", svg_txt)
                    html.append(f"<div class='brand-logo' style='width:420px; max-width:90vw; color:inherit;'>{svg_txt}</div>")
                except Exception:
                    with open(logo_path, "rb") as f:
                        data_b64 = base64.b64encode(f.read()).decode("ascii")
                    html.append(f"<img class='brand-logo' src='data:image/svg+xml;base64,{data_b64}' style='width:420px; max-width:90vw; height:auto;' />")
            else:
                with open(logo_path, "rb") as f:
                    data_b64 = base64.b64encode(f.read()).decode("ascii")
                mime = _img_mime_from_path(logo_path)
                # Fixed width with responsive max-width for smaller screens
                html.append(f"<img class='brand-logo' src='data:{mime};base64,{data_b64}' style='width:420px; max-width:90vw; height:auto;' />")
        except Exception:
            html.append("<div class='brand-logo' style='font-weight:700;opacity:.9'>Planning &amp; Development</div>")
    else:
        html.append("<div class='brand-logo' style='font-weight:700;opacity:.9'>Planning &amp; Development</div>")
    html.append("<div class='brand-title'>PDBOT</div>")
    html.append("<div style='text-align:center; opacity:0.5; margin-top:4px; font-size:0.9em;'>v2.1.0</div>")
    html.append("</div>")  # close brand-card
    html.append("<div class='brand-sub'>Ask questions grounded in your official planning manuals — secure, local, and intelligent.</div>")
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)

render_brand_header()
st.markdown("<style>.stMarkdown{font-size: 1rem;}</style>", unsafe_allow_html=True)
st.caption("Note: Please cross-check answers; the bot may be inaccurate sometimes.")

# ---- One-time Ollama warm-up (preloads tiny model to avoid short first answer) ----
if "warmup_done" not in st.session_state:
    try:
        import requests as _rq
        _ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        _model = os.getenv("OLLAMA_MODEL", "mistral:latest")
        _rq.post(f"{_ollama_url}/api/generate", json={
            "model": _model,
            "prompt": "hello",
            "stream": False,
            "options": {"num_predict": 5}
        }, timeout=5)
    except Exception:
        pass
    st.session_state.warmup_done = True

# ---- Session state boot & modals (name + rating) ----
def init_state():
    ss = st.session_state
    ss.setdefault("user_name", None)
    ss.setdefault("username", "")
    ss.setdefault("is_admin", False)
    ss.setdefault("login_ok", False)
    # chat stored as list of dicts: {role: 'user'|'assistant', content: str}
    ss.setdefault("chat_history", [])
    # generic session stability keys for request lifecycle
    ss.setdefault("messages", [])
    ss.setdefault("req_id", 0)
    ss.setdefault("loading", False)
    ss.setdefault("show_name_modal", False)
    ss.setdefault("show_rating_modal", False)
    ss.setdefault("post_rating_action", None)  # 'new' | 'clear' | None
    ss.setdefault("pending_question", "")
    ss.setdefault("busy", False)
    ss.setdefault("qa_stage", "idle")
    ss.setdefault("busy_since", 0.0)
    ss.setdefault("request_counter", 0)
    ss.setdefault("active_request_id", None)
    ss.setdefault("cancel_requested", False)
    # Default answer mode: Generative (user can switch to Exact Search)
    ss.setdefault("answer_mode", "Generative")
    # Manual loading state defaults
    ss.setdefault("raw_pages", [])
    ss.setdefault("raw_page_count", None)
    ss.setdefault("current_manual_path", "")
    ss.setdefault("source_file", "")
    ss.setdefault("last_index_count", 0)
    ss.setdefault("indexed_ok", False)
    ss.setdefault("builtin_indexed", False)
    ss.setdefault("manual_load_error", None)


init_state()

# ---- Early auto-load of manual for non-admin users (runs once) ----
try:
    if not st.session_state.get("raw_pages"):
        _load_builtin_manual(force=False)
    
    # v1.8.0: Always sync chunk count from Qdrant on startup
    if _RAG_OK and st.session_state.get("indexed_ok"):
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(url=_qdrant_url())
            collection = client.get_collection(RAG_COLLECTION)
            st.session_state["last_index_count"] = collection.points_count
        except Exception:
            pass  # Keep existing cached count if Qdrant unavailable
except Exception as _e_auto_manual:
    st.session_state["manual_load_error"] = str(_e_auto_manual)

# FIXED: Show RAG status warning at startup if components missing
if not _RAG_OK and _RAG_IMPORT_ERR:
    st.warning(f"⚠️ RAG components not fully available: {_RAG_IMPORT_ERR}. Retrieval will use fallback mode (raw pages only). Install langchain, langchain-community, langchain-text-splitters to enable vector search.")

# If a rerun was requested from within a callback, perform it now (one-shot)
if st.session_state.pop("_pending_rerun", False):
    try:
        if hasattr(st, "rerun"):
            st.rerun()
        else:  # pragma: no cover
            st.experimental_rerun()  # type: ignore
    except Exception:
        pass

# Backward-compatible helpers
def _append_chat(role: str, content: str):
    try:
        text = content if isinstance(content, str) else str(content)
        if not text.strip():
            text = "⚠️ No response returned. Please retry."
        st.session_state.chat_history.append({"role": role, "content": text})
    except Exception:
        st.session_state.chat_history.append({"role": role, "content": str(content)})

def _append_chat_dedup_assistant(content: str):
    """Append assistant content unless the last assistant message is identical.
    Prevents duplicate bot cards from rapid double submissions or stale returns.
    """
    try:
        hist = st.session_state.get("chat_history") or []
        if hist:
            last = hist[-1]
            last_role = last.get("role") if isinstance(last, dict) else ("assistant" if not str(last[0]).lower().startswith("you") else "user")
            last_content = last.get("content") if isinstance(last, dict) else last[1]
            if last_role == "assistant" and str(last_content).strip() == str(content).strip():
                return
    except Exception:
        pass
    _append_chat("assistant", content)

def _iter_chat():
    for item in st.session_state.get("chat_history", []):
        if isinstance(item, dict):
            yield item.get("role", "assistant"), item.get("content", "")
        else:
            # fallback from legacy tuple format
            try:
                role, msg = item
                # normalize legacy labels
                role = "user" if str(role).lower().startswith("you") else "assistant"
                yield role, msg
            except Exception:
                yield "assistant", str(item)

try:
    dialog_fn = st.dialog  # Streamlit >= 1.31
except Exception:  # pragma: no cover - fallback
    dialog_fn = st.experimental_dialog  # type: ignore

# State-only name modal: inline callbacks to avoid 'app' package import issues
def cb_name_continue():
    name = st.session_state.get("__name_input", "").strip()
    if name:
        st.session_state["user_name"] = name
        st.session_state["username"] = name
        st.session_state["__name_error"] = ""
        st.session_state["show_name_modal"] = False
        st.session_state["login_ok"] = True
        # Suppress modal/dialog render during the callback fragment rerun
        st.session_state["_suppress_modal_once"] = True
    else:
        st.session_state["__name_error"] = "Name is required."

def cb_name_exit():
    st.session_state["app_exit"] = True
    # Avoid rendering modal during callback fragment
    st.session_state["_suppress_modal_once"] = True

def name_modal():
    """Open a name prompt with robust fallback across Streamlit versions.
    Priority: st.modal (context manager) → st.dialog/experimental_dialog (decorator) → inline container fallback.
    """
    # If a callback requested suppression for this run, skip rendering the modal/dialog in fragment rerun
    if st.session_state.pop("_suppress_modal_once", False):
        return
    # Prefer modal as a context manager if available
    modal_cm = getattr(st, "modal", None)
    if False and callable(modal_cm):
        try:
            _modal_cm = cast(Any, modal_cm)
            with _modal_cm("Enter your name", key="__name_modal", closable=False):
                st.text_input("Your name", key="__name_input")
                c1, c2 = st.columns(2)
                with c1:
                    st.button("Continue", key="__btn_continue", on_click=cb_name_continue)
                with c2:
                    st.button("Exit", key="__btn_exit", on_click=cb_name_exit)
            return
        except Exception:
            # If the call signature differs (older/newer versions), retry without extras
            try:
                _modal_cm2 = cast(Any, modal_cm)
                with _modal_cm2("Enter your name"):
                    st.text_input("Your name", key="__name_input")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.button("Continue", key="__btn_continue", on_click=cb_name_continue)
                    with c2:
                        st.button("Exit", key="__btn_exit", on_click=cb_name_exit)
                return
            except Exception:
                pass

    # Fallback: dialog-style decorator (Streamlit >= 1.31, or experimental)
    dlg = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
    if False and callable(dlg):
        _dlg = cast(Any, dlg)
        @_dlg("Enter your name")
        def _name_dialog():
            st.text_input("Your name", key="__name_input")
            c1, c2 = st.columns(2)
            with c1:
                st.button("Continue", key="__btn_continue", on_click=cb_name_continue)
            with c2:
                st.button("Exit", key="__btn_exit", on_click=cb_name_exit)

        _name_dialog()
        return

    # Last-resort fallback: inline container (no modal/dialog available)
    # Name capture disabled

from pathlib import Path
from datetime import datetime
import re as _re

def _sanitize(s: str) -> str:
    try:
        return _re.sub(r"[^A-Za-z0-9_\-\.]+", "_", s).strip("_")
    except Exception:
        return "user"

def _execute_post_rating_action():
    act = st.session_state.post_rating_action
    st.session_state.post_rating_action = None
    if act in ("new", "clear"):
        # Reset to fresh state and prompt for new user on next render
        st.session_state.chat_history = []
        st.session_state.update({
            "login_ok": False,
            "show_name_modal": True,
            "username": "",
            "user_name": None,
            "is_admin": False,
            "_greeted": False,
        })
    safe_rerun()


@dialog_fn("Rate your experience")
def rating_modal():
    uname = st.session_state.get("user_name") or st.session_state.get("username") or "Guest"
    # Allow entering/updating username at feedback time
    name_in = st.text_input("Your name (optional)", key="__rating_name", value=str(uname))
    if isinstance(name_in, str) and name_in.strip():
        uname = name_in.strip()
        st.session_state["username"] = uname
        st.session_state["user_name"] = uname
    st.write(f"Thanks, **{uname}**. Please rate this chat (1–3 stars).")
    stars = st.radio("Rating", options=[1, 2, 3], format_func=lambda x: "⭐" * x, horizontal=True, key="__rating_choice")
    review = st.text_area("Optional comment", key="__rating_review", placeholder="What worked / what didn't?")

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("Submit", type="primary", key="btn_submit_rating"):
            # save file to feedback/<star>_star/
            try:
                folder = Path(_ROOT) / "feedback" / f"{stars}_star"
                folder.mkdir(parents=True, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                uname_s = _sanitize(uname)
                path = folder / f"{ts}_{uname_s}.txt"
                last_q = ""
                last_a = ""
                for role, content in reversed(list(_iter_chat())):
                    if role == "assistant" and not last_a:
                        last_a = content
                    elif role == "user" and not last_q:
                        last_q = content
                    if last_q and last_a:
                        break
                content_txt = (
                    f"User: {uname}\nTime: {ts}\nRating: {stars}\nReview: {review}\nLast_Q: {last_q}\nLast_A: {last_a}\n"
                )
                path.write_text(content_txt, encoding="utf-8")
                st.session_state.show_rating_modal = False
                _execute_post_rating_action()
            except Exception as _e:
                st.error(f"Failed to save feedback: {_e}")
    with c2:
        if st.button("Skip", key="btn_skip_rating"):
            st.session_state.show_rating_modal = False
            _execute_post_rating_action()
    with c3:
        if st.button("Cancel", key="btn_cancel_rating"):
            st.session_state.show_rating_modal = False
            safe_rerun()

def request_rating_then(action: str):
    st.session_state.post_rating_action = action
    st.session_state.show_rating_modal = True
    # Defer displaying the modal to the main render to avoid fragment rerun warnings
    try:
        safe_rerun()
    except Exception:
        pass

@dialog_fn("Rate this answer")
def answer_rating_modal():
    uname = st.session_state.get("username") or st.session_state.get("user_name") or "Guest"
    # Optional username override
    name_in = st.text_input("Your name (optional)", key="__ans_rating_name", value=str(uname))
    if isinstance(name_in, str) and name_in.strip():
        uname = name_in.strip()
        st.session_state["username"] = uname
        st.session_state["user_name"] = uname
    st.write(f"Please rate this answer, **{uname}**.")
    stars = st.radio("Rating", options=[1, 2, 3], format_func=lambda x: "⭐" * x, horizontal=True, key="__ans_rating_choice")
    review = st.text_area("Optional short review", key="__ans_rating_review", height=80)
    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("Submit", type="primary", key="btn_submit_ans_rating"):
            try:
                from datetime import datetime as _dt
                from pathlib import Path as _Path
                ts = _dt.now()
                date_str = ts.strftime("%Y-%m-%d")
                time_str = ts.strftime("%H%M%S")
                folder = _Path(_ROOT) / "ratings" / f"{stars}"
                folder.mkdir(parents=True, exist_ok=True)
                uname_s = (uname or "Guest").replace(" ", "_")
                fname = f"{date_str}_{uname_s}_{time_str}.txt"
                fpath = folder / fname
                last_q = st.session_state.get("last_question", "")
                mode = st.session_state.get("answer_mode", "Generative")
                content = (
                    f"user: {uname}\n"
                    f"time: {ts.isoformat()}\n"
                    f"stars: {stars}\n"
                    f"last_question: \"{last_q}\"\n"
                    f"mode: {mode}\n"
                    f"review: \"{review}\"\n"
                )
                fpath.write_text(content, encoding="utf-8")
                st.session_state["show_answer_rating_modal"] = False
                try:
                    safe_rerun()
                except Exception:
                    pass
            except Exception as _e:
                st.error(f"Failed to save rating: {_e}")
    with c2:
        if st.button("Skip", key="btn_skip_ans_rating"):
            st.session_state["show_answer_rating_modal"] = False
            try:
                safe_rerun()
            except Exception:
                pass

# ENTERPRISE v1.1.0: Removed Settings popover - actions moved to floating bar
# Simple header with download button only
act_cols = st.columns([6,1])
with act_cols[1]:
    # Prepare chat text for download
    lines = []
    for role, msg in _iter_chat():
        label = "You" if role == "user" else "PDBOT"
        # strip HTML cards when saving
        try:
            import re
            msg_txt = re.sub(r"<[^>]+>", "", str(msg))
        except Exception:
            msg_txt = str(msg)
        lines.append(f"{label}: {msg_txt}")
    txt_data = "\n\n".join(lines) if lines else "(empty)"
    st.download_button("⬇️ Download", data=txt_data, file_name="chat_history.txt", mime="text/plain", key="download_chat_header", help="Download chat history")

_CSS = """
<style>
/* Keep Streamlit defaults; only layout and component tweaks. */
html, body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; font-size: 14.5px; }
.block-container { max-width: 1200px; margin: 0 auto; padding-bottom: 12px; }

/* Smooth theme transitions */
* { transition: color .2s ease, background-color .2s ease; }

/* Hero (brand) container alignment and typography */
.hero { display:flex; align-items:center; justify-content:center; flex-direction:column; text-align:center; }
.hero .brand-title { font-weight:700; letter-spacing: .2px; }
[data-theme="light"] .hero { background-color:#F2F4F7; border:1px solid #E5E7EB; color:#111; }
[data-theme="dark"] .hero { background-color:#0B0F14; border:1px solid #1F2937; color:#E6E9EE; }
.hero { box-shadow: 0 8px 24px rgba(0,0,0,0.10); }

/* Header bar (ChatGPT style, inherit theme colors) */
.app-header.bar { display:flex; justify-content:space-between; align-items:center; padding:10px 16px; border-radius:12px; margin:8px 0 16px 0; border:1px solid rgba(0,0,0,0.12); }
.app-header .title{ font-weight:700; font-size:22px; line-height:1.2; }
.app-header .subtitle{ font-size:13px; opacity:0.95; }
.app-header .right{ display:flex; align-items:center; gap:10px; }
.app-header .brand{ font-weight:700; padding:4px 10px; border:1px solid rgba(0,0,0,0.2); border-radius:999px; }
.version-chip{ display:inline-block; padding:3px 10px; border:1px solid rgba(0,0,0,0.2); border-radius:999px; font-size:12px; font-weight:600; }

/* Sidebar tweaks */
[data-testid="stSidebar"] [data-testid="stSliderValue"] span,
[data-testid="stSidebar"] [data-testid="stSliderValue"] div{ background: transparent !important; box-shadow: none !important; border: 0 !important; }

/* Buttons */
.stButton > button{ background: linear-gradient(180deg, #0EA5E9, #6366F1); color:#fff; font-weight:700; border:none; border-radius:10px; padding:10px 18px; font-size:16px; box-shadow:0 2px 4px rgba(0,0,0,0.12); transition: transform .12s ease, box-shadow .12s ease, filter .12s ease; }
.stButton > button:hover{ filter:brightness(1.05); box-shadow:0 4px 10px rgba(0,0,0,0.18); transform: translateY(-1px); }
.stButton > button:active{ transform: translateY(0); box-shadow:0 2px 4px rgba(0,0,0,0.12); }
.stButton.secondary > button{ background:var(--panel); color:var(--text); border:1px solid var(--panel-border); }

/* Inputs */
textarea, .stTextInput > div > div > input{ border-radius:10px !important; }

/* File uploader padding/alignment */
[data-testid="stFileUploader"] > div{ border-radius:12px; padding:12px; }

/* Sliders */
.stSlider > div[data-baseweb] > div{ }
.stSlider [role=\"slider\"]{ }
.stSlider [data-testid=\"stTickBar\"] > div{ }

/* Slider value pill contrast (dark mode) */
[data-testid="stSidebar"] [data-testid="stSliderValue"] span,
[data-testid="stSidebar"] [data-testid="stSliderValue"] div{
    background: #1F2937 !important;
    color: #EAECEF !important;
    border: 1px solid #2A2F3A !important;
    border-radius: 999px !important;
    padding: 2px 8px !important;
    box-shadow: none !important;
}

/* Toggle */
[data-testid="stSwitch"] div[role="switch"]{ }

/* Expanders */
[data-testid="stExpander"]{ border-radius:12px; }
[data-testid="stExpander"] details{ border-radius:12px; }
[data-testid="stExpander"] summary{ }
[data-testid="stExpander"] .st-expanderContent{ padding-top:8px; }

/* Chat */
.chat-scroll { max-height: 460px; overflow-y: auto; padding: 12px; border-radius: 10px; box-shadow:0 1px 3px rgba(0,0,0,0.08); }
.chat-scroll { scroll-behavior: smooth; }
.small-muted { font-size: 12px; opacity: 0.9; }
.status-icon { font-size: 22px; line-height: 22px; }
.suggestion-row { display: flex; gap: 8px; flex-wrap: wrap; }
.suggestion-chip { font-size: 13px; padding: 6px 10px; border-radius: 999px; border: 1px solid rgba(0,0,0,0.1); cursor: pointer; transition: background .15s ease; }
.suggestion-chip:hover { background: rgba(0,0,0,0.05); }
.chat-msg { max-width: 80%; border: 1px solid rgba(37,99,235,0.35); border-radius: 12px; padding: 12px 14px; margin-bottom: 12px; box-shadow:0 1px 2px rgba(0,0,0,0.06); line-height:1.5; font-size:15.5px; }
.chat-msg.user { margin-left: auto; background: #0f141a; border-color: rgba(37,99,235,0.55); padding-left:14px; }
.chat-msg.bot { margin-right: auto; background: #1a1f28; border-color: rgba(148,163,184,0.35); border-radius: 14px; padding-left:14px; }
.chat-header { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border: 1px solid var(--panel-border); border-radius: 999px; margin-bottom: 6px; }
.chat-icon { font-size: 16px; }
.chat-body { white-space: pre-wrap; }
.chat-body { line-height: 1.6; }
.chat-actions { display: flex; gap: 8px; margin-top: 4px; }

/* Bigger input styling */
#qa-input input { font-size: 18px; padding: 12px 14px; }

/* Cards for responses (success/warn/error) */
.card{ border-radius:10px; padding:10px 12px; box-shadow:0 2px 5px rgba(0,0,0,0.08); border:1px solid rgba(0,0,0,0.12); }
.card.success{ border-color: rgba(22,163,74,0.45); background: rgba(22,163,74,0.08); }
.card.warn{ border-color: rgba(245,158,11,0.55); background: rgba(245,158,11,0.10); }
.card.error{ border-color: rgba(220,38,38,0.55); background: rgba(220,38,38,0.10); }

/* Alerts (success/info/error) */
[data-testid="stAlert"]{ border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.08); }

/* Download buttons styled as secondary */
[data-testid="stDownloadButton"] > button{ font-weight:700; border-radius:10px; }

/* Scrollbars */
/* WebKit */
*::-webkit-scrollbar { width: 10px; height: 10px; }
*::-webkit-scrollbar-track { }
*::-webkit-scrollbar-thumb { border-radius: 10px; }
/* Firefox */
* { scrollbar-width: thin; scrollbar-color: var(--accent) var(--panel); }

/* Responsive tweaks */
@media (max-width: 768px){
  .chat-msg{ max-width: 100%; }
}

/* ENTERPRISE v1.1.0: Floating Action Bar - Gemini-Style Pills at Bottom */
/* Target the container holding our marker */
div:has(> .floating-bar-marker) {
    position: fixed !important;
    bottom: 80px !important; /* Sits right above the chat input */
    left: 50% !important;
    transform: translateX(-50%) !important;
    z-index: 9999 !important;
    background-color: transparent !important;
    width: auto !important;
    padding: 0 !important;
}

/* Style the buttons inside to look like "Gemini Pills" */
div:has(> .floating-bar-marker) .stButton > button {
    border-radius: 20px !important;
    border: 1px solid rgba(128, 128, 128, 0.2) !important;
    background: rgba(255, 255, 255, 0.8) !important; /* Glass effect light */
    color: #333 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 6px 16px !important;
    min-height: 0px !important;
    height: 36px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
    backdrop-filter: blur(10px);
    transition: all 0.2s ease !important;
}

div:has(> .floating-bar-marker) .stButton > button:hover {
    background: rgba(255, 255, 255, 0.95) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    transform: translateY(-1px);
}

/* Dark mode adjustments for the pills */
@media (prefers-color-scheme: dark) {
    div:has(> .floating-bar-marker) .stButton > button {
        background: rgba(30, 30, 30, 0.8) !important;
        color: #eee !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    div:has(> .floating-bar-marker) .stButton > button:hover {
        background: rgba(40, 40, 40, 0.9) !important;
    }
}

/* Hide the mode indicator caption in floating bar */
div:has(> .floating-bar-marker) .stCaption {
    display: none !important;
}

/* Add padding to main content so text doesn't hide behind the footer */
.block-container { padding-bottom: 160px !important; }
    background: rgba(255,255,255,0.05);
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.2s ease;
}
.floating-action-bar button:hover {
    background: rgba(255,255,255,0.1);
    transform: translateY(-1px);
}
.chat-container-wrapper {
    padding-bottom: 160px; /* Make room for floating bar */
}
  .block-container { padding-left: 10px; padding-right: 10px; }
}

/* Bottom-left user badge */
.user-badge { position: fixed; left: 14px; bottom: 10px; font-size: 12px; color: rgba(255,255,255,0.65); padding: 2px 4px; }
/* Feedback */
.feedback-card{ border-radius:10px; padding:12px; border:1px solid rgba(0,0,0,0.2); background: rgba(31,41,55,0.35); }

/* Sidebar inputs alignment */
[data-testid="stSidebar"] .stTextInput>div>div>input { width: 100%; }
[data-testid="stSidebar"] .stSlider { padding-left: 6px; padding-right: 10px; }
</style>
"""
st.markdown(_CSS, unsafe_allow_html=True)

st.markdown(_CSS, unsafe_allow_html=True)

# Small helper
def _truncate_text(text: str, max_chars: int = 6000) -> str:
    try:
        return text if len(text) <= max_chars else (text[: max_chars - 3] + "...")
    except Exception:
        return text

# Run a blocking function with a timeout to prevent UI hangs
from concurrent.futures import ThreadPoolExecutor, TimeoutError as _TimeoutError
def call_with_timeout(fn, timeout: float, *args, **kwargs):
    try:
        with ThreadPoolExecutor(max_workers=1) as _ex:
            fut = _ex.submit(fn, *args, **kwargs)
            return fut.result(timeout=timeout)
    except _TimeoutError:
        return "⚠️ Timeout: model took too long."
    except Exception as e:
        return f"⚠️ Error: {e}"

def _split_sentences(text: str) -> list[str]:
    try:
        # Lightweight splitter avoiding heavy deps
        return [s.strip() for s in re.split(r"(?<=[\.\?\!])\s+", text) if s.strip()]
    except Exception:
        return [text]

# Lightweight keyword extraction and page scan fallback for long/complex questions
_STOPWORDS = set(
    """the a an and or of for to in on with without by as from at into over under between among about across during before after than then 
    is are was were be being been have has had do does did can could should would may might must this that these those it its they them their we our you your i me my mine ours yours his her hers him he she what which who whom whose where when why how not no nor only also if else than within per each such more most less least including include includes etc versus vs v 
    annual plan describe role translate translating national priorities priority government strategic policy policies program programme programs programmes project projects development sector sectors federal provincial division divisions commission planning economic technical finance economic affairs
    """.split()
)

def _keyword_fallback_hits(question: str, pages: list[str], max_pages: int = 3, max_sents: int = 8) -> list[dict]:
    try:
        ql = (question or "").lower()
        # terms: words >=4 chars not stopwords; also keep common bigrams present in the question
        words = [w.strip(".,:;()[]{}!?") for w in re.split(r"\s+", ql) if len(w.strip(".,:;()[]{}!?").strip()) >= 4]
        kws = [w for w in words if w not in _STOPWORDS]
        # simple bigram harvest from question
        bigrams = []
        toks = [t for t in re.split(r"\s+", ql) if t]
        for i in range(len(toks) - 1):
            bg = f"{toks[i]} {toks[i+1]}".strip()
            if len(bg) >= 7 and all(x not in _STOPWORDS for x in toks[i:i+2]):
                bigrams.append(bg)
        # de-dup and keep top ~12 terms
        seen = set()
        terms: list[str] = []
        for t in (bigrams + kws):
            if t not in seen:
                seen.add(t); terms.append(t)
            if len(terms) >= 12:
                break
        if not terms:
            return []
        # score pages by term frequency
        scores = []
        for idx, pg in enumerate(pages or [], start=1):
            low = (pg or "").lower()
            sc = sum(low.count(t) for t in terms)
            if sc > 0:
                scores.append((sc, idx, pg))
        scores.sort(reverse=True)
        picked = scores[:max_pages]
        hits: list[dict] = []
        for _sc, idx, pg in picked:
            sents = _split_sentences(pg)
            for s in sents:
                sl = s.lower()
                if any(t in sl for t in terms):
                    hits.append({"text": s.strip(), "page": idx, "score": None, "source": RAG_COLLECTION})
                    if len(hits) >= max_sents:
                        break
        return hits
    except Exception:
        return []

def compose_answer(mode: str, hits: list[dict], user_q: str, base_answer: str | None, words_target: int = 200, pages_limit: int = 3) -> str:
    """v1.7.0: ULTRA-MINIMAL - Return only 1-3 sentence answer (NO internal citations).
    Citations are appended externally via render_citations().
    """
    mode = (mode or "Generative").strip()
    hits = hits or []

    if mode == "Exact search" or mode == "Exact quotes":
        if not hits:
            return "No exact lines found. Try turning off 'exact phrase' or rewording."
        lines = [f"[p.{h.get('page','?')}] \"{h.get('text','').strip()}\"" for h in hits[:5]]
        return "\n\n".join(lines)

    # v1.7.0: Extract ONLY first paragraph from model output
    direct = ""
    if base_answer:
        # Take only first paragraph (before double newline)
        paragraphs = base_answer.strip().split("\n\n")
        first_para = paragraphs[0] if paragraphs else base_answer
        
        # Take first 5-7 sentences for fuller answers
        import re
        sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', first_para) if s.strip()]
        direct = " ".join(sents[:7]).strip()
        
        # Cap at 150 words
        words = direct.split()
        if len(words) > 150:
            direct = " ".join(words[:150])
    
    # v1.7.0: Return ONLY the answer (NO internal citation line)
    # Citations will be appended externally by render_citations()
    if direct:
        # Strip existing Source lines to avoid duplicates
        lines = [ln for ln in direct.splitlines() if not ln.strip().lower().startswith("source:")]
        direct_clean = "\n".join(lines).strip()
        if hits:
            top = hits[0]
            page = top.get("page", "?")
            doc = top.get("source_filename") or "Manual for Development Projects 2024"
            direct_clean = f"{direct_clean}\n\nSource: {doc}, p.{page}"
        return direct_clean
    else:
        return "Not found in the uploaded manual."

# --- Generative Mode (structured, cited) ---
# v2.0.2: Simplified system prompt - removed overly restrictive rules
SYSTEM_PROMPT = """You are PDBOT, an assistant for the Manual for Development Projects.
Answer questions based on the provided context.
Provide complete answers in 4-7 sentences (around 120-150 words)."""

USER_TEMPLATE = (
    "Answer the question using ONLY the context below. Maximum 80 words total.\n\n"
    "QUESTION: {question}\n\n"
    "CONTEXT:\n{context}\n\n"
    "Provide a SHORT answer with citation."
)

SELF_CHECK_PROMPT = (
    "Keep ONLY the first sentence. Remove everything else. Maximum 80 words."
)

def _sanitize_model_output(text: str) -> str:
    """Remove prompt echoes and normalize headings without changing facts."""
    import re
    t = (text or "").strip()
    if not t:
        return t
    drop_prefixes = (
        r"^question\s*:.*$",
        r"^task\s*:.*$",
        r"^context\s*:.*$",
        r"^[^A-Za-z0-9]*answer\s*:.*$",
        r"^[^A-Za-z0-9]*outline\s*:.*$",
        r"^structured as follows.*$",
        r"^provide only the final answer.*$",
        r"^review your answer.*$",
        r"^citations\s*:.*$",
    )
    kept = []
    for line in t.splitlines():
        l = line.strip()
        # Drop instruction-like lines
        if any(re.match(p, l, flags=re.I) for p in drop_prefixes):
            continue
        if re.search(r"<[^>]+>", l):  # placeholder tokens like <bullet>
            continue
        if re.search(r"numbered snippets|Use \[n\] where n refers", l, flags=re.I):
            continue
        if re.match(r"^-\s*\[n\]", l, flags=re.I):  # template bullet echo
            continue
        # Drop placeholder practical step lines
        if re.match(r"^practical\s*step[s]?\s*\(?s\)?\s*:\s*$", l, flags=re.I):
            # Keep the heading only if the next lines include non-placeholder steps; handled later – drop now
            continue
        if re.search(r"\[n\]\s*step\s*with\s*\[n\]", l, flags=re.I):
            continue
        # Drop explicit template echoes like "[n] bullet 1 (3–6 bullet points total)"
        if re.search(r"^\[n\]\s*bullet", l, flags=re.I):
            continue
        if re.search(r"bullet\s*points\s*total\)?", l, flags=re.I):
            continue
        # Drop bracket-only step placeholders like "[step 1 with [n]]"
        if re.match(r"^\[\s*step[^\]]*\]$", l, flags=re.I):
            continue
        # Drop raw CONTEXT snippets accidentally echoed (start-of-line [n])
        if re.match(r"^\[\d+\]\s+", l):
            continue
        kept.append(line)
    t = "\n".join(kept).strip()
    # Fix common heading typos observed in outputs
    t = re.sub(r"pratical step[e]?s?", "Practical Steps", t, flags=re.I)
    # Remove embedded 'Sources:' if the model added one; we append a unified block later
    t = re.sub(r"^\s*sources\s*:.*$", "", t, flags=re.I | re.M)
    # Collapse excessive blank lines
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t


def check_context_quality(hits: list[dict], question: str) -> dict:
    """Phase 2 & 5 FIX: Relaxed quality check with warning flag for low-confidence context.
    
    Phase 5 additions:
    - Acronym-only detection (PAD, PERT, PFM with no substance)
    - Numeric answer validation (duration, percentage, amount questions)
    
    Returns dict with:
    - passed: bool (whether to call LLM - False only if NO context at all)
    - warning: bool (whether to show low-confidence banner in UI)
    - max_score: float (max similarity score among hits)
    - reason: str (human-readable explanation)
    
    Thresholds lowered to allow land acquisition / annexure snippets through:
    - MIN_WORDS: 5 (was 15) - allows single-sentence answers like dates/thresholds
    - MIN_SCORE: 0.18 (was 0.25) - allows messy PDF embeddings from annexures
    
    CRITICAL: passed=False ONLY when hits is empty (no hallucination on zero context).
    """
    # Case 1: No hits at all - HARD FAIL (prevent hallucination)
    if not hits:
        return {
            "passed": False,
            "warning": True,
            "max_score": 0.0,
            "reason": "No context retrieved",
        }
    
    # Case 2: Check word count
    total_text = " ".join([h.get("text", "") for h in hits])
    word_count = len(total_text.split())
    
    MIN_WORDS = 5  # Lowered from 15 to allow land acquisition / threshold snippets
    
    if word_count < MIN_WORDS:
        return {
            "passed": True,       # Allow answer but warn
            "warning": True,
            "max_score": 0.0,
            "reason": f"Short context ({word_count} words)",
        }
    
    # Phase 5 Case 2.5: Detect acronym-only context (PAD/PERT/PFM hallucination fix)
    # Count how many words are ALL CAPS (likely acronyms)
    words = total_text.split()
    acronym_count = sum(1 for w in words if len(w) >= 2 and w.isupper() and not w.isdigit())
    acronym_ratio = acronym_count / len(words) if words else 0
    
    # Check if context lacks domain keywords (vehicle, transport, budget, etc.)
    domain_keywords = [
        "vehicle", "transport", "car", "land cruiser", "monetization", "operational",
        "project", "budget", "fund", "allocation", "procurement", "asset", "approval",
        "cost", "expenditure", "estimate", "justification", "purchase", "acquire"
    ]
    has_domain_content = any(kw in total_text.lower() for kw in domain_keywords)
    
    if acronym_ratio > 0.4 and not has_domain_content:
        # Context is mostly acronym list without substance
        return {
            "passed": False,
            "warning": True,
            "max_score": 0.0,
            "reason": "The retrieved excerpt only lists abbreviations and general information without detailed guidance. The Manual may describe this topic elsewhere, but it is not present in the current context.",
        }
    
    # Phase 5 Case 2.6: Numeric answer validation
    # Check if question asks for duration, percentage, or amount
    numeric_question_patterns = [
        r"\\b(how long|how many|duration|validity|period|years?|months?|days?)\\b",
        r"\\b(percentage|percent|%|threshold|limit|ceiling|maximum|minimum)\\b",
        r"\\b(cost|amount|rupees?|rs\\.?|price|budget|allocation)\\b",
    ]
    asks_numeric = any(re.search(p, question.lower()) for p in numeric_question_patterns)
    
    if asks_numeric:
        # Check if context contains relevant numbers
        numeric_indicators = [
            r"\\d+\\s*(year|month|day|percent|%|rupee|rs)",
            r"\\b(one|two|three|four|five|six|seven|eight|nine|ten)\\s+(year|month|day)",
            r"\\d+[,.]\\d+",  # Numbers like 1.5, 10,000
        ]
        has_numbers = any(re.search(p, total_text, re.IGNORECASE) for p in numeric_indicators)
        
        if not has_numbers:
            # Question asks for numeric info but context has no numbers
            return {
                "passed": False,
                "warning": True,
                "max_score": 0.0,
                "reason": "The retrieved text confirms the topic exists, but it does not state the specific duration/amount/percentage requested. The Manual may specify this elsewhere, but it is not present in this excerpt.",
            }
    
    # Case 3: Check similarity scores (if available)
    scores = [h.get("score", 0) for h in hits if h.get("score") is not None]
    
    if scores:
        max_score = max(scores)
        MIN_SCORE = 0.18  # Lowered from 0.25 to allow messy PDF / annexure embeddings
        
        if max_score < MIN_SCORE:
            return {
                "passed": True,       # Allow answer but warn
                "warning": True,
                "max_score": max_score,
                "reason": f"Low relevance ({max_score:.2f})",
            }
        
        # Case 4: Good enough context
        return {
            "passed": True,
            "warning": False,
            "max_score": max_score,
            "reason": "OK",
        }
    
    # No scores available - accept if we have reasonable text
    return {
        "passed": True,
        "warning": False if word_count >= 15 else True,  # Warn if short but no scores
        "max_score": 1.0,
        "reason": "OK (no scores available)",
    }


def expand_query_aggressively(question: str) -> list[str]:
    """Generate multiple query variants for comprehensive retrieval."""
    import re
    
    variants = [question]
    
    # Acronym expansions
    acronym_map = {
        "PC-I": ["PC-I", "Planning Commission Proforma I", "Planning Commission Form 1"],
        "PC-II": ["PC-II", "Planning Commission Proforma II", "feasibility study"],
        "PC-III": ["PC-III", "monitoring report", "progress report"],
        "PC-IV": ["PC-IV", "completion report", "project closure"],
        "PC-V": ["PC-V", "evaluation report"],
        "DDWP": ["DDWP", "Divisional Development Working Party"],
        "CDWP": ["CDWP", "Central Development Working Party"],
        "ECNEC": ["ECNEC", "Executive Committee National Economic Council"],
        "PDWP": ["PDWP", "Provincial Development Working Party"],
        "CHIRA": ["CHIRA", "Climate Hazard Initial Risk Assessment"],
        "VGF": ["VGF", "Viability Gap Fund"],
        "PPP": ["PPP", "Public Private Partnership"],
        "PAO": ["PAO", "Principal Accounting Officer"],
    }
    
    for abbr, expansions in acronym_map.items():
        if abbr in question:
            for exp in expansions[:2]:
                variants.append(question.replace(abbr, exp))
    
    # Extract key terms
    words = re.findall(r'\b[A-Za-z]{4,}\b', question)
    if len(words) >= 3:
        variants.append(" ".join(words[:10]))
    
    # Remove question words for keyword search
    q_clean = re.sub(r'^(what|when|where|who|why|how|explain|describe|list)\s+', 
                     '', question.lower(), flags=re.IGNORECASE)
    if q_clean != question.lower():
        variants.append(q_clean)
    
    return list(set(variants))[:5]


def detect_question_category(question: str) -> str:
    """Classify question into PC-form or topic category for targeted retrieval.
    
    ANTI-HALLUCINATION FIX: Route retrieval only to relevant manual sections.
    Prevents mixing PC-I, PC-II, PC-III, PC-IV, PC-V content inappropriately.
    """
    lower = question.lower()
    
    # PC-form detection (highest priority)
    if any(term in lower for term in ["pc-i", "pc i", "pc 1", "proforma i", "proforma 1"]):
        return "PC-I"
    if any(term in lower for term in ["pc-ii", "pc ii", "pc 2", "proforma ii", "proforma 2"]):
        return "PC-II"
    if any(term in lower for term in ["pc-iii", "pc iii", "pc 3", "proforma iii", "proforma 3"]):
        return "PC-III"
    if any(term in lower for term in ["pc-iv", "pc iv", "pc 4", "proforma iv", "proforma 4"]):
        return "PC-IV"
    if any(term in lower for term in ["pc-v", "pc v", "pc 5", "proforma v", "proforma 5"]):
        return "PC-V"
    
    # Topic detection
    if any(term in lower for term in ["monitor", "progress report", "tracking", "implementation"]):
        return "Monitoring"
    if any(term in lower for term in ["pfm act", "public finance", "finance management", "fiscal"]):
        return "PFM Act"
    if any(term in lower for term in ["budget", "allocation", "funding", "appropriation"]):
        return "Budget"
    if any(term in lower for term in ["ecnec", "cdwp", "ddwp", "approval", "scrutiny"]):
        return "Approval Process"
    
    return "General"


def decompose_question(question: str) -> list[str]:
    """Split compound questions into sub-questions for better retrieval.
    
    CRITICAL FIX #4: Handles multi-part questions like "What are stages AND which proforma for each?"
    Detects "and" that introduces a new question clause.
    """
    lower = question.lower()
    
    # Pattern: "What is X, and explain Y?" or "List X and describe Y"
    if " and " not in lower:
        return [question]
    
    idx = lower.index(" and ")
    after_and = question[idx+5:].strip()
    
    # Check if "and" starts a new question clause (question word or verb)
    question_starters = ["what", "which", "how", "explain", "describe", "list", "who", "when", "where", "why", "define"]
    if any(after_and.lower().startswith(w) for w in question_starters):
        part1 = question[:idx].strip()
        if not part1.endswith("?"):
            part1 += "?"
        
        part2 = after_and.strip()
        if not part2.endswith("?"):
            part2 += "?"
        
        return [part1, part2]
    
    return [question]


def rewrite_query_with_history(question: str, chat_history: list) -> str:
    """ENTERPRISE v1.1.0: LLM-based contextual query rewriting.
    
    Uses Ollama LLM to intelligently rewrite follow-up questions into standalone queries
    by analyzing chat history. Much more sophisticated than pattern matching.
    
    Example:
    - History: "Tell me about PC-I"
    - User asks: "Who signs it?"
    - Rewritten: "Who signs the PC-I form?"
    
    This enables true contextual memory for follow-up questions.
    """
    if not chat_history or len(chat_history) < 2:
        # No history or too short, return original
        return question
    
    # Extract last 4 messages (2 user + 2 bot turns) for context
    recent = chat_history[-4:] if len(chat_history) >= 4 else chat_history
    
    # Build history context
    history_text = ""
    for msg in recent:
        if isinstance(msg, dict):
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            if role == "user":
                history_text += f"User: {content}\\n"
            else:
                # Only include first 150 chars of bot response to avoid bloat
                history_text += f"Bot: {content[:150]}...\\n"
    
    # Check if question is short and ambiguous (likely a follow-up)
    is_followup = (
        len(question.split()) <= 10 and
        not any(pc in question.upper() for pc in ["PC-I", "PC-II", "PC-III", "PC-IV", "PC-V"]) and
        not question.lower().startswith(("what is the", "define", "explain", "tell me about"))
    )
    
    if not is_followup:
        # Question is detailed enough, return original
        return question
    
    # Use LLM to rewrite the question contextually
    try:
        from src.models.local_model import LocalModel
        rewriter = LocalModel(backend="ollama")
        
        rewrite_prompt = f"""Given this conversation history:
{history_text}

The user just asked: "{question}"

This is a follow-up question. Rewrite it into a complete, standalone question that includes relevant context from the conversation history. Keep it concise (under 20 words).

Standalone question:"""
        
        # Use low temperature for deterministic rewriting
        rewritten = rewriter._ollama_generate(
            rewrite_prompt, 
            max_tokens=50, 
            temperature=0.0,
            system="You are a query rewriter. Rewrite follow-up questions into standalone questions using conversation context. Be concise and accurate."
        )
        
        # Clean up the rewritten query
        rewritten = rewritten.strip()
        if rewritten and len(rewritten) > 5 and len(rewritten.split()) <= 25:
            return rewritten
        else:
            # Fallback to original if rewrite failed
            return question
            
    except Exception as e:
        # Fallback to original on any error
        import logging
        logging.getLogger("pdbot").warning(f"Query rewriting failed: {e}, using original question")
        return question


def generate_answer_generative(question: str) -> str:
    """Run the full Generative Mode pipeline and return markdown text with citations."""
    # ENTERPRISE FEATURE: Rewrite query using chat history for contextual memory
    chat_history = st.session_state.get("chat_history", [])
    contextualized_question = rewrite_query_with_history(question, chat_history)
    
    # Use contextualized question for retrieval, but keep original for display
    search_query = contextualized_question
    
    # Ensure manual is loaded at call-time if nothing is available yet
    try:
        if not (st.session_state.get("raw_pages") or []) and int(st.session_state.get("last_index_count") or 0) == 0:
            _load_builtin_manual(force=False)
    except Exception:
        pass
    
    # ANTI-HALLUCINATION FIX: Detect question category for targeted retrieval
    question_category = detect_question_category(search_query)
    
    # FIX #3: Generate query variants for better retrieval
    query_variants = expand_query_aggressively(search_query)
    
    # CRITICAL FIX #4: Decompose multi-part questions for comprehensive retrieval
    sub_questions = decompose_question(search_query)
    
    # Step 1: Retrieve for each query variant and sub-question
    all_hits: list[dict] = []
    use_qdrant = bool(st.session_state.get("indexed_ok") or int(st.session_state.get("last_index_count") or 0) > 0)
    
    for variant in query_variants:
        for sq in sub_questions:
            combined = f"{variant} {sq}".strip()
            sq_hits: list[dict] = []
            if use_qdrant and _RAG_OK and search is not None:
                try:
                    # v2.0.0: precise retrieval with sentence-level reranker
                    sq_hits = search(combined, top_k=3, qdrant_url=_qdrant_url(), mmr=False, lambda_mult=0.7, min_score=0.18)  # type: ignore
                except TypeError:
                    sq_hits = search(combined, top_k=3, qdrant_url=_qdrant_url())  # type: ignore
                except Exception:
                    sq_hits = []
            
            # ANTI-HALLUCINATION FIX: Filter by PC-form category if applicable
            if question_category in ["PC-I", "PC-II", "PC-III", "PC-IV", "PC-V"]:
                category_hits = []
                for h in sq_hits:
                    text_lower = h.get("text", "").lower()
                    # Only include if text mentions the specific PC form or is proforma-neutral
                    if question_category.lower() in text_lower or "proforma" not in text_lower:
                        category_hits.append(h)
                sq_hits = category_hits if category_hits else sq_hits  # Fallback to all if filtering removes everything
            
            all_hits.extend(sq_hits)
    
    hits = dedup_chunks(all_hits)
    if hits:
        hits = sorted(hits, key=lambda h: h.get("rerank_score", h.get("score", 0)), reverse=True)[:3]

    # Fallback: extract exact sentences from raw_pages if retrieval is empty
    if (not hits) and (st.session_state.get("raw_pages") or []):
        try:
            pages_full = st.session_state.get("raw_pages") or []
            locs_fb = find_exact_locations(question, pages_full, max_results=40)
            for it in (locs_fb or []):
                hits.append({
                    "text": (it.get("sentence") or "").strip(),
                    "page": it.get("page"),
                    "score": None,
                    "source": RAG_COLLECTION,
                })
        except Exception:
            pass

    # Final dedup safeguard before building context
    hits = dedup_chunks(hits)
    # Legacy retry disabled to keep top reranked chunks only

    # Step 3: Build context within ~6000 tokens (FIX #2: increased from 3500)
    # FIX #2: Increased token budget for more comprehensive context
    ctx_pack = build_context(hits, token_budget=6000)
    context_text = (ctx_pack.get("context") or "").strip()
    # Guard: if build_context returned empty but we have hits, build a simple context fallback
    if not context_text and hits:
        try:
            context_text = ("\n\n".join([str(h.get("text", "")).strip() for h in hits if h.get("text")])[:4000]).strip()
        except Exception:
            context_text = ""
    citations = ctx_pack.get("citations") or []
    citations = citations[:1]
    # Persist for UI panels and inline regen
    try:
        st.session_state["last_hits"] = hits
        st.session_state["last_context"] = context_text
        st.session_state["last_question"] = question
    except Exception:
        pass

    if not context_text:
        # Attempt keyword fallback before giving up
        pages_full = st.session_state.get("raw_pages") or []
        if pages_full:
            kw_hits = _keyword_fallback_hits(question, pages_full, max_pages=3, max_sents=8)
            if kw_hits:
                # treat as hits and continue
                hits = kw_hits
                # CRITICAL FIX #2: Use same increased token budget for keyword fallback
                ctx_pack = build_context(hits, token_budget=6000)
                context_text = (ctx_pack.get("context") or "").strip() or "\n\n".join([h.get("text","") for h in hits])
                citations = ctx_pack.get("citations") or []
        if not context_text:
            # Return a distinguishable warn card markdown for upstream renderer to wrap
            return (
                "<div class='card warn'>⚠️ <strong>Answer:</strong><br/>"
                "**Insufficient grounded context.**<br/>"
                "Try rephrasing your question or use Exact Search mode to locate precise passages.<br/><br/>"
                + render_citations([]) + "</div>"
            )
    
    # PHASE 2 FIX: Quality check with warning flag
    quality_check = check_context_quality(hits, question)
    
    # Hard fail: No context at all - refuse to answer
    if not quality_check["passed"]:
        return (
            "<div class='card warn'>⚠️ <strong>Answer:</strong><br/>"
            f"**{quality_check['reason']}**<br/>"
            "Try rephrasing your question or use Exact Search mode to locate precise passages.<br/><br/>"
            + render_citations(citations) + "</div>"
        )
    
    # Store warning flag for display after answer generation
    show_warning = quality_check.get("warning", False)
    warning_reason = quality_check.get("reason", "")

    # v2.1.0: Use multi-class classifier for fallback logic
    from src.core.multi_classifier import get_classification_result
    classification = get_classification_result(question)
    query_class = classification.query_class
    
    # v2.1.0: Generative answering with automatic Groq fallback
    base_answer = ""
    _page = hits[0].get("page", 0) if hits else 0
    
    try:
        gen = LocalModel(model_name=globals().get("model_name", os.getenv("OLLAMA_MODEL", "mistral:latest")), backend="ollama")
        
        # v2.1.0: Use generate_with_fallback for automatic Groq fallback
        base_answer = gen.generate_with_fallback(
            query=question,
            classification=query_class,
            retrieved_context=context_text,
            retrieved_chunks=hits,
            page=_page,
            max_new_tokens=120,
            temperature=0.15,
        ) or ""
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"[DEBUG] Generation error: {e}")
        base_answer = ""

    # v2.0.8: Use base_answer directly (already sanitized by LocalModel)
    cleaned = base_answer.strip()
    
    # v2.0.8: Add ✅ prefix if valid answer
    if cleaned and not cleaned.startswith("Not found") and "✅" not in cleaned:
        cleaned = "✅ Answer:" + cleaned
    
    # v1.7.0: LIMIT CITATIONS TO TOP 3 SOURCES ONLY (fixes citation spam)
    citations_limited = citations[:3]  # Maximum 3 sources
    sources_md = ""  # citation already appended to answer
    
    # PHASE 2 FIX: Add low-confidence warning banner if needed
    final_answer = cleaned.strip() + "\n\n" + sources_md
    if show_warning:
        warning_banner = (
            "\n\n⚠️ **Low-Confidence Context**: "
            f"{warning_reason}. Please verify this information directly in the PDF manual."
        )
        final_answer = final_answer.strip() + warning_banner
    
    return final_answer.strip()

# --- Safe execution and generation helpers for form-submit flow ---
from concurrent.futures import ThreadPoolExecutor as _TPExecutor, TimeoutError as _FuturesTimeout

def write_crash(exc: Exception) -> None:
    try:
        import traceback as _tb
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        crash_dir = os.path.join(root, "logs", "crash")
        os.makedirs(crash_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        path = os.path.join(crash_dir, f"crash-{ts}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("Exception in PDBOT\n\n")
            f.write("".join(_tb.format_exception(type(exc), exc, exc.__traceback__)))
    except Exception:
        pass

def safe_predict(fn, timeout_s: int = 120):
    with _TPExecutor(max_workers=1) as ex:
        fut = ex.submit(fn)
        try:
            return fut.result(timeout=timeout_s)
        except _FuturesTimeout:
            raise RuntimeError("The model took too long to respond.")

def append_and_save_chat(q: str, answer_html: str) -> None:
    try:
        st.session_state.chat_history.append({"role": "user", "content": q})
        st.session_state.chat_history.append({"role": "assistant", "content": answer_html})
    except Exception:
        pass
    try:
        items = load_chat_history() or []
        items.append({"role": "user", "content": q})
        items.append({"role": "assistant", "content": answer_html})
        save_chat_history(items)
    except Exception:
        pass

def stream_response(text: str):
    """Stream text word-by-word (configurable delay for typing effect).
    
    Set PDBOT_STREAM_DELAY_MS=0 for instant display (default).
    Set PDBOT_STREAM_DELAY_MS=20 for 50 words/sec typing effect.
    
    Yields: Individual words with optional delay.
    """
    import time
    delay_ms = int(os.getenv("PDBOT_STREAM_DELAY_MS", "0"))
    delay_sec = delay_ms / 1000.0
    
    words = text.split()
    for i, word in enumerate(words):
        # Add space except for last word
        yield word + (" " if i < len(words) - 1 else "")
        # Optional delay for typing effect (0 = instant)
        if delay_sec > 0:
            time.sleep(delay_sec)

def generate_answer(question: str) -> tuple[str, list[str]]:
    """
    v2.1.0: Updated with multi-class classifier and Groq fallback.
    
    Classification flow:
    1. Classify query into 12 classes
    2. If off_scope/red_line/abusive → return guardrail response
    3. If in_scope → proceed with RAG + optional retrieval hints
    4. If fallback_required → use Groq with same guardrails
    """
    from src.core.multi_classifier import MultiClassifier, get_classification_result
    from src.core.templates import get_guardrail_response, get_fallback_response
    
    # Define exception for type safety
    class RetrievalBackendError(Exception):
        """Raised when vector database is unavailable"""
        pass
    
    # STEP 1: Multi-class classification
    classifier = MultiClassifier()
    classification = classifier.classify(question)
    query_class = classification.query_class
    
    if DEBUG_MODE:
        print(f"[DEBUG] Classification: {query_class}/{classification.subcategory}")
    
    # STEP 2: Handle guardrail classes (NO RAG)
    if query_class in ["off_scope", "red_line", "abusive"]:
        response = get_guardrail_response(query_class, classification.subcategory or "")
        if DEBUG_MODE:
            print(f"[DEBUG] Returning guardrail response for {query_class}")
        return response, []  # No citations for safety queries
    
    # STEP 3: Proceed with RAG pipeline
    if DEBUG_MODE:
        print(f"[DEBUG] Proceeding with RAG, hints: {classification.retrieval_hints}")
    
    # Retrieve with classification hints
    top_k_local = int(min(8, max(1, int(st.session_state.get("top_k", 6) if "top_k" in st.session_state else (top_k if 'top_k' in globals() else 6)))))
    mode = st.session_state.get("answer_mode", "Generative")
    is_exact = str(mode).lower().startswith("exact")
    eff_top_k = min(8, 3 if is_exact else top_k_local)
    
    # Build context using vector search when available, else raw pages
    hits = []
    context = ""
    min_score = 0.15
    use_qdrant = bool(st.session_state.get("indexed_ok") or int(st.session_state.get("last_index_count") or 0) > 0)
    backend_error = None  # Track if backend fails
    
    if use_qdrant:
        try:
            if not _RAG_OK or search is None:  # type: ignore
                raise RuntimeError(f"Retrieval not available: {_RAG_IMPORT_ERR}")
            try:
                # v2.1.0: Pass retrieval hints to search
                hits = search(
                    question,
                    top_k=eff_top_k,
                    qdrant_url=_qdrant_url(),
                    mmr=True,
                    lambda_mult=0.5,
                    min_score=min_score,
                    retrieval_hints=classification.retrieval_hints,
                )  # type: ignore
            except TypeError:
                hits = search(question, top_k=eff_top_k, qdrant_url=_qdrant_url())  # type: ignore
            context = "\n\n".join([h.get("text", "") for h in hits])
        except RetrievalBackendError as e:
            backend_error = str(e)
            hits = []
            context = ""
            if DEBUG_MODE:
                print(f"[DEBUG] Backend error: {e}")
        except Exception as e:
            hits = []
            context = ""
            if DEBUG_MODE:
                print(f"[DEBUG] Unexpected retrieval error: {e}")
    
    if (not hits) and (st.session_state.get("raw_pages") or []):
        try:
            pages_full = st.session_state.get("raw_pages") or []
            locs_fb = find_exact_locations(question, pages_full, max_results=max(5, eff_top_k * 2))
            if locs_fb:
                hits = [{
                    "text": (it.get("sentence") or "").strip(),
                    "page": it.get("page"),
                    "score": None,
                    "source": RAG_COLLECTION,
                    "paragraph": it.get("paragraph"),
                    "line": it.get("line"),
                } for it in locs_fb]
        except Exception:
            pass
        if not context:
            pages = st.session_state.get("raw_pages") or []
            if hits:
                try:
                    context = _truncate_text("\n\n".join([h.get("text", "") for h in hits if h.get("text")]), max_chars=6000)
                except Exception:
                    context = ""
            if (not context) and pages:
                context = _truncate_text("\n\n".join(pages), max_chars=6000)

    # Answer
    citations: list[str] = []
    
    # Check for backend errors and return clear message
    if backend_error:
        answer = f"""⚠️ **System Error: Retrieval Backend Unavailable**

The vector database (Qdrant) is not responding. This prevents searching the manual.

**Error:** {backend_error}

**What to do:**
1. Check if Qdrant is running: `docker ps | grep qdrant`
2. Start Qdrant if needed: `docker start pndbot-qdrant`
3. Or restart: `docker run -d -p 6338:6333 qdrant/qdrant`
4. Contact IT support if the problem persists

*This is NOT a "manual doesn't cover this" situation - the system cannot search right now.*"""
        return answer, []
    
    if is_exact:
        pages = st.session_state.get("raw_pages") or []
        locs = find_exact_locations(question, pages, max_results=max(25, eff_top_k * 5)) if pages else []
        if locs:
            norm = []
            seen = set()
            for it in locs:
                pg = it.get('page')
                try:
                    if pg is not None:
                        pg = int(pg)
                        pg = pg if pg >= 1 else (pg + 1)
                except Exception:
                    pass
                para = it.get('paragraph'); line = it.get('line')
                sent = (it.get('sentence') or '').strip()
                key = (pg, para, line, sent)
                if key in seen: continue
                seen.add(key)
                norm.append({"page": pg, "paragraph": para, "line": line, "text": sent})
            lines = [f"Pg {n.get('page','?')}, Para {n.get('paragraph','?')}, Line {n.get('line','?')}: \"{n.get('text','')}\"" for n in norm]
            answer = "\n\n".join(lines) if lines else "No grounded passages found. Please rephrase or narrow the scope."
            hits = [{
                "text": n.get("text"),
                "page": n.get("page"),
                "score": None,
                "source": RAG_COLLECTION,
                "paragraph": n.get("paragraph"),
                "line": n.get("line"),
            } for n in norm]
        else:
            # Keyword fallback for common PC-forms queries (e.g., 'PC V')
            fallback_hits = []
            try:
                ql = (question or "").lower()
                variants = set()
                if "pc v" in ql or "pc-v" in ql or "pcv" in ql or "pc 5" in ql or "pc-5" in ql:
                    variants.update(["pc v", "pc-v", "pcv", "pc 5", "pc-5"])
                if "checklist" in ql:
                    variants.add("checklist")
                if pages and variants:
                    for idx, pg_text in enumerate(pages, start=1):
                        low = pg_text.lower()
                        if any(v in low for v in variants):
                            # Take up to 2 lines around the first occurrence
                            lines = [l.strip() for l in pg_text.splitlines() if l.strip()]
                            sample = []
                            for l in lines:
                                ll = l.lower()
                                if any(v in ll for v in variants):
                                    sample.append(l)
                                    if len(sample) >= 2:
                                        break
                            if sample:
                                for s in sample:
                                    fallback_hits.append({
                                        "text": s,
                                        "page": idx,
                                        "score": None,
                                        "source": RAG_COLLECTION,
                                        "paragraph": None,
                                        "line": None,
                                    })
                            if len(fallback_hits) >= max(5, eff_top_k):
                                break
            except Exception:
                pass
            if fallback_hits:
                hits = fallback_hits
                lines = [f"Pg {h.get('page','?')}: \"{h.get('text','').strip()}\"" for h in hits[:max(5, eff_top_k)]]
                answer = "\n\n".join(lines)
            else:
                answer = "No grounded passages found. Please rephrase or narrow the scope."
    else:
        # New structured Generative pipeline
        try:
            answer = generate_answer_generative(question)
        except Exception as _e_gen:
            logging.exception("Generative pipeline failed")
            if DEBUG_MODE:
                import traceback
                print(f"[DEBUG] Generative pipeline error: {_e_gen}")
                print(traceback.format_exc())
            answer = f"❌ **Error generating answer:** {str(_e_gen)}\n\nPlease try again or contact support if the problem persists."

    # Build HTML card and citations
    # Persist last Q/A context for inline Regenerate button visibility and behavior
    try:
        st.session_state["last_question"] = question
        st.session_state["last_hits"] = hits
        st.session_state["last_context"] = context
        # Minimal metadata used by inline regen (fallbacks exist if missing)
        _engine = st.session_state.engine if "engine" in st.session_state else "LLM (Ollama)"
        st.session_state["last_meta"] = {
            "backend": "ollama",
            "model": getattr(locals().get("generator", None), "model_name", os.getenv("OLLAMA_MODEL", "mistral:latest")),
            "max_new_tokens": int(globals().get("max_tokens", 768)),
            "top_k": int(globals().get("top_k", 6)),
            "exact_mode": str(st.session_state.get("answer_mode", "Generative")).lower().startswith("exact"),
            "temperature": float(globals().get("temperature", 0.2)),
        }
    except Exception:
        pass

    # Guard: if sanitization removed all model text, provide a fallback notice
    raw_ans = (answer or "").strip()
    if not raw_ans:
        raw_ans = "Not available in the provided document."
    ans_norm = normalize_markdown(raw_ans, enforce_bullets=True, max_line_len=110)
    src_lines = []
    for h in (hits or [])[:5]:
        pg = h.get("page")
        if pg is None or (isinstance(pg, str) and not str(pg).isdigit()):
            continue
        para = h.get("paragraph"); line = h.get("line")
        if para is not None or line is not None:
            src_lines.append(f"Page {pg} – Paragraph {para if para is not None else '?'} – Line {line if line is not None else '?'}")
        else:
            src_lines.append(f"Page {pg}")
    # Only show per-hit Source block for Exact mode; Generative mode already includes a Sources section
    src_block = ("<br/><br/>📘 <strong>Source:</strong><br/>" + "<br/>".join(src_lines)) if (src_lines and is_exact) else ""
    low = (answer or "").strip().lower()
    if low.startswith("not in the manual") or low.startswith("no grounded"):
        answer_html = f"<div class='card warn'>⚠️ <strong>Answer:</strong><br/>{ans_norm}{src_block}</div>"
    else:
        answer_html = f"<div class='card success'>✅ <strong>Answer:</strong><br/>{ans_norm}{src_block}</div>"
    return answer_html, src_lines

# Sidebar options (collapsible)
with st.sidebar:
    # ---- Manual: Fixed path only ----
    if "builtin_indexed" not in st.session_state:
        st.session_state.builtin_indexed = False
    if "current_manual_path" not in st.session_state:
        st.session_state.current_manual_path = ""
    if "source_file" not in st.session_state:
        st.session_state.source_file = ""
    # Upload/Paste removed: no pasted_text state

    def _load_builtin_manual(force: bool = False):
        """Load the built-in manual pages always; index into Qdrant when deps are available.
        This keeps Exact mode working even if LangChain/Qdrant aren't installed or running.
        """
        manual_path = _default_manual_path()
        if not os.path.isfile(manual_path):
            st.warning(f"Built-in manual not found: {manual_path}. Set DEFAULT_MANUAL_PATH or place a PDF at data/default/manual.pdf.")
            return

        # Skip rework if same manual already loaded (pages loaded or indexed) and not forced
        same_manual = st.session_state.get("current_manual_path") == manual_path
        already_have_pages = bool(st.session_state.get("raw_pages"))
        already_indexed = bool(int(st.session_state.get("last_index_count") or 0) > 0)
        if not force and same_manual and (already_have_pages or already_indexed):
            return

        # Always load raw pages for Exact mode and basic grounding
        pages_loaded = False
        try:
            loader = PyPDFLoader(manual_path)
            with st.spinner("Reading pages…"):
                docs = loader.load()
            st.session_state["raw_pages"] = [getattr(d, "page_content", "") for d in docs]
            st.session_state["raw_page_count"] = len(docs)
            pages_loaded = True
        except Exception as _e_pages:
            # Leave a compact message but don't crash; user can still attempt indexing
            st.warning(f"Unable to read PDF pages: {_e_pages}")
            st.session_state["raw_pages"] = []
            st.session_state["raw_page_count"] = None

        # Update file metadata regardless
        st.session_state["current_manual_path"] = manual_path
        st.session_state["source_file"] = os.path.basename(manual_path)

        # Try to index if RAG is available; otherwise keep graceful fallback
        n_indexed = 0
        try:
            if _RAG_OK and ingest_pdf is not None:  # type: ignore
                with st.spinner("Indexing built-in manual…"):
                    n_indexed = ingest_pdf(
                        manual_path,
                        qdrant_url=_qdrant_url(),
                    )  # type: ignore
                st.session_state["indexed_ok"] = n_indexed > 0
                st.session_state["last_index_count"] = n_indexed
                st.session_state["builtin_indexed"] = n_indexed > 0
            else:
                # Keep explicit but non-blocking notice; Exact mode remains available
                st.info("Retrieval indexing skipped (dependencies missing). Exact mode will still work.")
                st.session_state["indexed_ok"] = False
                st.session_state["last_index_count"] = 0
                st.session_state["builtin_indexed"] = False
        except Exception as e:
            st.error(f"Failed to index into Qdrant: {e}")
            st.session_state["indexed_ok"] = False
            st.session_state["last_index_count"] = 0
            st.session_state["builtin_indexed"] = False

        # Final status message
        src_name = os.path.basename(manual_path)
        if pages_loaded and n_indexed > 0:
            st.success(f"Loaded built-in manual: {src_name} • Pages: {st.session_state.get('raw_page_count')} • Indexed {n_indexed} chunks.")
        elif pages_loaded:
            st.success(f"Loaded built-in manual pages: {src_name} • Pages: {st.session_state.get('raw_page_count')}. Indexing not available.")
        else:
            st.error("Manual could not be read. Install 'langchain-community' or 'pypdf' to enable PDF reading.")

    with st.expander("Manual", expanded=True):
        st.caption("The app auto-loads the fixed manual once and reuses it.")
        st.text(f"Path: {_default_manual_path()}")
        if st.button("Reload manual", help="Force reload and re-index the manual"):
            _load_builtin_manual(force=True)
        # Auto-load on first run if not yet indexed
        _load_builtin_manual(force=False)

    with st.expander("Settings", expanded=False):
        st.markdown("**Chat Controls**")
        # Open a fresh session in a new tab and ask for name
        st.markdown(
            '<a href="./?ask_name=1" target="_blank" class="stButton"><button>New Chat ↗</button></a>',
            unsafe_allow_html=True,
        )
        if st.button("Clear Chat"):
            try:
                clear_chat_history()
                st.session_state["chat_history"] = []
                # no name prompt after clearing
                st.session_state["is_admin"] = False
                st.success("Cleared this session’s local history.")
            except Exception:
                st.warning("Unable to clear saved history.")
        # Quick status line
        src = st.session_state.get("source_file") or os.path.basename(_default_manual_path())
        n = int(st.session_state.get("last_index_count") or 0)
        pg = st.session_state.get("raw_page_count")
        st.markdown(f"Current file: `{src}` • Pages: {pg if pg is not None else '?'} • Chunks: {n}")

    # Initialize engine/predictor state defaults
    if "engine" not in st.session_state:
        st.session_state.engine = "LLM (Ollama)"
    # v2.0.5: Removed pretrained mode - Ollama only

    if st.session_state.get("is_admin", False):
        with st.expander("Options", expanded=True):
            # v2.0.5: Removed pretrained toggle - Ollama only
            engine = "LLM (Ollama)"
            st.session_state.engine = engine
            
            model_name = st.text_input("Ollama model", value=os.getenv("OLLAMA_MODEL", "mistral:latest"))
            # Answer mode control is available in the Chat input bar.
            # FIX #10: Increased defaults and ranges for better retrieval
            top_k = st.slider("Top-K context chunks", 1, 20, 10)
            # FIX #10: Increase upper bound and default (was 768 max 1000)
            max_tokens = st.slider("Max new tokens", 64, 2000, 1200, step=64)
            # FIX-3: default lower temperature to 0.2 to reduce hallucinations
            temperature = st.slider("Creativity (temperature)", 0.0, 1.5, 0.2, step=0.1)
            # Apply/Reset via flags (no UI in callbacks) — inline to avoid 'app' import
            def cb_apply():
                st.session_state["manual_action"] = "apply"
            def cb_reset():
                st.session_state["manual_action"] = "reset"
            cc1, cc2 = st.columns(2)
            with cc1:
                st.button("Apply", key="__apply", on_click=cb_apply)
            with cc2:
                st.button("Reset", key="__reset", on_click=cb_reset)
    with st.expander("Branding (admin)", expanded=False):
        # Upload a logo and persist it under src/assets/branding_logo.png
        up = st.file_uploader("Upload logo (PNG/JPG/SVG)", type=["png","jpg","jpeg","svg"], accept_multiple_files=False)
        col_ba, col_bb = st.columns([1,1])
        with col_ba:
            if up is not None:
                try:
                    assets_dir = os.path.join(_THIS_DIR, "assets")
                    os.makedirs(assets_dir, exist_ok=True)
                    # Determine extension
                    import pathlib as _pl
                    ext = _pl.Path(up.name).suffix.lower() or ".png"
                    if ext not in (".png", ".jpg", ".jpeg", ".svg"):
                        ext = ".png"
                    save_path = os.path.join(assets_dir, f"branding_logo{ext}")
                    with open(save_path, "wb") as f:
                        f.write(up.getbuffer())
                    # Persist path for future runs
                    cfg_dir = os.path.join(_ROOT, "config")
                    os.makedirs(cfg_dir, exist_ok=True)
                    with open(os.path.join(cfg_dir, "brand_logo_path.txt"), "w", encoding="utf-8") as f:
                        f.write(save_path)
                    st.session_state["brand_logo_path_override"] = save_path
                    try:
                        safe_rerun()
                    except Exception:
                        pass
                except Exception as _e_logo:
                    st.error(f"Failed to save logo: {_e_logo}")
        with col_bb:
            # Manual path entry if the file already exists elsewhere
            manual_logo = st.text_input("Or set logo path", value=st.session_state.get("brand_logo_path_override", ""), placeholder="C:/path/to/logo.png")
            if st.button("Apply logo path"):
                if manual_logo and os.path.isfile(manual_logo):
                    try:
                        cfg_dir = os.path.join(_ROOT, "config")
                        os.makedirs(cfg_dir, exist_ok=True)
                        with open(os.path.join(cfg_dir, "brand_logo_path.txt"), "w", encoding="utf-8") as f:
                            f.write(manual_logo)
                        st.session_state["brand_logo_path_override"] = manual_logo
                        try:
                            safe_rerun()
                        except Exception:
                            pass
                    except Exception as _e_lp:
                        st.error(f"Failed to save logo path: {_e_lp}")
                else:
                    st.warning("Please enter a valid file path to an image.")
    # Show a note when not in admin mode (can't use `else:` here because additional blocks follow)
    if not st.session_state.get("is_admin", False):
        st.sidebar.info("Admin controls are hidden.")

    # Handle settings action flags
    action = st.session_state.get("manual_action")
    if action == "apply":
        st.success("Settings applied.")
        st.session_state["manual_action"] = None
    elif action == "reset":
        st.info("Settings reset.")
        st.session_state["manual_action"] = None

    # v2.0.5: Removed pretrained options - Ollama only

    # Engine status (Ollama + Groq fallback)
    if st.session_state.get("is_admin", False):
        _lm_probe = LocalModel(model_name=model_name, backend="ollama")
        _status = _lm_probe.ollama_status()
        _groq_ok = _lm_probe.groq_available()
        icon = "✅" if _status.get("alive") else "❌"
        model_icon = "✅" if _status.get("has_model") else "❌"
        groq_icon = "✅" if _groq_ok else "❌"
        st.markdown(f"Ollama: {icon} &nbsp;&nbsp; Model '{model_name}': {model_icon} &nbsp;&nbsp; Groq fallback: {groq_icon}")
        with st.sidebar.expander("Backend status", expanded=False):
            st.write("Engine: LLM (Ollama + Groq fallback)")
            if _status.get("alive"):
                st.success("Ollama reachable")
            else:
                st.warning("Ollama not reachable. Will use Groq fallback if available.")
            if _groq_ok:
                st.success("Groq API available (fallback)")
            else:
                st.info("Groq API not available")
            
            # v2.0.7: Test Groq fallback button
            st.divider()
            st.caption("🧪 Test Groq Fallback")
            if "force_groq_fallback" not in st.session_state:
                st.session_state.force_groq_fallback = False
            force_groq = st.toggle(
                "Force Groq (bypass Ollama)",
                value=st.session_state.force_groq_fallback,
                key="groq_toggle",
                help="Enable to test Groq API directly, bypassing Ollama"
            )
            st.session_state.force_groq_fallback = force_groq
            if force_groq:
                st.info("🚀 Next query will use Groq API directly")
            else:
                st.caption("Normal mode: Ollama first, Groq as fallback")

    # Retrieval / LangChain / Qdrant status (compact: Online/Offline)
    if st.session_state.get("is_admin", False):
        with st.expander("Backend status", expanded=False):
            # LangChain availability
            try:
                import langchain  # type: ignore
                lc_ok = True
            except Exception:
                lc_ok = False
            try:
                import langchain_text_splitters  # type: ignore
                lcts_ok = True
            except Exception:
                lcts_ok = False
            try:
                import langchain_community  # type: ignore
                lcc_ok = True
            except Exception:
                lcc_ok = False
            _lc_label = "🟢 Installed" if (lc_ok and lcts_ok and lcc_ok) else "ℹ️ Not installed (optional)"
            st.markdown(f"LangChain: {_lc_label}")
            if not _RAG_OK and _RAG_IMPORT_ERR is not None:
                st.caption(f"RAG components missing; retrieval will be skipped until installed.")

            # Qdrant connectivity and collection presence
            q_url = _qdrant_url()
            coll = RAG_COLLECTION
            q_ok = False
            coll_ok = False
            try:
                from qdrant_client import QdrantClient  # type: ignore
                client = QdrantClient(url=q_url)
                # try a lightweight call
                client.get_collections()
                q_ok = True
                try:
                    client.get_collection(coll)
                    coll_ok = True
                except Exception:
                    coll_ok = False
            except Exception:
                q_ok = False
            st.markdown(f"Qdrant: {'🟢 Online' if q_ok else '🔴 Offline'}")
            if q_ok:
                st.markdown(f"Collection '{coll}': {'✅ Ready' if coll_ok else '⚠️ Missing'}")
            # Manual and engine summary
            src_name = st.session_state.get("source_file") or os.path.basename(os.getenv("DEFAULT_MANUAL_PATH", "manual.pdf"))
            pages_ct = st.session_state.get("raw_page_count")
            chunks_ct = int(st.session_state.get("last_index_count") or 0)
            
            # v1.8.0: Try to get live count from Qdrant if available
            if q_ok and _RAG_OK:
                try:
                    from qdrant_client import QdrantClient
                    qc_client = QdrantClient(url=_qdrant_url())
                    live_count = qc_client.get_collection(coll).points_count
                    chunks_ct = live_count
                    st.session_state["last_index_count"] = live_count
                except Exception:
                    pass  # Use cached count if query fails
            
            engine_label = "Local" if st.session_state.engine == "LLM (Ollama)" else "Pretrained"
            st.markdown(f"Manual: `{src_name}`")
            st.markdown(f"Pages: {pages_ct if pages_ct is not None else '?'} • Chunks: {chunks_ct}")
            st.markdown(f"Engine: {engine_label}")

    # Name entry removed from sidebar; handled via modal

# State
if "model_name" not in globals():
    model_name = os.getenv("OLLAMA_MODEL", "mistral:latest")
if "top_k" not in globals():
    top_k = 6
if "max_tokens" not in globals():
    max_tokens = 768
if "temperature" not in globals():
    temperature = 0.2
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of (role, text)
if "doc_text" not in st.session_state:
    st.session_state.doc_text = ""
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "doc_processed" not in st.session_state:
    st.session_state.doc_processed = False
if "raw_pages" not in st.session_state:
    st.session_state.raw_pages = []
if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""
if "_greeted" not in st.session_state:
    st.session_state._greeted = False
if "confirm_ui" not in st.session_state:
    st.session_state.confirm_ui = False
if "pending_question" not in st.session_state:
    st.session_state.pending_question = ""
if "pretrained_simple_toggle" not in st.session_state:
    st.session_state.pretrained_simple_toggle = False
# Ensure no late override flips the user's selection; defaults handled in init_state()

# Legacy modal login removed: inline optional name input is used; do not gate usage

# Sidebar visibility: only show for admins; persist until New/Clear
if st.session_state.get("is_admin"):
    st.markdown("<style>[data-testid='stSidebar']{display:flex !important;}</style>", unsafe_allow_html=True)
else:
    st.markdown("<style>[data-testid='stSidebar']{display:none !important;}</style>", unsafe_allow_html=True)

# Remove personalization/greeting: do not address user by name anywhere

# If a post-chat rating dialog is requested, display it here (outside callbacks)
if st.session_state.get("show_rating_modal"):
    rating_modal()

# Render notices (info/warn) once in main flow
_notice = st.session_state.pop("ui_notice", None)
if _notice and not st.session_state.get("busy"):
    try:
        level, msg = _notice
        if level == "warn":
            st.warning(msg)
        else:
            st.info(msg)
    except Exception:
        pass

# Feedback utilities
from datetime import datetime
from pathlib import Path

def save_feedback(rating: int, review: str, question: str, mode: str, model: str):
    folder = Path(os.path.dirname(_ROOT)) / "feedback" if False else Path(_ROOT) / "feedback"
    folder = folder / f"{rating}_star"
    folder.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    user = (st.session_state.get("username", "Guest") or "Guest").replace(" ", "_")
    path = folder / f"{ts}_{user}.txt"
    content = (
        f"User: {user}\nTime: {ts}\nRating: {rating}\nReview: {review}\nLast Question: {question}\nMode: {mode}\nModel: {model}"
    )
    path.write_text(content, encoding="utf-8")
    return str(path)

def render_feedback_panel():
    if not st.session_state.get("show_feedback"):
        return
    st.markdown("<div class='feedback-card'>", unsafe_allow_html=True)
    st.markdown("**Before starting a new session, please rate your experience with the bot.**")
    # Capture/confirm username for saving with feedback
    _default_name = st.session_state.get("username") or st.session_state.get("user_name") or ""
    _new_name = st.text_input("Your name (optional)", key="_rating_name", value=str(_default_name))
    if isinstance(_new_name, str) and _new_name.strip():
        st.session_state["username"] = _new_name.strip()
        st.session_state["user_name"] = _new_name.strip()
    c1, c2, c3 = st.columns(3)
    if c1.button("⭐", key="fb1"):
        st.session_state["_rating_sel"] = 1
    if c2.button("⭐⭐", key="fb2"):
        st.session_state["_rating_sel"] = 2
    if c3.button("⭐⭐⭐", key="fb3"):
        st.session_state["_rating_sel"] = 3
    review_txt = st.text_area("Optional review", key="_rating_review", height=80)
    if st.button("Submit Feedback"):
        rating = int(st.session_state.get("_rating_sel") or 0)
        if rating <= 0:
            st.warning("Please select a rating (1-3 stars).")
        else:
            last_q = st.session_state.get("last_question", "")
            mode = st.session_state.get("answer_mode", "Generative")
            model = (st.session_state.get("engine") or "LLM (Ollama)")
            save_feedback(rating, review_txt, last_q, mode, model)
            try:
                st.toast("✅ Thanks for your feedback!")
            except Exception:
                st.success("✅ Thanks for your feedback!")
            # Clear and start new session
            st.session_state.show_feedback = False
            st.session_state._rating_sel = 0
            st.session_state._rating_review = ""
            st.session_state.chat_history = []
            st.session_state["chat_input"] = ""
            _uname2 = st.session_state.get("username") or "Guest"
            st.session_state.chat_history.append({"role": "assistant", "content": f"Welcome {_uname2}, you’re connected to the Planning Department Manual Assistant."})
            try:
                safe_rerun()
            except Exception:
                pass
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# Tabs: Ask vs Instructions
tab_chat, tab_help = st.tabs(["❓ Ask Questions", "📘 Instructions"])

with tab_chat:
    # Manual status line moved to Backend status in the sidebar

    # Chat section
    with st.expander("💬 Chat", expanded=True):
        idx_ok = bool(
            st.session_state.get("indexed_ok") or
            int(st.session_state.get("last_index_count") or 0) > 0 or
            (st.session_state.get("raw_pages") and len(st.session_state.get("raw_pages") or []) > 0)
        )
        if not idx_ok:
            # Ensure UI doesn't get stuck disabled if user clicked while manual is still loading
            try:
                st.session_state["busy"] = False
                st.session_state.pop("_finalize", None)
            except Exception:
                pass
            with st.container(border=True):
                st.warning("Manual not loaded yet. Load it to enable answers.")
                c1, c2 = st.columns([1,1])
                with c1:
                    if st.button("Load manual now", key="btn_load_manual_top"):
                        _load_builtin_manual(force=True)
                        try:
                            safe_rerun()
                        except Exception:
                            pass
                with c2:
                    if st.session_state.get("is_admin"):
                        cur_guess = _default_manual_path()
                        newp = st.text_input("Manual PDF path (admin)", value=st.session_state.get("manual_path_override", cur_guess))
                        if st.button("Apply path and load", key="btn_apply_path_top"):
                            if newp and os.path.isfile(newp):
                                st.session_state["manual_path_override"] = newp
                                st.session_state["current_manual_path"] = ""
                                _load_builtin_manual(force=True)
                                try:
                                    safe_rerun()
                                except Exception:
                                    pass
                            else:
                                st.error("Path is invalid or not a file.")
            st.stop()

        # Pending result is now consumed at the top of the script for deterministic handoff

    # Chat UI
        st.subheader("Chat")
        # Pre-widget mutations must happen here to avoid Streamlit API exceptions
        # Do not clear the ask box automatically; keep user's text visible across reruns
        st.session_state.setdefault("qa_input", st.session_state.get("pending_question", ""))

        # Toolbar removed (moved to Settings menu)

        # Chat window - ENTERPRISE UI: Native Streamlit chat messages
        st.markdown("### Conversation")
        
        # Chat history display - Native st.chat_message (Gemini-style, auto-scrolling)
        chat_container = st.container()
        with chat_container:
            for idx, item in enumerate(st.session_state.chat_history[-200:]):
                if isinstance(item, dict):
                    role = item.get("role", "assistant")
                    msg = item.get("content", "")
                else:
                    r0, msg = cast(Any, item)
                    role = "user" if str(r0).lower().startswith("you") else "assistant"
                
                # Use native st.chat_message (handles avatars and scrolling automatically)
                with st.chat_message(role):
                    st.markdown(msg, unsafe_allow_html=True)

            # Sticky ask bar below the transcript (native st.chat_input is sticky by default)
            # If no manual is loaded yet, guide the user to enable admin and load it
            if not (st.session_state.get("raw_pages") or []):
                st.info("Manual not loaded yet. Type 'nufc' and press Enter to enable admin mode, then use Settings → Manual to load or reload the manual.")
            
            # ENTERPRISE v1.1.0: Floating Action Bar (Gemini-style pills at bottom)
            # This container will be "teleported" to the bottom via CSS :has() selector
            with st.container():
                st.markdown('<div class="floating-bar-marker"></div>', unsafe_allow_html=True)
                floating_cols = st.columns([1, 1, 1, 1])
                with floating_cols[0]:
                    if st.button("🆕 New", key="new_chat_btn_float", help="Start new conversation"):
                        request_rating_then("new")
                with floating_cols[1]:
                    if st.button("🧹 Clear", key="clear_chat_btn_float", help="Clear all chat history"):
                        request_rating_then("clear")
                with floating_cols[2]:
                    if st.button("↻ Regen", key="regen_chat_btn_float", help="Regenerate last answer", disabled=not st.session_state.get("last_question")):
                        st.session_state._regen_inline = True
                        st.rerun()
                with floating_cols[3]:
                    mode = st.session_state.get("answer_mode", "Generative")
                    new_mode = "Exact" if mode == "Generative" else "Gen"
                    if st.button(f"🔄 {new_mode}", key="toggle_mode_btn_float", help="Toggle answer mode"):
                        st.session_state["answer_mode"] = "Exact Search" if mode == "Generative" else "Generative"
                        st.rerun()
            
            # Chat input only (no duplicate text input)
            q = st.chat_input("Ask the Planning Manual?", key="chat_question_input")
            if q and q.strip():
                st.session_state.last_query = q.strip()
                try:
                    log = logging.getLogger("pdbot")
                    try:
                        log.info("ASK %s", q)
                    except Exception:
                        pass
                    # Special admin command: 'nufc' toggles admin mode and reveals sidebar
                    if q.strip().lower() == "nufc":
                        st.session_state["is_admin"] = True
                        # Announce on next run and rerender entire script so sidebar content appears
                        st.session_state["ui_notice"] = ("info", "Welcome, Admin. Admin mode enabled.")
                        st.rerun()
                    else:
                        # Add user message to history first
                        st.session_state.chat_history.append({"role": "user", "content": q})
                        
                        # v2.0.8: Display user question immediately in chat
                        with st.chat_message("user"):
                            st.markdown(q)
                        
                        with st.spinner("Generating answer…"):
                            # Generate answer
                            answer_html, citations = generate_answer(q)
                        
                        # ENTERPRISE UI: Stream the response for live typing effect
                        with st.chat_message("assistant"):
                            # Check if answer is HTML (has tags), if so display without streaming
                            if "<div" in answer_html or "<br" in answer_html:
                                st.markdown(answer_html, unsafe_allow_html=True)
                            else:
                                # Stream plain text answers
                                st.write_stream(stream_response(answer_html))
                        
                        # Save to history
                        st.session_state.chat_history.append({"role": "assistant", "content": answer_html})
                        try:
                            items = load_chat_history() or []
                            items.append({"role": "user", "content": q})
                            items.append({"role": "assistant", "content": answer_html})
                            save_chat_history(items)
                        except Exception:
                            pass
                except Exception as e:
                    try:
                        write_crash(e)
                    except Exception:
                        pass
                    with st.chat_message("assistant"):
                        debug_enabled = os.getenv("PNDBOT_DEBUG", "").lower() == "true"
                        if debug_enabled:
                            import traceback
                            st.error(f"❌ **Error:** {str(e)}\n\n```\n{traceback.format_exc()}\n```")
                        else:
                            st.error(f"⚠️ Something went wrong: {str(e)}\n\nPlease try again or enable DEBUG mode for details.")

        # Intercept ask handled directly by input handler above

        # If a finalize signal exists, proceed to ask the chosen question
        # Initialize progress placeholders to satisfy type checkers even if exceptions occur early
        progress_box: Any = None
        progress_side_box: Any = None
        _upd = (lambda *args, **kwargs: None)
        if st.session_state.get("_finalize"):
            try:
                question = (st.session_state.pop("_finalize") or "").strip()
                this_req_id = st.session_state.get("active_request_id")
                start_time = time.time()
                # Progress UI (both in-chat and sidebar when visible)
                progress_box = st.empty()
                progress_side_box = st.sidebar.empty()
                def _make_bars():
                    try:
                        with progress_box.container():
                            pb = st.progress(0)
                            txt = st.caption("Preparing…")
                    except Exception:
                        pb, txt = None, None
                    try:
                        with progress_side_box.container():
                            pb_s = st.progress(0)
                            txt_s = st.caption("Preparing…")
                    except Exception:
                        pb_s, txt_s = None, None
                    return pb, txt, pb_s, txt_s
                _pb, _txt, _pbs, _txts = _make_bars()
                def _upd(p, msg):
                    try:
                        if _pb: _pb.progress(min(max(int(p),0),100))
                        if _txt: _txt.write(f"{msg}  •  {int(time.time()-start_time)}s")
                        if _pbs: _pbs.progress(min(max(int(p),0),100))
                        if _txts: _txts.write(f"{msg}  •  {int(time.time()-start_time)}s")
                    except Exception:
                        pass
                _upd(5, "Starting…")
                st.session_state.confirm_ui = False
                # keep it visible in the input box
                st.session_state.pending_question = question
                st.session_state.pop("edit_question", None)
                st.session_state["_clear_input"] = False
                _append_chat("user", question)
                st.session_state.last_question = question

                # Build context: use Qdrant if indexed, else fall back to raw_pages (pasted/built-in without index)
                hits = []
                context = ""
                use_qdrant = bool(st.session_state.get("indexed_ok") or int(st.session_state.get("last_index_count") or 0) > 0)
                mode = st.session_state.get("answer_mode", "Generative")
                is_exact = str(mode).lower().startswith("exact")
                # Mode-based top-k defaults
                eff_top_k = min(8, 3 if is_exact else int(top_k))
                # Retrieval knobs
                # Looser score threshold to allow more evidence and avoid empty first answers
                min_score = 0.15
                _upd(15, "Retrieval: searching…")
                if use_qdrant:
                    try:
                        if not _RAG_OK or search is None:  # type: ignore
                            raise RuntimeError(f"Retrieval not available: {_RAG_IMPORT_ERR}")
                        # Try extended signature first (mmr, lambda_mult, min_score)
                        try:
                            hits = search(
                                question,
                                top_k=eff_top_k,
                                qdrant_url=_qdrant_url(),
                                mmr=True,
                                lambda_mult=0.5,
                                min_score=min_score,
                            )  # type: ignore
                        except TypeError:
                            hits = search(question, top_k=eff_top_k, qdrant_url=_qdrant_url())  # type: ignore
                        # If top score looks weak, expand context once
                        try:
                            if hits:
                                top_score = float((hits[0].get("score") or 0.0))
                                if top_score < 0.80:
                                    expanded_k = min(eff_top_k + 3, 10)
                                    try:
                                        hits = search(
                                            question,
                                            top_k=expanded_k,
                                            qdrant_url=_qdrant_url(),
                                            mmr=True,
                                            lambda_mult=0.5,
                                            min_score=min_score,
                                        )  # type: ignore
                                    except TypeError:
                                        hits = search(question, top_k=expanded_k, qdrant_url=_qdrant_url())  # type: ignore
                        except Exception:
                            pass
                    except Exception as e:
                        hits = []
                        st.error(f"Search failed: {e}")
                    context = "\n\n".join([h.get("text", "") for h in hits])
                else:
                    pages = st.session_state.get("raw_pages") or []
                    if pages:
                        context = _truncate_text("\n\n".join(pages), max_chars=6000)
                # Fallback: if no vector hits but we have raw pages, try finding exact locations
                    _upd(45, "Retrieval: compiling evidence…")
                    # Respect cancel between stages
                    if st.session_state.get("cancel_requested") or (st.session_state.get("active_request_id") != this_req_id):
                        _upd(0, "Canceled")
                        st.session_state["busy"] = False
                        raise RuntimeError("request_canceled")
                if (not hits) and (st.session_state.get("raw_pages") or []):
                    try:
                        pages_full = st.session_state.get("raw_pages") or []
                        locs_fb = find_exact_locations(question, pages_full, max_results=max(5, top_k * 2))
                        if locs_fb:
                            hits = [{
                                "text": (it.get("sentence") or "").strip(),
                                "page": it.get("page"),
                                "score": None,
                                "source": RAG_COLLECTION,
                                "paragraph": it.get("paragraph"),
                                "line": it.get("line"),
                            } for it in locs_fb]
                    except Exception:
                        pass
                st.session_state.last_hits = hits
                st.session_state.last_context = context
                # Generative confidence warning when all scores are weak
                if (not is_exact) and use_qdrant:
                    try:
                        if hits and max([float(h.get("score") or 0.0) for h in hits]) < 0.65:
                            st.warning("⚠️ Insufficient data found in the document. Please rephrase or check the manual directly.")
                    except Exception:
                        pass
                # Evidence guardrails removed to restore earlier permissive behavior.
                # We'll still refuse when absolutely no context is available below.
                # Progress feedback to avoid double-submit
                with st.spinner("Generating answer… please wait"):
                    _upd(60, "Generating…")
                    if is_exact:
                        # Use exact locations from full pages when available; fallback to top hits
                        pages = st.session_state.get("raw_pages") or []
                        locs = find_exact_locations(question, pages, max_results=max(25, top_k * 5)) if pages else []
                        if locs:
                            # Normalize and deduplicate occurrences
                            norm = []
                            seen = set()
                            for it in locs:
                                pg = it.get('page')
                                try:
                                    if pg is not None:
                                        pg = int(pg)
                                        pg = pg if pg >= 1 else (pg + 1)
                                except Exception:
                                    pass
                                para = it.get('paragraph')
                                line = it.get('line')
                                sent = (it.get('sentence') or '').strip()
                                key = (pg, para, line, sent)
                                if key in seen:
                                    continue
                                seen.add(key)
                                norm.append({"page": pg, "paragraph": para, "line": line, "text": sent})
                            lines = [f"Pg {n.get('page','?')}, Para {n.get('paragraph','?')}, Line {n.get('line','?')}: \"{n.get('text','')}\"" for n in norm]
                            answer = "\n\n".join(lines)
                            # map to hits for supporting/citation panels
                            hits = [{
                                "text": n.get("text"),
                                "page": n.get("page"),
                                "score": None,
                                "source": RAG_COLLECTION,
                                "paragraph": n.get("paragraph"),
                                "line": n.get("line"),
                            } for n in norm]
                            # update session evidence to reflect exact results
                            st.session_state.last_hits = hits
                        else:
                            answer = "No grounded passages found. Please rephrase or narrow the scope."
                        generator = None
                    else:
                        # Generative mode: if no context, strictly not found
                        if not context.strip():
                            answer = "Not available in the provided document."
                            generator = None
                        else:
                            engine = st.session_state.engine
                            # Dynamic target: decide automatically based on question length and evidence richness
                            q_len = len(question.split())
                            # Encourage fuller answers to avoid short outputs
                            words_target = 300 if q_len <= 18 else 360
                            if eff_top_k >= 6 or len(hits) >= 5:
                                words_target = max(words_target, 380)
                            # Pass only raw context to the model; LocalModel injects its own system prompt
                            base = ""
                            # v2.0.5: Ollama only (removed pretrained mode)
                            generator = LocalModel(model_name=model_name, backend="ollama")
                            try:
                                probe = generator.ollama_status()
                                if not probe.get("alive"):
                                    st.error("Ollama is not reachable. Please start Ollama and ensure the model is pulled.")
                                    raise RuntimeError("ollama_not_available")
                            except Exception:
                                st.error("Ollama not available.")
                                raise
                            base = call_with_timeout(
                                generator.generate_response,
                                30,
                                question=question,
                                context=context,
                                max_new_tokens=int(max_tokens),
                                temperature=0.15,
                            ) or ""

                            # First-answer shortness guard: retry once with more tokens if answer too short and we have evidence
                            try:
                                if len((base or "").strip()) < 220 and len(hits) >= 3:
                                    base = call_with_timeout(
                                        generator.generate_response,
                                        30,
                                        question=question,
                                        context=context,
                                        max_new_tokens=int(max_tokens * 1.25),
                                        temperature=0.12,
                                    ) or base
                            except Exception:
                                pass

                            # Avoid echo/too-short answers by composing from evidence when needed
                            def _looks_like_echo(txt: str, q: str) -> bool:
                                t = (txt or "").strip().strip('"').strip()
                                qn = (q or "").strip().strip('"').strip()
                                return (t.lower() == qn.lower()) or (len(t.split()) <= 6 and qn.lower() in t.lower())

                            if (not base) or _looks_like_echo(base, question) or len(base.split()) < 12:
                                composed = compose_answer("Generative", hits, question, base_answer="", words_target=max(260, words_target))
                            else:
                                composed = compose_answer("Generative", hits, question, base_answer=base, words_target=words_target)

                            if len(composed) < 50:
                                if hits:
                                    composed = compose_answer("Generative", hits, question, base_answer="", words_target=300)
                                else:
                                    composed = "Not available in the provided document."
                            answer = composed
                        _upd(90, "Formatting answer…")

                # Render answer as a styled card (success/warn)
                # Drop stale or canceled results
                if st.session_state.get("cancel_requested") or (st.session_state.get("active_request_id") != this_req_id):
                    _upd(0, "Canceled")
                    progress_box.empty(); progress_side_box.empty()
                    st.session_state["busy"] = False
                    st.info("Request was canceled.")
                    st.stop()
                # Final answer guards (prevent UI crash on non-string values)
                if not isinstance(answer, str) or not str(answer).strip():
                    answer = "⚠️ No response returned. Please retry."
                _ans = (answer or "").strip()
                _ans_norm = normalize_markdown(_ans, enforce_bullets=True, max_line_len=110)
                _low = _ans.lower()
                # Build source block from hits
                src_lines = []
                _hits_for_src = st.session_state.get("last_hits") or []
                if _hits_for_src:
                    # Use up to 5 citations with page/para/line when available
                    for h in _hits_for_src[:5]:
                        pg = h.get("page")
                        # Skip unknown pages to avoid 'Page None'
                        if pg is None or (isinstance(pg, str) and not pg.isdigit()):
                            continue
                        para = h.get("paragraph")
                        line = h.get("line")
                        if para is not None or line is not None:
                            src_lines.append(f"Page {pg} – Paragraph {para if para is not None else '?'} – Line {line if line is not None else '?'}")
                        else:
                            src_lines.append(f"Page {pg}")
                # Only append Source block for Exact mode (Generative answers carry their own Sources)
                src_block = ("<br/><br/>📘 <strong>Source:</strong><br/>" + "<br/>".join(src_lines)) if (src_lines and is_exact) else ""
                if _low.startswith("not in the manual") or _low.startswith("no grounded"):
                    rendered_ans = f"<div class='card warn'>⚠️ <strong>Answer:</strong><br/>{_ans_norm}{src_block}</div>"
                else:
                    rendered_ans = f"<div class='card success'>✅ <strong>Answer:</strong><br/>{_ans_norm}{src_block}</div>"
                # Defer display to outside this block to avoid fragment rerun race; store pending result
                st.session_state["__pending_result"] = {"id": this_req_id, "rendered": rendered_ans}
                # Proactively clear progress, then trigger a fresh render to show the answer
                try:
                    progress_box.empty(); progress_side_box.empty()
                except Exception:
                    pass
                try:
                    safe_rerun()
                except Exception:
                    pass
                # Show per-answer collapsible context and details below input on the next render
                effective_backend = "ollama" if st.session_state.engine == "LLM (Ollama)" else "pretrained"
                # generator may not exist when we short-circuit on empty context
                try:
                    model_used = getattr(generator, "model_name", model_name)  # type: ignore[name-defined]
                except Exception:
                    model_used = model_name
                st.session_state.last_meta = {
                    "backend": effective_backend,
                    "model": model_used,
                    "max_new_tokens": max_tokens,
                    "top_k": top_k,
                    "exact_mode": bool(is_exact),
                    "temperature": temperature,
                }

                # Keep suggestions disabled
                st.session_state.suggestions = []
                # Do not trigger rating dialog after each answer; only on New/Clear
                st.session_state["last_mode"] = mode
            except Exception as _e_any:
                # Ensure UI never stays disabled
                st.session_state["busy"] = False
                st.session_state.pop("_finalize", None)
                logging.exception("Error generating answer")
                st.error(f"⚠️ Something went wrong while generating the answer: {_e_any}")
                try:
                    _append_chat("assistant", "<div class='card warn'>⚠️ <strong>Answer:</strong><br/>Sorry, something went wrong. Please try again.</div>")
                except Exception:
                    pass
                # Always clear progress bars on error to avoid stuck UI state
                try:
                    progress_box.empty()
                except Exception:
                    pass
                try:
                    progress_side_box.empty()
                except Exception:
                    pass
                # Clear active request id on error
                st.session_state["active_request_id"] = None
            finally:
                # Hard-stop safety: if a run exits this block without clearing progress, do it now
                try:
                    if '_pb' in locals():
                        _upd(100, "Done")
                except Exception:
                    pass
                try:
                    progress_box.empty()
                except Exception:
                    pass
                try:
                    progress_side_box.empty()
                except Exception:
                    pass


    # Supporting sections (not nested inside Chat expander to avoid Streamlit limitation)

    # Supporting quotes (optional)
    if st.session_state.get("last_hits") is not None:
        with st.expander("Supporting quotes (optional)", expanded=False):
            hits = st.session_state.get("last_hits") or []
            if not hits:
                st.write("No supporting quotes.")
            else:
                for i, h in enumerate(hits[:10], start=1):
                    st.markdown(
                        f"**{i}.** [p.{h.get('page','?')}, para {h.get('paragraph','?')}, ln {h.get('line','?')}] \"{h.get('text','')}\""
                    )

    # Citations
    if st.session_state.get("last_hits") is not None:
        with st.expander("Citations", expanded=False):
            hits = st.session_state.get("last_hits") or []
            if not hits:
                st.write("No citations available.")
            else:
                # Group by page and list paragraph/line pairs
                by_page = {}
                for h in hits:
                    p = h.get("page", "?")
                    pl = (h.get("paragraph"), h.get("line"))
                    by_page.setdefault(p, set()).add(pl)
                for p in sorted(by_page, key=lambda x: (isinstance(x, int), x)):
                    details = ", ".join([f"para {a if a is not None else '?'} / line {b if b is not None else '?'}" for a, b in sorted(by_page[p])])
                    st.markdown(f"- Page {p}: {details if details else '(no paragraph/line metadata)'}")

    # Auto-scroll chat to bottom after render
    st.markdown(
                """
                <script>
                (function(){
                    const scrollBottom = () => {
                        const el = document.getElementById('chat-scroll');
                        if (el) { el.scrollTop = el.scrollHeight; }
                        const end = document.getElementById('chat-end');
                        if (end && end.scrollIntoView) { end.scrollIntoView({behavior:'instant', block:'end'}); }
                    };
                    if (window.requestAnimationFrame) requestAnimationFrame(scrollBottom);
                    setTimeout(scrollBottom, 60);
                    setTimeout(scrollBottom, 200);
                })();
                </script>
                """,
                unsafe_allow_html=True,
    )

    # Removed Answer details for cleaner layout

    # Handle inline regenerate after layout so the scroll stays at the latest answer
    if st.session_state.pop("_regen_inline", False):
        last_q = st.session_state.get("last_question", "")
        if last_q:
            # Remove last assistant answer if present so regen replaces it visually
            if st.session_state.chat_history:
                last_item = st.session_state.chat_history[-1]
                is_bot = (last_item.get("role") == "assistant") if isinstance(last_item, dict) else (not str(last_item[0]).lower().startswith("you"))
                if is_bot:
                    st.session_state.chat_history.pop()

            mode = st.session_state.get("answer_mode", "Generative")
            is_exact = str(mode).lower().startswith("exact")
            if is_exact:
                # Re-run exact search (database/page scan), not generation
                pages = st.session_state.get("raw_pages") or []
                locs = find_exact_locations(last_q, pages, max_results=40) if pages else []
                if locs:
                    norm = []
                    seen = set()
                    for it in locs:
                        pg = it.get('page')
                        try:
                            if pg is not None:
                                pg = int(pg)
                                pg = pg if pg >= 1 else (pg + 1)
                        except Exception:
                            pass
                        para = it.get('paragraph')
                        line = it.get('line')
                        sent = (it.get('sentence') or '').strip()
                        key = (pg, para, line, sent)
                        if key in seen:
                            continue
                        seen.add(key)
                        norm.append({"page": pg, "paragraph": para, "line": line, "text": sent})
                    lines = [f"Pg {n.get('page','?')}, Para {n.get('paragraph','?')}, Line {n.get('line','?')}: \"{n.get('text','')}\"" for n in norm]
                    answer = "\n\n".join(lines)
                    # Update evidence for panels
                    st.session_state.last_hits = [{
                        "text": n.get("text"),
                        "page": n.get("page"),
                        "score": None,
                        "source": RAG_COLLECTION,
                        "paragraph": n.get("paragraph"),
                        "line": n.get("line"),
                    } for n in norm]
                else:
                    answer = "No exact matches found. Try rephrasing."
                _ans = normalize_markdown(answer, enforce_bullets=False, max_line_len=110)
                rendered_ans = f"<div class='card success'>✅ <strong>Answer:</strong><br/>{_ans}</div>"
                st.session_state.chat_history.append({"role": "assistant", "content": rendered_ans})
            else:
                # Generative regen: run the new pipeline
                try:
                    composed = generate_answer_generative(last_q)
                except Exception:
                    composed = "Not available in the provided document."
                _ans = normalize_markdown(composed, enforce_bullets=True, max_line_len=110)
                rendered_ans = f"<div class='card success'>✅ <strong>Answer:</strong><br/>{_ans}</div>"
                st.session_state.chat_history.append({"role": "assistant", "content": rendered_ans})
            try:
                safe_rerun()
            except Exception:
                pass

with tab_help:
    st.markdown(
        """
        ### How to use
        - Answer modes:
            - Generative: grounded answer with [n] citations and a Sources block.
            - Exact Search: quoted lines/sentences with page references (Pg/Para/Line when available).
        - Chat: type your question and press Enter (or click Ask).
        - Regenerate: re-create the last answer using the current settings.
        - Supporting quotes and Citations: expand these panels to see the evidence and page numbers.
        """
    )

# Footer user badge removed: do not personalize UI with the name
