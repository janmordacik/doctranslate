"""Optional provider port for structured, context-aware translation batches."""

from __future__ import annotations

from dataclasses import dataclass, field
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
