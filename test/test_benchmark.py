import sys
import threading
import unittest

sys.path.insert(0, "src")

from doctranslate.ai.benchmark import BenchmarkRunner
from doctranslate.ai.benchmark_fixtures import load_builtin_fixtures
from doctranslate.ai.contracts import BackendError


class FakeBackend:
    def __init__(self, model):
        self.model = model

    def translate(self, text, source_language, target_language, *, target_variant="auto"):
        if self.model == "broken":
            raise BackendError("provider_error", "synthetic failure")
        return f"{self.model}:{target_variant}:{text}"


class BenchmarkTests(unittest.TestCase):
    def test_runs_equal_fixture_four_times_and_reports_warm_median(self):
        fixture = load_builtin_fixtures()[0]
        result = BenchmarkRunner(FakeBackend, repeats=4).run(["small"], fixture)
        self.assertEqual(len(result.samples), 4)
        self.assertEqual([sample.run_index for sample in result.samples], [0, 1, 2, 3])
        self.assertTrue(all(sample.status == "ok" for sample in result.samples))
        self.assertEqual(result.samples[0].target_variant, "auto")
        self.assertIsNotNone(result.warm_median_ms("small"))

    def test_backend_failure_is_recorded_and_next_model_continues(self):
        fixture = load_builtin_fixtures()[0]
        result = BenchmarkRunner(FakeBackend, repeats=1).run(["broken", "small"], fixture)
        self.assertEqual(result.samples[0].status, "error")
        self.assertEqual(result.samples[0].error_code, "provider_error")
        self.assertEqual(result.samples[1].status, "ok")

    def test_cancel_stops_before_next_model(self):
        fixture = load_builtin_fixtures()[0]
        event = threading.Event()
        event.set()
        result = BenchmarkRunner(FakeBackend).run(["small"], fixture, cancel_event=event)
        self.assertTrue(result.interrupted)
        self.assertEqual(result.samples, ())


if __name__ == "__main__":
    unittest.main()
