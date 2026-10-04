"""画面共通の小物。"""

import streamlit as st


def flash(message):
    """st.rerun() のあとに1回だけ表示するメッセージを積む。"""
    st.session_state["_flash"] = message


def show_flash():
    message = st.session_state.pop("_flash", None)
    if message:
        st.success(message)
