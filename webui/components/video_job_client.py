
"""
Macy AI - Streamlit Video Job API Client
"""

import requests

BASE_URL = "http://127.0.0.1:8081"


def submit_video(subject, script, keywords):
    """Submit a new video job to FastAPI."""

    if isinstance(keywords, str):
        keywords = [
            item.strip()
            for item in keywords.split(",")
            if item.strip()
        ]

    payload = {
        "subject": subject.strip(),
        "script": script.strip(),
        "keywords": keywords,
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/tasks/generate",
        json=payload,
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def get_video_status(task_id):
    """Retrieve the current video task status."""

    response = requests.get(
        f"{BASE_URL}/api/v1/tasks/{task_id}",
        timeout=15,
    )

    response.raise_for_status()
    return response.json()


def get_video_download_url(task_id):
    return (
        f"{BASE_URL}/api/v1/tasks/"
        f"{task_id}/download"
    )


def get_video_preview_url(task_id):
    return (
        f"{BASE_URL}/api/v1/tasks/"
        f"{task_id}/preview"
    )



def list_video_tasks():
    """Fetch video generation history from FastAPI."""

    response = requests.get(
        f"{BASE_URL}/api/v1/tasks",
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()
    tasks = data.get("tasks", [])

    if not isinstance(tasks, list):
        raise ValueError("Invalid task history response.")

    return tasks
