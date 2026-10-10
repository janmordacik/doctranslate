import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate import translate
from doctranslate.translate import configure_from_html, preflight_input_pdf


class CliInputTests(unittest.TestCase):
    def test_missing_html_reports_similar_filename_without_touching_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            similar = root / "Book – translated.html"
            similar.write_text("<html></html>", encoding="utf-8")
            missing = root / "Book - translated.html"
            args = SimpleNamespace(
                htmlfile=missing,
                infile=None,
                outfile=None,
                inlang=None,
                outlang=None,
            )
            with self.assertRaisesRegex(ValueError, r"Translation HTML does not exist") as caught:
                configure_from_html(args)
            self.assertIn(similar.name, str(caught.exception))

    def test_pdf_without_extractable_text_is_rejected_before_translation(self):
        class Page:
            def get_text(self, _kind):
                return ""

        class Document:
            needs_pass = False

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def __len__(self):
                return 1

            def __iter__(self):
                return iter((Page(),))

        with tempfile.TemporaryDirectory() as directory:
            with patch.object(translate.fitz, "open", return_value=Document()):
                with patch.object(translate, "INPUT_PDF", Path(directory) / "scan.pdf"):
                    with patch.object(translate, "PHASE", "html"):
                        with self.assertRaisesRegex(ValueError, "no extractable text"):
                            preflight_input_pdf()


if __name__ == "__main__":
    unittest.main()
