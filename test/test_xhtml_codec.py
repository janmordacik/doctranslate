import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.translate_core import (
    ResourceReference,
    SourceMetadata,
    XhtmlBlock,
    XhtmlCodec,
    XhtmlCodecError,
    XhtmlDocument,
)


class XhtmlCodecTests(unittest.TestCase):
    def document(self):
        return XhtmlDocument(
            metadata=SourceMetadata(
                source_path="book.pdf",
                media_type="application/pdf",
                source_language="en",
                target_language="cs",
                page_count=2,
                title="Book",
                source_sha256="abc",
                resources=(
                    ResourceReference("source", "source-template", "application/pdf", "book.pdf", "abc"),
                ),
                extensions={"pdf": {"rotation": 0}},
            ),
            blocks=(
                XhtmlBlock("p1", 1, 0, "Tom & Jerry", '<p>Tom &amp; Jerry<br/>!</p>', bbox=(1, 2, 3, 4)),
                XhtmlBlock("p2", 2, 1, "Chapter", "<h1>Chapter</h1>", style={"raw": "font-weight:bold"}),
            ),
        )

    def test_roundtrip_preserves_metadata_markup_and_order(self):
        with tempfile.TemporaryDirectory() as folder:
            path = XhtmlCodec().dump(self.document(), Path(folder) / "book.xhtml")
            loaded = XhtmlCodec().load(path)
        self.assertEqual(loaded.metadata.source_sha256, "abc")
        self.assertEqual(loaded.metadata.resources[0].role, "source-template")
        self.assertEqual([item.block_id for item in loaded.blocks], ["p1", "p2"])
        self.assertEqual(loaded.blocks[0].text, "Tom & Jerry!")
        self.assertIn("<br/>", loaded.blocks[0].markup)
        self.assertEqual(loaded.blocks[1].style["raw"], "font-weight:bold")

    def test_manual_body_edit_is_loaded_as_authoritative_text(self):
        with tempfile.TemporaryDirectory() as folder:
            path = XhtmlCodec().dump(self.document(), Path(folder) / "book.xhtml")
            value = path.read_text(encoding="utf-8").replace("Chapter", "Kapitola")
            path.write_text(value, encoding="utf-8")
            loaded = XhtmlCodec().load(path)
        self.assertEqual(loaded.blocks[1].text, "Kapitola")

    def test_rejects_duplicate_ids_and_active_elements(self):
        with tempfile.TemporaryDirectory() as folder:
            path = XhtmlCodec().dump(self.document(), Path(folder) / "book.xhtml")
            value = path.read_text(encoding="utf-8").replace('data-block-id="p2"', 'data-block-id="p1"')
            path.write_text(value, encoding="utf-8")
            with self.assertRaises(XhtmlCodecError):
                XhtmlCodec().load(path)

            path.write_text(path.read_text(encoding="utf-8").replace("</body>", "<script>x</script></body>"), encoding="utf-8")
            with self.assertRaises(XhtmlCodecError):
                XhtmlCodec().load(path)

    def test_unknown_newer_schema_is_rejected_without_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "book.xhtml"
            path.write_text(
                '<meta name="doctranslate-metadata" content="'
                + __import__("base64").urlsafe_b64encode(
                    json.dumps({"schema": 999, "source": {}}).encode()
                ).decode()
                + '"/>',
                encoding="utf-8",
            )
            with self.assertRaises(XhtmlCodecError):
                XhtmlCodec().load(path)


if __name__ == "__main__":
    unittest.main()
