
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

first_chunk = split_script(manifest["script"])[0]

# Keep the first 18 words as a shorter comparison.
short_chunk = " ".join(first_chunk.split()[:18])

output_dir = ROOT / "storage" / "voice_debug"
output_dir.mkdir(parents=True, exist_ok=True)


async def test_voice(label, voice, text):
    print(f"\nTesting: {label}", flush=True)
    print("Voice:", voice)
    print("Characters:", len(text))

    audio = output_dir / f"{label}.mp3"
    metadata = output_dir / f"{label}.jsonl"

    audio.unlink(missing_ok=True)
    metadata.unlink(missing_ok=True)

    try:
        await asyncio.wait_for(
            edge_tts.Communicate(
                text=text,
                voice=voice,
                boundary="WordBoundary",
            ).save(str(audio), str(metadata)),
            timeout=60,
        )

        if not audio.exists() or audio.stat().st_size == 0:
            raise RuntimeError("Audio is empty")

        print("SUCCESS: Audio generated")
        return True

    except Exception as error:
        print("FAILED:", type(error).__name__)
        print("Details:", str(error))
        return False


async def main():
    print("=== MACY AI VOICE CHUNK TEST ===")

    results = {}

    results["jenny_full"] = await test_voice(
        "jenny_full_chunk",
        "en-US-JennyNeural",
        first_chunk,
    )

    results["natasha_short"] = await test_voice(
        "natasha_short_chunk",
        "en-AU-NatashaNeural",
        short_chunk,
    )

    results["jenny_short"] = await test_voice(
        "jenny_short_chunk",
        "en-US-JennyNeural",
        short_chunk,
    )

    print("\n=== FINAL RESULTS ===")

    for name, passed in results.items():
        print(name, "PASS" if passed else "FAIL")


if __name__ == "__main__":
    asyncio.run(main())
