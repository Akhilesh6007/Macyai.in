
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.task import generate_full_video


def main():
    print("=== MACY AI FULL VIDEO TEST ===")

    manifest = (
        ROOT / "storage"
        / "tasks"
        / "step7_test"
        / "manifest.json"
    )

    print("Starting full video pipeline...")

    result = generate_full_video(manifest)

    print("\nSUCCESS: Full video generated")
    print("Task ID:", result["task_id"])
    print("Status:", result["state"])
    print("Output:", result["output"]["video_path"])


if __name__ == "__main__":
    main()
