"""Render saved task media into a NEW validation directory; no provider requests."""
import hashlib
import json
import time
import uuid
from pathlib import Path
from app.services.scene_timing import build_timed_scene_plan
from app.services.timed_video import render_timed_video

ROOT = Path(__file__).resolve().parents[1]

def main():
    source = ROOT / "storage/tasks/2b434425d2ce"
    output = ROOT / "storage/validation" / uuid.uuid4().hex[:12]
    output.mkdir(parents=True, exist_ok=False)
    files = [p for p in (ROOT / "storage/tasks").rglob("*") if p.is_file()]
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    plan = json.loads((source / "scene_plan.json").read_text(encoding="utf-8"))
    timed = build_timed_scene_plan(plan, source / "subtitle.srt")
    (output / "timed_scene_plan.json").write_text(json.dumps(timed, indent=2, ensure_ascii=False), encoding="utf-8")
    start = time.perf_counter()
    result = render_timed_video(timed, source / "audio.mp3", source / "subtitle.srt", output / "baseline.mp4")
    result["render_seconds"] = round(time.perf_counter() - start, 3)
    result["source_task_files_unchanged"] = all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == digest for p, digest in before.items())
    (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
