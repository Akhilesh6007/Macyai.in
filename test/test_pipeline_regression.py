"""Offline tests: python -m unittest discover -s test -p test_*.py -v."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services import video_jobs as jobs
from app.services.scene_timing import build_timed_scene_plan
from app.services.scenes import build_scene_plan
from app.services.timed_video import render_timed_video, TimedRenderError
from app.services.subtitle import generate_subtitles


class PipelineRegression(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.context = patch.object(jobs, "TASKS_DIR", self.root)
        self.context.start()
        self.addCleanup(self.context.stop)
        self.clip = self.root / "clip.mp4"
        self.clip.write_bytes(b"fixture")

    def test_job_builds_timing_before_render_and_preserves_completed(self):
        task = jobs.create_video_job("Robotics", "Robotics helps people solve problems every day.", ["robotics"])
        def voice(**kwargs):
            audio = Path(kwargs["output_path"])
            audio.write_bytes(b"audio")
            metadata = audio.with_suffix(".jsonl")
            metadata.write_text(json.dumps({"type": "WordBoundary", "text": "Robotics", "offset": 0, "duration": 10000000}))
            return {"metadata_path": str(metadata)}
        def renderer(**kwargs):
            plan = kwargs["timed_scene_plan"]
            self.assertEqual(plan["timing_method"], "srt_cue_boundary_v1")
            self.assertEqual(plan["scenes"][0]["start_seconds"], 0)
            self.assertTrue((self.root / task / "timed_scene_plan.json").is_file())
            Path(kwargs["output_path"]).write_bytes(b"completed")
            return {"duration": 1}
        video = {"id": 1, "videos": {"small": {"url": "fixture"}}}
        with patch.object(jobs, "search_videos", return_value=[video]), patch.object(jobs, "download_video", return_value=self.clip), patch.object(jobs, "generate_voiceover_sync", side_effect=voice), patch.object(jobs, "render_timed_video", side_effect=renderer) as render:
            result = jobs.run_video_job(task)
            self.assertIsNotNone(result)
            self.assertEqual(json.loads((self.root / task / "task.json").read_text())["state"], "completed")
            self.assertEqual(jobs.run_video_job(task), result)
            self.assertEqual(render.call_count, 1)
            self.assertEqual((self.root / task / "final_video.mp4").read_bytes(), b"completed")

    def test_failure_records_stage_and_traceback(self):
        task = jobs.create_video_job("Robotics", "A sufficiently long narration.", ["robotics"])
        with patch.object(jobs, "search_videos", return_value=[]):
            self.assertIsNone(jobs.run_video_job(task))
        state = json.loads((self.root / task / "task.json").read_text())
        self.assertEqual(state["state"], "failed")
        self.assertEqual(state["stage"], "materials")
        self.assertIn("No video footage", (self.root / task / "error_traceback.txt").read_text())

    def test_voice_selection(self):
        self.assertEqual(jobs.select_voice_for_script("Hello world"), "en-AU-NatashaNeural")
        self.assertEqual(jobs.select_voice_for_script("".join(chr(n) for n in (2344, 2350, 2360, 2381, 2340, 2375))), "hi-IN-SwaraNeural")

    def test_scene_plan_rejects_missing_assets(self):
        with self.assertRaises(ValueError):
            build_scene_plan("Hello world", [])

    def test_timing_is_continuous(self):
        subtitle = self.root / "subtitle.srt"
        subtitle.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n\n2\n00:00:01,000 --> 00:00:02,000\nworld\n")
        plan = build_timed_scene_plan({"scenes": [{"text": "Hello"}, {"text": "world"}]}, subtitle)
        self.assertEqual(plan["scenes"][0]["end_seconds"], plan["scenes"][1]["start_seconds"])

    def test_renderer_refuses_existing_output(self):
        output = self.root / "final.mp4"
        output.write_bytes(b"preserve")
        with self.assertRaises(FileExistsError):
            render_timed_video({"scenes": [{}]}, self.root / "audio.mp3", self.root / "subtitle.srt", output)
        self.assertEqual(output.read_bytes(), b"preserve")

    def test_renderer_rejects_odd_dimensions(self):
        with self.assertRaises(ValueError):
            render_timed_video({"scenes": [{}]}, "missing", "missing", "new.mp4", width=541)

    def test_subtitle_missing_word_boundaries(self):
        metadata = self.root / "audio.jsonl"
        metadata.write_text("{}")
        with self.assertRaises(ValueError):
            generate_subtitles(metadata, self.root / "subtitle.srt")


if __name__ == "__main__":
    unittest.main()
