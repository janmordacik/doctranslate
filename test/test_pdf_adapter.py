from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pymupdf

from doctranslate.translate_core import PdfInputAdapter, PdfOutputAdapter
from doctranslate.translate_core.pdf_adapter import PdfResourceError, resolve_source_resource


class PdfAdapterTests(unittest.TestCase):
    def test_input_exposes_template_resource_and_page_layout(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.pdf"
            document = pymupdf.open()
            page = document.new_page(width=200, height=100)
            page.insert_text((20, 30), "Hello")
            document.save(source)
            document.close()
            model = PdfInputAdapter().read(source)
            resolved = resolve_source_resource(model, Path(folder))
        self.assertEqual(model.metadata.page_count, 1)
        self.assertEqual(model.metadata.resources[0].role, "source-template")
        self.assertEqual(resolved, source.resolve())
        self.assertEqual(model.metadata.attributes["page_layouts"][0]["width"], 200.0)

    def test_hash_mismatch_is_rejected_and_writer_receives_document_and_target(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.pdf"
            source.write_bytes(b"pdf")
            model = PdfInputAdapter.__new__(PdfInputAdapter)
            from doctranslate.translate_core import SourceMetadata, XhtmlDocument
            model = XhtmlDocument(
                SourceMetadata("source.pdf", "application/pdf", "en", "cs",
                                source_sha256="wrong"),
                (),
            )
            with self.assertRaises(PdfResourceError):
                resolve_source_resource(model, Path(folder))

            received = []
            output = Path(folder) / "out.pdf"
            adapter = PdfOutputAdapter(lambda document, target: received.append((document, target)))
            self.assertEqual(adapter.write(model, output), output)
            self.assertEqual(received[0][1], output)


if __name__ == "__main__":
    unittest.main()
