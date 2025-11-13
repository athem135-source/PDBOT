import streamlit as st
from app.state import set_flag


def cb_name_continue():
    name = st.session_state.get("__name_input", "").strip()
    if name:
        st.session_state["user_name"] = name
        st.session_state["__name_error"] = ""
        st.session_state["show_name_modal"] = False
    else:
        st.session_state["__name_error"] = "Name is required."


def cb_name_exit():
    set_flag(st.session_state, "app_exit", True)


def cb_apply():
    st.session_state["manual_action"] = "apply"


def cb_reset():
    st.session_state["manual_action"] = "reset"
