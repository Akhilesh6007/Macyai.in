
import asyncio
import json
import sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.voice import split_script


TASK_ID = "20f9620f52db"

manifest_path = (
    ROOT / "storage" / "tasks"
    / TASK_ID / "manifest.json"
)

manifest = json.loads(
    manifest_path.read_text(encoding="utf-8")
)

first_chunk = split_script(
    manifest["script"]
)[0]

output_dir = ROOT / "storage" / "voice_debug"
output_dir.mkdir(parents=True, exist_ok=True)


async def test_voice(name, voice, text):
    print(f"\nTesting: {name}")
    print("Voice:", voice)
    print("Characters:", len(text))

    output = output_dir / f"{name}.mp3"
    metadata = output_dir / f"{name}.jsonl"

    output.unlink(missing_ok=True)
    metadata.unlink(missing_ok=True)

    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            connect_timeout=15,
            receive_timeout=30,
            boundary="WordBoundary",
        )

        await asyncio.wait_for(
            communicate.save(
                str(output),
                str(metadata),
            ),
            timeout=60,
        )

        if not output.exists() or output.stat().st_size == 0:
            raise RuntimeError("No audio file created")

        print("SUCCESS:", output)
        return True

    except Exception as error:
        print("FAILED:", type(error).__name__)
        print("Details:", str(error))
        return False


async def main():
    print("=== MACY AI EDGE TTS DIAGNOSTIC ===")

    sample = "Hello, this is a Macy AI voice test."

    voices = [
        ("natasha", "en-AU-NatashaNeural"),
        ("jenny", "en-US-JennyNeural"),
    ]

    working_voice = None

    for name, voice in voices:
        success = await test_voice(
            name + "_short",
            voice,
            sample,
        )

        if success and working_voice is None:
            working_voice = voice

    if working_voice is None:
        print("\nNeither voice generated a short sample.")
        print("Possible service or connection problem.")
        return

    print("\nTesting first actual script chunk...")

    success = await test_voice(
        "actual_script_chunk",
        working_voice,
        first_chunk,
    )

    print("\n=== RESULT ===")

    if success:
        print("SUCCESS: First script chunk works.")
        print("Working voice:", working_voice)
    else:
        print("Short audio works, but script chunk fails.")
        print("Investigate the specific script content.")


if __name__ == "__main__":
    asyncio.run(main())
