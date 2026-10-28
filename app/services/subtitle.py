
"""
Macy AI - Automatic Subtitle Generation

Converts Edge TTS WordBoundary metadata
into synchronized SRT subtitles.
"""

import json
from pathlib import Path


TICKS_PER_SECOND = 10_000_000


def format_srt_time(seconds):
    """Convert seconds to SRT timestamp format."""
    milliseconds = max(0, round(seconds * 1000))

    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    secs, millis = divmod(remainder, 1000)

    return (
        f"{hours:02}:{minutes:02}:"
        f"{secs:02},{millis:03}"
    )


def generate_subtitles(
    metadata_path,
    output_path,
    max_words=7,
    max_duration=3.5,
):
    """
    Generate subtitles using Edge TTS word timing.
    """

    metadata_path = Path(metadata_path)
    output_path = Path(output_path)

    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Timing metadata missing: {metadata_path}"
        )

    words = []

    with metadata_path.open(
        "r", encoding="utf-8"
    ) as file:

        for line in file:
            if not line.strip():
                continue

            event = json.loads(line)

            if event.get("type") != "WordBoundary":
                continue

            text = event.get("text", "").strip()

            if not text:
                continue

            start = int(
                event.get("offset", 0)
            ) / TICKS_PER_SECOND

            duration = int(
                event.get("duration", 0)
            ) / TICKS_PER_SECOND

            words.append({
                "text": text,
                "start": start,
                "end": start + duration,
            })

    if not words:
        raise ValueError(
            "No WordBoundary timing data found."
        )

    words.sort(key=lambda item: item["start"])

    subtitles = []
    group = []

    def save_group():
        if not group:
            return

        subtitles.append({
            "start": group[0]["start"],
            "end": max(
                group[-1]["end"],
                group[0]["start"] + 0.1
            ),
            "text": " ".join(
                word["text"] for word in group
            ),
        })

    for word in words:
        if group:
            elapsed = word["end"] - group[0]["start"]

            if (
                len(group) >= max_words
                or elapsed > max_duration
            ):
                save_group()
                group = []

        group.append(word)

        if word["text"].endswith((".", "!", "?")):
            save_group()
            group = []

    save_group()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w", encoding="utf-8"
    ) as file:

        for index, subtitle in enumerate(
            subtitles, start=1
        ):
            start = format_srt_time(
                subtitle["start"]
            )
            end = format_srt_time(
                subtitle["end"]
            )

            file.write(
                f"{index}\n"
                f"{start} --> {end}\n"
                f"{subtitle['text']}\n\n"
            )

    return {
        "subtitle_path": str(output_path),
        "subtitle_count": len(subtitles),
    }
