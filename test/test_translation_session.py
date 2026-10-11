import tempfile
import threading
import unittest
from pathlib import Path

from doctranslate.ai.context_backend import AgentCapability, AgentToolCall, AgentTurnResponse
from doctranslate.translation.context import ContextEnvelope
from doctranslate.translation.memory import JsonGlossaryStore
from doctranslate.translation.session import (
    AgentSegmentRequest,
    AgentSessionBudget,
    AgentSessionError,
    BoundedAgentSession,
)
from doctranslate.translation.tools import MemoryTools


class ScriptedBackend:
    def __init__(self, responses, *, cancel_event=None):
        self.responses = list(responses)
        self.calls = []
        self.cancel_event = cancel_event

    def agent_capability(self):
        return AgentCapability(True)

    def request_turn(self, request):
        self.calls.append(request)
        response = self.responses.pop(0)
        if self.cancel_event is not None:
            self.cancel_event.set()
        return response


class TranslationSessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = JsonGlossaryStore(Path(self.temp.name) / "glossary.json")
        self.tools = MemoryTools(self.store)
        self.context = ContextEnvelope(
            source_text="The orbit is stable.",
            source_language="en",
            target_language="cs",
            instructions="Preserve meaning.",
        )
        self.request = AgentSegmentRequest(
            "s1",
            "The orbit is stable.",
            "en",
            "cs",
            self.context,
            source_markup="<p>The orbit is stable.</p>",
            markup="<p>Oběžná dráha je stabilní.</p>",
        )

    def tearDown(self):
        self.temp.cleanup()

    def session(self, backend, **kwargs):
        return BoundedAgentSession(
            backend,
            self.tools,
            tool_schemas={
                "propose_term": {"type": "object"},
                "search_memory": {"type": "object"},
                "request_revision": {"type": "object"},
            },
            **kwargs,
        )

    def final(self, text):
        return AgentTurnResponse("final", final_text=text)

    def tool(self, name, arguments, call_id="call-1"):
        return AgentTurnResponse(
            "tool",
            tool_call=AgentToolCall(call_id, name, arguments),
        )

    def test_final_turn_returns_checkpointable_segment(self):
        result = self.session(ScriptedBackend([self.final("Oběžná dráha je stabilní.")])).run(self.request)
        self.assertTrue(result.completed)
        self.assertEqual(result.status, "done")
        self.assertEqual(result.turns, 1)
        checkpoint_segment = result.to_validated_segment()
        self.assertEqual(checkpoint_segment.source_markup, "<p>The orbit is stable.</p>")
        self.assertEqual(checkpoint_segment.markup, "<p>Oběžná dráha je stabilní.</p>")

    def test_memory_commit_precedes_checkpoint_and_binds_term(self):
        events = []
        backend = ScriptedBackend(
            [
                self.tool(
                    "propose_term",
                    {
                        "entry": {
                            "source_term": "orbit",
                            "target_term": "oběžná dráha",
                            "source_language": "en",
                            "target_language": "cs",
                        },
                        "evidence": ["s1"],
                        "expected_revision": 0,
                    }
                ),
                self.final("Oběžná dráha je stabilní."),
            ]
        )
        runner = self.session(
            backend,
            on_memory_committed=lambda value: events.append("memory"),
            on_checkpoint=lambda value: events.append("checkpoint"),
        )
        result = runner.run(self.request)
        self.assertTrue(result.completed)
        self.assertEqual(events, ["memory", "checkpoint"])
        self.assertEqual(result.used_memory_revision, 1)
        self.assertEqual(result.dirty_segment_ids, ("s1",))
        self.assertEqual(len(result.term_bindings), 1)
        self.assertEqual(self.store.load().revision, 1)

    def test_repeated_tool_result_stops_without_infinite_loop(self):
        call = {"query": "term that is absent"}
        backend = ScriptedBackend([self.tool("search_memory", call), self.tool("search_memory", call)])
        result = self.session(
            backend,
            budget=AgentSessionBudget(max_turns=6, max_tool_calls=6, max_revisions=1),
        ).run(self.request)
        self.assertEqual(result.status, "unresolved")
        self.assertEqual(result.reason, "stalled")
        self.assertEqual(result.tool_calls, 2)
        self.assertEqual(len(backend.calls), 2)

    def test_tool_budget_stops_before_dispatch(self):
        backend = ScriptedBackend(
            [
                self.tool(
                    "request_revision",
                    {"segment_ids": ["s1"], "reason": "Check terminology"},
                )
            ]
        )
        result = self.session(
            backend,
            budget=AgentSessionBudget(max_turns=2, max_tool_calls=0),
        ).run(self.request)
        self.assertEqual(result.reason, "tool_budget")
        self.assertEqual(self.store.load().revision, 0)

    def test_cancel_after_backend_response_discards_stale_output(self):
        event = threading.Event()
        backend = ScriptedBackend([self.final("stale")], cancel_event=event)
        with self.assertRaises(AgentSessionError) as error:
            self.session(backend).run(self.request, cancel_event=event)
        self.assertEqual(error.exception.code, "cancelled")

    def test_revision_budget_is_enforced(self):
        backend = ScriptedBackend(
            [
                self.tool(
                    "request_revision",
                    {"segment_ids": ["s1"], "reason": "First review"},
                ),
                self.tool(
                    "request_revision",
                    {"segment_ids": ["s1"], "reason": "Second review"},
                ),
            ]
        )
        result = self.session(
            backend,
            budget=AgentSessionBudget(max_turns=4, max_tool_calls=4, max_revisions=1),
        ).run(self.request)
        self.assertEqual(result.reason, "revision_budget")
        self.assertEqual(result.revisions, 1)

    def test_invalid_agent_capability_is_rejected(self):
        class Disabled(ScriptedBackend):
            def agent_capability(self):
                return AgentCapability(False, "not smoke tested")

        with self.assertRaises(Exception):
            self.session(Disabled([])).run(self.request)


if __name__ == "__main__":
    unittest.main()
