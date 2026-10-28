"""Voiceover and background music controls."""
import streamlit as st


def render_audio_panel() -> None:
    with st.container(border=True):
        st.subheader("Audio Settings")
        mode = st.radio(
            "Voiceover Mode", ["Auto", "Upload", "None"],
            horizontal=True, key="voiceover_mode",
        )
        if mode == "Auto":
            st.selectbox(
                "Voiceover Service", ["Edge TTS", "Azure Speech (later)"],
                key="voice_service",
            )
            st.selectbox(
                "Voice",
                ["en-AU-NatashaNeural", "en-US-JennyNeural", "en-US-GuyNeural"],
                key="voice_name",
            )
            st.selectbox(
                "Voiceover Volume", ["50%", "75%", "100%", "125%", "150%"],
                index=2, key="voice_volume",
            )
            st.selectbox(
                "Voiceover Speed", ["0.8x", "0.9x", "1.0x", "1.1x", "1.2x"],
                index=2, key="voice_speed",
            )
            if st.button("🔊 Voice Sample", use_container_width=True):
                st.info("Voice samples will be enabled when TTS is implemented.")
        elif mode == "Upload":
            st.file_uploader(
                "Upload Narration", type=["mp3", "wav", "m4a"], key="narration_upload"
            )
        else:
            st.caption("The video will not contain generated narration.")

        st.divider()
        music_source = st.selectbox(
            "Background Music Source", ["None", "Local Upload"],
            key="music_source",
        )
        if music_source == "Local Upload":
            st.file_uploader(
                "Upload Background Music", type=["mp3", "wav"], key="music_upload"
            )
        st.slider(
            "Background Music Volume", 0, 100, 20, format="%d%%", key="music_volume"
        )
