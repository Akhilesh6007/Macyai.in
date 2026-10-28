"""Controls for video topic, script, and search terms."""
import streamlit as st


def render_script_panel() -> tuple[str, str]:
    with st.container(border=True):
        st.subheader("Video Script Settings")
        subject = st.text_area(
            "Video Subject",
            placeholder="Example: How AI is changing everyday life",
            height=106,
            key="video_subject",
        )
        st.selectbox(
            "Script Language", ["Auto Detect", "English", "Hindi"],
            key="script_language",
        )
        with st.expander("Advanced Script Settings"):
            st.text_area("Custom Prompt (optional)", height=80, key="custom_prompt")
            st.number_input(
                "Paragraph Count", min_value=1, max_value=12, value=3,
                key="paragraph_count",
            )

        if st.button("✨ Generate Script & Keywords", use_container_width=True):
            st.info("Script generation will be connected to FastAPI later.")

        script = st.text_area("Video Script (Optional)", height=148, key="video_script")
        st.text_area("Video Keywords (Optional)", height=90, key="video_keywords")
    return subject, script
