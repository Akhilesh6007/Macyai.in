
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.timed_video import render_timed_video


def main():
    task_id = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "0993bebf1064"
    )

    task_dir = (
        ROOT / "storage" / "tasks" / task_id
    )

    print("=== MACY AI TIMED VIDEO TEST ===")
    print("Task ID:", task_id)

    result = render_timed_video(
        timed_scene_plan=(
            task_dir / "timed_scene_plan.json"
        ),
        audio_path=task_dir / "audio.mp3",
        subtitle_path=task_dir / "subtitle.srt",
        output_path=(
            task_dir / "final_video_timed_test.mp4"
        ),
        width=540,
        height=960,
        fps=20,
    )

    print("\nSUCCESS: Timed video rendered")
    print("Output:", result["video_path"])
    print("Scenes:", result["scene_count"])
    print("Duration:", result["duration"])


if __name__ == "__main__":
    main()
