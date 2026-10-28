
"""
Macy AI - Step 10 Video Rendering Service

Combines Pixabay clips, Edge TTS narration
and synchronized SRT subtitles using FFmpeg.
"""

import re
import shutil
import subprocess
from pathlib import Path

import imageio_ffmpeg


class VideoRenderError(Exception):
    """Raised when video rendering fails."""


def get_ffmpeg():
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except RuntimeError as error:
        raise VideoRenderError(
            "FFmpeg not found. Install imageio-ffmpeg."
        ) from error


def check_ffmpeg():
    """Check required video-rendering capabilities."""

    ffmpeg = get_ffmpeg()

    filters = subprocess.run(
        [ffmpeg, "-hide_banner", "-filters"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    encoders = subprocess.run(
        [ffmpeg, "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if filters.returncode != 0 or encoders.returncode != 0:
        raise VideoRenderError(
            "Unable to inspect FFmpeg capabilities."
        )

    if not re.search(r"\bsubtitles\b", filters.stdout):
        raise VideoRenderError(
            "This FFmpeg build lacks the subtitles filter. "
            "Use a build with libass support."
        )

    if not re.search(r"\blibx264\b", encoders.stdout):
        raise VideoRenderError(
            "This FFmpeg build lacks libx264 encoding."
        )

    return ffmpeg


def get_media_duration(media_path):
    """Read duration using FFmpeg's input metadata."""

    ffmpeg = get_ffmpeg()

    result = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-i",
            str(media_path),
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
        raise VideoRenderError(
            f"Could not determine duration: {media_path}"
        )

    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = float(match.group(3))

    return hours * 3600 + minutes * 60 + seconds


def render_video(
    video_paths,
    audio_path,
    subtitle_path,
    output_path,
    width=720,
    height=1280,
    fps=24,
):
    """
    Render a portrait video containing:
    - Sequential stock clips
    - Narration
    - Burned-in subtitles

    Video clips are looped when necessary.
    """

    video_paths = [Path(p).resolve() for p in video_paths]
    audio_path = Path(audio_path).resolve()
    subtitle_path = Path(subtitle_path).resolve()
    output_path = Path(output_path).resolve()

    if not video_paths:
        raise VideoRenderError("No video clips provided.")

    for path in [*video_paths, audio_path, subtitle_path]:
        if not path.is_file():
            raise FileNotFoundError(path)

    if width <= 0 or height <= 0 or fps <= 0:
        raise ValueError("Invalid video dimensions or FPS.")

    ffmpeg = check_ffmpeg()

    audio_duration = get_media_duration(audio_path)

    if audio_duration <= 0:
        raise VideoRenderError("Invalid audio duration.")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Staging subtitle with a simple relative filename
    # avoids Windows drive-letter escaping issues.
    local_subtitle = output_path.parent / "subtitle.srt"

    if subtitle_path != local_subtitle:
        shutil.copyfile(subtitle_path, local_subtitle)

    clip_duration = (
        audio_duration + 1.0
    ) / len(video_paths)

    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
    ]

    # Loop source videos in case they are too short.
    for path in video_paths:
        command.extend([
            "-stream_loop", "-1",
            "-i", str(path),
        ])

    # Add the narration as the last input.
    command.extend([
        "-i", str(audio_path),
    ])

    filters = []

    for index in range(len(video_paths)):
        filters.append(
            f"[{index}:v]"
            f"scale={width}:{height}:"
            "force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            "setsar=1,"
            f"fps={fps},"
            f"trim=duration={clip_duration:.3f},"
            "setpts=PTS-STARTPTS"
            f"[v{index}]"
        )

    clip_labels = "".join(
        f"[v{i}]" for i in range(len(video_paths))
    )

    subtitle_style = (
        "FontName=Arial,"
        "FontSize=18,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "Outline=2,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=75"
    )

    filters.append(
        f"{clip_labels}"
        f"concat=n={len(video_paths)}:v=1:a=0,"
        f"subtitles=subtitle.srt:"
        f"force_style='{subtitle_style}'"
        "[finalv]"
    )

    filter_complex = ";".join(filters)
    audio_index = len(video_paths)

    command.extend([
        "-filter_complex", filter_complex,
        "-map", "[finalv]",
        "-map", f"{audio_index}:a:0",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "26",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "160k",
        "-t", f"{audio_duration:.3f}",
        "-movflags", "+faststart",
        str(output_path),
    ])

    print("Rendering Macy AI video...")
    print("Audio duration:", round(audio_duration, 2), "seconds")
    print("Clips:", len(video_paths))
    print("Output:", output_path)

    try:
        result = subprocess.run(
            command,
            cwd=str(output_path.parent),
            capture_output=True,
            text=True,
            timeout=600,
        )

    except subprocess.TimeoutExpired as error:
        raise VideoRenderError(
            "FFmpeg rendering timed out."
        ) from error

    if result.returncode != 0:
        raise VideoRenderError(
            "FFmpeg failed:\n" + result.stderr[-4000:]
        )

    if not output_path.exists():
        raise VideoRenderError(
            "Final video was not created."
        )

    if output_path.stat().st_size == 0:
        raise VideoRenderError(
            "Final video is empty."
        )

    return {
        "video_path": str(output_path),
        "duration": audio_duration,
        "resolution": f"{width}x{height}",
        "clip_count": len(video_paths),
    }
