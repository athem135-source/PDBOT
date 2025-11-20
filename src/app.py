"""
PDBot - Modular Application Entry Point (v0.9.0)
Clean orchestration of all modular components
"""
import os
import sys
import warnings

# Suppress TensorFlow/Keras warnings early
warnings.filterwarnings("ignore", category=Warning)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

import streamlit as st

# Import modular components
from src.logic.state_manager import init_session_state, check_pending_rerun
from src.ui.layout import setup_page_config, inject_theme, auto_scroll_chat
from src.ui.sidebar import render_sidebar
from src.ui.chat_interface import (
    render_chat_history, 
    render_supporting_quotes, 
    render_citations,
    render_chat_input,
    inject_chat_styles
)

# Import utilities
from src.utils.persist import load_chat_history, save_chat_history

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    
    # 1. Setup page configuration
    setup_page_config()
    
    # 2. Initialize session state
    init_session_state()
    
    # 3. Load chat history
    try:
        history = load_chat_history()
        if history and not st.session_state.get("chat_history"):
            st.session_state["chat_history"] = history
    except Exception:
        pass
    
    # 4. Check for pending reruns
    check_pending_rerun()
    
    # 5. Inject theme CSS
    inject_theme()
    
    # 6. Create main tabs
    tab_chat, tab_help = st.tabs(["❓ Ask Questions", "📘 Instructions"])
    
    with tab_chat:
        # 8. Render sidebar (manual, settings, admin options)
        render_sidebar()
        
        # 9. Chat section
        with st.expander("💬 Chat", expanded=True):
            # Inject chat styles
            inject_chat_styles()
            
            # Render chat history
            render_chat_history()
            
            # Render chat input
            render_chat_input()
        
        # 10. Supporting sections (outside main chat to avoid nesting issues)
        render_supporting_quotes()
        render_citations()
        
        # 11. Auto-scroll to bottom
        auto_scroll_chat()
    
    with tab_help:
        st.markdown("""
        ### How to Use PDBot
        
        **1. Load the Manual**
        - The manual auto-loads on startup
        - Use the sidebar "Manual" section to reload if needed
        
        **2. Choose Answer Mode**
        - **Generative Mode**: AI-generated comprehensive answers (200-300 words)
        - **Exact Search Mode**: Fast keyword-based retrieval with highlighted matches
        
        **3. Ask Questions**
        - Type your question in the input box
        - Press Enter or click "Send"
        - View the answer with citations
        
        **4. View Source (v0.9.0)**
        - Click "📄 View Source Pages" to see actual PDF pages cited
        - High-quality rendering at 2x zoom (150 DPI)
        - Shows up to 5 most relevant pages
        
        **5. Review Evidence**
        - "Supporting Passages" shows retrieved context
        - "Citations" shows page numbers and sources
        - Use "Regenerate" for alternative wording
        
        **6. Provide Feedback**
        - Rate answers with ⭐ stars (1-5)
        - Add optional comments
        - Feedback is saved for analysis
        
        ### Admin Features
        
        Type `nufc` to enable admin mode:
        - Change LLM backend (Ollama / Pretrained)
        - Adjust RAG parameters (top-k, temperature, max tokens)
        - Upload custom branding logo
        - View backend status
        
        ### Troubleshooting
        
        - **Manual not loading?** Check the path in Settings → Manual
        - **Slow responses?** Reduce max_tokens in admin options
        - **No citations?** Manual may not be indexed - reload it
        - **Empty answers?** Try rephrasing your question with keywords
        """)


if __name__ == "__main__":
    main()
