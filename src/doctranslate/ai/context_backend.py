"""Optional provider port for structured, context-aware translation batches."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Mapping, Protocol, Sequence

from .contracts import BackendError
from ..translation.context import ContextEnvelope


@dataclass(frozen=True)
class ContextualCapability:
    available: bool
    reason: str = ""
    prompt_revision: str = "contextual-prompt-v1"


@dataclass(frozen=True)
class ContextualRequest:
    segment_id: str
    text: str
    source_language: str
    target_language: str
    markup: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContextualResult:
    segment_id: str
    text: str
    markup: str | None = None


class ContextualBackend(Protocol):
    """Provider port; legacy AiBackend remains valid without this capability."""

    def contextual_capability(self) -> ContextualCapability:
        ...

    def translate_batch(
        self, requests: Sequence[ContextualRequest], envelope: ContextEnvelope
    ) -> Sequence[ContextualResult]:
        ...


def require_contextual_capability(backend: object) -> ContextualCapability:
    """Reject advanced use explicitly instead of falling back to plain AI."""
    method = getattr(backend, "contextual_capability", None)
    if not callable(method):
        raise BackendError("context_unsupported", "Provider does not support contextual batches")
    capability = method()
    if not isinstance(capability, ContextualCapability):
        raise BackendError("invalid_capability", "Provider returned an invalid contextual capability")
    if not capability.available:
        raise BackendError("context_unsupported", capability.reason or "Contextual batches are unavailable")
    return capability


def decode_contextual_results(
    payload: object, requests: Sequence[ContextualRequest]
) -> tuple[ContextualResult, ...]:
    """Validate provider IDs and restore request order/markup mapping."""
    values = payload.get("segments") if isinstance(payload, dict) else payload
    if not isinstance(values, list):
        raise BackendError("invalid_response", "Contextual provider response must contain a segments list")
    expected = {request.segment_id for request in requests}
    decoded: dict[str, ContextualResult] = {}
    for item in values:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not isinstance(item.get("text"), str):
            raise BackendError("invalid_response", "Contextual provider returned an invalid segment")
        segment_id = item["id"]
        if segment_id not in expected or segment_id in decoded:
            raise BackendError("invalid_response", f"Unexpected or duplicate segment ID: {segment_id}")
        if not item["text"].strip():
            raise BackendError("empty_output", f"Contextual provider returned empty segment: {segment_id}")
        request = next(request for request in requests if request.segment_id == segment_id)
        markup = item.get("markup") if isinstance(item.get("markup"), str) else request.markup
        decoded[segment_id] = ContextualResult(segment_id, item["text"], markup)
    if set(decoded) != expected:
        missing = sorted(expected - set(decoded))
        missing_text = ", ".join(missing)
        raise BackendError(
            "invalid_response", f"Contextual provider omitted segments: {missing_text}"
        )
    return tuple(decoded[request.segment_id] for request in requests)


@dataclass(frozen=True)
class AgentCapability:
    """Explicitly enabled agent-turn capability; model names are not evidence."""

    available: bool
    reason: str = ""
    protocol_revision: str = "agent-turn-json-v1"


@dataclass(frozen=True)
class AgentToolCall:
    call_id: str
    name: str
    arguments: Mapping[str, Any]


@dataclass(frozen=True)
class AgentTurnRequest:
    messages: tuple[Mapping[str, str], ...]
    tools: Mapping[str, Mapping[str, Any]]
    max_output_tokens: int = 2048


@dataclass(frozen=True)
class AgentTurnResponse:
    kind: str
    final_text: str | None = None
    tool_call: AgentToolCall | None = None

    def __post_init__(self) -> None:
        if self.kind == "final":
            if not self.final_text or self.tool_call is not None:
                raise ValueError("final response must contain only final_text")
        elif self.kind == "tool":
            if self.tool_call is None or self.final_text is not None:
                raise ValueError("tool response must contain only tool_call")
        else:
            raise ValueError(f"unknown agent response kind: {self.kind}")


class AgentBackend(Protocol):
    """Optional provider port for one bounded model/tool turn."""

    def agent_capability(self) -> AgentCapability:
        ...

    def request_turn(self, request: AgentTurnRequest) -> AgentTurnResponse:
        ...


def require_agent_capability(backend: object) -> AgentCapability:
    """Reject agent mode unless the provider explicitly enabled and tested it."""
    method = getattr(backend, "agent_capability", None)
    if not callable(method):
        raise BackendError("agent_unsupported", "Provider has no agent-turn capability")
    capability = method()
    if not isinstance(capability, AgentCapability):
        raise BackendError("invalid_capability", "Provider returned an invalid agent capability")
    if not capability.available:
        raise BackendError("agent_unsupported", capability.reason or "Agent turns are unavailable")
    return capability


def decode_agent_turn_response(
    payload: object,
    allowed_tools: Sequence[str],
) -> AgentTurnResponse:
    """Decode the strict JSON envelope and reject hybrid or unknown responses."""
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise BackendError("invalid_response", "Agent response is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise BackendError("invalid_response", "Agent response must be a JSON object")
    allowed = set(allowed_tools)
    if not all(isinstance(item, str) and item.strip() for item in allowed):
        raise BackendError("invalid_schema", "Allowed tool names must be non-empty strings")
    response_type = payload.get("type")
    if response_type == "final":
        if set(payload) != {"type", "text"} or not isinstance(payload.get("text"), str):
            raise BackendError("invalid_response", "Final response must contain only type and text")
        text = payload["text"].strip()
        if not text:
            raise BackendError("empty_output", "Agent final response is empty")
        return AgentTurnResponse("final", final_text=text)
    if response_type == "tool":
        if set(payload) != {"type", "call_id", "name", "arguments"}:
            raise BackendError("invalid_response", "Tool response has an invalid envelope")
        call_id = payload.get("call_id")
        name = payload.get("name")
        arguments = payload.get("arguments")
        if not isinstance(call_id, str) or not call_id.strip():
            raise BackendError("invalid_response", "Tool response call_id is required")
        if not isinstance(name, str) or name not in allowed:
            raise BackendError("unknown_tool", f"Unknown agent tool: {name!r}")
        if not isinstance(arguments, dict):
            raise BackendError("invalid_response", "Tool arguments must be a JSON object")
        if len(json.dumps(arguments, ensure_ascii=False)) > 16384:
            raise BackendError("limit_exceeded", "Tool arguments exceed the bounded envelope")
        return AgentTurnResponse("tool", tool_call=AgentToolCall(call_id.strip(), name, dict(arguments)))
    raise BackendError("invalid_response", "Agent response must be a final or tool envelope")
