import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate import translate
from doctranslate.observability import JsonEventLogger


class ObservabilityTests(unittest.TestCase):
    def test_translation_preview_is_bounded_and_strips_layout_markup(self):
        old_hook = translate.PREVIEW_HOOK
        previews = []
        try:
            translate.PREVIEW_HOOK = previews.append
            translate.report_preview(
                job_id="job-a",
                block_id="p000001_b0001",
                stage="translating",
                source_text="<span id=\"s1\">line 1</span><br>" + "\n".join(
                    f"line {n}" for n in range(2, 130)
                ),
            )
        finally:
            translate.PREVIEW_HOOK = old_hook

        self.assertEqual(len(previews), 1)
        preview = previews[0]
        self.assertEqual(preview["page"], 1)
        self.assertNotIn("<span", preview["source_text"])
        self.assertLessEqual(preview["line_count"], translate.PREVIEW_MAX_LINES)
        self.assertTrue(preview["truncated"])

    def test_json_event_logger_writes_one_json_object_per_line(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.log"
            logger = JsonEventLogger(path)
            self.assertTrue(logger.event("job.started", job_id="a", input=Path("book.pdf")))
            self.assertTrue(logger.event("job.completed", duration_ms=12.5))

            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual([record["event"] for record in records], ["job.started", "job.completed"])
        self.assertEqual(records[0]["input"], "book.pdf")
        self.assertIn("time_utc", records[0])

    def test_translation_trace_uses_jsonl_logger(self):
        with tempfile.TemporaryDirectory() as directory:
            old_path, old_logger, old_trace = translate.RUN_LOG_PATH, translate.RUN_LOGGER, translate.TRACE
            try:
                translate.RUN_LOG_PATH = Path(directory) / "translation.run.log"
                translate.RUN_LOGGER = None
                translate.TRACE = False
                translate.trace_event("test.event", duration_ms=3)
                record = json.loads(translate.RUN_LOG_PATH.read_text(encoding="utf-8").strip())
            finally:
                translate.RUN_LOG_PATH, translate.RUN_LOGGER, translate.TRACE = (
                    old_path, old_logger, old_trace
                )

        self.assertEqual(record["event"], "test.event")
        self.assertEqual(record["duration_ms"], 3)

    def test_logger_failure_does_not_raise(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.log"
            path.mkdir()
            self.assertFalse(JsonEventLogger(path).event("cannot.write"))
