# Interview preparation

1. **Why FastAPI?** Typed request validation, generated OpenAPI documentation and lightweight routing. Work is delegated to a background function; FFmpeg does not run within a normal request response.
2. **How is REST used?** POST creates a task and returns 202; GET reads status or streams completed output. Incomplete preview returns 409.
3. **How is Gemini integrated?** Through the configurable OpenAI-compatible client, not a trained local model. JSON script/keyword output is validated; auth, quota and transport failures map to sanitized errors.
4. **Are jobs durable?** No. FastAPI BackgroundTasks runs in the server process. JSON persists status but restart recovery is missing. A bounded worker with recovery is a reasonable next step before adding infrastructure.
5. **How does FFmpeg render?** Normalize each looped input to a common crop, FPS and pixel format; trim by frame counts, reset timestamps, concatenate, burn SRT, encode H.264 and mux AAC.
6. **How are scenes matched?** Narration sections are tokenized, stop words excluded and clips ranked by keyword-set overlap. Stable ties preserve input order. This inexpensive heuristic lacks semantic or visual understanding.
7. **How are captions synchronized?** Edge TTS word boundaries are shifted by decoded chunk sample counts; words are grouped into SRT cues. Scene boundaries use weighted cue matching, an approximation rather than forced alignment.
8. **What caused the rendering bug?** timed_plan was assigned after a return in the exception handler. Moving the timing stage before render fixes control flow; a mocked lifecycle test checks the plan exists when rendering begins.
9. **How are failures handled?** Stage/state and traceback are persisted. Provider messages are sanitized for script generation. More robust interruption handling and resource limits are pending.
10. **What improves performance?** Existing footage/search caching and compressed output. Reuse of edited assets, bounded concurrency and measured profiling should guide further changes. No invented throughput or speedup claims.
11. **How would it scale?** Separate workers from API serving, enforce limits, store assets externally and use durable queue/storage when workload warrants it. Current JSON and in-process jobs are local-demo choices.
12. **What security controls exist?** Backend secrets, constrained download host and file-size checks, task-ID validation and loopback deployment. Authentication, resolved path containment and stronger concurrency isolation remain gaps.
13. **How was it tested?** Isolated unittest regressions mock network providers; an optional saved-media script runs real FFmpeg into a unique output folder and verifies task-file hashes. API/UI and real-provider checks remain explicitly unverified.

## Truthful resume bullets
- Developed a FastAPI and Streamlit video creation pipeline integrating provider-generated scripts, Pixabay footage, Edge TTS narration and FFmpeg MP4 rendering.
- Implemented deterministic keyword-based scene selection and narration-cue scene timing with SRT captions for a multilingual video workflow.
- Diagnosed an unreachable scene-timing stage and added eight isolated offline regression tests covering task lifecycle, timing, voice selection and output preservation.

Use these only to describe work you can explain and substantiate; no deployment, user-count or performance claims are implied.
