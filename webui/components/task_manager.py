
"""
Macy AI - Video Task Manager

Displays video history, generation status,
processing times, previews and download links.

Uses Streamlit columns instead of Pandas.
"""

import requests
import streamlit as st

from components.video_job_client import (
    list_video_tasks,
    get_video_preview_url,
    get_video_download_url,
)


def render_task_manager():

    st.divider()
    st.subheader("📁 Task Manager")

    st.caption(
        "View previous videos, monitor jobs, "
        "and download completed reels."
    )

    # Button triggers a Streamlit rerun.
    st.button(
        "🔄 Refresh Task History",
        key="macy_refresh_task_history",
    )

    # ==========================================
    # 1. LOAD TASKS
    # ==========================================

    try:
        tasks = list_video_tasks()

    except (requests.RequestException, ValueError) as error:
        st.error(
            f"Could not load task history: {error}"
        )
        return

    tasks = [
        task
        for task in tasks
        if isinstance(task, dict)
        and task.get("task_id")
    ]

    if not tasks:
        st.info("No video generation history found.")
        return

    tasks.sort(
        key=lambda task: task.get("updated_at") or "",
        reverse=True,
    )

    # ==========================================
    # 2. DASHBOARD SUMMARY
    # ==========================================

    completed = sum(
        task.get("state") == "completed"
        for task in tasks
    )

    failed = sum(
        task.get("state") == "failed"
        for task in tasks
    )

    active = sum(
        task.get("state") in ("queued", "processing")
        for task in tasks
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Videos", len(tasks))
    col2.metric("Completed", completed)
    col3.metric("Processing", active)
    col4.metric("Failed", failed)

    # ==========================================
    # 3. BUILD VIDEO HISTORY
    # ==========================================

    st.markdown("#### Video History")

    history = []

    for task in tasks[:30]:

        output = task.get("output") or {}

        history.append({
            "Task ID": task["task_id"],
            "Subject": task.get("subject", ""),
            "Status": task.get("state", "unknown"),
            "Stage": task.get("stage", ""),
            "Duration (s)": round(
                output.get("duration") or 0,
                2,
            ),
            "Updated": task.get("updated_at", ""),
        })

    # ==========================================
    # 4. DISPLAY HISTORY WITHOUT PANDAS
    # ==========================================

    headers = [
        "Task ID",
        "Video Subject",
        "Status",
        "Duration",
    ]

    widths = [1.8, 3.5, 1.4, 1.2]

    header_cols = st.columns(widths)

    for col, heading in zip(header_cols, headers):
        col.markdown(f"**{heading}**")

    st.divider()

    for item in history[:20]:

        cols = st.columns(widths)

        cols[0].caption(
            str(item.get("Task ID", ""))
        )

        cols[1].write(
            item.get("Subject") or "Untitled Video"
        )

        status = item.get("Status", "unknown")

        if status == "completed":
            cols[2].success("Completed")

        elif status == "failed":
            cols[2].error("Failed")

        elif status in ("queued", "processing"):
            cols[2].info(status.title())

        else:
            cols[2].write(status.title())

        duration = item.get("Duration (s)") or 0

        cols[3].write(
            f"{duration:.2f}s"
        )

    # ==========================================
    # 5. VIDEO TASK SELECTOR
    # ==========================================

    st.divider()
    st.markdown("#### Select a Video")

    task_lookup = {
        task["task_id"]: task
        for task in tasks
    }

    task_ids = list(task_lookup)

    selected_id = st.selectbox(
        "Choose a video task",
        options=task_ids,
        format_func=lambda task_id: (
            f"{task_lookup[task_id].get('subject') or 'Video'} "
            f"— {task_lookup[task_id].get('state', 'unknown')} "
            f"({task_id})"
        ),
        key="macy_history_selected_task",
    )

    task = task_lookup[selected_id]

    state = task.get("state", "unknown")
    stage = task.get("stage", "unknown")

    st.write("**Task ID:**", selected_id)
    st.write("**Status:**", state)
    st.write("**Stage:**", stage)

    if task.get("voice"):
        st.write(
            "**Voice:**",
            task["voice"],
        )

    # ==========================================
    # 6. PROCESSING TIME DETAILS
    # ==========================================

    stage_times = task.get("stage_seconds") or {}

    if stage_times:

        st.markdown("#### Processing Times")

        for stage_name, seconds in stage_times.items():

            st.write(
                f"**{stage_name.title()}:** "
                f"{seconds} seconds"
            )

    # ==========================================
    # 7. COMPLETED VIDEO PREVIEW
    # ==========================================

    if state == "completed":

        st.success(
            "Video generation completed!"
        )

        output = task.get("output") or {}

        duration = output.get("duration") or 0
        resolution = output.get(
            "resolution", "Unknown"
        )

        st.write(
            "**Duration:**",
            round(duration, 2),
            "seconds",
        )

        st.write(
            "**Resolution:**",
            resolution,
        )

        show_preview = st.checkbox(
            "Show Video Preview",
            key="macy_history_show_preview",
        )

        if show_preview:

            left, center, right = st.columns(
                [2, 1, 2]
            )

            with center:
                st.video(
                    get_video_preview_url(selected_id)
                )

        st.link_button(
            "⬇ Download Video",
            get_video_download_url(selected_id),
            use_container_width=True,
        )

    # ==========================================
    # 8. FAILED OR PROCESSING TASKS
    # ==========================================

    elif state == "failed":

        st.error(
            task.get("error")
            or "Video generation failed."
        )

    elif state in ("queued", "processing"):

        st.info(
            f"Video generation in progress: {stage}"
        )

    else:

        st.warning(
            f"Unrecognized task state: {state}"
        )
