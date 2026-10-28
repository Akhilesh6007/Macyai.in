"""Provider settings UI (prototype only, no credential persistence)."""
import streamlit as st


@st.dialog("⚙️ Macy AI Settings", width="large")
def show_settings() -> None:
    llm_tab, material_tab, interface_tab = st.tabs(
        ["LLM Settings", "Material Sources", "Interface"]
    )

    with llm_tab:
        st.selectbox(
            "LLM Provider",
            ["Kimi / Moonshot AI", "OpenAI", "Google Gemini", "DeepSeek", "Ollama"],
            key="llm_provider",
        )
        st.text_input("API Key", type="password", key="llm_api_key")
        st.text_input("Base URL (optional)", key="llm_base_url")
        st.text_input(
            "Model Name", key="llm_model_name",
            placeholder="Enter a model available to your account",
        )
        st.warning("This is a UI prototype. Do not enter real API keys yet.")

    with material_tab:
        st.selectbox(
            "Default Material Source", ["Pexels", "Pixabay", "Local Files"],
            key="default_video_source",
        )
        st.text_input("Pexels API Key", type="password", key="pexels_api_key")
        st.text_input("Pixabay API Key", type="password", key="pixabay_api_key")
        st.caption("Source connections will be added in later steps.")

    with interface_tab:
        st.selectbox("Display Language", ["English"], key="settings_language")
        st.toggle("Enable subtitles by default", value=True, key="default_subtitles")

    if st.button("Apply Settings", type="primary", use_container_width=True):
        st.success("UI settings updated for this session; they are not saved to disk.")
