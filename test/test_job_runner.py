from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.ai import SegmentRequest, SegmentResult
from doctranslate.formats import FormatDescriptor, FormatRegistry
from doctranslate.job_runner import JobRunner, JobSpec, RunContext
from doctranslate.translate_core import SourceMetadata, XhtmlBlock, XhtmlDocument


class InputAdapter:
    def __init__(self, document):
        self.document = document
    def read(self, source):
        return self.document


class OutputAdapter:
    def __init__(self):
        self.received = None
        self.writes = []
    def write(self, document, target):
        self.received = (document, target)
        self.writes.append((document, target))
        Path(target).write_text(document.blocks[0].text, encoding="utf-8")
        return target


class Backend:
    name = "fake"
    provider_id = "fake"
    model = "fake:1b"
    def __init__(self):
        self.requests = ()
    def translate(self, text, source_language, target_language):
        return "Ahoj"
    def translate_segments(self, requests):
        self.requests = tuple(requests)
        return tuple(SegmentResult(item.segment_id, item.text.replace("Hello", "Ahoj")) for item in requests)


class JobRunnerTests(unittest.TestCase):
    def test_run_writes_output_and_restart_uses_checkpoint(self):
        document = XhtmlDocument(
            SourceMetadata("book.pdf", "application/pdf", "en", "cs", source_sha256="hash"),
            (XhtmlBlock("a", 1, 0, "Hello"),),
        )
        input_adapter = InputAdapter(document)
        output_adapter = OutputAdapter()
        registry = FormatRegistry()
        registry.register(FormatDescriptor("fake", "Fake", "x/fake", (".in",), lambda: input_adapter, "input"))
        registry.register(FormatDescriptor("fake", "Fake", "x/fake", (".out",), lambda: output_adapter, "output"))
        runner = JobRunner(registry)
        with tempfile.TemporaryDirectory() as folder:
            spec = JobSpec("job", Path(folder) / "book.in", Path(folder) / "book.out", "en", "cs",
                           input_format="fake", output_format="fake", provider_id="fake", model="fake",
                           target_variant="cs-expert")
            checkpoint = Path(folder) / "checkpoint.json"
            first_backend = Backend()
            first = runner.run(spec, RunContext(Path(folder), checkpoint_path=checkpoint), backend=first_backend)
            first_document = output_adapter.writes[0][0]
            second = runner.run(spec, RunContext(Path(folder), checkpoint_path=checkpoint), backend=Backend())
        self.assertEqual(first_document.blocks[0].text, "Ahoj")
        self.assertEqual(first.translated_blocks, 1)
        self.assertEqual(second.resumed_blocks, 1)
        self.assertEqual(output_adapter.received[0].blocks[0].text, "Ahoj")
        self.assertEqual(first_backend.requests[0].attributes["target_variant"], "cs-expert")
        self.assertEqual(
            output_adapter.received[0].metadata.extensions["translation_target_variant"],
            "cs-expert",
        )
        self.assertTrue(output_adapter.received[0].metadata.extensions["translation_style_revision"])
        self.assertEqual(
            output_adapter.received[0].metadata.extensions["translation_prompt_revision"],
            "translate-segments-v1",
        )

    def test_identity_changes_with_provider_and_prompt_revision(self):
        spec = JobSpec("job", Path("a"), Path("b"), "en", "cs", provider_id="ollama", model="a")
        changed = JobSpec("job", Path("a"), Path("b"), "en", "cs", provider_id="openai", model="a")
        self.assertNotEqual(JobRunner.identity(spec), JobRunner.identity(changed))
        changed_variant = JobSpec("job", Path("a"), Path("b"), "en", "cs", target_variant="cs-expert")
        self.assertNotEqual(JobRunner.identity(spec), JobRunner.identity(changed_variant))
        changed_revision = JobSpec("job", Path("a"), Path("b"), "en", "cs", style_revision="changed")
        self.assertNotEqual(JobRunner.identity(spec), JobRunner.identity(changed_revision))


if __name__ == "__main__":
    unittest.main()
