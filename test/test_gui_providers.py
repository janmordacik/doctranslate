from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.gui.provider_dialogs import provider_options
from doctranslate.queue_app import GUI_TEXT, make_job


class GuiProviderTests(unittest.TestCase):
    def test_provider_options_are_provider_specific(self):
        ollama = provider_options("ollama")
        self.assertFalse(ollama["has_profile"])
        self.assertFalse(ollama["has_configuration"])
        self.assertTrue(ollama["model_discovery"])

        gemini = provider_options("gemini")
        self.assertTrue(gemini["has_profile"])
        self.assertTrue(gemini["has_configuration"])
        self.assertTrue(gemini["supports_login"])

        self.assertFalse(provider_options("openai")["supports_login"])
        self.assertTrue(provider_options("claude")["requires_api_key"])

    def test_job_contains_provider_profile_and_model_without_secret(self):
        job = make_job(
            "book.pdf",
            model="gpt-test",
            provider="openai",
            profile="work",
        )
        self.assertEqual(job["provider"], "openai")
        self.assertEqual(job["profile"], "work")
        self.assertNotIn("api_key", job)
        self.assertIn("provider", GUI_TEXT["cs"])
        self.assertIn("configure", GUI_TEXT["en"])


if __name__ == "__main__":
    unittest.main()
