import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.translate_core import (
    AdapterRegistry,
    MarkupTranslation,
    SourceMetadata,
    TranslationContractError,
    TranslationPipeline,
    XhtmlBlock,
    XhtmlDocument,
)
from doctranslate.translate_core.pipeline import translated_markup


class UpperBackend:
    name = "upper"

    def translate(self, texts, *, source_language, target_language):
        return [text.upper() for text in texts]


class BadBackend:
    name = "bad"

    def translate(self, texts, *, source_language, target_language):
        return list(texts[:-1])


def document():
    return XhtmlDocument(
        metadata=SourceMetadata(
            source_path="book.pdf",
            media_type="application/pdf",
            source_language="en",
            target_language="cs",
        ),
        blocks=(
            XhtmlBlock("p000001_b0001", 1, 0, "hello", bbox=(1, 2, 3, 4)),
            XhtmlBlock("p000001_b0002", 1, 1, "   "),
            XhtmlBlock("p000002_b0001", 2, 0, "world"),
        ),
    )


class CoreContractTests(unittest.TestCase):
    def test_pipeline_preserves_order_and_layout_metadata(self):
        result = TranslationPipeline(UpperBackend()).translate(document())
        self.assertEqual([block.text for block in result.blocks], ["HELLO", "   ", "WORLD"])
        self.assertEqual(result.blocks[0].bbox, (1, 2, 3, 4))
        self.assertEqual(result.metadata.source_path, "book.pdf")

    def test_pipeline_updates_simple_markup_and_preserves_tags(self):
        result = TranslationPipeline(UpperBackend()).translate(
            document().with_blocks((XhtmlBlock("a", 1, 0, "hello", markup="<p>hello</p>"),))
        )
        self.assertEqual(result.blocks[0].markup, "<p>HELLO</p>")

    def test_pipeline_rejects_non_string_backend_value(self):
        class NoneBackend:
            name = "none"
            def translate(self, texts, **kwargs):
                return [None for _ in texts]
        with self.assertRaises(TranslationContractError):
            TranslationPipeline(NoneBackend()).translate(document())

    def test_markup_with_multiple_text_nodes_requires_structured_backend(self):
        with self.assertRaises(TranslationContractError):
            translated_markup("<p>Hello <b>world</b></p>", "Hello world", "Ahoj světe")

    def test_markup_preserves_entities_inline_style_and_hard_break_on_noop(self):
        self.assertEqual(
            translated_markup(
                '<p class="lead">Tom &amp; Jerry</p>',
                "Tom & Jerry",
                "Tomáš & Jerry",
            ),
            '<p class="lead">Tomáš &amp; Jerry</p>',
        )
        hard_break = "<p>Hello<br/>world</p>"
        self.assertEqual(translated_markup(hard_break, "Hello world", "Hello world"), hard_break)

    def test_structured_backend_can_translate_multiple_markup_nodes(self):
        class StructuredBackend:
            name = "structured"

            def translate(self, texts, **_kwargs):
                self.asserted_texts = texts
                return [MarkupTranslation("Ahoj světe", "<p>Ahoj <b>světe</b></p>")]

        source = document().with_blocks(
            (XhtmlBlock("a", 1, 0, "Hello world", markup="<p>Hello <b>world</b></p>"),)
        )
        result = TranslationPipeline(StructuredBackend()).translate(source)
        self.assertEqual(result.blocks[0].text, "Ahoj světe")
        self.assertEqual(result.blocks[0].markup, "<p>Ahoj <b>světe</b></p>")

    def test_pipeline_rejects_wrong_cardinality(self):
        with self.assertRaises(TranslationContractError):
            TranslationPipeline(BadBackend()).translate(document())

    def test_registry_selects_plugins(self):
        registry = AdapterRegistry()
        adapter = object()
        registry.register("application/pdf", adapter)
        self.assertIs(registry.get("APPLICATION/PDF"), adapter)
        self.assertEqual(registry.media_types(), ("application/pdf",))

    def test_core_does_not_require_pdf_runtime(self):
        self.assertEqual(Path("src/doctranslate/translate_core/contracts.py").read_text(encoding="utf-8").count("pymupdf"), 0)


if __name__ == "__main__":
    unittest.main()
