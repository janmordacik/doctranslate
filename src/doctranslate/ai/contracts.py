"""Small provider-neutral text translation contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True)
class BackendError(RuntimeError):
    """Safe error crossing the provider boundary."""

    code: str
    message: str
    retryable: bool = False
    request_id: str | None = None
    retry_after: float | None = None
    remedy: str | None = None

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True)
class SegmentRequest:
    """One format-neutral text unit sent to a translation provider."""

    segment_id: str
    text: str
    source_language: str
    target_language: str
    context: str = ""
    markup: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SegmentResult:
    """Provider output tied to the original segment identifier."""

    segment_id: str
    text: str
    markup: str | None = None


class AiBackend(Protocol):
    """Minimal contract used by the document pipeline, independent of format."""

    name: str
    provider_id: str
    model: str

    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """Translate one text value without knowing the source file format."""
        ...

    def translate_segments(
        self,
        requests: Sequence[SegmentRequest],
    ) -> Sequence[SegmentResult]:
        """Translate ordered segments and preserve their identifiers."""
        ...


def normalize_language(value: str) -> str:
    """Return a canonical language tag and reject an empty value."""
    normalized = value.strip().lower().replace("_", "-")
    if not normalized:
        raise ValueError("language must not be empty")
    return normalized
