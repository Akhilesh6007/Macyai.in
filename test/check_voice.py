
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.voice import generate_voiceover_sync


def main():
    print("=== MACY AI VOICEOVER TEST ===")

    manifest_path = (
        ROOT / "storage" / "tasks"
        / "step7_test" / "manifest.json"
    )

    if not manifest_path.exists():
        raise SystemExit("Step 7 manifest is missing.")

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    script = manifest.get("script", "").strip()

    if not script:
        raise SystemExit("No script found in manifest.")

    # Short sample before generating full narration.
    sample_script = script[:400]

    output = (
        ROOT / "storage" / "tasks"
        / "step8_test" / "audio.mp3"
    )

    result = generate_voiceover_sync(
        script=sample_script,
        output_path=output,
    )

    print("SUCCESS: Voiceover generated")
    print("Audio:", result["audio_path"])
    print("Timing:", result["metadata_path"])
    print("Voice:", result["voice"])
    print(
        "Size:",
        round(output.stat().st_size / 1024, 2),
        "KB"
    )


if __name__ == "__main__":
    main()
