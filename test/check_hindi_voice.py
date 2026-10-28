
import asyncio
import json
import sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.voice import split_script

manifest_path = (
    ROOT / "storage" / "tasks"
    / "20f9620f52db" / "manifest.json"
)

manifest = json.loads(
    manifest_path.read_text(encoding="utf-8")
)

script = manifest["script"]
first_chunk = split_script(script)[0]

output_dir = ROOT / "storage" / "voice_debug"
output_dir.mkdir(parents=True, exist_ok=True)


async def test_voice(voice, name, text):
    print(f"\nTesting: {voice}")
    print("Characters:", len(text))

    audio = output_dir / f"{name}.mp3"
    metadata = output_dir / f"{name}.jsonl"

    audio.unlink(missing_ok=True)
    metadata.unlink(missing_ok=True)

    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            boundary="WordBoundary",
        )

        await asyncio.wait_for(
            communicate.save(
                str(audio),
                str(metadata),
            ),
            timeout=90,
        )

        if not audio.exists() or audio.stat().st_size == 0:
            raise RuntimeError("Audio file is empty")

        print("SUCCESS:", audio)
        return True

    except Exception as error:
        print("FAILED:", type(error).__name__)
        print("Details:", str(error))
        return False


async def main():
    print("=== MACY AI HINDI VOICE TEST ===")

    for voice, name in [
        ("hi-IN-SwaraNeural", "swara"),
        ("hi-IN-MadhurNeural", "madhur"),
    ]:
        await test_voice(
            voice,
            f"{name}_sample",
            "नमस्ते, मैसी एआई में आपका स्वागत है।",
        )

        await test_voice(
            voice,
            f"{name}_actual_chunk",
            first_chunk,
        )


if __name__ == "__main__":
    asyncio.run(main())
