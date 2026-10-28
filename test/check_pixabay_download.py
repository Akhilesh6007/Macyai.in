
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.material import (
    search_videos,
    download_video,
    MaterialError,
)


def main():
    print("=== MACY AI PIXABAY DOWNLOAD TEST ===")

    keyword = "robot technology"

    try:
        videos = search_videos(keyword)

        print("Search keyword:", keyword)
        print("Videos found:", len(videos))

        if not videos:
            print("No matching videos found.")
            return

        selected = videos[0]

        print("Selected video ID:", selected["id"])
        print("Duration:", selected.get("duration"))
        print("Source:", selected.get("pageURL"))

        print("\nDownloading MP4...")

        path = download_video(
            selected,
            quality="small",
        )

        print("\nSUCCESS: Video downloaded")
        print("File:", path)
        print("Size:", round(path.stat().st_size / 1024 / 1024, 2), "MB")

    except (MaterialError, ValueError, OSError) as error:
        print("TEST FAILED:", error)


if __name__ == "__main__":
    main()
