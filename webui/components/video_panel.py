"""Video footage and rendering configuration controls."""
import streamlit as st


def render_video_panel() -> None:
    with st.container(border=True):
        st.subheader("Video Settings")
        source = st.selectbox(
            "Video Source", ["Pexels", "Pixabay", "Local Files"], key="video_source"
        )
        if source == "Local Files":
            st.file_uploader(
                "Upload Videos / Images",
                type=["mp4", "mov", "jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key="local_media",
            )
        st.selectbox(
            "Video Concatenation Mode",
            ["Random Concatenation", "Sequential Concatenation"],
            key="concat_mode",
        )
        st.checkbox("Match Visuals to Script Order", value=False, key="match_script_order")
        st.selectbox("Video Transition Mode", ["None", "Fade"], key="transition_mode")
        st.selectbox(
            "Video Aspect Ratio", ["Portrait 9:16", "Landscape 16:9", "Square 1:1"],
            key="video_aspect_ratio",
        )
        st.selectbox(
            "Source Frame Fit", ["Fill (center crop)", "Contain"], key="frame_fit"
        )
        st.select_slider(
            "Maximum Clip Duration (seconds)",
            options=[1, 2, 3, 4, 5, 6, 8, 10, 15],
            value=3,
            key="clip_duration",
        )
