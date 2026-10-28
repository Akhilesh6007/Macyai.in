
import asyncio
import json
import re
import sys
import unicodedata
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

original = split_script(manifest["script"])[0]
short = " ".join(original.split()[:18])

# Normalize unusual Unicode and replace
# non-ASCII characters for diagnostic purposes.
cleaned = unicodedata.normalize("NFKC", short)
cleaned = cleaned.encode(
    "ascii", errors="ignore"
).decode("ascii")

cleaned = re.sub(r"\s+", " ", cleaned).strip()

neutral = (
    "Artificial intelligence helps people learn, "
    "create and solve problems."
)

print("=== MACY AI TEXT DIAGNOSTIC ===")

print("Actual short text:", repr(short))
print("Cleaned text:", repr(cleaned))

print("\nUnusual characters:")

for char in set(short):
    if ord(char) > 127 or unicodedata.category(char).startswith("C"):
        print(
            repr(char),
            "Unicode:", f"U+{ord(char):04X}",
            unicodedata.name(char, "UNKNOWN"),
        )

output_dir = ROOT / "storage" / "voice_debug"
output_dir.mkdir(parents=True, exist_ok=True)


async def test(label, text):
    audio = output_dir / f"text_{label}.mp3"

    audio.unlink(missing_ok=True)

    try:
        await asyncio.wait_for(
            edge_tts.Communicate(
                text=text,
                voice="en-US-JennyNeural",
            ).save(str(audio)),
            timeout=60,
        )

        passed = (
            audio.exists()
            and audio.stat().st_size > 0
        )

        print(
            label,
            "PASS" if passed else "FAIL"
        )

    except Exception as error:
        print(
            label,
            "FAIL",
            type(error).__name__,
        )


async def main():
    await test(
        "known_good",
        "Hello, welcome to Macy AI.",
    )

    await test("neutral", neutral)
    await test("actual_script", short)

    if cleaned != short:
        await test("cleaned_script", cleaned)


if __name__ == "__main__":
    asyncio.run(main())
