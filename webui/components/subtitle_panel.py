"""Subtitle visual styling controls."""
import streamlit as st


def render_subtitle_panel() -> None:
    with st.container(border=True):
        st.subheader("Subtitle Settings")
        enabled = st.checkbox(
            "Enable Subtitles", value=True, key="enable_subtitles"
        )
        if not enabled:
            st.caption("Subtitles are disabled for this video.")
            return
        st.selectbox(
            "Font", ["MicrosoftYaHeiBold.ttc", "Arial", "DejaVuSans"],
            key="subtitle_font",
        )
        st.selectbox(
            "Position", ["Bottom (Recommended)", "Center", "Top"],
            key="subtitle_position",
        )
        st.selectbox(
            "Subtitle Display", ["Whole sentence", "Word by word"],
            key="subtitle_display",
        )
        st.selectbox(
            "Entrance Animation", ["None", "Pop"],
            key="subtitle_animation",
        )
        st.color_picker("Text Color", "#FFFFFF", key="subtitle_text_color")
        st.slider("Font Size", 20, 100, 60, key="subtitle_font_size")
        st.color_picker("Outline Color", "#000000", key="subtitle_outline_color")
        st.slider(
            "Outline Width", 0.0, 5.0, 1.5, 0.5,
            key="subtitle_outline_width",
        )
