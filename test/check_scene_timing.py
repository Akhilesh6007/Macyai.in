
"""
Macy AI - Scene Timing Test

Uses an existing task's scene plan
and subtitle file.

No API requests or video rendering.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.scene_timing import (
    build_timed_scene_plan,
)


def main():
    print("=== MACY AI SCENE TIMING TEST ===")

    tasks_dir = ROOT / "storage" / "tasks"

    if len(sys.argv) > 1:
        task_dir = tasks_dir / sys.argv[1]

    else:
        available = [
            folder
            for folder in tasks_dir.iterdir()
            if folder.is_dir()
            and (folder / "scene_plan.json").is_file()
            and (folder / "subtitle.srt").is_file()
        ] if tasks_dir.exists() else []

        if not available:
            raise SystemExit(
                "No task with scene_plan.json "
                "and subtitle.srt was found."
            )

        task_dir = max(
            available,
            key=lambda folder: (
                folder / "scene_plan.json"
            ).stat().st_mtime,
        )

    scene_file = task_dir / "scene_plan.json"
    subtitle_file = task_dir / "subtitle.srt"

    if not scene_file.is_file():
        raise SystemExit("Scene plan not found")

    if not subtitle_file.is_file():
        raise SystemExit("Subtitle file not found")

    plan = json.loads(
        scene_file.read_text(encoding="utf-8")
    )

    timed = build_timed_scene_plan(
        plan,
        subtitle_file,
    )

    scenes = timed["scenes"]

    assert all(
        scene["duration_seconds"] > 0
        for scene in scenes
    )

    for previous, current in zip(
        scenes, scenes[1:]
    ):
        assert (
            previous["end_seconds"]
            == current["start_seconds"]
        )

    output = task_dir / "timed_scene_plan.json"

    output.write_text(
        json.dumps(
            timed,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("Task ID:", task_dir.name)
    print("Scene count:", len(scenes))

    for scene in scenes:
        print(
            f"Scene {scene['scene']}: "
            f"{scene['start_seconds']}s - "
            f"{scene['end_seconds']}s"
        )
        print("Keyword:", scene["keyword"])

    print("\nSUCCESS: Scene timing plan created")
    print("Saved:", output)


if __name__ == "__main__":
    main()
