import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.__main__ import _print_dependency_error, main


class BootstrapTests(unittest.TestCase):
    def test_queue_status_does_not_import_pdf_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            queue = Path(directory) / "queue.json"
            output = io.StringIO()
            with patch.dict(sys.modules, {"fitz": None}):
                with contextlib.redirect_stdout(output):
                    result = main(["--queue", str(queue), "status"])
            self.assertEqual(result, 0)
            self.assertIn("worker=stopped", output.getvalue())

    def test_missing_pymupdf_has_actionable_message(self):
        error = ModuleNotFoundError("No module named 'fitz'", name="fitz")
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            result = _print_dependency_error(error)
        self.assertEqual(result, 2)
        self.assertIn("PyMuPDF", output.getvalue())
        self.assertIn("pip install", output.getvalue())


if __name__ == "__main__":
    unittest.main()
