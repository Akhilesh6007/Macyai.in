# Development roadmap

Each milestone follows inspect, plan, implement, test, review, report. Preserve FastAPI/Streamlit architecture and navy CSS. No paid calls, public deployment or commits without authorization.

| Phase | Work | Verification gate |
|---|---|---|
| 1 | Repair unreachable timing; protect outputs; isolated regressions | Compilation, mocked lifecycle, real saved-media render, API preview/download |
| 2 | Validated FPS/resolution/aspect, trims/loops, ordering, transitions, fallback | All ratios, frame boundaries, sync, no gaps |
| 3 | Local music library, mix levels, ducking/fades, voice controls | With/without music, no clipping, persisted API options |
| 4 | Safe subtitle styles, Hindi fonts, optional animation | English/Hindi visual QA and timing |
| 5 | Saved structured storyboard, lexical fallback, optional Gemini planning | Reload, relevant matching, quota failure |
| 6 | Streamlit scene editor and revision tasks | Edit/save/refresh/re-render without overwrites |
| 7 | Connect controls and presets, polish existing UI | Actual backend and browser walkthrough |
| 8 | Bounded jobs, recovery/retry/cancel, locks, path safety | Interrupted and concurrent job tests |
| 9 | Expand isolated unit/API/media coverage | No credentials in normal suite; explicit opt-in provider smoke |
| 10 | Dependencies, environment, Docker and local setup | Clean installation and health checks |
| 11 | Architecture/API/setup/test/demo/interview documents | Claims traceable to implementation and measured tests |

Current gate: preferred Python311 environment is broken. Use system Python314 only for explicitly qualified offline service checks; do not substitute .venv-1. Restore Python 3.11 and recreate a compatible environment before claiming full application validation.
