"""
Sidebar UI Component
Handles all sidebar controls: manual loading, settings, model configuration.
"""
import streamlit as st
import os


# Manual path configuration
MANUAL_ABSOLUTE_PATH = r"D:\\PLANNING WORK\\Manual-for-Development-Project-2024.pdf"


def _default_manual_path() -> str:
    """Return the fixed manual path used by the app."""
    return MANUAL_ABSOLUTE_PATH


def _qdrant_url() -> str:
    """Get Qdrant URL from environment or default."""
    return os.getenv("QDRANT_URL", "http://localhost:6333")


def load_builtin_manual(force: bool = False):
    """Load the built-in manual pages and index into Qdrant when available.
    
    Args:
        force: Force reload even if already loaded
    """
    # Try to import RAG function (may fail if dependencies missing)
    try:
        from src.rag_langchain import ingest_pdf_sentence_level
        rag_available = True
    except Exception as e:
        ingest_pdf_sentence_level = None
        rag_available = False
        import logging
        logging.warning(f"RAG indexing not available: {e}")
    
    # Import PyPDF loader
    try:
        from pypdf import PdfReader
        
        class PyPDFLoader:
            def __init__(self, file_path: str):
                self.file_path = file_path
            def load(self):
                reader = PdfReader(self.file_path)
                docs = []
                for i, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    docs.append(type('Doc', (), {'page_content': text, 'metadata': {'page': i+1}})())
                return docs
    except ImportError:
        st.error("pypdf not available. Cannot load manual.")
        return
    
    manual_path = _default_manual_path()
    if not os.path.isfile(manual_path):
        st.warning(f"Built-in manual not found: {manual_path}")
        return
    
    # Skip rework if same manual already loaded and not forced
    same_manual = st.session_state.get("current_manual_path") == manual_path
    already_have_pages = bool(st.session_state.get("raw_pages"))
    already_indexed = bool(int(st.session_state.get("last_index_count") or 0) > 0)
    
    if not force and same_manual and (already_have_pages or already_indexed):
        return
    
    # Load raw pages for Exact mode
    pages_loaded = False
    try:
        loader = PyPDFLoader(manual_path)
        with st.spinner("Reading pages…"):
            docs = loader.load()
        st.session_state["raw_pages"] = [getattr(d, "page_content", "") for d in docs]
        st.session_state["raw_page_count"] = len(docs)
        pages_loaded = True
    except Exception as e:
        st.warning(f"Unable to read PDF pages: {e}")
        st.session_state["raw_pages"] = []
        st.session_state["raw_page_count"] = None
    
    # Update file metadata
    st.session_state["current_manual_path"] = manual_path
    st.session_state["source_file"] = os.path.basename(manual_path)
    
    # Index into Qdrant
    n_indexed = 0
    if rag_available and ingest_pdf_sentence_level is not None:
        try:
            with st.spinner("Indexing built-in manual…"):
                n_indexed = ingest_pdf_sentence_level(manual_path, qdrant_url=_qdrant_url())
            st.session_state["indexed_ok"] = n_indexed > 0
            st.session_state["last_index_count"] = n_indexed
            st.session_state["builtin_indexed"] = n_indexed > 0
        except Exception as e:
            st.error(f"Failed to index into Qdrant: {e}")
            st.session_state["indexed_ok"] = False
            st.session_state["last_index_count"] = 0
            st.session_state["builtin_indexed"] = False
    else:
        st.session_state["indexed_ok"] = False
        st.session_state["last_index_count"] = 0
        st.session_state["builtin_indexed"] = False
    
    # Status message
    src_name = os.path.basename(manual_path)
    if pages_loaded and n_indexed > 0:
        st.success(f"Loaded: {src_name} • Pages: {st.session_state.get('raw_page_count')} • Indexed {n_indexed} chunks.")
    elif pages_loaded:
        st.success(f"Loaded pages: {src_name} • Pages: {st.session_state.get('raw_page_count')}. Indexing not available.")
    else:
        st.error("Manual could not be read.")


def render_sidebar():
    """Render the complete sidebar UI."""
    from src.utils.persist import clear_chat_history
    
    with st.sidebar:
        # ==== Manual Section ====
        with st.expander("Manual", expanded=True):
            st.caption("The app auto-loads the fixed manual once and reuses it.")
            st.text(f"Path: {_default_manual_path()}")
            if st.button("Reload manual", help="Force reload and re-index the manual"):
                load_builtin_manual(force=True)
            # Auto-load on first run
            load_builtin_manual(force=False)
        
        # ==== Settings Section ====
        with st.expander("Settings", expanded=False):
            st.markdown("**Chat Controls**")
            
            # New Chat button
            st.markdown(
                '<a href="./?ask_name=1" target="_blank" class="stButton"><button>New Chat ↗</button></a>',
                unsafe_allow_html=True,
            )
            
            # Clear Chat button
            if st.button("Clear Chat"):
                try:
                    clear_chat_history()
                    st.session_state["chat_history"] = []
                    st.session_state["is_admin"] = False
                    st.success("Cleared this session's local history.")
                except Exception:
                    st.warning("Unable to clear saved history.")
            
            # Status line
            src = st.session_state.get("source_file") or os.path.basename(_default_manual_path())
            n = int(st.session_state.get("last_index_count") or 0)
            pg = st.session_state.get("raw_page_count")
            st.markdown(f"Current file: `{src}` • Pages: {pg if pg is not None else '?'} • Chunks: {n}")
        
        # ==== Admin Options ====
        if st.session_state.get("is_admin", False):
            with st.expander("Options", expanded=True):
                # Pretrained mode toggle
                use_pretrained = st.toggle(
                    "Pretrained mode",
                    value=(st.session_state.engine == "Pretrained (local)"),
                    help="Turn ON to use a small built-in model (Qwen). Turn OFF to use Ollama."
                )
                st.session_state.engine = "Pretrained (local)" if use_pretrained else "LLM (Ollama)"
                
                # Set default entrypoint for pretrained
                if use_pretrained and not st.session_state.get("pretrained_entry"):
                    st.session_state.pretrained_entry = "src.models.qwen_pretrained:predict"
                
                # Model settings
                if st.session_state.engine == "LLM (Ollama)":
                    model_name = st.text_input("Ollama model", value=os.getenv("OLLAMA_MODEL", "tinyllama"))
                else:
                    model_name = st.text_input(
                        "Ollama model (for reference)",
                        value=os.getenv("OLLAMA_MODEL", "tinyllama"),
                        help="Not used in Pretrained mode"
                    )
                
                # RAG parameters
                top_k = st.slider("Top-K context chunks", 1, 20, 10)
                max_tokens = st.slider("Max new tokens", 64, 2000, 1200, step=64)
                temperature = st.slider("Creativity (temperature)", 0.0, 1.5, 0.2, step=0.1)
                
                # Apply/Reset callbacks
                def cb_apply():
                    st.session_state["manual_action"] = "apply"
                def cb_reset():
                    st.session_state["manual_action"] = "reset"
                
                cc1, cc2 = st.columns(2)
                with cc1:
                    st.button("Apply", key="__apply", on_click=cb_apply)
                with cc2:
                    st.button("Reset", key="__reset", on_click=cb_reset)
            
            # Handle settings actions
            action = st.session_state.get("manual_action")
            if action == "apply":
                st.success("Settings applied.")
                st.session_state["manual_action"] = None
            elif action == "reset":
                st.info("Settings reset.")
                st.session_state["manual_action"] = None
            
            # ==== Branding Section ====
            with st.expander("Branding (admin)", expanded=False):
                up = st.file_uploader("Upload logo (PNG/JPG/SVG)", type=["png","jpg","jpeg","svg"], accept_multiple_files=False)
                
                col_ba, col_bb = st.columns([1,1])
                with col_ba:
                    if up is not None:
                        try:
                            this_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                            assets_dir = os.path.join(this_dir, "assets")
                            os.makedirs(assets_dir, exist_ok=True)
                            
                            import pathlib
                            ext = pathlib.Path(up.name).suffix.lower() or ".png"
                            if ext not in (".png", ".jpg", ".jpeg", ".svg"):
                                ext = ".png"
                            
                            save_path = os.path.join(assets_dir, f"branding_logo{ext}")
                            with open(save_path, "wb") as f:
                                f.write(up.getbuffer())
                            
                            # Save to config
                            root = os.path.dirname(os.path.dirname(this_dir))
                            cfg_dir = os.path.join(root, "config")
                            os.makedirs(cfg_dir, exist_ok=True)
                            with open(os.path.join(cfg_dir, "brand_logo_path.txt"), "w", encoding="utf-8") as f:
                                f.write(save_path)
                            
                            st.session_state["brand_logo_path_override"] = save_path
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to save logo: {e}")
                
                with col_bb:
                    manual_logo = st.text_input(
                        "Or set logo path",
                        value=st.session_state.get("brand_logo_path_override", ""),
                        placeholder="C:/path/to/logo.png"
                    )
                    if st.button("Apply logo path"):
                        if manual_logo and os.path.isfile(manual_logo):
                            try:
                                this_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                                root = os.path.dirname(os.path.dirname(this_dir))
                                cfg_dir = os.path.join(root, "config")
                                os.makedirs(cfg_dir, exist_ok=True)
                                with open(os.path.join(cfg_dir, "brand_logo_path.txt"), "w", encoding="utf-8") as f:
                                    f.write(manual_logo)
                                st.session_state["brand_logo_path_override"] = manual_logo
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to save logo path: {e}")
                        else:
                            st.warning("Please enter a valid file path to an image.")
        else:
            st.sidebar.info("Admin controls are hidden.")
