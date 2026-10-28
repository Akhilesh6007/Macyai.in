
"""
Macy AI - Scene Matching Test

Runs locally without Gemini or Pixabay API calls.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.scenes import build_scene_plan


script = (
    "Robotics technology is transforming factories. "
    "Scientists use artificial intelligence "
    "in modern research laboratories. "
    "Smart city traffic systems improve transportation. "
    "Modern technology helps people solve problems."
)

downloaded = [
    {
        "video_id": 101,
        "keyword": "smart city traffic",
        "file": "city.mp4",
    },
    {
        "video_id": 102,
        "keyword": "robotics technology",
        "file": "robot.mp4",
    },
    {
        "video_id": 103,
        "keyword": "artificial intelligence laboratory",
        "file": "laboratory.mp4",
    },
]

print("=== MACY AI SCENE MATCHING TEST ===")

plan = build_scene_plan(
    script,
    downloaded,
)

assert plan["scene_count"] == 3

assert len({
    scene["video_id"]
    for scene in plan["scenes"]
}) == 3

assert all(
    scene["text"].strip()
    for scene in plan["scenes"]
)

assert " ".join(
    scene["text"]
    for scene in plan["scenes"]
) == script

print("SUCCESS: Scene plan generated")

for scene in plan["scenes"]:
    print(f"\nScene {scene['scene']}")
    print("Narration:", scene["text"])
    print("Keyword:", scene["keyword"])
    print("Clip:", scene["video_path"])
    print("Matching terms:", scene["match_terms"])

output = ROOT / "storage" / "scene_test.json"

output.parent.mkdir(
    parents=True,
    exist_ok=True,
)

output.write_text(
    json.dumps(
        plan,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)

print("\nScene plan saved:", output)
