import importlib.util
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


REGRESSION_SCRIPT = Path(__file__).parent / "regression" / "translate_regression.py"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_regression():
    spec = importlib.util.spec_from_file_location("translate_regression", REGRESSION_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ArchivedRegressionSuiteTests(unittest.TestCase):
    def test_archived_offline_suite(self):
        suite = load_regression()
        with tempfile.TemporaryDirectory(prefix="doctranslate-regression-") as output:
            result = suite.main([
                "--script", str(PROJECT_ROOT / "src" / "doctranslate" / "translate.py"),
                "--outdir", output,
            ])
        self.assertEqual(result, 0)
