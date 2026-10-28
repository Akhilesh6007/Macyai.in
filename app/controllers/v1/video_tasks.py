
"""
Macy AI - Video Task Management API

Read task status, list existing tasks,
preview completed videos and download MP4s.
"""

import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from fastapi import BackgroundTasks
from pydantic import BaseModel, Field

from app.services.video_jobs import (
    create_video_job,
    run_video_job,
)

router = APIRouter(
    prefix="/api/v1/tasks",
    tags=["Video Tasks"],
)

ROOT = Path(__file__).resolve().parents[3]
TASKS_DIR = ROOT / "storage" / "tasks"


class GenerateVideoJobRequest(BaseModel):
    subject: str = Field(
        min_length=3,
        max_length=300,
    )

    script: str = Field(
        min_length=20,
        max_length=20000,
    )

    keywords: list[str] = Field(
        min_length=1,
        max_length=15,
    )


@router.post("/generate", status_code=202)
def submit_video_job(
    request: GenerateVideoJobRequest,
    background_tasks: BackgroundTasks,
):
    """Submit a video-generation job."""

    task_id = create_video_job(
        subject=request.subject,
        script=request.script,
        keywords=request.keywords,
    )

    background_tasks.add_task(
        run_video_job,
        task_id,
    )

    return {
        "task_id": task_id,
        "state": "queued",
        "status_url": f"/api/v1/tasks/{task_id}",
        "preview_url": f"/api/v1/tasks/{task_id}/preview",
        "download_url": f"/api/v1/tasks/{task_id}/download",
    }



def get_task_directory(task_id: str) -> Path:
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", task_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid task ID",
        )

    return TASKS_DIR / task_id


def read_task(task_id: str) -> dict:
    task_dir = get_task_directory(task_id)
    task_file = task_dir / "task.json"

    if not task_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    try:
        data = json.loads(
            task_file.read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        raise HTTPException(
            status_code=500,
            detail="Task metadata could not be read",
        )

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=500,
            detail="Invalid task metadata",
        )

    return data


@router.get("")
def list_tasks():
    """List previously saved video tasks."""

    tasks = []

    if TASKS_DIR.exists():
        for task_file in TASKS_DIR.glob("*/task.json"):
            try:
                data = json.loads(
                    task_file.read_text(encoding="utf-8")
                )
                if isinstance(data, dict):
                    tasks.append(data)
            except (OSError, ValueError):
                continue

    tasks.sort(
        key=lambda item: item.get("updated_at", ""),
        reverse=True,
    )

    return {
        "count": len(tasks),
        "tasks": tasks,
    }


@router.get("/{task_id}")
def get_task(task_id: str):
    """Get task status and output information."""

    return read_task(task_id)


def completed_video(task_id: str) -> Path:
    task = read_task(task_id)

    if task.get("state") != "completed":
        raise HTTPException(
            status_code=409,
            detail="Video is not completed",
        )

    video_file = (
        get_task_directory(task_id) / "final_video.mp4"
    )

    if not video_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Video file not found",
        )

    return video_file


@router.get("/{task_id}/preview")
def preview_video(task_id: str):
    """Stream completed video in the browser."""

    video_file = completed_video(task_id)

    return FileResponse(
        video_file,
        media_type="video/mp4",
        content_disposition_type="inline",
    )


@router.get("/{task_id}/download")
def download_video(task_id: str):
    """Download completed MP4 file."""

    video_file = completed_video(task_id)

    return FileResponse(
        video_file,
        media_type="video/mp4",
        filename=f"macy_ai_{task_id}.mp4",
    )
