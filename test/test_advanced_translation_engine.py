import tempfile
import threading
import unittest
from pathlib import Path

from doctranslate.ai.context_backend import ContextualCapability, ContextualResult
from doctranslate.translate_core.contracts import SourceMetadata, XhtmlBlock, XhtmlDocument
from doctranslate.translation.advanced import AdvancedTranslationEngine
from doctranslate.translation.checkpoint import JsonCheckpointStore
from doctranslate.translation.context import ContextBuilder
from doctranslate.translation.contracts import TranslationError, TranslationOptions
from doctranslate.translation.planning import SemanticBatchPlanner


class ExactCounter:
    def count(self, text):
        return len(text)


class FakeBackend:
    def __init__(self, unchanged=False):
        self.calls = []
        self.unchanged = unchanged

    def contextual_capability(self):
        return ContextualCapability(True, prompt_revision="fake-context-v1")

    def translate_batch(self, requests, envelope):
        self.calls.append((tuple(requests), envelope))
        return tuple(ContextualResult(
            request.segment_id, request.text if self.unchanged else "CZ:" + request.text, request.markup
        ) for request in requests)


class AdvancedEngineTests(unittest.TestCase):
    def document(self, text_a="Hello.", text_b="World."):
        return XhtmlDocument(
            SourceMetadata("book.pdf", "application/pdf", "en", "cs", source_sha256="hash"),
            (
                XhtmlBlock("a", 1, 1, text_a, "<p>Hello.</p>"),
                XhtmlBlock("b", 1, 2, text_b, "<p>World.</p>"),
            ),
        )

    def engine(self, backend, checkpoint=None):
        return AdvancedTranslationEngine(
            backend, planner=SemanticBatchPlanner(ExactCounter()),
            context_builder=ContextBuilder(ExactCounter()),
            checkpoint_store=checkpoint,
        )

    def options(self, **extra):
        values = {
            "max_context_tokens": 40, "instruction_tokens": 1,
            "schema_tokens": 1, "reserved_output_tokens": 5,
            "max_attempts": 1, "quality_policy": "warn",
        }
        values.update(extra)
        return TranslationOptions("en", "cs", translator_options=values)

    def test_standard_engine_translates_with_bounded_fake_backend(self):
        backend = FakeBackend()
        result = self.engine(backend).translate(self.document(), self.options())
        self.assertEqual([block.text for block in result.document.blocks], ["CZ:Hello.", "CZ:World."])
        self.assertEqual(result.metrics.segments, 2)
        self.assertEqual(result.metrics.ai_calls, 1)
        self.assertEqual(len(backend.calls), 1)
        self.assertEqual(backend.calls[0][1].source_text, "Hello.\n\nWorld.")

    def test_checkpoint_resume_skips_valid_segments(self):
        with tempfile.TemporaryDirectory() as folder:
            checkpoint = JsonCheckpointStore(Path(folder) / "checkpoint.json")
            first_backend = FakeBackend()
            first = self.engine(first_backend, checkpoint).translate(self.document(), self.options())
            self.assertEqual(len(first_backend.calls), 1)
            second_backend = FakeBackend()
            second = self.engine(second_backend, checkpoint).translate(self.document(), self.options())
            self.assertEqual(len(second_backend.calls), 0)
            self.assertEqual(second.metrics.resumed, 2)
            self.assertEqual([block.text for block in second.document.blocks], ["CZ:Hello.", "CZ:World."])

    def test_long_block_is_split_and_reassembled(self):
        document = self.document("First. Second. Third.", "")
        backend = FakeBackend()
        result = self.engine(backend).translate(document, self.options(max_context_tokens=18))
        self.assertEqual(result.document.blocks[0].text, "CZ:First. CZ:Second. CZ:Third.")

    def test_warn_and_strict_quality_policies_are_explicit(self):
        warning = self.engine(FakeBackend(unchanged=True)).translate(self.document(), self.options())
        self.assertTrue(warning.warnings)
        with self.assertRaises(TranslationError) as error:
            self.engine(FakeBackend(unchanged=True)).translate(
                self.document(), self.options(quality_policy="strict")
            )
        self.assertEqual(error.exception.code, "quality_warning")

    def test_registry_marks_advanced_unavailable_without_factory(self):
        from doctranslate.translation.registry import TranslationEngineRegistry, register_advanced_standard
        registry = TranslationEngineRegistry()
        register_advanced_standard(registry)
        self.assertFalse(registry.get("advanced").available)
        compatible = TranslationEngineRegistry()
        register_advanced_standard(compatible, lambda _deps, _options: self.engine(FakeBackend()))
        self.assertTrue(compatible.get("advanced").available)
    def test_cancel_before_ai_call(self):
        event = threading.Event()
        event.set()
        with self.assertRaises(Exception) as error:
            self.engine(FakeBackend()).translate(
                self.document(), self.options(),
                context=__import__("doctranslate.translation.contracts", fromlist=["TranslationContext"]).TranslationContext(cancel_event=event),
            )
        self.assertEqual(getattr(error.exception, "code", None), "cancelled")


if __name__ == "__main__":
    unittest.main()
