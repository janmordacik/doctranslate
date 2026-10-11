"""Bounded per-segment agent session for optional translation revisions."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import time
from typing import Any, Callable, Mapping

from doctranslate.ai.context_backend import (
    AgentBackend,
    AgentTurnRequest,
    AgentTurnResponse,
    require_agent_capability,
)
from doctranslate.translation.checkpoint import ValidatedSegment
from doctranslate.translation.context import ContextEnvelope
from doctranslate.translation.tools import MemoryToolError, MemoryTools


class AgentSessionError(RuntimeError):
    """Typed orchestration error; provider and memory errors stay distinguishable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class AgentSessionBudget:
    max_turns: int = 6
    max_tool_calls: int = 8
    max_revisions: int = 2
    max_seconds: float = 120.0
    max_tokens: int = 12000
    max_output_tokens: int = 2048

    def __post_init__(self) -> None:
        if self.max_turns < 1 or self.max_tool_calls < 0 or self.max_revisions < 0:
            raise ValueError("agent call budgets are invalid")
        if self.max_seconds <= 0 or self.max_tokens < 1 or self.max_output_tokens < 1:
            raise ValueError("agent time and token budgets are invalid")


@dataclass(frozen=True)
class AgentSegmentRequest:
    segment_id: str
    source_text: str
    source_language: str
    target_language: str
    context: ContextEnvelope
    source_markup: str = ""
    markup: str = ""

    def __post_init__(self) -> None:
        if not self.segment_id or not self.source_text.strip():
            raise ValueError("agent segment requires an ID and source text")


@dataclass(frozen=True)
class AgentSessionResult:
    status: str
    segment_id: str
    translated_text: str = ""
    source_text: str = ""
    source_markup: str = ""
    markup: str = ""
    turns: int = 0
    tool_calls: int = 0
    revisions: int = 0
    used_memory_revision: int | None = None
    dirty_segment_ids: tuple[str, ...] = ()
    reason: str = ""
    term_bindings: tuple[str, ...] = ()

    @property
    def completed(self) -> bool:
        return self.status == "done" and bool(self.translated_text.strip())

    def to_validated_segment(self) -> ValidatedSegment:
        if not self.completed:
            raise AgentSessionError("unresolved", "Only a completed session has a checkpoint segment")
        return ValidatedSegment(
            segment_id=self.segment_id,
            source_text=self.source_text,
            text=self.translated_text,
            source_markup=self.source_markup,
            markup=self.markup,
            term_bindings=self.term_bindings,
            provenance={
                "session_status": self.status,
                "turns": self.turns,
                "tool_calls": self.tool_calls,
                "revisions": self.revisions,
                "memory_revision": self.used_memory_revision,
            },
        )


MemoryCommitCallback = Callable[[Any], None]
CheckpointCallback = Callable[[AgentSessionResult], None]


class BoundedAgentSession:
    """Run one segment with a bounded tool loop and no document-wide chat history."""

    def __init__(
        self,
        backend: AgentBackend,
        memory_tools: MemoryTools,
        *,
        budget: AgentSessionBudget | None = None,
        tool_schemas: Mapping[str, Mapping[str, Any]] | None = None,
        on_memory_committed: MemoryCommitCallback | None = None,
        on_checkpoint: CheckpointCallback | None = None,
    ) -> None:
        self.backend = backend
        self.memory_tools = memory_tools
        self.budget = budget or AgentSessionBudget()
        schemas = dict(tool_schemas or {})
        unknown = set(schemas) - set(memory_tools.TOOL_NAMES)
        if unknown:
            raise ValueError(f"unknown managed tool schemas: {sorted(unknown)}")
        self.tool_schemas = schemas
        self.on_memory_committed = on_memory_committed
        self.on_checkpoint = on_checkpoint

    def run(self, request: AgentSegmentRequest, *, cancel_event: Any = None) -> AgentSessionResult:
        require_agent_capability(self.backend)
        started = time.monotonic()
        base_messages = ({"role": "user", "content": self._initial_content(request)},)
        exchange: tuple[Mapping[str, str], ...] = ()
        turns = 0
        tool_calls = 0
        revisions = 0
        token_count = 0
        seen_calls: dict[str, str] = {}
        dirty: set[str] = set(self.memory_tools.dirty_segment_ids)
        memory_revision: int | None = None
        term_bindings: tuple[str, ...] = ()

        while turns < self.budget.max_turns:
            self._check_cancel(cancel_event)
            self._check_time(started)
            messages = base_messages + exchange
            turn_tokens = self._estimate(messages)
            if token_count + turn_tokens > self.budget.max_tokens:
                return self._unresolved(
                    request, turns, tool_calls, revisions, memory_revision, dirty,
                    "token_budget", term_bindings,
                )
            response = self.backend.request_turn(
                AgentTurnRequest(
                    messages=messages,
                    tools=self.tool_schemas,
                    max_output_tokens=self.budget.max_output_tokens,
                )
            )
            self._check_cancel(cancel_event)
            turns += 1
            token_count += turn_tokens + self._estimate(response)
            if token_count > self.budget.max_tokens:
                return self._unresolved(
                    request, turns, tool_calls, revisions, memory_revision, dirty,
                    "token_budget", term_bindings,
                )
            if response.kind == "final":
                return AgentSessionResult(
                    "done", request.segment_id, response.final_text or "",
                    request.source_text, request.source_markup, request.markup,
                    turns, tool_calls, revisions, memory_revision,
                    tuple(sorted(dirty)), "", term_bindings,
                )
            call = response.tool_call
            if call is None:
                raise AgentSessionError("invalid_response", "Agent returned no tool call")
            if tool_calls >= self.budget.max_tool_calls:
                return self._unresolved(
                    request, turns, tool_calls, revisions, memory_revision, dirty,
                    "tool_budget", term_bindings,
                )
            if call.name == "request_revision" and revisions >= self.budget.max_revisions:
                return self._unresolved(
                    request, turns, tool_calls, revisions, memory_revision, dirty,
                    "revision_budget", term_bindings,
                )
            tool_calls += 1
            call_key = json.dumps(
                {"name": call.name, "arguments": call.arguments},
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )
            try:
                result = self.memory_tools.dispatch(call.name, call.arguments)
                result_mapping = self._result_mapping(result)
                serialized = json.dumps(
                    result_mapping, ensure_ascii=False, sort_keys=True, default=str,
                )
                if seen_calls.get(call_key) == serialized:
                    return self._unresolved(
                        request, turns, tool_calls, revisions, memory_revision, dirty,
                        "stalled", term_bindings,
                    )
                seen_calls[call_key] = serialized
                if call.name == "request_revision":
                    revisions += 1
                if isinstance(result_mapping, Mapping):
                    dirty.update(result_mapping.get("dirty_segment_ids", ()))
                    if isinstance(result_mapping.get("revision"), int):
                        memory_revision = result_mapping["revision"]
                    proposal = result_mapping.get("proposal")
                    entry = result_mapping.get("entry")
                    for value in (proposal, entry):
                        if isinstance(value, Mapping) and isinstance(value.get("key"), str):
                            term_bindings = tuple(sorted(set(term_bindings + (value["key"],))))
                if call.name in {"propose_term", "accept_proposal", "reject_proposal"}:
                    if self.on_memory_committed is not None:
                        self.on_memory_committed(result)
                result_message = json.dumps(result_mapping, ensure_ascii=False, sort_keys=True)
            except MemoryToolError as exc:
                result_message = json.dumps({"error": {"code": exc.code, "message": str(exc)}})
                serialized = result_message
                if seen_calls.get(call_key) == serialized:
                    return self._unresolved(
                        request, turns, tool_calls, revisions, memory_revision, dirty,
                        "stalled", term_bindings,
                    )
                seen_calls[call_key] = serialized
            exchange = (
                {"role": "assistant", "content": json.dumps(
                    {"type": "tool", "call_id": call.call_id, "name": call.name,
                     "arguments": dict(call.arguments)},
                    ensure_ascii=False,
                )},
                {"role": "tool", "content": result_message},
                {"role": "user", "content": "Use this bounded result or finish the segment."},
            )
            if self.on_checkpoint is not None:
                self._unresolved(
                    request, turns, tool_calls, revisions, memory_revision, dirty,
                    "pending", term_bindings,
                )
        return self._unresolved(
            request, turns, tool_calls, revisions, memory_revision, dirty,
            "turn_budget", term_bindings,
        )

    @staticmethod
    def _initial_content(request: AgentSegmentRequest) -> str:
        return json.dumps(
            {
                "segment": {
                    "id": request.segment_id,
                    "source_language": request.source_language,
                    "target_language": request.target_language,
                    "text": request.source_text,
                },
                "context": request.context.to_mapping(),
                "instruction": "Translate this segment. Use managed tools only when needed. Return final text in a final envelope.",
            },
            ensure_ascii=False,
            sort_keys=True,
        )

    @staticmethod
    def _result_mapping(value: Any) -> Any:
        method = getattr(value, "to_mapping", None)
        if callable(method):
            return method()
        if isinstance(value, Mapping):
            return dict(value)
        raise AgentSessionError("invalid_tool_result", "Managed tool returned no serializable result")

    def _unresolved(
        self,
        request: AgentSegmentRequest,
        turns: int,
        tool_calls: int,
        revisions: int,
        memory_revision: int | None,
        dirty: set[str],
        reason: str,
        term_bindings: tuple[str, ...],
    ) -> AgentSessionResult:
        result = AgentSessionResult(
            "unresolved",
            request.segment_id,
            source_text=request.source_text,
            source_markup=request.source_markup,
            markup=request.markup,
            turns=turns,
            tool_calls=tool_calls,
            revisions=revisions,
            used_memory_revision=memory_revision,
            dirty_segment_ids=tuple(sorted(dirty)),
            reason=reason,
            term_bindings=term_bindings,
        )
        if self.on_checkpoint is not None:
            self.on_checkpoint(result)
        return result

    def _check_time(self, started: float) -> None:
        if time.monotonic() - started > self.budget.max_seconds:
            raise AgentSessionError("time_budget", "Agent session time budget exceeded")

    @staticmethod
    def _check_cancel(cancel_event: Any) -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise AgentSessionError("cancelled", "Agent session was cancelled")

    @staticmethod
    def _estimate(value: Any) -> int:
        return max(1, (len(json.dumps(value, ensure_ascii=False, default=str)) + 3) // 4)
