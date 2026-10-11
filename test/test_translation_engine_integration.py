import json
import threading
import unittest
from types import SimpleNamespace

from doctranslate.ai.benchmark import EngineBenchmarkRunner
from doctranslate.ai.benchmark_fixtures import load_builtin_fixtures
from doctranslate.ai.contracts import SegmentResult
from doctranslate.ai.context_backend import ContextualCapability, ContextualResult
from doctranslate.translate_core.contracts import SourceMetadata, XhtmlBlock, XhtmlDocument
from doctranslate.translation import (
    BasicTranslationEngine,
    EngineDescriptor,
    TranslationEngineRegistry,
    TranslationOptions,
    TranslationContext,
    TranslationError,
)
from doctranslate.translation.planning import (
    ConservativeTokenCounter,
    SemanticBatchPlanner,
)
from doctranslate.translation.registry import register_advanced_standard
from doctranslate.translation.advanced import AdvancedTranslationEngine
from doctranslate.translation.context import ContextBuilder
from doctranslate.translation.planning import ConservativeTokenCounter
from doctranslate.queue_worker import WorkerTranslationDispatcher


class FakeExecutor:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.calls = 0

    def execute(self, requests, options, *, context):
        self.calls += 1
        if self.fail:
            raise TranslationError("fake_failure", "simulated executor failure")
        return tuple(SegmentResult(item.segment_id, "CZ:" + item.text, item.markup) for item in requests)


class FakeContextBackend:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.calls = 0

    def contextual_capability(self):
        return ContextualCapability(True, prompt_revision="fake-v1")

    def translate_batch(self, requests, envelope):
        self.calls += 1
        if self.fail:
            raise TranslationError("fake_failure", "simulated contextual failure")
        return tuple(ContextualResult(item.segment_id, "CZ:" + item.text, item.markup) for item in requests)


class TranslationEngineIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = load_builtin_fixtures()[0]
        self.document = XhtmlDocument(
            SourceMetadata(
                "fixture.pdf",
                "application/pdf",
                self.fixture.source_language,
                self.fixture.target_language,
                source_sha256=self.fixture.content_hash,
            ),
            (
                XhtmlBlock("a", 1, 1, self.fixture.source[:40], "<p>a</p>"),
                XhtmlBlock("b", 1, 2, self.fixture.source[40:], "<p>b</p>"),
            ),
        )
        self.options = TranslationOptions(
            self.fixture.source_language,
            self.fixture.target_language,
            translator_options={
                "batch_size": 2,
                "max_attempts": 1,
                "max_context_tokens": 256,
                "instruction_tokens": 1,
                "schema_tokens": 1,
                "reserved_output_tokens": 16,
                "glossary_limit": 2,
                "occurrence_limit": 1,
                "quality_policy": "warn",
            },
        )

    def advanced(self, backend):
        return AdvancedTranslationEngine(
            backend,
            planner=SemanticBatchPlanner(ConservativeTokenCounter()),
            context_builder=ContextBuilder(ConservativeTokenCounter()),
        )

    def test_dispatcher_creates_mixed_basic_and_advanced_jobs(self):
        basic_executor = FakeExecutor()
        registry = TranslationEngineRegistry()
        registry.register(
            EngineDescriptor(
                "basic",
                "Basic",
                "basic-v1",
                options_schema={"batch_size": int, "max_attempts": int},
                factory=lambda dependencies, options: BasicTranslationEngine(
                    dependencies["basic"]
                ),
            )
        )
        register_advanced_standard(
            registry,
            lambda dependencies, options: self.advanced(dependencies["advanced"]),
        )
        dispatcher = WorkerTranslationDispatcher(registry)
        basic, basic_descriptor, _ = dispatcher.create(
            {"translator_id": "basic", "inlang": "en", "outlang": "cs",
             "translator_options": {"batch_size": 2, "max_attempts": 1}},
            {"basic": basic_executor},
        )
        advanced_backend = FakeContextBackend()
        advanced_options = {
            key: value for key, value in self.options.translator_options.items()
            if key in {"max_context_tokens", "instruction_tokens", "schema_tokens",
                       "reserved_output_tokens", "max_attempts", "glossary_limit",
                       "occurrence_limit", "quality_policy"}
        }
        advanced, advanced_descriptor, _ = dispatcher.create(
            {"translator_id": "advanced", "inlang": "en", "outlang": "cs",
             "translator_options": advanced_options},
            {"advanced": advanced_backend},
        )
        basic_result = basic.translate(self.document, TranslationOptions("en", "cs"))
        advanced_result = advanced.translate(self.document, self.options)
        self.assertEqual(basic_descriptor.id, "basic")
        self.assertEqual(advanced_descriptor.id, "advanced")
        self.assertEqual(basic_result.document.blocks[0].text[:3], "CZ:")
        self.assertEqual(advanced_result.document.blocks[1].text[:3], "CZ:")
        self.assertEqual(basic_executor.calls, 1)
        self.assertEqual(advanced_backend.calls, 1)

    def test_engine_benchmark_uses_one_unique_fixture_and_emits_jsonl(self):
        def basic_runner(fixture):
            return "basic:" + fixture.source

        def advanced_runner(fixture):
            return "advanced:" + fixture.source

        result = EngineBenchmarkRunner(
            {"basic": basic_runner, "advanced": advanced_runner},
            repeats=2,
        ).run(self.fixture)
        self.assertEqual(len(result.samples), 4)
        self.assertEqual({item.fixture_hash for item in result.samples}, {self.fixture.content_hash})
        self.assertEqual({item.engine_id for item in result.samples}, {"basic", "advanced"})
        lines = [json.loads(line) for line in result.jsonl().splitlines()]
        self.assertEqual(len(lines), 4)
        self.assertTrue(all(item["wall_ms"] >= 0 for item in lines))
        self.assertTrue(all(item["status"] == "ok" for item in lines))

    def test_engine_benchmark_extracts_quality_and_token_metadata(self):
        document = self.document
        result = SimpleNamespace(
            document=document,
            metrics=SimpleNamespace(
                translator_id="advanced",
                translator_revision="v1",
                batches=2,
                segments=2,
                ai_calls=2,
                resumed=1,
                prompt_tokens=10,
                output_tokens=7,
                token_accounting={"source": "measured"},
                revisions=1,
            ),
            warnings=("one quality warning",),
        )
        sample = EngineBenchmarkRunner({"advanced": lambda fixture: result}).run(self.fixture).samples[0]
        self.assertEqual(sample.token_count, 17)
        self.assertEqual(sample.repair_count, 1)
        self.assertEqual(sample.quality, "warnings")
        self.assertEqual(sample.metadata["prompt_tokens"], 10)

    def test_engine_benchmark_records_failures_without_stopping_other_engine(self):
        result = EngineBenchmarkRunner(
            {
                "basic": lambda fixture: (_ for _ in ()).throw(RuntimeError("boom")),
                "advanced": lambda fixture: "ok",
            }
        ).run(self.fixture)
        self.assertEqual(result.samples[0].status, "error")
        self.assertEqual(result.samples[0].error_code, "RuntimeError")
        self.assertEqual(result.samples[1].status, "ok")

    def test_cancel_and_failure_are_kept_out_of_successful_engine_output(self):
        event = threading.Event()
        event.set()
        executor = FakeExecutor()
        with self.assertRaises(Exception):
            BasicTranslationEngine(executor).translate(
                self.document,
                TranslationOptions("en", "cs"),
                context=TranslationContext(cancel_event=event),
            )
        self.assertEqual(executor.calls, 0)
        with self.assertRaises(TranslationError) as error:
            self.advanced(FakeContextBackend(fail=True)).translate(
                self.document,
                self.options,
            )
        self.assertEqual(error.exception.code, "fake_failure")


if __name__ == "__main__":
    unittest.main()
