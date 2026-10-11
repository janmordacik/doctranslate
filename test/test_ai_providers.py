from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.ai import (
    AiProfile,
    ApiKeyAuth,
    MemoryCredentialStore,
    build_default_provider_registry,
)
from doctranslate.ai.contracts import BackendError
from doctranslate.ai.transport import HttpResponse
from doctranslate.ai.claude import ClaudeBackend
from doctranslate.ai.gemini import GeminiBackend
from doctranslate.ai.ollama import OllamaBackend, is_translategemma_model
from doctranslate.ai.openai import OpenAIBackend


class FakeTransport:
    def __init__(self, body, status=200):
        self.body = body
        self.status = status
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return HttpResponse(self.status, {}, self.body)


class OllamaRuntimeTransport(FakeTransport):
    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if url.endswith("/api/tags"):
            body = {
                "models": [{
                    "name": "translategemma:4b",
                    "size": 3_300_000_000,
                    "details": {"context_length": 131072},
                }],
            }
        elif url.endswith("/api/ps"):
            body = {
                "models": [{
                    "model": "translategemma:4b",
                    "size": 3_500_000_000,
                    "size_vram": 3_200_000_000,
                    "context_length": 8192,
                }],
            }
        else:
            body = {"message": {"content": "Ahoj"}}
        return HttpResponse(200, {}, body)


class ProviderTests(unittest.TestCase):
    def credentials(self):
        store = MemoryCredentialStore()
        store.set("key", "sentinel-api-key")
        return store

    def test_ollama_native_response(self):
        transport = FakeTransport({"message": {"content": "Ahoj"}})
        backend = OllamaBackend("translategemma:12b", transport=transport)
        self.assertEqual(backend.translate("Hello", "en", "cs"), "Ahoj")
        self.assertIn("/api/chat", transport.calls[0][1])
        prompt = transport.calls[0][2]["payload"]["messages"][0]["content"]
        self.assertIn("professional English (en) to Czech (cs) translator", prompt)
        self.assertIn("Produce only the Czech translation", prompt)
        self.assertTrue(is_translategemma_model("translategemma:12b@sha256:test"))
        self.assertTrue(is_translategemma_model("translategemma:4b"))
        self.assertFalse(is_translategemma_model("qwen3.8:27b"))

    def test_ollama_runtime_capabilities_are_logged_from_api(self):
        transport = OllamaRuntimeTransport(None)
        events = []
        backend = OllamaBackend("translategemma:4b", transport=transport)
        backend.configure_runtime(
            logger=lambda event, **fields: events.append((event, fields)),
        )

        self.assertEqual(backend.translate("Hello", "en", "cs"), "Ahoj")
        runtime_events = [fields for event, fields in events if event == "worker.translation.ollama.runtime"]
        self.assertEqual(len(runtime_events), 2)
        self.assertEqual(runtime_events[0]["supported_context"], 131072)
        self.assertEqual(runtime_events[0]["runtime_context"], 8192)
        self.assertEqual(runtime_events[0]["model_size"], 3_300_000_000)
        self.assertEqual(runtime_events[0]["runtime_size_vram"], 3_200_000_000)
        chat = next(call for call in transport.calls if call[1].endswith("/api/chat"))
        self.assertNotIn("num_ctx", chat[2]["payload"]["options"])

    def test_cloud_provider_responses_and_auth_headers(self):
        openai = FakeTransport({"choices": [{"message": {"content": "Ahoj"}}]})
        backend = OpenAIBackend(
            "gpt-test", transport=openai, credential_store=self.credentials(),
            auth=ApiKeyAuth("key"), base_url="https://example.test/v1",
        )
        self.assertEqual(backend.translate("Hello", "en", "cs"), "Ahoj")
        self.assertEqual(openai.calls[0][2]["headers"]["Authorization"], "Bearer sentinel-api-key")

        gemini = FakeTransport({"candidates": [{"content": {"parts": [{"text": "Ahoj"}]}}]})
        gemini_backend = GeminiBackend(
            "gemini-test", transport=gemini, credential_store=self.credentials(),
            auth=ApiKeyAuth("key"), base_url="https://example.test/v1beta",
        )
        self.assertEqual(gemini_backend.translate("Hello", "en", "cs"), "Ahoj")
        self.assertNotIn("sentinel-api-key", gemini.calls[0][1])
        self.assertEqual(gemini.calls[0][2]["headers"]["x-goog-api-key"], "sentinel-api-key")

        claude = FakeTransport({"content": [{"type": "text", "text": "Ahoj"}]})
        claude_backend = ClaudeBackend(
            "claude-test", transport=claude, credential_store=self.credentials(),
            auth=ApiKeyAuth("key"), base_url="https://example.test",
        )
        self.assertEqual(claude_backend.translate("Hello", "en", "cs"), "Ahoj")
        self.assertEqual(claude.calls[0][2]["headers"]["x-api-key"], "sentinel-api-key")

    def test_http_errors_are_provider_neutral_and_retryable_when_appropriate(self):
        for status, code, retryable in ((401, "auth_required", False), (429, "rate_limited", True), (503, "service_unavailable", True)):
            transport = FakeTransport({}, status=status)
            backend = OllamaBackend("model", transport=transport)
            with self.assertRaises(BackendError) as context:
                backend.translate("Hello", "en", "cs")
            self.assertEqual(context.exception.code, code)
            self.assertEqual(context.exception.retryable, retryable)

    def test_default_registry_is_lazy_and_creates_profiles(self):
        registry = build_default_provider_registry()
        self.assertEqual([item.provider_id for item in registry.list()], ["claude", "gemini", "ollama", "openai"])
        profile = AiProfile("local", 1, "ollama", "model")
        self.assertEqual(registry.create(profile, self.credentials()).provider_id, "ollama")


if __name__ == "__main__":
    unittest.main()
