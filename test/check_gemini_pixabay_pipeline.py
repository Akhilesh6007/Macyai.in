
import sys
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.material import (
    search_videos,
    download_video,
    MaterialError,
)

API = "http://127.0.0.1:8081/api/v1/scripts/generate"


def main():
    print("=== MACY AI - GEMINI + PIXABAY TEST ===")

    payload = {
        "subject": "How AI will change the future",
        "language": "English",
        "paragraph_count": 3,
        "custom_prompt": "",
    }

    print("\n1. Generating script and keywords...")

    response = requests.post(
        API,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    result = response.json()

    script = result.get("script", "")
    keywords = result.get("keywords", [])

    if not isinstance(keywords, list):
        raise ValueError("Expected a list of keywords.")

    if not script or not keywords:
        raise ValueError("AI returned empty content.")

    print("Script generated successfully.")
    print("Keywords:", keywords)

    print("\n2. Searching Pixabay...")

    downloaded = []
    used_ids = set()

    # Limit requests during this integration test.
    for keyword in keywords[:4]:
        if len(downloaded) >= 2:
            break

        if not isinstance(keyword, str):
            continue

        keyword = keyword.strip()[:100]

        if not keyword:
            continue

        print("\nSearching:", keyword)

        try:
            videos = search_videos(
                keyword,
                per_page=3,
            )

            for video in videos:
                video_id = video.get("id")

                if video_id in used_ids:
                    continue

                if not video.get("videos", {}).get("small", {}).get("url"):
                    continue

                path = download_video(
                    video,
                    quality="small",
                )

                used_ids.add(video_id)

                downloaded.append({
                    "keyword": keyword,
                    "video_id": video_id,
                    "source": video.get("pageURL"),
                    "file": str(path),
                })

                print("Downloaded:", path.name)
                break

        except (MaterialError, ValueError) as error:
            print("Skipped keyword:", error)

    output_dir = ROOT / "storage" / "tasks" / "step7_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "subject": payload["subject"],
        "script": script,
        "keywords": keywords,
        "videos": downloaded,
    }

    manifest_path = output_dir / "manifest.json"

    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print("\n=== TEST RESULT ===")
    print("Downloaded videos:", len(downloaded))
    print("Manifest:", manifest_path)

    if downloaded:
        print("SUCCESS: Integrated workflow completed.")
    else:
        print("No matching videos downloaded.")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, ValueError) as error:
        print("TEST FAILED:", error)
        raise SystemExit(1)
