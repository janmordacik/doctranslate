from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.translation import (
    CheckpointError,
    CheckpointState,
    JsonCheckpointStore,
    TranslationOptions,
    ValidatedSegment,
    canonical_identity,
)


class TranslationCheckpointTests(unittest.TestCase):
    def identity(self, **extra):
        return canonical_identity(
            source={"sha256": "source", "pages": 3},
            translator_id="basic",
            translator_revision="basic-v1",
            provider_id="ollama",
            model="translategemma:4b",
            style_revision="style-v1",
            prompt_revision="prompt-v1",
            segment_policy="block-v1",
            options=TranslationOptions(
                "EN",
                "CS",
                translator_options={"max_attempts": 2, **extra},
            ),
        )

    def state(self, identity):
        return CheckpointState(
            identity=identity,
            validated_segments=(
                ValidatedSegment(
                    "a",
                    "Hello",
                    "Ahoj",
                    "<p>Hello</p>",
                    "<p>Ahoj</p>",
                    ("hello",),
                    {"source_page": 1, "engine": "basic"},
                ),
            ),
            used_memory_revision="memory-2",
            counters={"batches": 1, "segments": 1},
        )

    def test_identity_is_order_independent_but_changes_for_inputs(self):
        first = canonical_identity(
            source={"a": 1, "b": 2},
            translator_id="basic",
            translator_revision="basic-v1",
            options={"z": 1, "a": {"second": 2, "first": 1}},
        )
        second = canonical_identity(
            source={"b": 2, "a": 1},
            translator_id="basic",
            translator_revision="basic-v1",
            options={"a": {"first": 1, "second": 2}, "z": 1},
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first, self.identity(model="other"))
        self.assertNotEqual(first, self.identity(max_attempts=3))
        self.assertNotEqual(first, canonical_identity(
            source={"a": 1, "b": 3},
            translator_id="basic",
            translator_revision="basic-v1",
            options={"z": 1, "a": 2},
        ))

    def test_save_and_load_preserves_markup_provenance_and_revision(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "checkpoint.json"
            state = self.state(self.identity())
            store = JsonCheckpointStore(path)
            self.assertEqual(store.save(state), path)
            loaded = store.load(state.identity)
            self.assertEqual(loaded, state)
            raw = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(raw["schema"], 1)
        self.assertEqual(raw["validated_segments"][0]["markup"], "<p>Ahoj</p>")
        self.assertEqual(raw["validated_segments"][0]["term_bindings"], ["hello"])

    def test_mismatch_and_invalid_schema_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "checkpoint.json"
            store = JsonCheckpointStore(path)
            state = self.state(self.identity())
            store.save(state)
            with self.assertRaises(CheckpointError) as mismatch:
                store.load("different")
            self.assertEqual(mismatch.exception.code, "identity_mismatch")
            path.write_text('{"schema": 99, "identity": "x"}', encoding="utf-8")
            with self.assertRaises(CheckpointError) as invalid:
                store.load()
            self.assertEqual(invalid.exception.code, "invalid_schema")

    def test_failed_atomic_write_keeps_previous_checkpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "checkpoint.json"
            initial = self.state(self.identity())
            JsonCheckpointStore(path).save(initial)

            def failing_writer(target, payload):
                raise OSError("disk full")

            replacement = self.state(self.identity(model="new"))
            with self.assertRaises(CheckpointError) as failure:
                JsonCheckpointStore(path, atomic_writer=failing_writer).save(replacement)
            self.assertEqual(failure.exception.code, "storage_error")
            self.assertEqual(JsonCheckpointStore(path).load(initial.identity), initial)

    def test_duplicate_segment_ids_are_rejected_before_write(self):
        with self.assertRaises(ValueError):
            CheckpointState(
                identity="x",
                validated_segments=(
                    ValidatedSegment("same", "a", "b"),
                    ValidatedSegment("same", "c", "d"),
                ),
            )


if __name__ == "__main__":
    unittest.main()
