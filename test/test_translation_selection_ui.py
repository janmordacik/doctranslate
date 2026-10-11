import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from doctranslate.queue_app import (
    QueueStore,
    cli_main,
    make_job,
    translation_module_catalog,
)
from doctranslate.translate import cli_parser, entrypoint


class TranslationSelectionTests(unittest.TestCase):
    def test_catalog_exposes_production_advanced_module(self):
        catalog = {item["id"]: item for item in translation_module_catalog()}
        self.assertTrue(catalog["basic"]["available"])
        self.assertTrue(catalog["advanced"]["available"])
        self.assertTrue(catalog["advanced"]["reason"])

    def test_make_job_persists_translator_selection(self):
        job = make_job(Path("book.pdf"), translator_id="advanced",
                      translator_options={"mode": "standard"})
        self.assertEqual(job["translator_id"], "advanced")
        self.assertEqual(job["translator_options"], {"mode": "standard"})

    def test_queue_cli_and_direct_parser_use_same_selection_name(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "book.pdf"
            source.write_bytes(b"%PDF-test")
            queue = root / "queue.json"
            with patch("doctranslate.queue_app.WorkerController.start", return_value=False):
                result = cli_main(["--queue", str(queue), "add", str(source),
                                   "--translator", "advanced"])
            self.assertEqual(result, 0)
            self.assertEqual(QueueStore(queue).jobs()[0]["translator_id"], "advanced")
        self.assertEqual(cli_parser().parse_args(["--translator", "basic"]).translator, "basic")

    def test_direct_runner_rejects_unwired_non_basic_module(self):
        with self.assertRaises(SystemExit):
            entrypoint(["--translator", "advanced", "--infile", "book.pdf"])


if __name__ == "__main__":
    unittest.main()
