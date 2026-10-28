# REST API

Base: http://127.0.0.1:8081. Interactive schema: /docs. No authentication; bind to loopback.

| Method | Route | Behavior |
|---|---|---|
| GET | / | Service/version |
| GET | /health | Static process health, not provider readiness |
| POST | /api/v1/scripts/demo | Deterministic English template; no provider calls |
| POST | /api/v1/scripts/generate | Configured live script and keywords |
| POST | /api/v1/tasks/generate | Queue generation; HTTP 202 |
| GET | /api/v1/tasks | Task count/history |
| GET | /api/v1/tasks/{task_id} | Saved task state/stage/output/error |
| GET | /api/v1/tasks/{task_id}/preview | Inline video/mp4 after completion |
| GET | /api/v1/tasks/{task_id}/download | MP4 attachment after completion |

Script request: subject (3?300 characters), language (default Auto Detect), paragraph_count (1?12); live generation also accepts custom_prompt (up to 1500). Response contains script, keywords, language_requested, mode; live includes model. Demo does not translate its English template.

Video request example:
```json
{"subject":"Robotics","script":"Robotics helps people solve practical problems every day.","keywords":["robotics","technology"]}
```
Only these three video fields are currently connected. Music, voice/style settings and editor revisions have no supported task API contract yet. Subject max 300, script 20?20000, keywords list 1?15. Individual keyword length and whitespace-only values need stronger validation.

202 response: task_id, state, status_url, preview_url, download_url. Task states: queued, processing, completed, failed. Stages include materials, voiceover, subtitles, scene_matching, scene_timing, rendering, finished. output includes duration, resolution, scene counts, footage and measured stage/total seconds. Historical records may omit newer fields.

Errors: validation 422, invalid ID 400, missing task/file 404, incomplete output 409, unreadable metadata 500, missing AI configuration 503, provider failure 502. Task generation failures are recorded asynchronously in task.json with stage and error_traceback.txt. Do not expose raw logs publicly. Existing routes and response structures are preserved.
