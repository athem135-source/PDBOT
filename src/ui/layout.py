"""
UI Layout Manager
Handles page configuration, CSS injection, and header/footer rendering.
"""
import streamlit as st
import os
import base64


# Theme CSS definitions
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
div.stChatMessage, .stChatMessage { background:#F6F8FC !important; color:#0B0F14 !important; border:1px solid #D8E2F0 !important; border-radius:12px !important; }
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
"""


def setup_page_config():
    """Configure Streamlit page settings. Call once at app startup."""
    st.set_page_config(
        page_title="PDBOT",
        page_icon=":robot_face:",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    # Render brand header immediately after page config
    render_brand_header()


def inject_theme():
    """Inject custom CSS theme based on session state."""
    css = _THEME_DARK if st.session_state.get("_force_dark") else _THEME_LIGHT
    
    if st.session_state.get("_use_new_theme", False):
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def _find_logo_path() -> str | None:
    """Find the brand logo path from various sources.
    
    Priority:
    1. Session state override
    2. Config file
    3. Default assets location
    
    Returns:
        Path to logo file or None
    """
    # Check session state override
    override = st.session_state.get("brand_logo_path_override")
    if override and os.path.isfile(override):
        return override
        
    # Check config file
    try:
        this_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        root = os.path.dirname(this_dir)
        cfg_path = os.path.join(root, "config", "brand_logo_path.txt")
        
        if os.path.isfile(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                path = f.read().strip()
                if path and os.path.isfile(path):
                    return path
    except Exception:
        pass
        
    # Check default assets
    try:
        this_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(this_dir, "assets")
        
        for ext in ["png", "jpg", "jpeg", "svg"]:
            candidate = os.path.join(assets_dir, f"branding_logo.{ext}")
            if os.path.isfile(candidate):
                return candidate
    except Exception:
        pass
        
    return None


def render_brand_header():
    """Render the application header with logo and title."""
    def _img_mime_from_path(p: str) -> str:
        ext = os.path.splitext(p)[1].lower()
        if ext == ".svg":
            return "image/svg+xml"
        elif ext in (".jpg", ".jpeg"):
            return "image/jpeg"
        return "image/png"
    
    logo_path = _find_logo_path()
    html = []
    html.append("<div class='hero' style='margin-top:0; margin-bottom:2rem;'>")
    html.append("<div style='text-align:center;'>")
    
    if logo_path:
        try:
            with open(logo_path, "rb") as f:
                data = f.read()
            data_b64 = base64.b64encode(data).decode("utf-8")
            
            if logo_path.lower().endswith(".svg"):
                try:
                    svg_txt = data.decode("utf-8")
                    html.append(f"<div class='brand-logo' style='width:420px; max-width:90vw; color:inherit;'>{svg_txt}</div>")
                except Exception:
                    html.append(f"<img class='brand-logo' src='data:image/svg+xml;base64,{data_b64}' style='width:420px; max-width:90vw; height:auto;' />")
            else:
                mime = _img_mime_from_path(logo_path)
                html.append(f"<img class='brand-logo' src='data:{mime};base64,{data_b64}' style='width:420px; max-width:90vw; height:auto;' />")
        except Exception:
            html.append("<div class='brand-logo' style='font-weight:700;opacity:.9'>Planning &amp; Development</div>")
    else:
        html.append("<div class='brand-logo' style='font-weight:700;opacity:.9'>Planning &amp; Development</div>")
    
    html.append("<div class='title'>Planning &amp; Development Bot</div>")
    html.append("<div class='subtitle'>Ask questions about the Manual for Development Projects 2024</div>")
    html.append("</div></div>")
    
    st.markdown("".join(html), unsafe_allow_html=True)


def render_footer():
    """Render application footer (optional)."""
    st.markdown(
        """
        <div style='text-align:center; margin-top:3rem; padding:1.5rem; opacity:0.6; font-size:0.85rem;'>
        Powered by PDBOT v0.9.0 | Enterprise RAG Pipeline
        </div>
        """,
        unsafe_allow_html=True
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
