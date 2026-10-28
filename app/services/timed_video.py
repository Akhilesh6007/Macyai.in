
"""
Macy AI - Timed Scene Video Renderer

Renders scenes using narration-aligned timestamps.

Preserves:
- English/Hindi narration
- SRT subtitles
- Portrait video
- H.264 MP4 export

Does not modify the original video.py.
"""

import json
import math
import uuid
import re
import shutil
import subprocess
from pathlib import Path

import imageio_ffmpeg


class TimedRenderError(Exception):
    pass


def get_audio_duration(audio_path, ffmpeg):
    """Read audio duration from FFmpeg metadata."""

    result = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-i",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    match = re.search(
        r"Duration:\s*(\d+):(\d+):([\d.]+)",
        result.stderr,
    )

    if not match:
        raise TimedRenderError(
            "Could not determine audio duration."
        )

    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = float(match.group(3))

    return hours * 3600 + minutes * 60 + seconds


def render_timed_video(
    timed_scene_plan,
    audio_path,
    subtitle_path,
    output_path,
    width=540,
    height=960,
    fps=20,
):
    """
    Render video scenes at planned timestamps.

    Scene changes are aligned to the nearest frame.
    The last scene covers the remaining audio.
    """

    if isinstance(timed_scene_plan, (str, Path)):
        timed_scene_plan = json.loads(
            Path(timed_scene_plan).read_text(
                encoding="utf-8"
            )
        )

    scenes = timed_scene_plan.get("scenes", [])

    if not scenes:
        raise TimedRenderError(
            "Timed scene plan contains no scenes."
        )

    if (not all(isinstance(v, int) for v in (width, height, fps))
            or width <= 0 or height <= 0 or fps <= 0
            or width % 2 or height % 2):
        raise ValueError("Invalid output settings.")

    audio_path = Path(audio_path).resolve()
    subtitle_path = Path(subtitle_path).resolve()
    output_path = Path(output_path).resolve()

    if output_path.exists():
        raise FileExistsError("Refusing to overwrite an existing video")

    for file in (audio_path, subtitle_path):
        if not file.is_file():
            raise FileNotFoundError(file)

    video_paths = []

    for scene in scenes:
        video_path = Path(
            scene["video_path"]
        ).resolve()

        if not video_path.is_file():
            raise FileNotFoundError(video_path)

        video_paths.append(video_path)

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    audio_duration = get_audio_duration(
        audio_path, ffmpeg
    )

    if audio_duration <= 0:
        raise TimedRenderError(
            "Audio duration must be positive."
        )

    # Validate continuous scene timing.
    previous_end = 0.0

    for scene in scenes:
        start = float(scene["start_seconds"])
        end = float(scene["end_seconds"])

        if not math.isfinite(start) or not math.isfinite(end) or end <= start:
            raise TimedRenderError(
                "Scene has invalid duration."
            )

        if abs(start - previous_end) > 0.02:
            raise TimedRenderError(
                "Scene timeline has a gap or overlap."
            )

        previous_end = end

    if previous_end > audio_duration + 0.25:
        raise TimedRenderError(
            "Scene plan extends beyond audio duration."
        )

    # Convert scene boundaries into frame counts.
    # This prevents cumulative rounding drift.
    total_frames = round(audio_duration * fps)

    boundaries = [0]

    for scene in scenes[:-1]:
        boundary = round(
            float(scene["end_seconds"]) * fps
        )
        boundaries.append(boundary)

    boundaries.append(total_frames)

    frame_counts = [
        boundaries[i + 1] - boundaries[i]
        for i in range(len(scenes))
    ]

    if any(count <= 0 for count in frame_counts):
        raise TimedRenderError(
            "At least one scene is shorter than one frame."
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Use a relative subtitle filename to avoid
    # Windows drive-letter escaping issues.
    local_subtitle = (
        output_path.parent / f"timed_subtitles_{uuid.uuid4().hex}.srt"
    )

    if subtitle_path != local_subtitle:
        shutil.copyfile(
            subtitle_path,
            local_subtitle,
        )

    command = [
        ffmpeg,
        "-n",
        "-hide_banner",
        "-loglevel",
        "error",
    ]

    # Each clip loops only as long as needed.
    for path, count in zip(
        video_paths,
        frame_counts,
    ):
        required_seconds = count / fps

        command.extend([
            "-stream_loop", "-1",
            "-t", f"{required_seconds + 1:.3f}",
            "-i", str(path),
        ])

    command.extend([
        "-i", str(audio_path),
    ])

    filters = []

    for index, frame_count in enumerate(
        frame_counts
    ):
        filters.append(
            f"[{index}:v]"
            f"scale={width}:{height}:"
            "force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            "setsar=1,"
            f"fps={fps},"
            f"trim=end_frame={frame_count},"
            "setpts=PTS-STARTPTS,"
            "format=yuv420p"
            f"[v{index}]"
        )

    labels = "".join(
        f"[v{i}]" for i in range(len(scenes))
    )

    filters.append(
        f"{labels}"
        f"concat=n={len(scenes)}:v=1:a=0"
        "[merged]"
    )

    subtitle_style = (
        "FontName=Arial,"
        "FontSize=18,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "Outline=2,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=55"
    )

    filters.append(
        "[merged]"
        f"subtitles={local_subtitle.name}:"
        f"force_style='{subtitle_style}'"
        "[finalv]"
    )

    audio_index = len(video_paths)

    command.extend([
        "-filter_complex", ";".join(filters),
        "-map", "[finalv]",
        "-map", f"{audio_index}:a:0",
        "-c:v", "libx264",
        "-preset", "superfast",
        "-crf", "26",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "160k",
        "-t", f"{audio_duration:.3f}",
        "-movflags", "+faststart",
        str(output_path),
    ])

    print("=== MACY AI TIMED RENDER ===")
    print("Scenes:", len(scenes))
    print("Audio duration:", audio_duration)
    print("Resolution:", f"{width}x{height}")

    for index, count in enumerate(
        frame_counts, start=1
    ):
        print(
            f"Scene {index}: "
            f"{count / fps:.2f} seconds"
        )

    try:
        result = subprocess.run(
            command,
            cwd=str(output_path.parent),
            capture_output=True,
            text=True,
            timeout=600,
        )

    except subprocess.TimeoutExpired as error:
        raise TimedRenderError(
            "FFmpeg rendering timed out."
        ) from error
    finally:
        if subtitle_path != local_subtitle:
            local_subtitle.unlink(missing_ok=True)

    if result.returncode != 0:
        raise TimedRenderError(
            "FFmpeg failed:\n"
            + result.stderr[-4000:]
        )

    if (
        not output_path.is_file()
        or output_path.stat().st_size == 0
    ):
        raise TimedRenderError(
            "Final MP4 was not created."
        )

    return {
        "video_path": str(output_path),
        "duration": audio_duration,
        "resolution": f"{width}x{height}",
        "clip_count": len(scenes),
        "scene_count": len(scenes),
        "timed_scenes": True,
    }
