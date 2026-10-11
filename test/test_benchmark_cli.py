import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "src")

from doctranslate.ai.benchmark import BenchmarkResult, BenchmarkSample
from doctranslate.translate import cli_parser


class BenchmarkCliTests(unittest.TestCase):
    def test_parser_distinguishes_absent_empty_and_explicit_models(self):
        parser = cli_parser()
        self.assertIsNone(parser.parse_args([]).benchmark)
        self.assertEqual(parser.parse_args(["--benchmark"]).benchmark, [])
        self.assertEqual(
            parser.parse_args(["--benchmark", "translategemma:4b", "qwen3.8:27b"]).benchmark,
            ["translategemma:4b", "qwen3.8:27b"],
        )
        self.assertEqual(
            parser.parse_args(["--benchmark", "--style", "cs-expert"]).target_variant,
            "cs-expert",
        )

    def test_report_shape_keeps_text_and_timings(self):
        sample = BenchmarkSample(
            "model", "fixture", "hash", "auto", 0, "ok", text="Ahoj", wall_ms=12.5
        )
        result = BenchmarkResult((sample,))
        payload = {
            "samples": [item.__dict__ for item in result.samples],
            "fixture": {"source": "source", "references": ["reference"]},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["samples"][0]["text"], "Ahoj")
        self.assertEqual(loaded["samples"][0]["wall_ms"], 12.5)


if __name__ == "__main__":
    unittest.main()
