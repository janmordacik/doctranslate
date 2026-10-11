from pathlib import Path
import sys
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.ai.contracts import SegmentRequest, SegmentResult
from doctranslate.integration import (
    LegacyBatchAdapter,
    TranslationBridgeError,
    document_to_legacy_groups,
    legacy_groups_to_document,
)
from doctranslate.translation import TranslationContext, TranslationOptions


def legacy_groups():
    return [
        (
            0,
            [
                {
                    "block_id": "custom-a",
                    "markup": "<span>Hello</span><br/><math>x</math>",
                    "bbox": (1, 2, 30, 40),
                    "rotation": 90,
                    "styles": {"font": ("Times", 12)},
                    "row_layout": [{"baseline": 10}],
                    "images": [{"resource_id": "figure-1"}],
                },
                {
                    "markup": "<p>World</p>",
                    "bbox": (5, 6, 50, 60),
                    "styles": {"font": ("Times", 10)},
                },
            ],
        )
    ]


class TranslationBridgeTests(unittest.TestCase):
    def test_round_trip_preserves_layout_resources_and_inline_markup(self):
        metadata = {
            "input": "book.pdf",
            "inlang": "en",
            "outlang": "cs",
            "source_hash": "hash",
            "layout_revision": 2,
            "resources": [
                {
                    "resource_id": "figure-1",
                    "role": "image",
                    "media_type": "image/png",
                    "path": "figure.png",
                }
            ],
        }
        original = legacy_groups()
        document = legacy_groups_to_document(metadata, original)
        self.assertEqual(document.blocks[0].block_id, "custom-a")
        self.assertEqual(document.blocks[0].bbox, (1.0, 2.0, 30.0, 40.0))
        self.assertEqual(document.blocks[0].attributes["rotation"], 90)
        self.assertEqual(len(document.metadata.resources), 1)

        translated = document.with_blocks(
            [
                document.blocks[0].translated(
                    "Ahoj",
                    "<span>Ahoj</span><br/><math>x</math>",
                ),
                document.blocks[1].translated("Svete", "<p>Svete</p>"),
            ]
        )
        restored = document_to_legacy_groups(translated, original)
        first = restored[0][1][0]
        second = restored[0][1][1]
        self.assertEqual(first["markup"], "<span>Ahoj</span><br/><math>x</math>")
        self.assertEqual(first["rotation"], 90)
        self.assertEqual(first["images"], [{"resource_id": "figure-1"}])
        self.assertEqual(first["bbox"], (1, 2, 30, 40))
        self.assertEqual(second["markup"], "<p>Svete</p>")

    def test_mapping_mismatch_is_rejected_before_writing_legacy_groups(self):
        document = legacy_groups_to_document({"inlang": "en", "outlang": "cs"}, legacy_groups())
        changed = document.with_blocks(tuple(document.blocks[:1]))
        with self.assertRaises(TranslationBridgeError) as failure:
            document_to_legacy_groups(changed, legacy_groups())
        self.assertEqual(failure.exception.code, "mapping_mismatch")

    def test_legacy_batch_adapter_forwards_contract_without_importing_legacy_module(self):
        calls = []
        context = TranslationContext()
        options = TranslationOptions("en", "cs")
        requests = (
            SegmentRequest("a", "Hello", "en", "cs"),
        )

        def execute(batch, selected, runtime):
            calls.append((batch, selected, runtime))
            return (SegmentResult("a", "Ahoj"),)

        result = LegacyBatchAdapter(execute).execute(
            requests, options, context=context
        )
        self.assertEqual(result[0].text, "Ahoj")
        self.assertIs(calls[0][0], requests)
        self.assertIs(calls[0][1], options)
        self.assertIs(calls[0][2], context)

    def test_custom_ids_are_used_for_reverse_mapping(self):
        groups = [(0, [{"block_id": "custom-a", "markup": "Hello"}])]
        document = legacy_groups_to_document(
            {"inlang": "en", "outlang": "cs"},
            groups,
            {"custom-a": "<span>Ahoj</span>"},
        )
        self.assertEqual(document.blocks[0].text, "Ahoj")
        translated = document.with_blocks(
            (document.blocks[0].translated("Ahoj", "Ahoj"),)
        )
        self.assertEqual(
            document_to_legacy_groups(translated, groups)[0][1][0]["markup"],
            "Ahoj",
        )


if __name__ == "__main__":
    unittest.main()
