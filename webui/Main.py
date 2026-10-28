
from pathlib import Path
import streamlit as st
import requests

from components.video_job_client import (
    submit_video,
    get_video_status,
    get_video_preview_url,
    get_video_download_url,
)

from components.task_manager import render_task_manager

# FastAPI backend address
API_BASE_URL = "http://127.0.0.1:8081"



# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Macy AI | Video Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# BACKEND API - DEMO SCRIPT GENERATION
# =========================================================

def generate_script():
    """Generate with either the free demo endpoint or the configured live AI."""
    subject = st.session_state.get("video_subject", "").strip()
    if len(subject) < 3:
        st.session_state["script_error"] = "Enter a subject with at least 3 characters."
        st.session_state.pop("script_success", None)
        return

    mode = st.session_state.get("script_generator_mode", "Demo (offline)")
    endpoint = (
        "/api/v1/scripts/generate"
        if mode == "AI (live)"
        else "/api/v1/scripts/demo"
    )
    payload = {
        "subject": subject,
        "language": st.session_state.get("script_language", "Auto Detect"),
        "paragraph_count": int(st.session_state.get("paragraph_count", 3)),
        "custom_prompt": st.session_state.get("custom_prompt", ""),
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}", json=payload, timeout=75
        )
        if not response.ok:
            try:
                detail = response.json().get("detail", "API request failed.")
            except ValueError:
                detail = "API request failed."
            raise ValueError(f"HTTP {response.status_code}: {detail}")

        result = response.json()
        script = result["script"]
        keywords = result["keywords"]
        if not isinstance(script, str) or not isinstance(keywords, list):
            raise ValueError("Unexpected API response format.")

        st.session_state["video_script"] = script
        st.session_state["video_keywords"] = ", ".join(map(str, keywords))
        st.session_state["script_success"] = (
            "AI script generated successfully!" if mode == "AI (live)"
            else "Demo script generated successfully!"
        )
        st.session_state.pop("script_error", None)

    except (requests.RequestException, ValueError, KeyError) as exc:
        st.session_state["script_error"] = f"Script generation failed: {exc}"
        st.session_state.pop("script_success", None)



# =========================================================
# 2. LOAD CUSTOM CSS
# =========================================================

CSS_PATH = (
    Path(__file__).resolve().parent
    / "styles"
    / "custom.css"
)

if CSS_PATH.is_file():
    st.markdown(
        f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )


# =========================================================
# 3. SETTINGS DIALOG
# =========================================================

@st.dialog("⚙️ Macy AI Settings", width="large")
def show_settings():

    llm_tab, sources_tab, interface_tab = st.tabs(
        [
            "LLM Settings",
            "Material Sources",
            "Interface",
        ]
    )

    # LLM SETTINGS
    with llm_tab:
        st.subheader("AI Model Configuration")

        st.selectbox(
            "LLM Provider",
            [
                "Kimi / Moonshot AI",
                "OpenAI",
                "Google Gemini",
                "DeepSeek",
                "Ollama",
            ],
            key="llm_provider",
        )

        st.text_input(
            "API Key",
            type="password",
            key="llm_api_key",
        )

        st.text_input(
            "Base URL (Optional)",
            key="llm_base_url",
        )

        st.text_input(
            "Model Name",
            placeholder="Enter your AI model name",
            key="llm_model_name",
        )

        st.info(
            "AI provider integration is not connected yet. "
            "Do not enter real API keys."
        )

    # MATERIAL SETTINGS
    with sources_tab:
        st.subheader("Material Source Configuration")

        st.selectbox(
            "Default Material Source",
            [
                "Pexels",
                "Pixabay",
                "Local Files",
            ],
            key="default_video_source",
        )

        st.text_input(
            "Pexels API Key",
            type="password",
            key="pexels_api_key",
        )

        st.text_input(
            "Pixabay API Key",
            type="password",
            key="pixabay_api_key",
        )

        st.caption(
            "Video download integration will be added later."
        )

    # INTERFACE SETTINGS
    with interface_tab:
        st.subheader("Interface Preferences")

        st.selectbox(
            "Display Language",
            ["English"],
            key="interface_language",
        )

        st.toggle(
            "Enable Subtitles by Default",
            value=True,
            key="default_subtitles",
        )

        st.caption(
            "These preferences are currently stored "
            "only in the Streamlit session."
        )

    if st.button(
        "Apply Settings",
        type="primary",
        use_container_width=True,
    ):
        st.success(
            "Settings applied to the current session."
        )


# =========================================================
# 4. HEADER
# =========================================================

brand_col, manager_col, settings_col, lang_col = (
    st.columns(
        [5.7, 1.45, 1.2, 1.65],
        gap="small",
        vertical_alignment="center",
    )
)

with brand_col:
    st.markdown(
        """
        <div class="macy-brand">
            Macy <span style="color:#60A5FA">AI</span> 🎬
        </div>
        <p class="macy-subtitle">
            Turn Your Ideas Into Videos
        </p>
        """,
        unsafe_allow_html=True,
    )

with manager_col:
    with st.popover(
        "Task Manager",
        use_container_width=True,
    ):
        st.subheader("Task Manager")

        st.info(
            "No tasks available yet. "
            "Task management will be connected later."
        )

with settings_col:
    if st.button(
        "⚙ Settings",
        use_container_width=True,
    ):
        show_settings()

with lang_col:
    st.selectbox(
        "Interface Language",
        ["English"],
        label_visibility="collapsed",
        key="header_language",
    )

st.write("")



# Check backend connectivity
try:
    response = requests.get(
        f"{API_BASE_URL}/health",
        timeout=3,
    )
    response.raise_for_status()

    if response.json().get("status") == "ok":
        st.caption("🟢 Macy AI Backend Connected")
    else:
        st.warning("Backend returned an unexpected response.")

except (requests.RequestException, ValueError):
    st.warning(
        "Backend is offline. Start FastAPI on port 8081."
    )



# =========================================================
# 5. FOUR MAIN SETTINGS PANELS
# =========================================================

script_col, video_col, audio_col, subtitle_col = (
    st.columns(4, gap="small")
)


# =========================================================
# 6. VIDEO SCRIPT SETTINGS
# =========================================================

with script_col:
    with st.container(border=True):

        st.subheader("Video Script Settings")

        subject = st.text_area(
            "Video Subject",
            placeholder=(
                "Example: How AI is changing everyday life"
            ),
            height=106,
            key="video_subject",
        )

        st.selectbox(
            "Script Language",
            [
                "Auto Detect",
                "English",
                "Hindi",
            ],
            key="script_language",
        )

        with st.expander("Advanced Script Settings"):

            st.text_area(
                "Custom Prompt (Optional)",
                height=90,
                key="custom_prompt",
            )

            st.number_input(
                "Paragraph Count",
                min_value=1,
                max_value=12,
                value=3,
                key="paragraph_count",
            )

        
        st.selectbox(
            "Script Generator",
            ["Demo (offline)", "AI (live)"],
            help="Live AI uses your backend .env API credentials and may incur charges.",
            key="script_generator_mode",
        )

        # A Streamlit callback runs before the widgets are drawn again.
        # This lets the callback safely populate the script and keywords.
        st.button(
            "✨ Generate Script & Keywords",
            use_container_width=True,
            on_click=generate_script,
        )

        if st.session_state.get("script_error"):
            st.error(st.session_state["script_error"])
        elif st.session_state.get("script_success"):
            st.success(st.session_state["script_success"])

        # These fields must be visible on every run, not just after a click.
        script = st.text_area(
            "Video Script (Optional)",
            height=148,
            key="video_script",
        )

        st.text_area(
            "Video Keywords (Optional)",
            height=90,
            key="video_keywords",
        )


# =========================================================
# 7. VIDEO SETTINGS
# =========================================================

with video_col:
    with st.container(border=True):

        st.subheader("Video Settings")

        video_source = st.selectbox(
            "Video Source",
            [
                "Pexels",
                "Pixabay",
                "Local Files",
            ],
            key="video_source",
        )

        if video_source == "Local Files":
            st.file_uploader(
                "Upload Video or Images",
                type=[
                    "mp4",
                    "mov",
                    "jpg",
                    "jpeg",
                    "png",
                ],
                accept_multiple_files=True,
                key="local_media",
            )

        st.selectbox(
            "Video Concatenation Mode",
            [
                "Random Concatenation",
                "Sequential Concatenation",
            ],
            key="concat_mode",
        )

        st.checkbox(
            "Match Visuals to Script Order",
            value=False,
            key="match_script_order",
        )

        st.selectbox(
            "Video Transition Mode",
            ["None", "Fade"],
            key="transition_mode",
        )

        st.selectbox(
            "Video Aspect Ratio",
            [
                "Portrait 9:16",
                "Landscape 16:9",
                "Square 1:1",
            ],
            key="video_aspect",
        )

        st.selectbox(
            "Source Frame Fit",
            [
                "Fill (center crop)",
                "Contain",
            ],
            key="frame_fit",
        )

        st.select_slider(
            "Maximum Clip Duration (seconds)",
            options=[
                1, 2, 3, 4, 5,
                6, 8, 10, 15,
            ],
            value=3,
            key="clip_duration",
        )


# =========================================================
# 8. AUDIO SETTINGS
# =========================================================

with audio_col:
    with st.container(border=True):

        st.subheader("Audio Settings")

        voice_mode = st.radio(
            "Voiceover Mode",
            [
                "Auto",
                "Upload",
                "None",
            ],
            horizontal=True,
            key="voiceover_mode",
        )

        if voice_mode == "Auto":

            st.selectbox(
                "Voiceover Service",
                [
                    "Edge TTS",
                    "Azure Speech (Later)",
                ],
                key="voice_service",
            )

            st.selectbox(
                "Voice",
                [
                    "en-AU-NatashaNeural",
                    "en-US-JennyNeural",
                    "en-US-GuyNeural",
                ],
                key="voice_name",
            )

            st.selectbox(
                "Voiceover Volume",
                [
                    "50%",
                    "75%",
                    "100%",
                    "125%",
                    "150%",
                ],
                index=2,
                key="voice_volume",
            )

            st.selectbox(
                "Voiceover Speed",
                [
                    "0.8x",
                    "0.9x",
                    "1.0x",
                    "1.1x",
                    "1.2x",
                ],
                index=2,
                key="voice_speed",
            )

            if st.button(
                "🔊 Voice Sample",
                use_container_width=True,
            ):
                st.info(
                    "Voice preview will be "
                    "implemented later."
                )

        elif voice_mode == "Upload":

            st.file_uploader(
                "Upload Narration",
                type=["mp3", "wav", "m4a"],
                key="narration_file",
            )

        else:
            st.caption(
                "The video will not contain narration."
            )

        st.divider()

        music_source = st.selectbox(
            "Background Music Source",
            [
                "None",
                "Local Upload",
            ],
            key="music_source",
        )

        if music_source == "Local Upload":

            st.file_uploader(
                "Upload Background Music",
                type=["mp3", "wav"],
                key="music_file",
            )

        st.slider(
            "Background Music Volume",
            min_value=0,
            max_value=100,
            value=20,
            format="%d%%",
            key="music_volume",
        )


# =========================================================
# 9. SUBTITLE SETTINGS
# =========================================================

with subtitle_col:
    with st.container(border=True):

        st.subheader("Subtitle Settings")

        subtitles_enabled = st.checkbox(
            "Enable Subtitles",
            value=True,
            key="enable_subtitles",
        )

        if subtitles_enabled:

            st.selectbox(
                "Font",
                [
                    "MicrosoftYaHeiBold.ttc",
                    "Arial",
                    "DejaVuSans",
                ],
                key="subtitle_font",
            )

            st.selectbox(
                "Position",
                [
                    "Bottom (Recommended)",
                    "Center",
                    "Top",
                ],
                key="subtitle_position",
            )

            st.selectbox(
                "Subtitle Display",
                [
                    "Whole sentence",
                    "Word by word",
                ],
                key="subtitle_display",
            )

            st.selectbox(
                "Entrance Animation",
                [
                    "None",
                    "Pop",
                ],
                key="subtitle_animation",
            )

            st.color_picker(
                "Text Color",
                value="#FFFFFF",
                key="subtitle_color",
            )

            st.slider(
                "Font Size",
                min_value=20,
                max_value=100,
                value=60,
                key="subtitle_font_size",
            )

            st.color_picker(
                "Outline Color",
                value="#000000",
                key="subtitle_outline_color",
            )

            st.slider(
                "Outline Width",
                min_value=0.0,
                max_value=5.0,
                value=1.5,
                step=0.5,
                key="subtitle_outline_width",
            )

        else:
            st.caption(
                "Subtitles are disabled."
            )


# =========================================================
# 10. VIDEO GENERATION SECTION
# =========================================================

st.divider()

st.subheader("Generate Video")



video_count = st.number_input(
    "Number of Videos",
    min_value=1,
    max_value=5,
    value=1,
    key="video_count",
)


# =========================================================
# MACY AI - GENERATE VIDEO BACKEND INTEGRATION
# =========================================================

import re

if st.button(
    "🎬 Generate Video",
    type="primary",
    use_container_width=True,
):
    video_subject = st.session_state.get(
        "video_subject", ""
    ).strip()

    video_script = st.session_state.get(
        "video_script", ""
    ).strip()

    keywords_text = st.session_state.get(
        "video_keywords", ""
    )

    video_keywords = [
        keyword.strip()
        for keyword in re.split(r"[,;\n]+", keywords_text)
        if keyword.strip()
    ]

    selected_source = st.session_state.get(
        "video_source", "Pexels"
    )

    if video_count != 1:
        st.warning(
            "Batch generation is not connected yet. "
            "Set Number of Videos to 1."
        )

    elif selected_source != "Pixabay":
        st.warning(
            "The current backend supports Pixabay. "
            "Select Pixabay in Video Source."
        )

    elif len(video_subject) < 3:
        st.warning(
            "Enter a Video Subject with at least "
            "3 characters."
        )

    elif len(video_script) < 20:
        st.warning(
            "Generate an AI script first, or enter "
            "a script with at least 20 characters."
        )

    elif not video_keywords:
        st.warning(
            "Generate video keywords before "
            "creating a video."
        )

    else:
        try:
            with st.spinner(
                "Submitting video generation task..."
            ):
                result = submit_video(
                    subject=video_subject,
                    script=video_script,
                    keywords=video_keywords[:15],
                )

            task_id = result["task_id"]

            st.session_state["macy_video_task_id"] = (
                task_id
            )

            st.success(
                "Video generation task submitted!"
            )
            st.info(f"Task ID: {task_id}")

        except (requests.RequestException, ValueError,
                KeyError) as error:
            st.error(
                f"Could not submit video task: {error}"
            )


# =========================================================
# MACY AI - VIDEO TASK STATUS AND PREVIEW
# =========================================================

task_id = st.session_state.get(
    "macy_video_task_id"
)

if task_id:
    st.markdown("### Video Generation Status")

    if st.button(
        "🔄 Refresh Video Status",
        key="refresh_video_status",
    ):
        pass

    try:
        task = get_video_status(task_id)

        state = task.get("state", "unknown")
        stage = task.get("stage", "unknown")

        st.write("**Task ID:**", task_id)
        st.write("**Status:**", state)
        st.write("**Current Stage:**", stage)

        if state == "queued":
            st.info("Video task is queued.")

        elif state == "processing":
            st.info(
                f"Video processing: {stage}"
            )

            progress = {
                "materials": 20,
                "voiceover": 45,
                "subtitles": 65,
                "rendering": 85,
            }

            st.progress(
                progress.get(stage, 5)
            )

            st.caption(
                "Progress is based on pipeline stages, "
                "not exact processing percentage."
            )

        elif state == "completed":
            st.success(
                "Your Macy AI video is ready!"
            )

            st.progress(100)

            output = task.get("output") or {}

            duration = output.get("duration", 0)
            resolution = output.get(
                "resolution", "Unknown"
            )

            st.write(
                f"**Duration:** {duration:.2f} seconds"
            )
            st.write(
                f"**Resolution:** {resolution}"
            )

            preview_url = get_video_preview_url(
                task_id
            )

            download_url = get_video_download_url(
                task_id
            )

            
# Compact centered video player
            left_space, video_column, right_space = st.columns(
                [1, 0.9, 1]
            )

            with video_column:
                st.video(preview_url)


            st.link_button(
                "⬇ Download MP4",
                download_url,
                use_container_width=True,
            )

        elif state == "failed":
            st.error(
                task.get("error")
                or "Video generation failed."
            )

        else:
            st.warning(
                f"Unknown task status: {state}"
            )

    except (requests.RequestException, ValueError) as error:
        st.error(
            f"Unable to retrieve task status: {error}"
        )


# =========================================================
# 11. FOOTER
# =========================================================

# ==========================================
# MACY AI TASK MANAGER
# ==========================================

with st.expander("📁 Task Manager & Video History"):
    render_task_manager()

st.caption(
    "Macy AI • Video Creation Studio • "
    "Frontend Prototype"
)
