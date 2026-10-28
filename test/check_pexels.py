
"""
Macy AI - Step 7 Pexels Test
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.material import (
    search_pexels_videos,
    download_pexels_video,
    PexelsError,
)


def main():
    print("=== MACY AI PEXELS TEST ===")

    keyword = "robot working in factory"

    print("\nSearching:", keyword)

    try:
        videos = search_pexels_videos(
            query=keyword,
            orientation="portrait",
            per_page=3,
        )

        print("Videos found:", len(videos))

        for video in videos:
            print(
                "ID:", video["id"],
                "Duration:", video["duration"],
                "Source:", video["pexels_url"],
            )

        if not videos:
            print("No footage found for this keyword.")
            return

        print("\nDownloading first video...")

        saved = download_pexels_video(
            videos[0],
            ROOT / "storage" / "pexels_test",
        )

        print("\nSUCCESS")
        print("Saved video:", saved)

    except (PexelsError, ValueError) as error:
        print("\nTEST FAILED:", error)


if __name__ == "__main__":
    main()
