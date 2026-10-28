
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.video import (
    render_video,
    VideoRenderError,
)


def main():
    print("=== MACY AI VIDEO RENDER TEST ===")

    manifest_path = (
        ROOT / "storage" / "tasks"
        / "step7_test" / "manifest.json"
    )

    audio_dir = ROOT / "storage" / "tasks" / "step8_test"
    output_dir = ROOT / "storage" / "tasks" / "step10_test"

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    video_paths = [
        item["file"]
        for item in manifest.get("videos", [])
    ]

    print("Video files:", len(video_paths))

    result = render_video(
        video_paths=video_paths,
        audio_path=audio_dir / "audio.mp3",
        subtitle_path=audio_dir / "subtitle.srt",
        output_path=output_dir / "final_video.mp4",
        width=720,
        height=1280,
        fps=24,
    )

    print("\nSUCCESS: Video rendered")
    print("File:", result["video_path"])
    print("Duration:", round(result["duration"], 2), "seconds")
    print("Resolution:", result["resolution"])


if __name__ == "__main__":
    try:
        main()
    except (
        VideoRenderError,
        FileNotFoundError,
        ValueError,
        OSError,
    ) as error:
        print("\nRENDER FAILED:", error)
        raise SystemExit(1)
