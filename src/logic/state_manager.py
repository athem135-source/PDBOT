"""
Session State Manager
Centralizes all st.session_state initialization and management.
"""
import streamlit as st


def init_session_state():
    """Initialize all session state variables with defaults.
    
    Call this once at app startup before any UI rendering.
    """
    ss = st.session_state
    
    # User identity
    ss.setdefault("user_name", None)
    ss.setdefault("username", "")
    ss.setdefault("is_admin", False)
    ss.setdefault("login_ok", False)
    
    # Chat history (list of dicts: {role: 'user'|'assistant', content: str})
    ss.setdefault("chat_history", [])
    ss.setdefault("messages", [])
    
    # Request lifecycle
    ss.setdefault("req_id", 0)
    ss.setdefault("loading", False)
    ss.setdefault("busy", False)
    ss.setdefault("qa_stage", "idle")
    ss.setdefault("busy_since", 0.0)
    ss.setdefault("request_counter", 0)
    ss.setdefault("active_request_id", None)
    ss.setdefault("cancel_requested", False)
    
    # Modals/dialogs
    ss.setdefault("show_name_modal", False)
    ss.setdefault("show_rating_modal", False)
    ss.setdefault("post_rating_action", None)  # 'new' | 'clear' | None
    ss.setdefault("pending_question", "")
    
    # Answer mode
    ss.setdefault("answer_mode", "Generative")
    
    # Manual/document state
    ss.setdefault("raw_pages", [])
    ss.setdefault("raw_page_count", None)
    ss.setdefault("current_manual_path", "")
    ss.setdefault("source_file", "")
    ss.setdefault("last_index_count", 0)
    ss.setdefault("indexed_ok", False)
    ss.setdefault("builtin_indexed", False)
    ss.setdefault("manual_load_error", None)
    
    # Model/engine settings
    ss.setdefault("engine", "LLM (Ollama)")
    ss.setdefault("pretrained_entry", "")
    ss.setdefault("pretrained_path", "")
    
    # RAG/retrieval state
    ss.setdefault("last_hits", None)
    ss.setdefault("last_context", "")
    ss.setdefault("last_question", "")
    ss.setdefault("last_meta", {})
    ss.setdefault("last_mode", "")
    ss.setdefault("suggestions", [])
    
    # Theme
    ss.setdefault("_use_new_theme", False)
    ss.setdefault("_force_dark", False)
    
    # Misc
    ss.setdefault("app_exit", False)
    ss.setdefault("_pending_rerun", False)
    ss.setdefault("_last_rerun_ts", 0)


def append_chat(role: str, content: str):
    """Append a message to chat history.
    
    Args:
        role: 'user' or 'assistant'
        content: Message content (HTML or plain text)
    """
    try:
        text = content if isinstance(content, str) else str(content)
        if not text.strip():
            text = "⚠️ No response returned. Please retry."
        st.session_state.chat_history.append({"role": role, "content": text})
    except Exception:
        st.session_state.chat_history.append({"role": role, "content": str(content)})


def append_chat_dedup_assistant(content: str):
    """Append assistant content unless the last assistant message is identical.
    
    Prevents duplicate bot cards from rapid double submissions or stale returns.
    
    Args:
        content: Message content to append
    """
    try:
        hist = st.session_state.get("chat_history") or []
        if hist:
            last = hist[-1]
            last_role = last.get("role") if isinstance(last, dict) else (
                "assistant" if not str(last[0]).lower().startswith("you") else "user"
            )
            last_content = last.get("content") if isinstance(last, dict) else last[1]
            if last_role == "assistant" and str(last_content).strip() == str(content).strip():
                return
    except Exception:
        pass
    append_chat("assistant", content)


def iter_chat():
    """Iterator over chat history with normalized format.
    
    Yields:
        Tuples of (role, content) where role is 'user' or 'assistant'
    """
    for item in st.session_state.get("chat_history", []):
        if isinstance(item, dict):
            yield item.get("role", "assistant"), item.get("content", "")
        else:
            # Fallback from legacy tuple format
            try:
                role, msg = item
                # Normalize legacy labels
                role = "user" if str(role).lower().startswith("you") else "assistant"
                yield role, msg
            except Exception:
                yield "assistant", str(item)


def safe_rerun(throttle_ms: int = 300):
    """Safely trigger a Streamlit rerun with throttling.
    
    Args:
        throttle_ms: Minimum milliseconds between reruns
    """
    import time
    now = time.time() * 1000
    last = float(st.session_state.get("_last_rerun_ts") or 0)
    
    if now - last < throttle_ms:
        st.session_state["_pending_rerun"] = True
        return
        
    st.session_state["_last_rerun_ts"] = now
    
    try:
        if hasattr(st, "rerun"):
            st.rerun()
        else:
            st.experimental_rerun()  # type: ignore
    except Exception:
        st.session_state["_pending_rerun"] = True


def check_pending_rerun():
    """Check and execute any pending reruns. Call after state initialization."""
    if st.session_state.pop("_pending_rerun", False):
        try:
            if hasattr(st, "rerun"):
                st.rerun()
            else:
                st.experimental_rerun()  # type: ignore
        except Exception:
            pass
