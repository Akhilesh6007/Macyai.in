# Macy AI repository audit

Inspected 2026-10-28 before implementation. No Git repository is present; existing files cannot be compared against a commit. Credentials were not read or printed.

## Existing implementation
FastAPI registers script demo/live and task generation/history/status/preview/download. Streamlit Main.py calls these endpoints. Pixabay search caches results and restricts downloads to HTTPS cdn.pixabay.com, with size limits. Edge TTS chunks narration, retries transient failures and saves word timings. SRT generation, deterministic lexical scene matching, SRT-based scene timing and two FFmpeg renderers exist. These are code findings, not proof of live-provider success.

## Confirmed broken behavior
Task 2b434425d2ce traceback identifies timed_plan accessed before assignment in video_jobs.py. Its assignment is after return None in the exception handler, hence unreachable. The preferred .venv references a missing Python311 installation and cannot launch. System Python314 has no project dependencies installed. Limited service checks can borrow pure-Python packages from .venv; this is not a reproducible supported setup.

## Incomplete features and dead code
Main.py exposes video source, aspect, ordering, transitions, clip duration, voice, speed, volume, music and subtitle styling controls, but submit_video sends only subject/script/keywords. Settings dialog is a prototype; its credentials do not configure the backend. Header task popover is stale although the lower task manager is connected. Component panel files duplicate Main.py layouts; backup files and legacy task.py are not the active REST pipeline. app/router.py, models/schema.py, config/config.py, pyproject.toml and config.example.toml are empty. requirements.txt omits Edge TTS, aiohttp and imageio-ffmpeg. Existing test/check_*.py files are manual scripts, several call providers or write to saved task directories. No isolated regression suite was found.

## Risks
FastAPI BackgroundTasks is in-process, unbounded and loses work on restart; no cancellation/recovery or job locking. JSON status replacement is atomic but concurrent writers can lose updates. Timed renderer writes directly to final output with -y, uses a shared subtitle filename and lacks finite-value/even-dimension validation. Arial fallback does not prove Hindi glyph coverage. Timing is approximate cue matching, not forced alignment or visual understanding. No implemented music mix or interactive persisted scene editor was found. Local unauthenticated API should stay on loopback. Task routes validate IDs but should also enforce resolved path containment against directory junctions. Provider availability, browser playback, Hindi glyph rendering and performance are unverified.

## Recommended order and acceptance
1. Move timing before render, remove dead block, protect completed output, add mocked lifecycle regressions and isolated saved-media rendering. Compile and test before feature expansion.
2. Restore supported Python environment and validate API/UI plus English/Hindi smoke tests with explicit provider approval.
3. Wire validated render settings, test three aspect ratios and frame timing, then add transitions.
4. Implement local music and ducking; captions and verified Devanagari fonts.
5. Persist storyboard edits and render revisions in new tasks with asset reuse.
6. Add bounded execution, interruption recovery, retry/cancellation, path hardening and caching locks.
7. Finish deployment, measured benchmarks, demo and interview documents.

Definition of done: real generation succeeds, controls affect output, captions/audio align, preview/download succeed, failure diagnostics are useful, old outputs stay intact, offline regressions pass, and limitations are documented. Do not label untested provider integrations or missing features complete.
