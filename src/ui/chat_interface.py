"""
Chat Interface Component
Handles chat display, message rendering, and PDF source viewing.
"""
import streamlit as st
import os
from typing import Any, Optional


def render_chat_history():
    """Render the chat message history with View Source feature."""
    from src.logic.state_manager import iter_chat
    from src.utils.pdf_renderer import get_page_image, is_pdf_renderer_available
    
    st.markdown("<div id='chat-scroll' class='chat-scroll'>", unsafe_allow_html=True)
    
    last_bot_index = None
    chat_items = list(st.session_state.chat_history[-200:])
    
    for idx, item in enumerate(chat_items):
        # Parse message format
        if isinstance(item, dict):
            role = item.get("role", "assistant")
            msg = item.get("content", "")
        else:
            r0, msg = item
            role = "user" if str(r0).lower().startswith("you") else "assistant"
        
        is_user = (role == "user")
        icon = "🧑" if is_user else "🤖"
        label = "You" if is_user else "PDBOT"
        klass = "chat-user" if is_user else "chat-bot"
        
        # Render message card
        st.markdown(
            f"<div class='{klass}'>"
            f"  <div class='chat-header'><span class='chat-icon'>{icon}</span><strong>{label}</strong></div>"
            f"  <div class='chat-body'>{msg}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        
        # Add View Source feature for assistant messages
        if not is_user:
            last_bot_index = idx
            _render_view_source_expander()
    
    # Regenerate button for last bot message
    if last_bot_index is not None and st.session_state.get("last_question"):
        if st.button("↻ Regenerate", key="regen_inline", help="Recreate the last answer using current settings"):
            st.session_state._regen_inline = True
    
    st.markdown("<div id='chat-end'></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_view_source_expander():
    """Render View Source expander for the current message if citations exist."""
    from src.utils.pdf_renderer import get_page_image, is_pdf_renderer_available
    
    hits = st.session_state.get("last_hits", [])
    if not hits:
        return
    
    # Check if PDF renderer is available
    if not is_pdf_renderer_available():
        return
    
    # Get PDF path
    pdf_path = st.session_state.get("current_manual_path", "")
    if not pdf_path or not os.path.isfile(pdf_path):
        return
    
    # Extract unique pages from citations
    pages_cited = set()
    for h in hits[:10]:  # Limit to first 10 citations
        pg = h.get("page")
        if pg is not None:
            try:
                pages_cited.add(int(pg))
            except (ValueError, TypeError):
                pass
    
    if not pages_cited:
        return
    
    # Render expander with PDF pages
    pages_sorted = sorted(pages_cited)
    pages_str = ", ".join([str(p) for p in pages_sorted[:5]])  # Show first 5 page numbers
    if len(pages_sorted) > 5:
        pages_str += f" (+{len(pages_sorted) - 5} more)"
    
    with st.expander(f"📄 View Source Pages ({pages_str})", expanded=False):
        for page_num in pages_sorted[:5]:  # Render up to 5 pages
            st.markdown(f"**Page {page_num}**")
            
            try:
                img = get_page_image(pdf_path, page_num, zoom=2.0, dpi=150)
                if img:
                    st.image(img, caption=f"Page {page_num}", use_column_width=True)
                else:
                    st.warning(f"Unable to render page {page_num}")
            except Exception as e:
                st.error(f"Error rendering page {page_num}: {e}")
            
            # Add spacing between pages
            if page_num != pages_sorted[:5][-1]:
                st.markdown("---")


def render_supporting_quotes():
    """Render the supporting quotes expander."""
    if st.session_state.get("last_hits") is None:
        return
    
    with st.expander("Supporting quotes (optional)", expanded=False):
        hits = st.session_state.get("last_hits") or []
        if not hits:
            st.write("No supporting quotes.")
        else:
            for i, h in enumerate(hits[:10], start=1):
                pg = h.get('page', '?')
                para = h.get('paragraph', '?')
                ln = h.get('line', '?')
                text = h.get('text', '')
                st.markdown(f"**{i}.** [p.{pg}, para {para}, ln {ln}] \"{text}\"")


def render_citations():
    """Render the citations expander."""
    if st.session_state.get("last_hits") is None:
        return
    
    with st.expander("Citations", expanded=False):
        hits = st.session_state.get("last_hits") or []
        if not hits:
            st.write("No citations available.")
        else:
            # Group by page
            by_page = {}
            for h in hits:
                p = h.get("page", "?")
                pl = (h.get("paragraph"), h.get("line"))
                by_page.setdefault(p, set()).add(pl)
            
            for p in sorted(by_page, key=lambda x: (isinstance(x, int), x)):
                details = ", ".join([
                    f"para {a if a is not None else '?'} / line {b if b is not None else '?'}"
                    for a, b in sorted(by_page[p])
                ])
                st.markdown(f"- Page {p}: {details if details else '(no paragraph/line metadata)'}")


def render_chat_input():
    """Render the user input area with answer mode selector."""
    st.subheader("Ask a question")
    
    # Answer mode selector
    st.radio("Answer mode", ["Generative", "Exact Search"], key="answer_mode", horizontal=True)
    
    # Guide for unloaded manual
    if not (st.session_state.get("raw_pages") or []):
        st.info("Manual not loaded yet. Type 'nufc' and press Enter to enable admin mode, then use Settings → Manual to load or reload the manual.")
    
    # Chat input
    q = st.chat_input("Ask the Planning Manual…", key="chat_question_input")
    
    if q and q.strip():
        _handle_user_question(q.strip())


def _handle_user_question(question: str):
    """Process user question and generate answer."""
    import logging
    
    try:
        log = logging.getLogger("pdbot")
        try:
            log.info("ASK %s", question)
        except Exception:
            pass
        
        # Special admin command
        if question.lower() == "nufc":
            st.session_state["is_admin"] = True
            st.session_state["ui_notice"] = ("info", "Welcome, Admin. Admin mode enabled.")
            st.rerun()
            return
        
        # Generate answer
        with st.spinner("Generating answer…"):
            from src.app import generate_answer  # Import from main app for now
            answer_html, citations = generate_answer(question)
        
        # Display answer
        with st.chat_message("assistant"):
            st.markdown(answer_html, unsafe_allow_html=True)
        
        # Save to history
        from src.utils.persist import save_chat_history
        from src.logic.state_manager import append_chat
        
        append_chat("user", question)
        append_chat("assistant", answer_html)
        
        try:
            save_chat_history(st.session_state.chat_history)
        except Exception:
            pass
        
    except Exception as e:
        try:
            from src.app import write_crash
            write_crash(e)
        except Exception:
            pass
        
        with st.chat_message("assistant"):
            st.error("Something went wrong while generating the answer. Please try again.")


def inject_chat_styles():
    """Inject CSS styles for chat interface."""
    st.markdown(
        """
        <style>
        .chat-scroll {
            max-height: 60vh;
            overflow-y: auto;
            padding: 0 4px;
            margin-bottom: 1rem;
        }
        .chat-user, .chat-bot {
            margin-bottom: 1rem;
            padding: 0.75rem;
            border-radius: 8px;
        }
        .chat-user {
            background-color: rgba(28, 131, 225, 0.1);
            border-left: 4px solid #1c83e1;
        }
        .chat-bot {
            background-color: rgba(76, 175, 80, 0.1);
            border-left: 4px solid #4caf50;
        }
        .chat-header {
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .chat-icon {
            font-size: 1.2rem;
        }
        .chat-body {
            line-height: 1.6;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def auto_scroll_chat():
    """Inject JavaScript to auto-scroll chat to bottom."""
    st.markdown(
        """
        <script>
        (function(){
            const scrollBottom = () => {
                const el = document.getElementById('chat-scroll');
                if (el) { el.scrollTop = el.scrollHeight; }
                const end = document.getElementById('chat-end');
                if (end && end.scrollIntoView) {
                    end.scrollIntoView({behavior:'instant', block:'end'});
                }
            };
            if (window.requestAnimationFrame) requestAnimationFrame(scrollBottom);
            setTimeout(scrollBottom, 60);
            setTimeout(scrollBottom, 200);
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )
