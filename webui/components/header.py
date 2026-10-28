"""Macy AI page header and navigation."""
import streamlit as st
from components.settings_dialog import show_settings


def render_header() -> None:
    brand_col, tasks_col, settings_col, language_col = st.columns(
        [5.7, 1.45, 1.2, 1.65], gap="small", vertical_alignment="center"
    )

    with brand_col:
        st.markdown(
            '<div class="macy-brand">Macy <span>AI</span> 🎬</div>'
            '<p class="macy-subtitle">Turn Your Ideas Into Videos</p>',
            unsafe_allow_html=True,
        )
    with tasks_col:
        with st.popover("Task Manager", use_container_width=True):
            st.subheader("Task Manager")
            st.info("No video tasks yet. Task tracking is coming later.")
    with settings_col:
        if st.button("⚙ Settings", use_container_width=True):
            show_settings()
    with language_col:
        st.selectbox(
            "Interface Language", ["English"], key="header_language",
            label_visibility="collapsed",
        )
