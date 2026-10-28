# Setup guide

Use Windows Python 3.11 and `.venv`, not `.venv-1`. Current `.venv/pyvenv.cfg` points to missing `C:\Users\ak200\AppData\Local\Programs\Python\Python311\python.exe`. Restore Python 3.11 at that location or deliberately recreate the environment after preserving it. Environment restoration was not performed in this change.

On a fresh checkout with Python 3.11 installed:
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```
Copy the template only when `.env` does not already exist. Set MACY_LLM_API_KEY, MACY_LLM_MODEL, optional MACY_LLM_BASE_URL and PIXABAY_API_KEY privately. Gemini uses its compatible endpoint. Model availability/quotas depend on the account. Restart backend after configuration changes.

Start commands are in README. Do not launch duplicate servers on 8081/8501. Edge TTS and Pixabay require network access. imageio-ffmpeg supplies an executable on supported platforms; confirm it supports libx264, AAC and libass subtitles. Windows drive-letter escaping is avoided using a renderer-local relative subtitle copy. Installed fonts determine Devanagari coverage; Hindi visual validation is still required. OneDrive synchronization and antivirus can affect media IO; avoid simultaneous runs in the same task directory.

No Docker build or clean install has been verified. Linux deployment needs suitable fonts and FFmpeg codecs. Public hosting, authentication, TLS, resource limits and durable jobs remain pending; do not expose the current local service publicly.

Temporary diagnostic workaround used in this audit: system Python314 with `.venv/Lib/site-packages` on sys.path can run the service regressions and FFmpeg renderer. It cannot import the application's Python311 pydantic_core binary. It is not a supported launch procedure or substitute for environment repair.
