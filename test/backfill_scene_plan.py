
"""
Macy AI - Scene Plan Recovery

Generate scene plans for existing video tasks
using saved scripts, footage and subtitles.

No Gemini or Pixabay API calls.
No video re-rendering.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.scenes import build_scene_plan
from app.services.scene_timing import (
    build_timed_scene_plan,
)

TASKS_DIR = ROOT / "storage" / "tasks"


def main():
    print("=== MACY AI SCENE PLAN RECOVERY ===")

    if not TASKS_DIR.exists():
        raise SystemExit("Tasks folder not found.")

    task_dirs = sorted(
        (
            folder for folder in TASKS_DIR.iterdir()
            if folder.is_dir()
        ),
        key=lambda folder: folder.stat().st_mtime,
        reverse=True,
    )

    for task_dir in task_dirs:
        manifest_path = task_dir / "manifest.json"
        subtitle_path = task_dir / "subtitle.srt"
        scene_path = task_dir / "scene_plan.json"

        if not manifest_path.is_file():
            continue

        if not subtitle_path.is_file():
            continue

        try:
            manifest = json.loads(
                manifest_path.read_text(
                    encoding="utf-8"
                )
            )

            videos = manifest.get("videos") or []
            script = manifest.get("script") or ""

            if not script.strip() or not videos:
                print(
                    "Skipping task:",
                    task_dir.name,
                    "- script or footage missing"
                )
                continue

            if scene_path.is_file():
                plan = json.loads(
                    scene_path.read_text(
                        encoding="utf-8"
                    )
                )
            else:
                plan = build_scene_plan(
                    script=script,
                    downloaded=videos,
                )

            timed_plan = build_timed_scene_plan(
                plan,
                subtitle_path,
            )

            # Write only after validation succeeds.
            if not scene_path.exists():
                scene_path.write_text(
                    json.dumps(
                        plan,
                        indent=2,
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )

            output_path = (
                task_dir / "timed_scene_plan.json"
            )

            output_path.write_text(
                json.dumps(
                    timed_plan,
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            print("\nSUCCESS: Scene plan recovered")
            print("Task ID:", task_dir.name)
            print(
                "Scenes:",
                timed_plan["scene_count"]
            )
            print(
                "Duration:",
                timed_plan["duration_seconds"],
                "seconds",
            )
            print("Scene plan:", scene_path)
            print("Timed plan:", output_path)

            return

        except (
            ValueError,
            KeyError,
            TypeError,
            OSError,
            json.JSONDecodeError,
        ) as error:
            print(
                "Skipping task:",
                task_dir.name,
                "-",
                error,
            )

    raise SystemExit(
        "No suitable completed task was found. "
        "A task needs a script, downloaded footage "
        "and subtitle.srt."
    )


if __name__ == "__main__":
    main()
