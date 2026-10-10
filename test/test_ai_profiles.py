import json
from pathlib import Path
import os
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.ai import (
    AiProfile,
    ApiKeyAuth,
    EnvCredentialStore,
    MemoryCredentialStore,
    ProfileError,
    ProfileStore,
    redact_secrets,
)
from doctranslate.config import save_config


class AiProfileTests(unittest.TestCase):
    def profile(self, **changes):
        value = {
            "profile_id": "local",
            "revision": 1,
            "provider_id": "ollama",
            "model": "translategemma:12b",
            "auth_type": "none",
        }
        value.update(changes)
        return AiProfile(**value)

    def test_profile_roundtrip_preserves_existing_config(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "translate.config.json"
            path.write_text(json.dumps({"schema": 1, "profiles": []}), encoding="utf-8")
            store = ProfileStore(path)
            store.save(self.profile())
            save_config(Path(folder), path, language="cs")
            value = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(value["schema"], 2)
        self.assertEqual(value["language"], "cs")
        self.assertEqual(value["profiles"][0]["model"], "translategemma:12b")

    def test_legacy_config_without_profiles_can_save_provider_profile(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "translate.config.json"
            path.write_text(json.dumps({"schema": 1, "language": "en"}), encoding="utf-8")
            store = ProfileStore(path)
            store.save(self.profile(provider_id="openai", model="gpt-test", auth_type="api_key",
                                     credential_ref="env:OPENAI_API_KEY"))
            value = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(value["schema"], 2)
        self.assertEqual(len(value["profiles"]), 1)
        self.assertEqual(value["profiles"][0]["provider"], "openai")

    def test_revision_is_immutable_and_latest_is_selected(self):
        with tempfile.TemporaryDirectory() as folder:
            store = ProfileStore(Path(folder) / "config.json")
            store.save(self.profile())
            store.save(self.profile(revision=2, model="new-model"))
            selected = store.get("local")
        self.assertEqual(selected.revision, 2)
        self.assertEqual(selected.model, "new-model")

    def test_secrets_are_not_allowed_in_profile_options(self):
        with self.assertRaises(ProfileError):
            self.profile(options={"api_key": "sentinel"})

    def test_credentials_use_store_or_explicit_environment_only(self):
        memory = MemoryCredentialStore()
        memory.set("openai-key", "sentinel")
        self.assertEqual(ApiKeyAuth("openai-key").resolve(memory), "sentinel")
        os.environ["DOCTRANSLATE_TEST_KEY"] = "env-sentinel"
        try:
            self.assertEqual(EnvCredentialStore().get("env:DOCTRANSLATE_TEST_KEY"), "env-sentinel")
        finally:
            os.environ.pop("DOCTRANSLATE_TEST_KEY", None)

    def test_diagnostics_can_redact_secret(self):
        self.assertEqual(redact_secrets({"token": "abc"}, ("abc",)), {"token": "***"})


if __name__ == "__main__":
    unittest.main()
