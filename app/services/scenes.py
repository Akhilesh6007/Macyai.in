
"""
Macy AI - Scene Matching Service

Divides narration into scene sections and
matches each section to downloaded footage.

No external AI or API calls are required.
"""

import re


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at",
    "be", "by", "for", "from", "in",
    "into", "is", "it", "of", "on",
    "or", "our", "that", "the", "their",
    "this", "to", "was", "we",
    "will", "with", "you", "your",
}


def extract_terms(text: str) -> set[str]:
    """Extract words for keyword matching."""

    words = re.findall(
        r"[^\W_]+",
        text.lower(),
        flags=re.UNICODE,
    )

    return {
        word for word in words
        if len(word) > 2
        and word not in STOP_WORDS
    }


def divide_narration(
    script: str,
    scene_count: int,
) -> list[str]:
    """
    Divide narration into approximately equal
    sections, preferring nearby sentence endings.
    """

    words = script.split()

    if not words:
        raise ValueError("Narration is empty")

    scene_count = min(
        max(1, scene_count),
        len(words),
    )

    sections = []
    cursor = 0

    for index in range(scene_count):
        remaining_scenes = scene_count - index
        remaining_words = len(words) - cursor

        target_size = (
            remaining_words + remaining_scenes - 1
        ) // remaining_scenes

        target_end = cursor + target_size

        if index == scene_count - 1:
            end = len(words)

        else:
            lower = max(
                cursor + 1,
                target_end - 3,
            )

            upper = min(
                len(words) - (remaining_scenes - 1),
                target_end + 3,
            )

            sentence_endings = [
                position
                for position in range(lower, upper + 1)
                if words[position - 1].endswith(
                    (".", "!", "?", "।", "॥")
                )
            ]

            if sentence_endings:
                end = min(
                    sentence_endings,
                    key=lambda pos: abs(
                        pos - target_end
                    ),
                )
            else:
                end = target_end

        sections.append(
            " ".join(words[cursor:end])
        )

        cursor = end

    return sections


def build_scene_plan(
    script: str,
    downloaded: list[dict],
) -> dict:
    """
    Match narration sections with different
    downloaded video clips.

    Each clip is used at most once in the plan.
    """

    if not isinstance(script, str) or not script.strip():
        raise ValueError(
            "A non-empty video script is required"
        )

    available_clips = []
    seen_ids = set()

    for item in downloaded:

        if not isinstance(item, dict):
            continue

        if not item.get("file"):
            continue

        clip_id = str(
            item.get("video_id") or item["file"]
        )

        if clip_id in seen_ids:
            continue

        seen_ids.add(clip_id)
        available_clips.append(item)

    if not available_clips:
        raise ValueError(
            "No downloaded footage available"
        )

    narration_sections = divide_narration(
        script,
        len(available_clips),
    )

    remaining = available_clips.copy()
    scenes = []

    for index, section in enumerate(
        narration_sections,
        start=1,
    ):
        section_terms = extract_terms(section)

        def match_score(clip):
            keyword_terms = extract_terms(
                str(clip.get("keyword", ""))
            )

            return len(
                section_terms & keyword_terms
            )

        # Select the highest keyword overlap.
        # Original search order breaks ties.
        best_clip = max(
            remaining,
            key=match_score,
        )

        score = match_score(best_clip)

        remaining.remove(best_clip)

        scenes.append({
            "scene": index,
            "text": section,
            "keyword": str(
                best_clip.get("keyword", "")
            ),
            "video_id": best_clip.get("video_id"),
            "video_path": str(best_clip["file"]),
            "match_terms": score,
        })

    return {
        "method": "keyword_overlap_v1",
        "scene_count": len(scenes),
        "scenes": scenes,
        "note": (
            "Lexical matching only. Exact scene "
            "timing is not yet synchronized."
        ),
    }
