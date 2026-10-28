
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.subtitle import generate_subtitles


def main():
    print("=== MACY AI SUBTITLE TEST ===")

    task_dir = ROOT / "storage" / "tasks" / "step8_test"

    metadata = task_dir / "audio.jsonl"
    output = task_dir / "subtitle.srt"

    result = generate_subtitles(
        metadata_path=metadata,
        output_path=output,
        max_words=7,
    )

    print("\nSUCCESS: Subtitles generated")
    print("File:", result["subtitle_path"])
    print("Subtitle segments:", result["subtitle_count"])

    print("\nPreview:")
    print(
        output.read_text(encoding="utf-8")[:1000]
    )


if __name__ == "__main__":
    main()
