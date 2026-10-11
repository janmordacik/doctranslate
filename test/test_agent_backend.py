import json
import unittest

from doctranslate.ai.context_backend import (
    AgentCapability,
    AgentTurnRequest,
    decode_agent_turn_response,
    require_agent_capability,
)
from doctranslate.ai.contracts import BackendError
from doctranslate.ai.ollama import OllamaBackend
from doctranslate.ai.transport import HttpResponse


class FakeTransport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def request(self, method, url, *, headers, payload, timeout):
        self.calls.append((method, url, payload))
        return self.response


class AgentBackendTests(unittest.TestCase):
    def test_final_response_is_strict(self):
        response = decode_agent_turn_response(
            '{"type":"final","text":"hotový překlad"}',
            ("lookup_terms",),
        )
        self.assertEqual(response.kind, "final")
        self.assertEqual(response.final_text, "hotový překlad")
        with self.assertRaises(BackendError) as error:
            decode_agent_turn_response(
                {"type": "final", "text": "x", "name": "lookup_terms"},
                ("lookup_terms",),
            )
        self.assertEqual(error.exception.code, "invalid_response")

    def test_tool_response_is_validated_and_bounded(self):
        response = decode_agent_turn_response(
            {
                "type": "tool",
                "call_id": "call-1",
                "name": "lookup_terms",
                "arguments": {"terms": "bank", "limit": 4},
            },
            ("lookup_terms",),
        )
        self.assertEqual(response.kind, "tool")
        self.assertEqual(response.tool_call.name, "lookup_terms")
        self.assertEqual(response.tool_call.arguments["limit"], 4)
        with self.assertRaises(BackendError) as error:
            decode_agent_turn_response(
                {
                    "type": "tool",
                    "call_id": "call-2",
                    "name": "open_file",
                    "arguments": {},
                },
                ("lookup_terms",),
            )
        self.assertEqual(error.exception.code, "unknown_tool")
        with self.assertRaises(BackendError) as error:
            decode_agent_turn_response(
                {"type": "tool", "call_id": "call-3", "name": "lookup_terms", "arguments": []},
                ("lookup_terms",),
            )
        self.assertEqual(error.exception.code, "invalid_response")

    def test_malformed_json_and_hybrid_response_are_rejected(self):
        with self.assertRaises(BackendError) as error:
            decode_agent_turn_response("not-json", ())
        self.assertEqual(error.exception.code, "invalid_response")
        with self.assertRaises(BackendError):
            decode_agent_turn_response(
                {
                    "type": "tool",
                    "call_id": "call-1",
                    "name": "lookup_terms",
                    "arguments": {},
                    "text": "also final",
                },
                ("lookup_terms",),
            )

    def test_capability_never_follows_model_name(self):
        backend = OllamaBackend("translategemma:4b")
        self.assertFalse(backend.agent_capability().available)
        with self.assertRaises(BackendError):
            require_agent_capability(backend)
        enabled = OllamaBackend("translategemma:4b", agent_tools_enabled=True)
        self.assertTrue(enabled.agent_capability().available)
        self.assertEqual(enabled.agent_capability().protocol_revision, "agent-turn-json-v1")

    def test_ollama_request_turn_uses_strict_json_envelope(self):
        response = {
            "message": {
                "content": json.dumps(
                    {
                        "type": "tool",
                        "call_id": "call-1",
                        "name": "lookup_terms",
                        "arguments": {"terms": "bank"},
                    }
                )
            }
        }
        transport = FakeTransport(HttpResponse(200, {}, response))
        backend = OllamaBackend(
            "qwen3.8:27b",
            agent_tools_enabled=True,
            transport=transport,
        )
        request = AgentTurnRequest(
            messages=({"role": "user", "content": "Přelož blok."},),
            tools={"lookup_terms": {"type": "object", "properties": {"terms": {"type": "string"}}}},
            max_output_tokens=300,
        )
        result = backend.request_turn(request)
        self.assertEqual(result.kind, "tool")
        self.assertEqual(result.tool_call.call_id, "call-1")
        payload = transport.calls[0][2]
        self.assertEqual(payload["format"], "json")
        self.assertEqual(payload["options"]["num_predict"], 300)
        self.assertEqual(payload["tools"][0]["name"], "lookup_terms")
        self.assertIn("exactly one JSON object", payload["messages"][0]["content"])
        self.assertEqual(payload["messages"][1]["content"], "Přelož blok.")

    def test_provider_rejects_invalid_request_before_http(self):
        transport = FakeTransport(HttpResponse(200, {}, {"message": {"content": "{}"}}))
        backend = OllamaBackend("qwen3.8:27b", agent_tools_enabled=True, transport=transport)
        with self.assertRaises(BackendError) as error:
            backend.request_turn(object())
        self.assertEqual(error.exception.code, "invalid_schema")
        self.assertEqual(transport.calls, [])


if __name__ == "__main__":
    unittest.main()
