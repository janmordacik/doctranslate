from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.ai.contracts import SegmentResult
from doctranslate.job_runner import JobSpec
from doctranslate.translate_core import SourceMetadata, XhtmlBlock, XhtmlDocument
from doctranslate.translation import (
    BasicTranslationEngine,
    TranslationCancelled,
    TranslationContext,
    TranslationError,
    TranslationOptions,
)


class FakeExecutor:
    def __init__(self, *, fail_once=False, cancel_after=False, invalid=False):
        self.calls = []
        self.fail_once = fail_once
        self.cancel_after = cancel_after
        self.invalid = invalid

    def execute(self, requests, options, *, context):
        self.calls.append(tuple(requests))
        if self.fail_once and len(self.calls) == 1:
            raise TranslationError("temporary", "retry this batch", retryable=True)
        if self.cancel_after and context.cancel_event is not None:
            context.cancel_event.set()
        if self.invalid:
            return (SegmentResult("unknown", "bad"),)
        return tuple(
            SegmentResult(
                request.segment_id,
                request.text.replace("Hello", "Ahoj").replace("World", "Svete"),
            )
            for request in requests
        )


def document():
    return XhtmlDocument(
        SourceMetadata("book.pdf", "application/pdf", "en", "cs"),
        (
            XhtmlBlock("a", 1, 0, "Hello", "<p>Hello</p>"),
            XhtmlBlock("blank", 1, 1, "   ", "<p>   </p>"),
            XhtmlBlock("b", 1, 2, "World", "<span>World</span>"),
        ),
    )


class BasicTranslationEngineTests(unittest.TestCase):
    def test_translates_batches_and_preserves_empty_blocks_and_markup(self):
        executor = FakeExecutor(fail_once=True)
        engine = BasicTranslationEngine(executor)
        result = engine.translate(
            document(),
            TranslationOptions("en", "cs", target_variant="literary",
                               translator_options={"batch_size": 1}),
        )

        self.assertEqual(result.metrics.batches, 2)
        self.assertEqual(result.metrics.segments, 2)
        self.assertEqual(len(executor.calls), 3)
        self.assertEqual([block.block_id for block in result.document.blocks],
                         ["a", "blank", "b"])
        self.assertEqual(result.document.blocks[0].text, "Ahoj")
        self.assertEqual(result.document.blocks[0].markup, "<p>Ahoj</p>")
        self.assertEqual(result.document.blocks[1].text, "   ")
        self.assertEqual(result.document.blocks[2].markup, "<span>Svete</span>")
        self.assertEqual(
            executor.calls[1][0].attributes["target_variant"],
            "literary",
        )

    def test_cancellation_before_and_after_executor_is_terminal(self):
        before = threading.Event()
        before.set()
        executor = FakeExecutor()
        engine = BasicTranslationEngine(executor)
        with self.assertRaises(TranslationCancelled):
            engine.translate(document(), TranslationOptions("en", "cs"),
                             context=TranslationContext(cancel_event=before))
        self.assertEqual(executor.calls, [])

        after = threading.Event()
        cancelling = BasicTranslationEngine(FakeExecutor(cancel_after=True))
        with self.assertRaises(TranslationCancelled):
            cancelling.translate(document(), TranslationOptions("en", "cs"),
                                 context=TranslationContext(cancel_event=after))

    def test_invalid_executor_result_has_typed_error(self):
        engine = BasicTranslationEngine(FakeExecutor(invalid=True))
        with self.assertRaises(TranslationError) as failure:
            engine.translate(document(), TranslationOptions("en", "cs"))
        self.assertEqual(failure.exception.code, "invalid_result")

    def test_invalid_limits_are_rejected_before_executor(self):
        executor = FakeExecutor()
        engine = BasicTranslationEngine(executor)
        with self.assertRaises(TranslationError) as failure:
            engine.translate(
                document(),
                TranslationOptions("en", "cs",
                                   translator_options={"max_attempts": 0}),
            )
        self.assertEqual(failure.exception.code, "invalid_options")
        self.assertEqual(executor.calls, [])


if __name__ == "__main__":
    unittest.main()
