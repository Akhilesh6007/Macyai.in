
"""
Macy AI - Background Video Job Service

Pipeline:
Pixabay footage -> Edge TTS narration ->
Subtitles -> FFmpeg rendering -> Completed video

Features:
- English and Hindi voice selection
- Up to 4 unique Pixabay clips
- Task progress tracking
- Processing time measurements
- Footage metadata
- Detailed error logging
"""

import json
import logging
import time
import uuid
import traceback

from datetime import datetime, timezone
from pathlib import Path
from app.services.scenes import build_scene_plan
from app.services.scene_timing import build_timed_scene_plan
from app.services.timed_video import render_timed_video
from app.services.material import (
    search_videos,
    download_video,
    MaterialError,
)

from app.services.voice import generate_voiceover_sync
from app.services.subtitle import generate_subtitles
from app.services.video import render_video


# ==============================================
# CONFIGURATION
# ==============================================

ROOT = Path(__file__).resolve().parents[2]
TASKS_DIR = ROOT / "storage" / "tasks"

logger = logging.getLogger(__name__)

MAX_VIDEO_CLIPS = 4
MAX_SEARCH_KEYWORDS = 8

VIDEO_WIDTH = 540
VIDEO_HEIGHT = 960
VIDEO_FPS = 20


# ==============================================
# LANGUAGE-BASED VOICE SELECTION
# ==============================================

def select_voice_for_script(script: str) -> str:
    """
    Select a voice for predominantly
    English or Hindi narration.
    """

    letters = [
        char for char in script
        if char.isalpha()
    ]

    if not letters:
        return "en-AU-NatashaNeural"

    hindi_letters = sum(
        "\u0900" <= char <= "\u097F"
        for char in letters
    )

    hindi_ratio = hindi_letters / len(letters)

    if hindi_ratio >= 0.30:
        return "hi-IN-SwaraNeural"

    return "en-AU-NatashaNeural"


# ==============================================
# TASK STATUS MANAGEMENT
# ==============================================

def update_job_status(task_id, **changes):
    """
    Update the task status JSON file.
    """

    task_dir = TASKS_DIR / task_id
    task_file = task_dir / "task.json"

    task_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    if task_file.exists():
        status = json.loads(
            task_file.read_text(
                encoding="utf-8"
            )
        )
    else:
        status = {
            "task_id": task_id
        }

    status.update(changes)

    status["updated_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    temporary = task_dir / "task.json.tmp"

    temporary.write_text(
        json.dumps(
            status,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    temporary.replace(task_file)

    return status


# ==============================================
# CREATE VIDEO GENERATION JOB
# ==============================================

def create_video_job(subject, script, keywords):
    """
    Create a new video task and manifest.
    """

    task_id = uuid.uuid4().hex[:12]

    task_dir = TASKS_DIR / task_id

    task_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    manifest = {
        "subject": subject,
        "script": script,
        "keywords": keywords,
        "videos": [],
    }

    manifest_path = task_dir / "manifest.json"

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    update_job_status(
        task_id,
        state="queued",
        stage="queued",
        subject=subject,
        output=None,
        error=None,
        voice=None,
        stage_seconds={},
    )

    logger.info(
        "Created Macy AI video job: %s",
        task_id,
    )

    return task_id


# ==============================================
# MAIN VIDEO GENERATION PIPELINE
# ==============================================

def run_video_job(task_id):
    """
    Execute the full Macy AI video pipeline.
    """

    task_dir = TASKS_DIR / task_id
    manifest_path = task_dir / "manifest.json"

    # Completed jobs are immutable; retries must create a new task.
    status_file = task_dir / "task.json"
    if status_file.is_file():
        previous = json.loads(status_file.read_text(encoding="utf-8"))
        if previous.get("state") == "completed":
            return previous.get("output")

    stage = "starting"
    timings = {}
    selected_voice = None

    try:

        # ======================================
        # LOAD MANIFEST
        # ======================================

        manifest = json.loads(
            manifest_path.read_text(
                encoding="utf-8"
            )
        )

        script = manifest["script"].strip()
        keywords = manifest["keywords"]

        if not script:
            raise ValueError(
                "Video script cannot be empty."
            )

        if not keywords:
            raise ValueError(
                "Video keywords cannot be empty."
            )

        logger.info(
            "Starting Macy AI video job: %s",
            task_id,
        )

        # ======================================
        # STAGE 1: PIXABAY FOOTAGE
        # ======================================

        stage = "materials"
        stage_start = time.perf_counter()

        update_job_status(
            task_id,
            state="processing",
            stage=stage,
        )

        downloaded = []
        used_ids = set()

        for keyword in keywords[:MAX_SEARCH_KEYWORDS]:

            if len(downloaded) >= MAX_VIDEO_CLIPS:
                break

            keyword = str(keyword).strip()[:100]

            if not keyword:
                continue

            logger.info(
                "Searching Pixabay: %s",
                keyword,
            )

            try:

                videos = search_videos(
                    keyword,
                    per_page=3,
                )

                for video in videos:

                    video_id = video.get("id")

                    if not video_id:
                        continue

                    if video_id in used_ids:
                        continue

                    video_url = (
                        video.get("videos", {})
                        .get("small", {})
                        .get("url")
                    )

                    if not video_url:
                        continue

                    try:

                        path = download_video(
                            video,
                            quality="small",
                        )

                    except MaterialError:

                        logger.warning(
                            "Pixabay download failed "
                            "for video %s",
                            video_id,
                        )

                        continue

                    used_ids.add(video_id)

                    downloaded.append({
                        "keyword": keyword,
                        "video_id": video_id,
                        "source": video.get("pageURL"),
                        "file": str(path),
                    })

                    logger.info(
                        "Downloaded Pixabay video: %s",
                        video_id,
                    )

                    break

            except MaterialError:

                logger.warning(
                    "Pixabay search failed for: %s",
                    keyword,
                )

        if not downloaded:

            raise RuntimeError(
                "No video footage could be downloaded."
            )

        # Save downloaded footage to manifest.
        manifest["videos"] = downloaded

        manifest_path.write_text(
            json.dumps(
                manifest,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        timings["materials"] = round(
            time.perf_counter() - stage_start,
            2,
        )

        logger.info(
            "Materials completed: %d clips in %.2fs",
            len(downloaded),
            timings["materials"],
        )

        # ======================================
        # STAGE 2: VOICEOVER GENERATION
        # ======================================

        stage = "voiceover"
        stage_start = time.perf_counter()

        selected_voice = select_voice_for_script(
            script
        )

        logger.info(
            "Selected voice: %s",
            selected_voice,
        )

        update_job_status(
            task_id,
            state="processing",
            stage=stage,
            voice=selected_voice,
            stage_seconds=timings,
        )

        audio_path = task_dir / "audio.mp3"

        voice_result = generate_voiceover_sync(
            script=script,
            output_path=audio_path,
            voice=selected_voice,
        )

        if not audio_path.is_file():

            raise RuntimeError(
                "Voiceover audio was not generated."
            )

        if audio_path.stat().st_size == 0:

            raise RuntimeError(
                "Generated voiceover audio is empty."
            )

        metadata_path = voice_result["metadata_path"]

        if not Path(metadata_path).is_file():

            raise RuntimeError(
                "Voiceover timing metadata is missing."
            )

        timings["voiceover"] = round(
            time.perf_counter() - stage_start,
            2,
        )

        logger.info(
            "Voiceover completed in %.2fs",
            timings["voiceover"],
        )

        # ======================================
        # STAGE 3: SUBTITLE GENERATION
        # ======================================

        stage = "subtitles"
        stage_start = time.perf_counter()

        update_job_status(
            task_id,
            state="processing",
            stage=stage,
            stage_seconds=timings,
        )

        subtitle_path = task_dir / "subtitle.srt"

        generate_subtitles(
            metadata_path=metadata_path,
            output_path=subtitle_path,
            max_words=7,
        )

        if not subtitle_path.is_file():

            raise RuntimeError(
                "Subtitle file was not generated."
            )

        if subtitle_path.stat().st_size == 0:

            raise RuntimeError(
                "Generated subtitle file is empty."
            )

        timings["subtitles"] = round(
            time.perf_counter() - stage_start,
            2,
        )

        logger.info(
            "Subtitles completed in %.2fs",
            timings["subtitles"],
        )

        # ======================================
        # STAGE 4: FFMPEG VIDEO RENDERING
        # ======================================


        
        # ======================================
        # SCENE MATCHING
        # ======================================

        stage = "scene_matching"
        scene_start = time.perf_counter()

        update_job_status(
            task_id,
            state="processing",
            stage=stage,
            stage_seconds=timings,
        )

        scene_plan = build_scene_plan(
            script=script,
            downloaded=downloaded,
        )

        scene_plan_path = (
            task_dir / "scene_plan.json"
        )

        scene_plan_path.write_text(
            json.dumps(
                scene_plan,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        timings["scene_matching"] = round(
            time.perf_counter() - scene_start,
            2,
        )

        logger.info(
            "Task %s: planned %d scenes",
            task_id,
            scene_plan["scene_count"],
        )


        # ======================================
        # SCENE TIMING
        # ======================================

        stage = "scene_timing"
        stage_start = time.perf_counter()

        update_job_status(
            task_id,
            state="processing",
            stage=stage,
            stage_seconds=timings,
        )

        scene_plan_path = (
            task_dir / "scene_plan.json"
        )

        if scene_plan_path.is_file():
            scene_plan = json.loads(
                scene_plan_path.read_text(
                    encoding="utf-8"
                )
            )
        else:
            scene_plan = build_scene_plan(
                script=script,
                downloaded=downloaded,
            )

            scene_plan_path.write_text(
                json.dumps(
                    scene_plan,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        timed_plan = build_timed_scene_plan(
            scene_plan,
            subtitle_path,
        )

        timed_plan_path = (
            task_dir / "timed_scene_plan.json"
        )

        timed_plan_path.write_text(
            json.dumps(
                timed_plan,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        timings["scene_timing"] = round(
            time.perf_counter() - stage_start,
            2,
        )

        stage = "rendering"

        update_job_status(
            task_id,
            state="processing",
            stage=stage,
            stage_seconds=timings,
        )

        output_path = task_dir / "final_video.mp4"

        # Start timer BEFORE rendering.
        render_start = time.perf_counter()

        
        result = render_timed_video(
            timed_scene_plan=timed_plan,
            audio_path=audio_path,
            subtitle_path=subtitle_path,
            output_path=output_path,
            width=VIDEO_WIDTH,
            height=VIDEO_HEIGHT,
            fps=VIDEO_FPS,
        )


        timings["rendering"] = round(
            time.perf_counter() - render_start,
            2,
        )

        if not output_path.is_file():

            raise RuntimeError(
                "Final MP4 was not generated."
            )

        if output_path.stat().st_size == 0:

            raise RuntimeError(
                "Generated MP4 is empty."
            )

        if not isinstance(result, dict):

            raise RuntimeError(
                "Video renderer returned "
                "an invalid result."
            )

        logger.info(
            "FFmpeg rendering completed in %.2fs",
            timings["rendering"],
        )

        # ======================================
        # STAGE 5: OUTPUT METADATA
        # ======================================

        result["render_seconds"] = timings["rendering"]

        result["clip_count"] = len(downloaded)
        result["scene_count"] = scene_plan["scene_count"]
        result["scene_plan"] = "scene_plan.json"

        result["video_path"] = str(output_path)

        result["footage"] = [
            {
                "video_id": item["video_id"],
                "keyword": item["keyword"],
                "source": item["source"],
            }
            for item in downloaded
        ]

        total_processing_time = round(
            sum(timings.values()),
            2,
        )

        result["processing_seconds"] = (
            total_processing_time
        )

        # ======================================
        # STAGE 6: MARK JOB AS COMPLETED
        # ======================================

        update_job_status(
            task_id,
            state="completed",
            stage="finished",
            output=result,
            error=None,
            voice=selected_voice,
            stage_seconds=timings,
        )

        logger.info(
            "Macy AI task completed: %s",
            task_id,
        )

        logger.info(
            "Total processing time: %.2fs",
            total_processing_time,
        )

        return result

    # ==========================================
    # ERROR HANDLING
    # ==========================================

    except Exception as error:

        full_error = traceback.format_exc()

        logger.error(
            "Macy AI task %s failed during %s\n%s",
            task_id,
            stage,
            full_error,
        )

        # Save the full traceback for debugging.
        error_log = task_dir / "error_traceback.txt"

        try:
            error_log.write_text(
                full_error,
                encoding="utf-8",
            )

        except OSError:
            logger.exception(
                "Unable to write traceback for task %s",
                task_id,
            )

        update_job_status(
            task_id,
            state="failed",
            stage=stage,
            voice=selected_voice,
            stage_seconds=timings,
            error=(
                f"Task failed during {stage}. "
                f"Error type: {type(error).__name__}. "
                "Check error_traceback.txt for details."
            ),
        )

        return None
