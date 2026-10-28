
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

TASK_ID = "20f9620f52db"

manifest_path = (
    ROOT / "storage" / "tasks"
    / TASK_ID / "manifest.json"
)

print("=== MACY AI FAILED VOICEOVER DIAGNOSTIC ===")

if not manifest_path.exists():
    raise SystemExit("Task manifest not found.")

manifest = json.loads(
    manifest_path.read_text(encoding="utf-8")
)

script = manifest.get("script", "").strip()

print("Script length:", len(script))
print("Word count:", len(script.split()))

if not script:
    raise SystemExit("Script is empty.")

output = (
    ROOT / "storage" / "voice_debug"
    / "audio.mp3"
)


selected_voice = select_voice_for_script(script)
print("Selected voice:", selected_voice, flush=True)


try:
    result = generate_voiceover_sync(
        script=script,
        output_path=output,
        voice=selected_voice,
    )

    print("\nSUCCESS: Full narration generated")
    print("Audio:", result["audio_path"])
    print("Timing:", result["metadata_path"])

except Exception:
    print("\nVOICEOVER FAILED")
    traceback.print_exc()
    sys.exit(1)
