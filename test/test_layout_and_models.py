import sys
import unittest
from pathlib import Path

import pymupdf as fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.queue_app import parse_ollama_models
from doctranslate.translate import (annotate_inline_fragments, hard_line_breaks,
                                    layout_block, preserve_number_prefix)


def pdf_line(text, x, baseline):
    span = {"text": text, "size": 10.9, "origin": (x, baseline)}
    return {
        "bbox": (x, baseline - 10, x + max(8, len(text) * 5), baseline + 2),
        "spans": [span],
    }


class TocLayoutTests(unittest.TestCase):
    def test_toc_subsection_number_is_preserved_from_source(self):
        source = "7.5 Filologické a lingvistické studie . . . 221"
        translated = "7.6 Filologické a lingvistické studie . . . 221"
        self.assertEqual(preserve_number_prefix(source, translated), source)

    def test_standalone_subsection_numbers_start_new_rows(self):
        lines = [
            pdf_line("1", 92, 100),
            pdf_line("Zrození vědy", 109, 100),
            pdf_line("5", 470, 100),
            pdf_line("1.1", 109, 114),
            pdf_line("Smazání vědecké revoluce . . . . . . . .", 137, 114),
            pdf_line("5", 470, 114),
            pdf_line("1.2", 109, 128),
            pdf_line("O slově", 137, 128),
            pdf_line(". . . . . . . . . .", 275, 128),
            pdf_line("10", 469, 128),
            pdf_line("1.3", 109, 142),
            pdf_line("Věda . . . . . . . . . .", 137, 142),
            pdf_line("15", 469, 142),
        ]
        self.assertEqual(hard_line_breaks(lines), {3, 6, 10})

    def test_overlapping_inline_fragment_keeps_source_indent(self):
        previous = {"rect": fitz.Rect(92, 500, 480, 542)}
        block = {
            "rect": fitz.Rect(92, 530, 480, 607),
            "size": 10,
            "line_height": 1.0,
            "lines": [
                {"bbox": (465, 530, 480, 544),
                 "spans": [{"text": "7", "origin": (465, 540)}]},
                {"bbox": (92, 541, 480, 552),
                 "spans": [{"text": "the", "origin": (92, 551)}]},
            ],
            "line_idents": [["s0", "s2"], ["s3"]],
            "styles": {
                "s0": ("Times", 10, 0, 0),
                "s2": ("Times", 10, 0, 0),
                "s3": ("Times", 10, 0, 0),
            },
            "markup": '<span id="s0">7 </span><span id="s2">of </span>'
                      '<span id="s3">the actual value</span>',
            "breaks": 0,
        }
        annotate_inline_fragments([previous, block])

        self.assertEqual(block["inline_fragment"]["prefix_end"], "s2")
        self.assertGreater(block["inline_fragment"]["indent"], 300)

        class Fonts:
            faces = {}
            folder = "."

            @staticmethod
            def resolve(_source, _page, _style, _text):
                return "serif"

        markup, _css = layout_block(
            None,
            None,
            block,
            '<span id="s0">7 </span><span id="s2">z </span>'
            '<span id="s3">skutečné hodnoty</span>',
            Fonts(),
        )
        self.assertIn('margin-left:373pt', markup)
        self.assertIn('margin-top:1pt', markup)
        self.assertGreater(markup.index("skutečné"), markup.index("margin-top:1pt"))


class OllamaModelTests(unittest.TestCase):
    def test_parse_ollama_models_returns_unique_sorted_names(self):
        payload = {"models": [{"name": "qwen3.8:27b"}, {"name": "translategemma:12b"},
                              {"name": "qwen3.8:27b"}, {"name": ""}, {"digest": "missing"}]}
        self.assertEqual(parse_ollama_models(payload), ("qwen3.8:27b", "translategemma:12b"))

    def test_parse_ollama_models_handles_unavailable_response(self):
        self.assertEqual(parse_ollama_models({"error": "offline"}), ())


if __name__ == "__main__":
    unittest.main()
