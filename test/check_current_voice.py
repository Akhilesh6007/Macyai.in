
"""
Macy AI - Current Voiceover Error Diagnostic

Reproduce voiceover errors without creating
another full video generation job.
"""

import json
import logging
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.voice import generate_voiceover_sync
from app.services.video_jobs import select_voice_for_script

logging.basicConfig(level=logging.INFO)

TASK_ID = "9c2dfd4b2203"

manifest_path = (
    ROOT / "storage" / "tasks"
    / TASK_ID / "manifest.json"
)

print("=== MACY AI CURRENT VOICEOVER TEST ===")

if not manifest_path.is_file():
    raise SystemExit("Task manifest not found.")

manifest = json.loads(
    manifest_path.read_text(encoding="utf-8")
)

script = manifest.get("script", "").strip()

if not script:
    raise SystemExit("Script is empty.")

selected_voice = select_voice_for_script(script)

print("Task ID:", TASK_ID)
print("Script length:", len(script))
print("Words:", len(script.split()))
print("Selected voice:", selected_voice, flush=True)

output = (
    ROOT / "storage" / "voice_debug"
    / f"{TASK_ID}.mp3"
)

output.parent.mkdir(parents=True, exist_ok=True)

try:
    result = generate_voiceover_sync(
        script=script,
        output_path=output,
        voice=selected_voice,
    )

    print("\nSUCCESS: Voiceover generated")
    print("Audio:", result["audio_path"])
    print("Timing:", result["metadata_path"])

except Exception as error:
    print("\nVOICEOVER FAILED")
    print("Error type:", type(error).__name__)
    print("Error message:", str(error))
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
