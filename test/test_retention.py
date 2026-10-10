import json
import os
from pathlib import Path
import tempfile
import time
import unittest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.retention import RetentionPolicy, cleanup_queue_workdirs, cleanup_workdir


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.queue = self.root / "queue.json"
        self.queue.write_text(json.dumps({"items": [{"kind": "control"}]}), encoding="utf-8")
        self.now = time.time()

    def tearDown(self):
        self.temp.cleanup()

    def old_file(self, name, age_days=60):
        path = self.root / name
        path.write_text("artifact", encoding="utf-8")
        timestamp = self.now - age_days * 86400
        os.utime(path, (timestamp, timestamp))
        return path

    def test_cleanup_removes_old_sidecars_but_keeps_documents(self):
        old_plan = self.old_file("old.plan.json")
        old_log = self.old_file("old.run.log")
        old_pdf = self.old_file("old.pdf")
        old_html = self.old_file("old.html")
        recent = self.root / "recent.plan.json"
        recent.write_text("recent", encoding="utf-8")
        report = cleanup_workdir(
            self.root,
            self.queue,
            policy=RetentionPolicy(sidecar_days=30, keep_latest_sidecar_sets=1),
            now=self.now,
        )
        self.assertEqual(report["removed_count"], 2)
        self.assertFalse(old_plan.exists())
        self.assertFalse(old_log.exists())
        self.assertTrue(old_pdf.exists())
        self.assertTrue(old_html.exists())
        self.assertTrue(recent.exists())

    def test_cleanup_does_not_touch_active_worker_or_its_sidecars(self):
        output = self.root / "active.pdf"
        output.write_text("pdf", encoding="utf-8")
        sidecar = self.old_file("active.plan.json")
        self.queue.write_text(json.dumps({
            "items": [{"kind": "control"}, {
                "kind": "job", "state": "in_progress", "output": str(output),
            }],
        }), encoding="utf-8")
        (self.root / "worker.lock").write_text("locked", encoding="utf-8")
        report = cleanup_queue_workdirs(
            self.queue,
            policy=RetentionPolicy(sidecar_days=0, keep_latest_sidecar_sets=0),
            dry_run=False,
        )
        self.assertTrue(report[0]["active_worker"])
        self.assertTrue(sidecar.exists())

    def test_cleanup_removes_old_empty_test_directories(self):
        for name in ("root-pycache", "worker-smoke-test"):
            directory = self.root / name
            directory.mkdir()
            timestamp = self.now - 2 * 86400
            os.utime(directory, (timestamp, timestamp))
        report = cleanup_workdir(
            self.root,
            self.queue,
            policy=RetentionPolicy(temporary_hours=1),
            now=self.now,
        )
        self.assertEqual(report["removed_count"], 2)
        self.assertFalse((self.root / "root-pycache").exists())
        self.assertFalse((self.root / "worker-smoke-test").exists())

    def test_cleanup_removes_oversized_unprotected_sidecar(self):
        sidecar = self.old_file("oversized.run.log", age_days=1)
        sidecar.write_bytes(b"01234567890")
        report = cleanup_workdir(
            self.root,
            self.queue,
            policy=RetentionPolicy(
                sidecar_days=30,
                keep_latest_sidecar_sets=0,
                max_sidecar_bytes=10,
            ),
            now=self.now,
        )
        self.assertIn(str(sidecar), report["oversized"])
        self.assertFalse(sidecar.exists())
        self.assertFalse(report["sidecar_limit_exceeded"])


if __name__ == "__main__":
    unittest.main()
