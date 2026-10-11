import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.ai import (
    AiProfile, ApiKeyAuth, MemoryCredentialStore, ProfileStore,
    build_default_provider_registry, probe_profile, save_profile_configuration,
)
from doctranslate.ai.contracts import BackendError
from doctranslate.ai.openai import OpenAIBackend
from doctranslate.ai.transport import HttpResponse


class FakeTransport:
    def __init__(self, body, status=200):
        self.body = body
        self.status = status
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return HttpResponse(self.status, {}, self.body)


class CloudConfigurationTests(unittest.TestCase):
    def profile(self):
        return AiProfile("cloud", 1, "openai", "gpt-test", "api_key", "key")

    def test_probe_uses_model_listing_without_generation(self):
        transport = FakeTransport({"data": [{"id": "gpt-test"}]})
        backend = OpenAIBackend(
            "gpt-test", base_url="https://example.test/v1", transport=transport,
            credential_store=MemoryCredentialStore(), auth=ApiKeyAuth("key"),
        )
        backend.credential_store.set("key", "secret")
        result = backend.probe()
        self.assertTrue(result.ok)
        self.assertEqual(result.status, "available")
        self.assertEqual(transport.calls[0][0], "GET")
        self.assertNotIn("secret", result.message + str(result.remedy))

    def test_probe_distinguishes_missing_model_and_auth(self):
        missing = OpenAIBackend(
            "missing", base_url="https://example.test/v1",
            transport=FakeTransport({"data": [{"id": "gpt-test"}]}),
            credential_store=MemoryCredentialStore(), auth=ApiKeyAuth("key"),
        )
        missing.credential_store.set("key", "secret")
        self.assertEqual(missing.probe().status, "model_not_found")
        denied = OpenAIBackend(
            "gpt-test", base_url="https://example.test/v1",
            transport=FakeTransport({}, status=401),
            credential_store=MemoryCredentialStore(), auth=ApiKeyAuth("key"),
        )
        denied.credential_store.set("key", "secret")
        self.assertEqual(denied.probe().status, "auth_required")

    def test_save_configuration_keeps_secret_out_of_profile(self):
        with tempfile.TemporaryDirectory() as folder:
            profiles = ProfileStore(Path(folder) / "config.json")
            store = MemoryCredentialStore()
            saved = save_profile_configuration(
                self.profile(), profiles, store, model="gpt-new",
                credential_ref="", api_key="secret", base_url="https://example.test/v1",
                oauth_client_id="123456.apps.googleusercontent.com",
            )
            persisted = profiles.get("cloud")
        self.assertEqual(saved.credential_ref, "keyring:openai:cloud")
        self.assertEqual(store.get(saved.credential_ref), "secret")
        self.assertNotIn("secret", str(persisted.to_dict()))
        self.assertEqual(persisted.options["base_url"], "https://example.test/v1")
        self.assertEqual(
            persisted.options["oauth_client_id"],
            "123456.apps.googleusercontent.com",
        )

    def test_registry_publishes_cloud_capabilities(self):

        registry = build_default_provider_registry()
        self.assertTrue(registry.get("openai").configuration_supported)
        self.assertTrue(registry.get("openai").model_discovery_supported)
        self.assertTrue(registry.get("gemini").login_supported)
        self.assertFalse(registry.get("claude").login_supported)
    def test_probe_maps_endpoint_and_rate_limit_failures(self):
        for status, expected in ((429, "rate_limited"), (503, "service_unavailable")):
            backend = OpenAIBackend(
                "gpt-test", base_url="https://example.test/v1",
                transport=FakeTransport({}, status=status),
                credential_store=MemoryCredentialStore(), auth=ApiKeyAuth("key"),
            )
            backend.credential_store.set("key", "secret")
            self.assertEqual(backend.probe().status, expected)

    def test_gemini_oauth_profile_uses_bearer_header(self):
        store = MemoryCredentialStore()
        store.set("oauth", json.dumps({"access_token": "oauth-token"}))
        profile = AiProfile("gemini", 1, "gemini", "gemini-test", "oauth", "oauth")
        backend = build_default_provider_registry().get("gemini").factory(profile, store)
        backend.transport = FakeTransport({"models": [{"name": "models/gemini-test"}]})
        self.assertEqual(backend.list_models(), ("gemini-test",))
        headers = backend.transport.calls[0][2]["headers"]
        self.assertEqual(headers["Authorization"], "Bearer oauth-token")
        self.assertNotIn("x-goog-api-key", headers)



if __name__ == "__main__":
    unittest.main()

