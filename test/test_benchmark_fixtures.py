import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, "src")

from doctranslate.ai.benchmark_fixtures import (
    BenchmarkFixtureError,
    load_builtin_fixtures,
)


class BenchmarkFixtureTests(unittest.TestCase):
    def test_builtin_fixtures_are_versioned_and_have_provenance(self):
        fixtures = load_builtin_fixtures()
        self.assertEqual([fixture.id for fixture in fixtures], [
            "en-cs-escalating-01",
            "cs-cs-register-01",
        ])
        self.assertTrue(all(fixture.version and fixture.provenance for fixture in fixtures))
        self.assertTrue(all(fixture.content_hash for fixture in fixtures))

    def test_fixture_hash_is_recomputed_from_source(self):
        fixture = load_builtin_fixtures()[0]
        self.assertEqual(
            fixture.content_hash,
            hashlib.sha256(fixture.source.encode("utf-8")).hexdigest(),
        )
        self.assertIn("42", fixture.source)
        self.assertIn("3.14", fixture.source)
        self.assertIn("{{name}}", fixture.source)

    def test_invalid_declared_hash_is_rejected(self):
        path = Path("src/doctranslate/ai/data/benchmark.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["fixtures"][0]["content_hash"] = "invalid"
        from doctranslate.ai.benchmark_fixtures import BenchmarkFixture

        with self.assertRaises(BenchmarkFixtureError):
            BenchmarkFixture.from_dict(payload["fixtures"][0])


if __name__ == "__main__":
    unittest.main()
