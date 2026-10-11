import json
import unittest

from doctranslate.ai.context_backend import (
    ContextualCapability,
    ContextualRequest,
    decode_contextual_results,
    require_contextual_capability,
)
from doctranslate.ai.contracts import BackendError
from doctranslate.ai.ollama import OllamaBackend
from doctranslate.ai.transport import HttpResponse
from doctranslate.translation.context import ContextEnvelope


class FakeTransport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def request(self, method, url, *, headers, payload, timeout):
        self.calls.append((method, url, payload))
        return self.response


class ContextualBackendTests(unittest.TestCase):
    def setUp(self):
        self.requests = (
            ContextualRequest("b", "Hello", "en", "cs", markup="<p>Hello</p>"),
            ContextualRequest("a", "World", "en", "cs", markup="<p>World</p>"),
        )
        self.envelope = ContextEnvelope(
            source_text="Hello World", source_language="en", target_language="cs",
            instructions="Use the approved terminology and return JSON.",
        )

    def test_capability_without_port_is_rejected(self):
        with self.assertRaises(BackendError) as error:
            require_contextual_capability(object())
        self.assertEqual(error.exception.code, "context_unsupported")

    def test_unavailable_capability_is_typed(self):
        class Backend:
            def contextual_capability(self):
                return ContextualCapability(False, "model lacks structured output")
        with self.assertRaises(BackendError) as error:
            require_contextual_capability(Backend())
        self.assertEqual(error.exception.code, "context_unsupported")

    def test_decoder_restores_request_order_and_markup(self):
        result = decode_contextual_results(
            {"segments": [{"id": "a", "text": "Svět"}, {"id": "b", "text": "Ahoj"}]},
            self.requests,
        )
        self.assertEqual([item.segment_id for item in result], ["b", "a"])
        self.assertEqual(result[0].markup, "<p>Hello</p>")

    def test_ollama_payload_keeps_context_separate_and_uses_fake_transport(self):
        response = {"message": {"content": json.dumps(
            {"segments": [{"id": "b", "text": "Ahoj"}, {"id": "a", "text": "Svět"}]},
            ensure_ascii=False
        )}}
        transport = FakeTransport(HttpResponse(200, {}, response))
        backend = OllamaBackend("translategemma:4b", transport=transport)
        result = backend.translate_batch(self.requests, self.envelope)
        self.assertEqual([item.text for item in result], ["Ahoj", "Svět"])
        self.assertEqual(backend.contextual_capability().prompt_revision, "translategemma-prompt-v1")
        payload = transport.calls[0][2]
        self.assertEqual(payload["format"], "json")
        self.assertIn("approved terminology", payload["messages"][0]["content"])
        user = json.loads(payload["messages"][1]["content"])
        self.assertEqual(user["source"]["segments"][0]["text"], "Hello")
        self.assertNotIn("approved terminology", user["source"]["segments"][0]["text"])
        self.assertIn("context", user)

    def test_decoder_rejects_missing_or_unexpected_ids(self):
        with self.assertRaises(BackendError):
            decode_contextual_results({"segments": [{"id": "b", "text": "Ahoj"}]}, self.requests)
        with self.assertRaises(BackendError):
            decode_contextual_results({"segments": [{"id": "b", "text": "Ahoj"}, {"id": "x", "text": "?"}]}, self.requests)


if __name__ == "__main__":
    unittest.main()
