
from pathlib import Path

import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
config = dotenv_values(ROOT / ".env")
api_key = config.get("PIXABAY_API_KEY", "")

if not api_key or api_key.startswith("YOUR_"):
    raise SystemExit("Configure PIXABAY_API_KEY in .env first.")

print("=== MACY AI PIXABAY TEST ===")

try:
    response = requests.get(
        "https://pixabay.com/api/videos/",
        params={
            "key": api_key,
            "q": "robot technology",
            "per_page": 3,
            "safesearch": "true",
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    videos = data.get("hits", [])
    print("Videos found:", len(videos))

    for video in videos:
        print("ID:", video["id"])
        print("Source:", video["pageURL"])
        print("Duration:", video.get("duration"))
        print("---")

    if videos:
        print("SUCCESS: Pixabay video search works.")

except requests.RequestException as error:
    status = getattr(error.response, "status_code", None)
    print("Pixabay request failed. HTTP status:", status)
    print("Error type:", type(error).__name__)
