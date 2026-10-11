from pathlib import Path
import copy
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.job_runner import JobRunner, JobSpec
from doctranslate.queue_app import QueueStore, make_job
from doctranslate.queue_worker import JobOptions


class TranslationJobSelectionTests(unittest.TestCase):
    def test_make_job_defaults_legacy_records_to_basic(self):
        job = make_job(
            "book.pdf",
            translator_id="advanced",
            translator_options={"mode": "standard", "limits": {"batches": 2}},
        )
        self.assertEqual(job["translator_id"], "advanced")
        self.assertEqual(job["translator_options"]["mode"], "standard")
        job["translator_options"]["limits"]["batches"] = 9
        self.assertEqual(job["translator_options"]["limits"]["batches"], 9)

        legacy = make_job("legacy.pdf")
        legacy.pop("translator_id")
        legacy.pop("translator_options")
        with tempfile.TemporaryDirectory() as folder:
            store = QueueStore(Path(folder) / "queue.json")
            store.set_jobs([legacy])
            loaded = store.jobs()[0]
        self.assertEqual(loaded["translator_id"], "basic")
        self.assertEqual(loaded["translator_options"], {})

    def test_unavailable_future_id_is_syntactically_storable(self):
        job = make_job(
            "book.pdf",
            translator_id="future.advanced-v2",
            translator_options={"mode": "standard"},
        )
        with tempfile.TemporaryDirectory() as folder:
            store = QueueStore(Path(folder) / "queue.json")
            store.set_jobs([job])
            loaded = store.jobs()[0]
        self.assertEqual(loaded["translator_id"], "future.advanced-v2")

    def test_invalid_id_or_options_are_rejected_by_queue_schema(self):
        for invalid in ("", "bad id", "../engine"):
            job = make_job("book.pdf")
            job["translator_id"] = invalid
            with tempfile.TemporaryDirectory() as folder:
                store = QueueStore(Path(folder) / "queue.json")
                with self.assertRaises(ValueError):
                    store.set_jobs([job])

        job = make_job("book.pdf")
        job["translator_options"] = {"not-json": object()}
        with tempfile.TemporaryDirectory() as folder:
            store = QueueStore(Path(folder) / "queue.json")
            with self.assertRaises(ValueError):
                store.set_jobs([job])

    def test_worker_and_runner_copy_selection_without_shared_mutation(self):
        job = make_job(
            "book.pdf",
            translator_id="advanced",
            translator_options={"max_context_tokens": 4096},
        )
        worker_options = JobOptions.from_job(job)
        worker_options.translator_options["max_context_tokens"] = 8192
        self.assertEqual(job["translator_options"]["max_context_tokens"], 4096)

        basic = JobSpec("job", Path("in"), Path("out"), "en", "cs")
        advanced = JobSpec(
            "job",
            Path("in"),
            Path("out"),
            "en",
            "cs",
            translator_id="advanced",
            translator_options={"mode": "standard"},
        )
        self.assertNotEqual(JobRunner.identity(basic), JobRunner.identity(advanced))


if __name__ == "__main__":
    unittest.main()
