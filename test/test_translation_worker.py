from pathlib import Path
from unittest import mock
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.queue_app import QueueStore, make_job
from doctranslate.queue_worker import Worker
from doctranslate.translation import (
    EngineDescriptor,
    TranslationCancelled,
    TranslationContext,
    TranslationEngineRegistry,
    TranslationError,
    TranslationOptions,
)


class FakeEngine:
    def __init__(self, dependencies, options):
        self.dependencies = dependencies
        self.options = options


class TranslationWorkerTests(unittest.TestCase):
    def make_worker(self, folder, job, runner=None):
        queue_path = Path(folder) / "queue.json"
        Path(job["input"]).write_bytes(b"%PDF-test")
        store = QueueStore(queue_path)
        store.append_job(job)
        registry = TranslationEngineRegistry()
        registry.register(
            EngineDescriptor(
                "basic",
                "Basic",
                "fake-v1",
                options_schema={"mode": str},
                factory=FakeEngine,
            )
        )
        worker = Worker(
            queue_path,
            engine_registry=registry,
            engine_runner=runner,
        )
        return worker, store

    def test_run_job_uses_selected_registry_engine_and_callbacks(self):
        calls = []

        def runner(engine, options, context):
            calls.append((engine, options, context))
            context.on_progress(1, 1)

        with tempfile.TemporaryDirectory() as folder:
            job = make_job(
                Path(folder) / "book.pdf",
                phase="html",
                translator_id="basic",
                translator_options={"mode": "standard"},
            )
            worker, store = self.make_worker(folder, job, runner)
            worker.run_job(job)
            saved = store.jobs()[0]

        self.assertEqual(saved["state"], "done")
        self.assertEqual(len(calls), 1)
        engine, options, context = calls[0]
        self.assertIsInstance(engine, FakeEngine)
        self.assertIsInstance(options, TranslationOptions)
        self.assertEqual(options.translator_options["mode"], "standard")
        self.assertIsInstance(context, TranslationContext)
        self.assertEqual(context.cancel_event, worker.cancel_event)

    def test_pdf_phase_is_render_only_and_does_not_create_engine(self):
        runner_calls = []

        with tempfile.TemporaryDirectory() as folder:
            input_path = Path(folder) / "book.pdf"
            html_path = Path(folder) / "book.html"
            html_path.write_text("<html></html>", encoding="utf-8")
            job = make_job(input_path, phase="pdf", html_file=html_path, translator_id="basic")
            worker, store = self.make_worker(
                folder,
                job,
                lambda *args: runner_calls.append(args),
            )
            with mock.patch("doctranslate.translate.main") as legacy_main:
                worker.run_job(job)
                saved_state = store.jobs()[0]["state"]

        legacy_main.assert_called_once()
        self.assertEqual(runner_calls, [])
        self.assertEqual(saved_state, "done")

    def test_advanced_uses_production_dispatch_and_reports_input_error(self):
        with tempfile.TemporaryDirectory() as folder:
            queue_path = Path(folder) / "queue.json"
            store = QueueStore(queue_path)
            job = make_job(Path(folder) / "book.pdf", phase="html", translator_id="advanced")
            Path(job["input"]).write_bytes(b"%PDF-test")
            store.append_job(job)
            worker = Worker(queue_path)
            worker.run_job(job)
            saved = store.jobs()[0]

        self.assertEqual(saved["state"], "failed")
        self.assertNotIn("engine_unavailable", saved["error"])
        self.assertIn("FileDataError", saved["error"])

    def test_typed_cancellation_keeps_job_restartable(self):
        def runner(engine, options, context):
            raise TranslationCancelled("stop requested")

        with tempfile.TemporaryDirectory() as folder:
            job = make_job(Path(folder) / "book.pdf", phase="html")
            worker, store = self.make_worker(folder, job, runner)
            with self.assertRaises(KeyboardInterrupt):
                worker.run_job(job)
            saved = store.jobs()[0]

        self.assertEqual(saved["state"], "in_progress")

    def test_exhausted_request_timeout_pauses_job_without_marking_failed(self):
        def runner(engine, options, context):
            raise TranslationError("request_timeout", "AI request exceeded 1800 seconds")

        with tempfile.TemporaryDirectory() as folder:
            job = make_job(Path(folder) / "book.pdf", phase="html")
            worker, store = self.make_worker(folder, job, runner)
            worker.run_job(job)
            saved = store.jobs()[0]

        self.assertEqual(saved["state"], "paused")
        self.assertIn("request_timeout", saved["error"])
        self.assertNotEqual(saved["state"], "failed")


if __name__ == "__main__":
    unittest.main()
