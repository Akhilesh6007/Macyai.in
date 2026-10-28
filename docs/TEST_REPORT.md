# Test report ? 2026-10-28

## Executed checks
- Python compilation: `python -m compileall -q app webui test` passed.
- Isolated offline suite: `python -m unittest discover -s test -p 'test_*.py' -v`: **8 passed**, 0 failed on final run (0.051 seconds). An initial fixture encoding failure was corrected by constructing Devanagari characters from code points; it was not an application voice-selection defect.
- Real saved-media render: `test/offline_saved_render.py` passed, using task 2b434425d2ce narration, captions and four downloaded clips. Output `storage/validation/4b715fabdde1/baseline.mp4`. No provider requests.
- Render settings: 540x960, 20 FPS, four planned scenes (17.55, 21.05, 19.45, 20.05 seconds); measured source audio duration 78.1 seconds; wall-clock rendering 44.618 seconds on this machine. This single sample is not a general performance benchmark.
- FFmpeg full MP4 decode to null: exit 0, empty error output. Metadata reports H.264 video and AAC mono audio, container duration 78.05 seconds (one configured frame shorter than probed source duration). Exact frame/sync analysis remains a phase 2 check.
- Extracted frame at 5 seconds: inspected visually; footage and legible English captions present. This is one frame, not whole-video visual/audio QA. Saved `preview.png` beside baseline output.
- SHA-256 comparison of all existing task files before/after rendering: unchanged.

## Environment qualification
Preferred `.venv/Scripts/python.exe` failed: missing base Python311 executable. Checks ran with `C:/Program Files/Python314/python.exe`, temporarily adding existing `.venv/Lib/site-packages` to sys.path. No use of `.venv-1`. The service subset imports successfully. Full ASGI import fails because Python314 cannot load the Python311 pydantic_core binary (`ArgsKwargs` import error). This workaround is not clean-install verification.

## Regression coverage
Timing construction before rendering and saved plan existence; completed task idempotence; failure state/stage/traceback; English/Hindi voice selection; empty footage rejection; continuous SRT scene timing; existing output protection; odd output dimension rejection; missing subtitle word metadata. Network providers and renderer are mocked in lifecycle tests; the separate saved-media test uses real FFmpeg.

## Not executed / remaining
API requests and preview/download endpoint verification; browser UI interaction; live Gemini/Pixabay/Edge TTS; listening QA; Hindi glyph inspection; all aspect ratios; music, transitions, animated captions or editor (not implemented); restart/concurrency/cancellation tests; clean dependency installation; Docker or public deployment. Existing manual provider scripts were not run. No tests required API keys.

Real-provider end-to-end smoke testing requires explicit approval and a working environment. Proposed procedure: choose one short script, generate a new task, poll to completion, verify audio/captions and preview/download, record provider/model and timings without exposing secrets. It is not part of the default offline suite.
