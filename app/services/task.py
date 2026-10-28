
"""
Macy AI - Video Generation Task Pipeline
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.services.voice import generate_voiceover_sync
from app.services.subtitle import generate_subtitles
from app.services.video import render_video


ROOT = Path(__file__).resolve().parents[2]
TASKS_DIR = ROOT / "storage" / "tasks"


def save_status(task_dir, status):
    """Save task progress as JSON."""

    status["updated_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    file_path = task_dir / "task.json"

    file_path.write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )


def generate_full_video(manifest_path):
    """
    Generate a complete video from a Step 7 manifest.
    """

    manifest_path = Path(manifest_path)

    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    script = manifest.get("script", "").strip()

    if not script:
        raise ValueError("Video script is empty.")

    videos = manifest.get("videos", [])

    video_paths = [
        Path(item["file"])
        for item in videos
        if isinstance(item, dict) and item.get("file")
    ]

    if not video_paths:
        raise ValueError("No video footage available.")

    for video_path in video_paths:
        if not video_path.is_file():
            raise FileNotFoundError(video_path)

    task_id = uuid.uuid4().hex[:12]
    task_dir = TASKS_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=False)

    status = {
        "task_id": task_id,
        "state": "processing",
        "stage": "starting",
        "subject": manifest.get("subject", ""),
        "output": None,
    }

    save_status(task_dir, status)

    try:
        # 1. Generate full narration
        status["stage"] = "voiceover"
        save_status(task_dir, status)

        audio_path = task_dir / "audio.mp3"

        voice_result = generate_voiceover_sync(
            script=script,
            output_path=audio_path,
            voice="en-AU-NatashaNeural",
        )

        # 2. Generate synchronized subtitles
        status["stage"] = "subtitles"
        save_status(task_dir, status)

        subtitle_path = task_dir / "subtitle.srt"

        generate_subtitles(
            metadata_path=voice_result["metadata_path"],
            output_path=subtitle_path,
            max_words=7,
        )

        # 3. Render final MP4
        status["stage"] = "rendering"
        save_status(task_dir, status)

        output_path = task_dir / "final_video.mp4"

        render_result = render_video(
            video_paths=video_paths,
            audio_path=audio_path,
            subtitle_path=subtitle_path,
            output_path=output_path,
            width=720,
            height=1280,
            fps=24,
        )

        status["state"] = "completed"
        status["stage"] = "finished"
        status["output"] = render_result

        save_status(task_dir, status)

        return status

    except Exception as error:
        status["state"] = "failed"
        status["error"] = str(error)
        save_status(task_dir, status)
        raise
