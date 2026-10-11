import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate import translate


class GeneratedFilenameTests(unittest.TestCase):
    def test_generated_stem_removes_diacritics_but_keeps_spaces_and_hyphens(self):
        value = translate.normalize_generated_stem(
            "Lucio Russo – Zapomenutá revoluce"
        )
        self.assertEqual(value, "Lucio Russo - Zapomenuta revoluce")

    def test_suggested_output_normalizes_only_application_created_name(self):
        source = Path("Lucio Russo – Zapomenutá revoluce.pdf")
        self.assertEqual(
            translate.suggested_output(source, "cs").name,
            "Lucio Russo - Zapomenuta revoluce-cs-layout.pdf",
        )

    def test_explicit_output_path_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "Vstup – kniha.pdf"
            target = root / "Výstup – moje verze.pdf"
            source.write_bytes(b"%PDF-1.7")
            previous = (
                translate.INPUT_PDF,
                translate.OUTPUT_PDF,
                translate.PLAN_FILE,
                translate.CACHE_FILE,
                translate.HTML_FILE,
            )
            try:
                translate.configure(source, target, "en", "cs")
                self.assertEqual(translate.OUTPUT_PDF, target.resolve())
                self.assertEqual(
                    translate.HTML_FILE.name,
                    "Vystup - moje verze.html",
                )
            finally:
                (translate.INPUT_PDF, translate.OUTPUT_PDF,
                 translate.PLAN_FILE, translate.CACHE_FILE,
                 translate.HTML_FILE) = previous

    def test_existing_legacy_sidecar_remains_readable(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "Výstup.pdf"
            legacy = target.with_suffix(".html")
            legacy.write_text("legacy", encoding="utf-8")
            self.assertEqual(translate.generated_sidecar(target, ".html"), legacy)

    def test_explicit_style_allows_same_language_conversion(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            target = Path(directory) / "target.pdf"
            source.write_bytes(b"%PDF-1.7")
            previous = translate.TARGET_VARIANT
            try:
                translate.TARGET_VARIANT = "cs-expert"
                translate.configure(source, target, "cs", "cs")
            finally:
                translate.TARGET_VARIANT = previous


if __name__ == "__main__":
    unittest.main()
