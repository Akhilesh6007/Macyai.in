
"""
Macy AI - Narration-Based Scene Timing

Aligns scene boundaries with existing
subtitle (SRT) timestamps.

Does not generate or render videos.
"""

import re
from pathlib import Path


TIME_PATTERN = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)


def timestamp_seconds(value):
    """Convert an SRT timestamp into seconds."""

    match = TIME_PATTERN.search(value)

    if not match:
        raise ValueError(
            f"Invalid timestamp: {value}"
        )

    hours, minutes, seconds, millis = map(
        int, match.groups()
    )

    return (
        hours * 3600
        + minutes * 60
        + seconds
        + millis / 1000
    )


def read_srt(subtitle_path):
    """Read subtitle text and real timestamps."""

    content = Path(subtitle_path).read_text(
        encoding="utf-8-sig"
    )

    content = content.replace(
        "\r\n", "\n"
    ).replace("\r", "\n")

    subtitles = []

    for block in re.split(
        r"\n\s*\n", content.strip()
    ):
        lines = [
            line.strip()
            for line in block.splitlines()
            if line.strip()
        ]

        time_index = next(
            (
                i for i, line in enumerate(lines)
                if "-->" in line
            ),
            None,
        )

        if time_index is None:
            continue

        left, right = lines[time_index].split(
            "-->", 1
        )

        start = timestamp_seconds(left)
        end = timestamp_seconds(right)

        if end <= start:
            raise ValueError(
                "Invalid subtitle duration"
            )

        if subtitles and start < subtitles[-1]["start"]:
            raise ValueError(
                "Subtitle timestamps are not ordered"
            )

        subtitles.append({
            "start": start,
            "end": end,
            "text": " ".join(
                lines[time_index + 1:]
            ),
        })

    if not subtitles:
        raise ValueError(
            "No valid subtitle entries found"
        )

    return subtitles


def build_timed_scene_plan(scene_plan, subtitle_path):
    """
    Align scene changes with subtitle boundaries.

    Each scene receives a continuous time range.
    Boundaries are chosen by approximate
    narration word proportions.
    """

    scenes = scene_plan.get("scenes", [])

    if not scenes:
        raise ValueError("Scene plan is empty")

    subtitles = read_srt(subtitle_path)

    if len(subtitles) < len(scenes):
        raise ValueError(
            "Not enough subtitle segments for "
            "the planned number of scenes"
        )

    scene_weights = [
        max(
            1,
            len(str(scene.get("text", "")).split())
        )
        for scene in scenes
    ]

    subtitle_weights = [
        max(
            1,
            len(subtitle["text"].split())
        )
        for subtitle in subtitles
    ]

    total_scene_words = sum(scene_weights)
    total_subtitle_words = sum(subtitle_weights)

    subtitle_prefix = [0]

    for count in subtitle_weights:
        subtitle_prefix.append(
            subtitle_prefix[-1] + count
        )

    cuts = []
    cumulative_scene_words = 0

    for index in range(1, len(scenes)):
        cumulative_scene_words += scene_weights[
            index - 1
        ]

        target = (
            cumulative_scene_words
            / total_scene_words
            * total_subtitle_words
        )

        lower = (cuts[-1] if cuts else 0) + 1
        upper = len(subtitles) - (
            len(scenes) - index
        )

        best_cut = min(
            range(lower, upper + 1),
            key=lambda position: abs(
                subtitle_prefix[position] - target
            ),
        )

        cuts.append(best_cut)

    boundaries = (
        [0.0]
        + [
            subtitles[index]["start"]
            for index in cuts
        ]
        + [subtitles[-1]["end"]]
    )

    timed_scenes = []

    for index, scene in enumerate(scenes):
        start = boundaries[index]
        end = boundaries[index + 1]

        if end <= start:
            raise ValueError(
                "Invalid scene timing boundaries"
            )

        timed_scenes.append({
            **scene,
            "start_seconds": round(start, 3),
            "end_seconds": round(end, 3),
            "duration_seconds": round(
                end - start, 3
            ),
        })

    return {
        **scene_plan,
        "timing_method": "srt_cue_boundary_v1",
        "duration_seconds": round(
            boundaries[-1], 3
        ),
        "scenes": timed_scenes,
    }
