from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.formats import (
    Availability,
    FormatDescriptor,
    FormatRegistry,
    FormatSelectionError,
    build_default_registry,
)


class FormatRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = FormatRegistry()
        self.registry.register(FormatDescriptor(
            "text", "Text", "text/plain", (".txt",), lambda: "reader", "input"
        ))
        self.registry.register(FormatDescriptor(
            "text", "Text", "text/plain", (".txt",), lambda: "writer", "output"
        ))

    def test_explicit_and_extension_selection_are_directional(self):
        self.assertEqual(self.registry.resolve("input", "book.txt").id, "text")
        self.assertEqual(self.registry.create("output", "book.txt"), "writer")

    def test_missing_extension_requires_explicit_format(self):
        with self.assertRaisesRegex(FormatSelectionError, "specify"):
            self.registry.resolve("input", "book")

    def test_conflict_and_duplicate_are_descriptive(self):
        self.registry.register(FormatDescriptor(
            "other", "Other", "text/other", (".txt",), lambda: "other", "input"
        ))
        with self.assertRaisesRegex(FormatSelectionError, "ambiguous"):
            self.registry.resolve("input", "book.txt")
        with self.assertRaisesRegex(FormatSelectionError, "Duplicate"):
            self.registry.register(FormatDescriptor(
                "text", "Again", "text/plain", (".md",), lambda: "x", "input"
            ))

    def test_unavailable_factory_is_not_called(self):
        called = []
        self.registry.register(FormatDescriptor(
            "missing", "Missing", "x/missing", (".missing",),
            lambda: called.append(True), "input",
            lambda: Availability(False, "missing_dependency", "not installed", "install it"),
        ))
        with self.assertRaisesRegex(FormatSelectionError, "install it"):
            self.registry.resolve("input", "a.missing")
        self.assertEqual(called, [])

    def test_default_pdf_registry_lists_without_eager_pdf_import(self):
        registry = build_default_registry()
        self.assertEqual([item.id for item in registry.descriptors("input")], ["pdf"])
        self.assertEqual(registry.get("output", "pdf").media_type, "application/pdf")


if __name__ == "__main__":
    unittest.main()
