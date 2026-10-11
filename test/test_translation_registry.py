from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.translation import (
    EngineDescriptor,
    TranslationEngineRegistry,
    TranslationError,
    TranslationOptions,
    TranslationRegistryError,
)


class FakeEngine:
    def __init__(self, dependencies, options):
        self.dependencies = dependencies
        self.options = options

    def translate(self, document, options, *, context=None):
        raise NotImplementedError


def options(**values):
    return TranslationOptions("EN_us", "CS", translator_options=values)


class TranslationRegistryTests(unittest.TestCase):
    def test_list_is_deterministic_and_does_not_construct_engines(self):
        calls = []

        def factory(dependencies, selected):
            calls.append((dependencies, selected))
            return FakeEngine(dependencies, selected)

        registry = TranslationEngineRegistry()
        registry.register(
            EngineDescriptor("basic", "Basic", "basic-v1", factory=factory)
        )
        registry.register(
            EngineDescriptor(
                "advanced",
                "Advanced",
                "advanced-v1",
                available=False,
                reason="engine is not implemented",
            )
        )

        self.assertEqual([item.id for item in registry.list()], ["advanced", "basic"])
        self.assertEqual(calls, [])
        self.assertFalse(registry.get("advanced").available)

    def test_create_validates_options_and_injects_dependencies(self):
        registry = TranslationEngineRegistry()
        registry.register(
            EngineDescriptor(
                "basic",
                "Basic",
                "basic-v1",
                options_schema={"max_attempts": int, "quality_policy": str},
                factory=FakeEngine,
            )
        )

        selected = options(max_attempts=2, quality_policy="warn")
        engine = registry.create("BASIC", {"name": "deps"}, selected)

        self.assertIsInstance(engine, FakeEngine)
        self.assertEqual(engine.dependencies["name"], "deps")
        self.assertEqual(engine.options.source_language, "en-us")
        self.assertEqual(engine.options.target_language, "cs")
        self.assertEqual(engine.options.translator_options["max_attempts"], 2)

    def test_unknown_duplicate_unavailable_and_invalid_options_are_typed(self):
        registry = TranslationEngineRegistry()
        registry.register(
            EngineDescriptor("basic", "Basic", "basic-v1", factory=FakeEngine)
        )

        with self.assertRaises(TranslationRegistryError) as unknown:
            registry.create("missing", None, options())
        self.assertEqual(unknown.exception.code, "unknown_engine")

        with self.assertRaises(TranslationRegistryError) as duplicate:
            registry.register(
                EngineDescriptor("BASIC", "Basic again", "basic-v2", factory=FakeEngine)
            )
        self.assertEqual(duplicate.exception.code, "duplicate_engine")

        registry.register(
            EngineDescriptor(
                "advanced",
                "Advanced",
                "advanced-v1",
                available=False,
                reason="context backend unavailable",
            )
        )
        with self.assertRaises(TranslationRegistryError) as unavailable:
            registry.create("advanced", None, options())
        self.assertEqual(unavailable.exception.code, "engine_unavailable")
        self.assertIn("context backend unavailable", str(unavailable.exception))

        with self.assertRaises(TranslationRegistryError) as unknown_option:
            registry.create("basic", None, options(unexpected=True))
        self.assertEqual(unknown_option.exception.code, "unknown_option")

        registry.register(
            EngineDescriptor(
                "typed",
                "Typed",
                "typed-v1",
                options_schema={"max_attempts": int},
                factory=FakeEngine,
            )
        )
        with self.assertRaises(TranslationRegistryError) as bad_type:
            registry.create("typed", None, options(max_attempts="two"))
        self.assertEqual(bad_type.exception.code, "invalid_option_type")

    def test_options_reject_non_string_language_values(self):
        with self.assertRaises(ValueError):
            TranslationOptions(1, "cs")
        with self.assertRaises(ValueError):
            TranslationOptions("en", "cs", target_variant=3)

    def test_contract_errors_expose_code_and_reason(self):
        error = TranslationError(
            "checkpoint_invalid",
            "checkpoint identity does not match",
            checkpoint_reference="checkpoint.json",
        )
        self.assertEqual(error.code, "checkpoint_invalid")
        self.assertEqual(error.checkpoint_reference, "checkpoint.json")
        self.assertIn("checkpoint_invalid", str(error))


if __name__ == "__main__":
    unittest.main()
