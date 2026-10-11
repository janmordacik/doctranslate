import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from doctranslate import translate
from doctranslate.queue_app import QueueStore, make_job
from doctranslate.queue_worker import Worker
from doctranslate.translation.composition import build_worker_translation_runtime
from doctranslate.translation.composition import _default_backend_factory
from doctranslate.translation.contracts import TranslationOptions


class FakeContextualBackend:
    def contextual_capability(self):
        return {"available": True}


class TranslationCompositionTests(unittest.TestCase):
    def test_default_ollama_timeout_is_long_and_configurable(self):
        with patch("doctranslate.translation.composition.OllamaBackend") as backend:
            _default_backend_factory(
                {
                    "provider": "ollama",
                    "model": "translategemma:4b",
                    "translator_options": {"request_timeout": 42},
                },
                translate,
            )
            self.assertEqual(backend.call_args.kwargs["timeout"], 42)

            backend.reset_mock()
            _default_backend_factory(
                {"provider": "ollama", "model": "translategemma:4b"},
                translate,
            )
            self.assertEqual(backend.call_args.kwargs["timeout"], 1800)
            self.assertTrue(backend.call_args.kwargs["managed_ollama"])
            self.assertEqual(backend.call_args.kwargs["ollama_port"], 11435)
            self.assertIsNone(backend.call_args.kwargs["ollama_context_length"])

    def test_production_registry_constructs_advanced_engine(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            queue = root / "queue.json"
            store = QueueStore(queue)
            job = make_job(
                root / "book.pdf",
                phase="html",
                translator_id="advanced",
            )
            job["output"] = str(root / "book-out.pdf")
            store.append_job(job)
            worker = Worker(queue)
            worker.current_job_id = job["id"]

            registry, runner = build_worker_translation_runtime(
                worker,
                translate,
                backend_factory=lambda current, module: FakeContextualBackend(),
            )
            descriptor = registry.get("advanced")
            engine = registry.create(
                "advanced",
                {"worker": worker, "translate": translate},
                TranslationOptions("en", "cs"),
            )

        self.assertTrue(descriptor.available)
        self.assertEqual(descriptor.id, "advanced")
        self.assertEqual(engine.translator_id, "advanced")
        self.assertTrue(callable(runner))


if __name__ == "__main__":
    unittest.main()
