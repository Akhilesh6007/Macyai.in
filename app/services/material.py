
"""
Macy AI - Pixabay Video Material Service
Search and download royalty-free stock footage.
"""

import hashlib
import json
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import dotenv_values


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / ".env"
CACHE_DIR = ROOT / "storage" / "cache_pixabay"
VIDEO_DIR = ROOT / "storage" / "pixabay_videos"

API_URL = "https://pixabay.com/api/videos/"
CACHE_SECONDS = 24 * 60 * 60


class MaterialError(Exception):
    pass


def get_api_key():
    key = (dotenv_values(CONFIG).get("PIXABAY_API_KEY") or "").strip()

    if not key or key.startswith("YOUR_"):
        raise MaterialError("Configure PIXABAY_API_KEY in .env")

    return key


def search_videos(keyword, per_page=3):
    """Search Pixabay and cache the result for 24 hours."""

    keyword = keyword.strip()

    if not keyword or len(keyword) > 100:
        raise ValueError("Keyword must be 1-100 characters.")

    if not 3 <= per_page <= 200:
        raise ValueError("per_page must be between 3 and 200.")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache_id = hashlib.sha256(
        f"{keyword.lower()}:{per_page}".encode()
    ).hexdigest()

    cache_file = CACHE_DIR / f"{cache_id}.json"

    if cache_file.exists():
        if time.time() - cache_file.stat().st_mtime < CACHE_SECONDS:
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass

    try:
        response = requests.get(
            API_URL,
            params={
                "key": get_api_key(),
                "q": keyword,
                "per_page": per_page,
                "safesearch": "true",
            },
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

    except requests.RequestException as error:
        status = getattr(error.response, "status_code", None)
        raise MaterialError(
            f"Pixabay API request failed. HTTP status: {status}"
        ) from error

    except ValueError as error:
        raise MaterialError("Invalid Pixabay JSON response") from error

    videos = data.get("hits", [])

    cache_file.write_text(
        json.dumps(videos, indent=2),
        encoding="utf-8",
    )

    return videos


def download_video(video, quality="small", max_mb=50):
    """Download one Pixabay MP4 to local storage."""

    video_id = video.get("id")
    video_info = video.get("videos", {}).get(quality, {})
    video_url = video_info.get("url", "")

    if type(video_id) is not int or not video_url:
        raise MaterialError("Invalid video ID or download URL")

    parsed = urlparse(video_url)

    if (
        parsed.scheme != "https"
        or parsed.hostname != "cdn.pixabay.com"
    ):
        raise MaterialError("Untrusted video download URL")

    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    output_file = VIDEO_DIR / f"pixabay_{video_id}_{quality}.mp4"
    temp_file = output_file.with_suffix(".part")

    if output_file.exists() and output_file.stat().st_size > 0:
        return output_file

    max_bytes = max_mb * 1024 * 1024
    total = 0

    try:
        with requests.get(
            video_url,
            stream=True,
            timeout=(10, 60),
            allow_redirects=False,
        ) as response:

            if response.is_redirect:
                raise MaterialError("Unexpected video URL redirect")

            response.raise_for_status()

            with temp_file.open("wb") as file:
                for chunk in response.iter_content(1024 * 1024):
                    if not chunk:
                        continue

                    total += len(chunk)

                    if total > max_bytes:
                        raise MaterialError("Video exceeds size limit")

                    file.write(chunk)

        if total < 12:
            raise MaterialError("Downloaded file is too small")

        with temp_file.open("rb") as file:
            header = file.read(12)

        if header[4:8] != b"ftyp":
            raise MaterialError("Downloaded file is not a valid MP4 header")

        temp_file.replace(output_file)
        return output_file

    except requests.RequestException as error:
        status = getattr(error.response, "status_code", None)
        raise MaterialError(
            f"Video download failed. HTTP status: {status}"
        ) from error

    finally:
        if temp_file.exists():
            temp_file.unlink()
