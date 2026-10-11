import tempfile
import unittest
from pathlib import Path

from doctranslate import translate
from doctranslate.queue_app import QueueStore, make_job
from doctranslate.queue_worker import Worker
from doctranslate.translation.composition import build_worker_translation_runtime
from doctranslate.translation.contracts import TranslationOptions


class FakeContextualBackend:
    def contextual_capability(self):
        return {"available": True}


class TranslationCompositionTests(unittest.TestCase):
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
