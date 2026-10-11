import json
from pathlib import Path
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.ai import (
    AiProfile,
    ApiKeyAuth,
    EnvCredentialStore,
    MemoryCredentialStore,
    CredentialStoreUnavailable,
    KeyringCredentialStore,
    ProfileError,
    ProfileStore,
    credential_storage_status,
    redact_secrets,
)
from doctranslate.ai.provider_runtime import ChainedCredentialStore
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

    def test_missing_keyring_has_actionable_diagnostic_without_secret(self):
        with patch.dict("sys.modules", {"keyring": None}):
            status = credential_storage_status()
            self.assertFalse(status.available)
            self.assertFalse(status.writable)
            self.assertEqual(status.backend, "unavailable")
            self.assertIn("pip install keyring", status.remedy)
            self.assertNotIn("secret", status.message.lower())

    def test_missing_keyring_store_raises_typed_error_with_remedy(self):
        with patch.dict("sys.modules", {"keyring": None}):
            with self.assertRaises(CredentialStoreUnavailable) as context:
                KeyringCredentialStore()
        self.assertEqual(context.exception.code, "credentials_unavailable")
        self.assertIn("pip install keyring", context.exception.remedy)

    def test_environment_reference_remains_read_only_without_keyring(self):
        store = ChainedCredentialStore()
        with patch.dict("os.environ", {"DOCTRANSLATE_TEST_KEY": "env-secret"}):
            self.assertEqual(store.get("env:DOCTRANSLATE_TEST_KEY"), "env-secret")
        with self.assertRaises(CredentialStoreUnavailable):
            store.set("keyring:openai:profile", "secret")
        with self.assertRaises(CredentialStoreUnavailable):
            EnvCredentialStore().set("env:DOCTRANSLATE_TEST_KEY", "secret")

    def test_available_keyring_can_store_and_read_without_cloud(self):
        values = {}
        fake_keyring = types.SimpleNamespace(
            set_password=lambda service, reference, secret: values.__setitem__((service, reference), secret),
            get_password=lambda service, reference: values.get((service, reference)),
            delete_password=lambda service, reference: values.pop((service, reference), None),
        )
        with patch.dict("sys.modules", {"keyring": fake_keyring}):
            store = KeyringCredentialStore()
            store.set("openai:profile", "secret")
            self.assertEqual(store.get("openai:profile"), "secret")
            status = credential_storage_status()
        self.assertTrue(status.available)
        self.assertTrue(status.writable)
        self.assertTrue(status.backend.startswith("keyring:"))
        self.assertNotIn("secret", status.message)


if __name__ == "__main__":
    unittest.main()
